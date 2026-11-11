"""Synthetic Sprint 4 protocol, freeze, integrity and bounded HTTP regression tests."""

import json

import numpy as np
import pytest
import torch
from api.main import create_app
from fastapi.testclient import TestClient
from src.data.preprocessing import sha256_file, write_json_atomic
from src.models.frozen import FrozenBaseline, transform
from src.models.tabular import TabularCNN
from src.models.tuning import (
    Trial,
    default_trials,
    fit_temperature,
    probability_metrics,
    tune_baseline,
    validation_partitions,
)


@pytest.fixture
def ember(tmp_path):
    root = tmp_path / "ember"
    root.mkdir()
    rng = np.random.default_rng(42)
    for name, count in (("train", 48), ("val", 64), ("test", 32)):
        y = np.tile([0, 1], count // 2).astype(np.int8)
        X = rng.normal(size=(count, 2381)).astype(np.float32)
        X[:, 0] = (y * 2 - 1).astype(np.float32)
        X[:, 1] *= 1e20  # finite heavy tails must not produce exploding BCE.
        np.save(root / f"{name}_X.npy", X)
        np.save(root / f"{name}_y.npy", y)
    write_json_atomic(root / "feature_names.json", [f"f{i}" for i in range(2381)])
    write_json_atomic(root / "label_mapping.json", {"0": "benign", "1": "malicious"})
    manifest = {
        "dataset": "ember2018",
        "subset": True,
        "artifacts": {
            p.stem: {"file": p.name, "sha256": sha256_file(p), "size_bytes": p.stat().st_size}
            for p in root.iterdir()
        },
    }
    write_json_atomic(root / "manifest.json", manifest)
    return root


def test_validation_partitions_and_temperature():
    y = np.tile([0, 1], 100)
    parts = validation_partitions(y, 42)
    assert [len(p) for p in parts] == [100, 50, 50]
    assert len(set(np.concatenate(parts))) == len(y)
    assert all(set(y[p]) == {0, 1} for p in parts)
    assert all(
        np.array_equal(a, b) for a, b in zip(parts, validation_partitions(y, 42), strict=True)
    )
    logits = np.where(y, 8.0, -8.0)
    logits[::5] *= -1
    temperature = fit_temperature(logits, y)
    assert temperature > 1
    assert (
        probability_metrics(y, logits, temperature)["log_loss"]
        < probability_metrics(y, logits, 1)["log_loss"]
    )
    assert len(default_trials()) == 6
    assert TabularCNN()(torch.zeros(2, 2381)).shape == (2,)


def test_subset_search_never_opens_test_and_reproduces(ember, tmp_path):
    (ember / "test_X.npy").unlink()
    args = dict(trials=(Trial(hidden=(8,), epochs=2, batch_size=16),), log_mlflow=False)
    first = tune_baseline(ember, tmp_path / "first", **args)
    second = tune_baseline(ember, tmp_path / "second", **args)
    assert first["status"] == "blocked_subset" and not first["test_evaluated"]
    for a, b in zip(first["trials"], second["trials"], strict=True):
        assert {k: v for k, v in a.items() if k != "training_seconds"} == {
            k: v for k, v in b.items() if k != "training_seconds"
        }
    assert first["temperature"] == second["temperature"]
    assert first["calibration"]["after"]["log_loss"] <= first["calibration"]["before"]["log_loss"]
    assert first["train_raw_max_abs"] > 1e20
    with pytest.raises(ValueError, match="No frozen"):
        FrozenBaseline(tmp_path / "first")
    candidate = FrozenBaseline(tmp_path / "first", require_frozen=False)
    train_rows = np.load(ember / "train_X.npy").astype(np.float64)
    logged_train = np.sign(train_rows) * np.log1p(np.abs(train_rows))
    np.testing.assert_allclose(candidate.mean, logged_train.mean(axis=0), atol=1e-10)
    rows = np.load(ember / "val_X.npy")[:2]
    kwargs = dict(
        preprocessing_id=first["preprocessing_sha256"], schema_id=first["feature_schema_sha256"]
    )
    raw = candidate.predict(rows, representation="raw", **kwargs)
    scaled = candidate.predict(
        transform(rows, candidate.mean, candidate.scale), representation="scaled", **kwargs
    )
    assert raw["predictions"] == scaled["predictions"]
    with pytest.raises(FileExistsError):
        tune_baseline(ember, tmp_path / "first", **args)


@pytest.fixture
def frozen(ember, tmp_path, monkeypatch):
    # Protocol-only fixture: known perfect synthetic logits, never research evidence.
    import src.models.tuning as tuning

    path = ember / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["subset"] = False
    write_json_atomic(path, manifest)
    monkeypatch.setattr(
        tuning, "logits_for", lambda model, X, indices, mean, scale: np.asarray(X[indices, 0]) * 5
    )
    out = tmp_path / "frozen"
    report = tune_baseline(
        ember, out, trials=(Trial(hidden=(8,), epochs=1, batch_size=16),), log_mlflow=False
    )
    assert report["status"] == "frozen" and report["test_evaluated"]
    assert report["test_operating_point"]["threshold"] == report["operating_threshold"]
    return out, report


def test_full_gate_and_bundle_integrity(frozen):
    root, report = frozen
    baseline = FrozenBaseline(root)
    assert baseline.record["model_version"] == "baseline_v1"
    with (root / "weights.pt").open("ab") as handle:
        handle.write(b"tampered")
    with pytest.raises(ValueError, match="integrity"):
        FrozenBaseline(root)
    assert report["test_metrics"]["accuracy"] == 1


def test_failed_full_validation_gate_does_not_open_test(ember, tmp_path, monkeypatch):
    import src.models.tuning as tuning

    manifest = json.loads((ember / "manifest.json").read_text())
    manifest["subset"] = False
    write_json_atomic(ember / "manifest.json", manifest)
    (ember / "test_X.npy").unlink()
    monkeypatch.setattr(
        tuning,
        "logits_for",
        lambda model, X, indices, mean, scale: np.zeros(len(indices), dtype=np.float32),
    )
    report = tune_baseline(
        ember, tmp_path / "blocked", trials=(Trial(hidden=(8,), epochs=1),), log_mlflow=False
    )
    assert report["status"] == "blocked_validation_accuracy"
    assert not report["test_evaluated"]


def test_api_prediction_disabled_and_auth(frozen, monkeypatch):
    root, report = frozen
    monkeypatch.delenv("PREDICTION_API_TOKEN", raising=False)
    client = TestClient(create_app(baseline_dir=root))
    assert client.post("/predict").status_code == 503
    monkeypatch.setenv("PREDICTION_API_TOKEN", "x" * 32)
    assert client.get("/v1/baseline").status_code == 401
    client.headers["Authorization"] = "Bearer " + "x" * 32
    identity = client.get("/v1/baseline")
    assert identity.status_code == 200
    assert identity.json()["preprocessing_sha256"] == report["preprocessing_sha256"]
    assert identity.json()["feature_count"] == 2381
    assert identity.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "change",
    [
        pytest.param({"rows": []}, id="empty-batch"),
        pytest.param({"rows": [[0]]}, id="wrong-dimension"),
        pytest.param({"rows": [[True] * 2381]}, id="boolean-features"),
        pytest.param({"rows": [["0"] * 2381]}, id="string-features"),
        pytest.param({"rows": [[1e31] * 2381]}, id="raw-overflow"),
        pytest.param({"preprocessing_id": "0" * 64}, id="wrong-preprocessing"),
        pytest.param({"feature_schema_sha256": "0" * 64}, id="wrong-schema"),
        pytest.param({"representation": "unknown"}, id="unknown-representation"),
        pytest.param({"model_version": "candidate"}, id="unfrozen-version"),
        pytest.param({"path": "/tmp/model.pt"}, id="extra-path"),
        pytest.param({"rows": [[0] * 2381] * 33}, id="oversized-batch"),
    ],
)
def test_api_prediction_rejects_invalid_payload(prediction_client, change):
    client, payload = prediction_client
    response = client.post("/predict", json={**payload, **change})
    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    assert "Traceback" not in response.text


@pytest.mark.parametrize(
    ("body", "content_type", "status"),
    [
        pytest.param(b"{}", "text/plain", 415, id="non-json"),
        pytest.param(b"x" * (2 * 1024 * 1024 + 1), "application/json", 413, id="body-limit"),
        pytest.param(b'{"rows": NaN}', "application/json", 422, id="nonfinite-json"),
        pytest.param(b"{", "application/json", 422, id="malformed-json"),
        pytest.param(b"\xff", "application/json", 422, id="invalid-encoding"),
    ],
)
def test_api_prediction_rejects_invalid_bodies(prediction_client, body, content_type, status):
    client, _ = prediction_client
    response = client.post("/predict", content=body, headers={"Content-Type": content_type})
    assert response.status_code == status
    assert response.headers["cache-control"] == "no-store"


def test_missing_bundle_and_invalid_config(tmp_path, monkeypatch):
    monkeypatch.setenv("PREDICTION_API_TOKEN", "x" * 32)
    client = TestClient(create_app(baseline_dir=tmp_path / "missing"))
    response = client.get("/v1/baseline", headers={"Authorization": "Bearer " + "x" * 32})
    assert response.status_code == 503 and "Traceback" not in response.text
    for trial in (Trial(architecture="rf"), Trial(dropout=float("nan")), Trial(batch_size=1)):
        with pytest.raises(ValueError):
            trial.validate()


def test_test_accuracy_gate_cannot_freeze(ember, tmp_path, monkeypatch):
    import src.models.tuning as tuning

    path = ember / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["subset"] = False
    write_json_atomic(path, manifest)

    def logits(model, X, indices, mean, scale):
        sign = -1 if str(getattr(X.base, "filename", "")).endswith("test_X.npy") else 1
        return sign * np.asarray(X[indices, 0]) * 5

    monkeypatch.setattr(tuning, "logits_for", logits)
    root = tmp_path / "test_miss"
    report = tune_baseline(ember, root, trials=(Trial(hidden=(8,), epochs=1),), log_mlflow=False)
    assert report["test_evaluated"] and report["status"] == "blocked_test_accuracy"
    assert report["test_metrics"]["accuracy"] == 0
    with pytest.raises(ValueError, match="No frozen"):
        FrozenBaseline(root)


def test_manifest_tamper_rejected_before_output(ember, tmp_path):
    with (ember / "train_X.npy").open("ab") as handle:
        handle.write(b"tampered")
    out = tmp_path / "not_created"
    with pytest.raises(ValueError, match="verification"):
        tune_baseline(ember, out, log_mlflow=False)
    assert not out.exists()


def test_bundle_metadata_identity_and_subset_gates(frozen):
    root, report = frozen
    for change in (
        {"subset": True},
        {"preprocessing_sha256": "0" * 64},
        {"test_evaluated": False},
        {"temperature": -1},
        {"test_metrics": {"accuracy": 0.92}},
    ):
        write_json_atomic(root / "bundle.json", {**report, **change})
        with pytest.raises(ValueError):
            FrozenBaseline(root)


def test_cli_subset_exit_and_mlflow_record(ember, tmp_path):
    import os

    import mlflow
    from scripts.tune_baseline import main

    out = tmp_path / "cli"
    published = tmp_path / "report.json"
    assert (
        main(
            [
                "--data-dir",
                str(ember),
                "--output-dir",
                str(out),
                "--epochs",
                "1",
                "--no-mlflow",
                "--report",
                str(published),
            ]
        )
        == 2
    )
    assert json.loads(published.read_text())["status"] == "blocked_subset"
    tracking = tmp_path / "tracking"
    report = tune_baseline(
        ember,
        tmp_path / "tracked",
        trials=(Trial(hidden=(8,), epochs=1),),
        tracking_uri=tracking.as_uri(),
    )
    client = mlflow.tracking.MlflowClient(tracking_uri=tracking.as_uri())
    assert client.get_run(report["mlflow_run_id"]).info.status == "FINISHED"
    os.environ.pop("MLFLOW_TRACKING_URI", None)


def test_cli_missing_inputs(tmp_path):
    from scripts.tune_baseline import main

    assert main(["--data-dir", str(tmp_path / "missing"), "--no-mlflow"]) == 1


@pytest.mark.parametrize(
    "artifact", ["train_X", "train_y", "val_X", "val_y", "feature_names", "label_mapping"]
)
def test_tuning_requires_every_training_digest_before_creating_output(ember, tmp_path, artifact):
    path = ember / "manifest.json"
    manifest = json.loads(path.read_text())
    del manifest["artifacts"][artifact]["sha256"]
    write_json_atomic(path, manifest)
    out = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="SHA-256"):
        tune_baseline(ember, out, trials=(Trial(hidden=(8,), epochs=1),), log_mlflow=False)
    assert not out.exists()


@pytest.mark.parametrize("digest", [None, "", "0" * 63, "z" * 64, 123])
def test_tuning_rejects_malformed_integrity_digests(ember, tmp_path, digest):
    path = ember / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["artifacts"]["train_X"]["sha256"] = digest
    write_json_atomic(path, manifest)
    out = tmp_path / "must-not-exist"
    with pytest.raises(ValueError):
        tune_baseline(ember, out, trials=(Trial(hidden=(8,), epochs=1),), log_mlflow=False)
    assert not out.exists()


@pytest.mark.parametrize("artifact", ["test_X", "test_y"])
def test_test_integrity_failure_keeps_selection_locked_without_freezing(
    frozen, ember, tmp_path, artifact
):
    path = ember / "manifest.json"
    manifest = json.loads(path.read_text())
    del manifest["artifacts"][artifact]["sha256"]
    write_json_atomic(path, manifest)
    out = tmp_path / "locked"
    with pytest.raises(ValueError, match="verification failed"):
        tune_baseline(ember, out, trials=(Trial(hidden=(8,), epochs=1),), log_mlflow=False)
    selection = json.loads((out / "selection.json").read_text())
    assert selection["test_evaluated"] is False
    assert selection["model_version"] == "sprint4_candidate"
    assert not (out / "bundle.json").exists()


@pytest.mark.parametrize("artifact", ["weights", "scaler", "features"])
def test_frozen_bundle_requires_every_integrity_digest(frozen, artifact):
    root, report = frozen
    del report["artifacts"][artifact]["sha256"]
    write_json_atomic(root / "bundle.json", report)
    with pytest.raises(ValueError, match="integrity"):
        FrozenBaseline(root)


@pytest.fixture
def prediction_client(frozen, monkeypatch):
    root, report = frozen
    monkeypatch.setenv("PREDICTION_API_TOKEN", "x" * 32)
    monkeypatch.setenv("API_ALLOWED_HOSTS", "testserver")
    payload = {
        "model_version": "baseline_v1",
        "representation": "raw",
        "preprocessing_id": report["preprocessing_sha256"],
        "feature_schema_sha256": report["feature_schema_sha256"],
        "rows": [[0] * 2381],
    }
    with TestClient(create_app(baseline_dir=root)) as client:
        client.headers["Authorization"] = "Bearer " + "x" * 32
        yield client, payload


@pytest.fixture
def prediction_clock(monkeypatch):
    from types import SimpleNamespace

    import api.prediction as prediction

    now = [100.0]
    # Replace this module's clock, not the process-wide time module used by async I/O.
    monkeypatch.setattr(prediction, "time", SimpleNamespace(monotonic=lambda: now[0]))
    return now


def test_prediction_budget_is_shared_by_routes_and_resets_at_60_seconds(
    prediction_client, prediction_clock
):
    client, payload = prediction_client
    now = prediction_clock
    for _ in range(15):
        assert client.get("/v1/baseline").status_code == 200
        assert client.post("/predict", json=payload).status_code == 200
    now[0] = 159.999
    exhausted = client.post("/predict", json=payload)
    assert exhausted.status_code == 429
    assert exhausted.headers["retry-after"] == "60"
    assert exhausted.headers["cache-control"] == "no-store"
    now[0] = 160.0
    assert client.post("/predict", json=payload).status_code == 200


def test_forwarding_headers_cannot_bypass_prediction_budget(prediction_client, prediction_clock):
    client, _ = prediction_client
    for number in range(30):
        response = client.get("/v1/baseline", headers={"X-Forwarded-For": f"192.0.2.{number}"})
        assert response.status_code == 200
    response = client.get(
        "/v1/baseline", headers={"X-Forwarded-For": "198.51.100.1", "Forwarded": "for=198.51.100.1"}
    )
    assert response.status_code == 429


def test_unauthorized_requests_do_not_consume_authenticated_budget(
    prediction_client, prediction_clock
):
    client, _ = prediction_client
    for _ in range(31):
        response = client.get("/v1/baseline", headers={"Authorization": "Bearer wrong"})
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
    for _ in range(30):
        assert client.get("/v1/baseline").status_code == 200
    assert client.get("/v1/baseline").status_code == 429


def test_prediction_budget_isolated_by_socket_peer(prediction_client, prediction_clock):
    first, _ = prediction_client
    for _ in range(30):
        assert first.get("/v1/baseline").status_code == 200
    assert first.get("/v1/baseline").status_code == 429
    with TestClient(first.app, client=("192.0.2.1", 45000)) as second:
        second.headers["Authorization"] = first.headers["Authorization"]
        assert second.get("/v1/baseline").status_code == 200
    assert first.get("/v1/baseline").status_code == 429


@pytest.mark.parametrize(("representation", "bound"), [("raw", 1e30), ("scaled", 1e6)])
def test_prediction_numeric_bounds_are_inclusive(prediction_client, representation, bound):
    client, payload = prediction_client
    payload["representation"] = representation
    for value, expected in ((bound, 200), (-bound, 200), (bound * 1.01, 422), (-bound * 1.01, 422)):
        payload["rows"][0][0] = value
        assert client.post("/predict", json=payload).status_code == expected


@pytest.mark.parametrize(("score", "label"), [(0.25, 0), (0.5, 1), (0.75, 1)])
def test_http_predictions_match_known_calibrated_logits_for_maximum_batch(
    frozen, monkeypatch, score, label
):
    root, report = frozen
    # Write a real, constant-logit neural checkpoint with a known temperature.
    baseline = FrozenBaseline(root)
    with torch.no_grad():
        for parameter in baseline.model.parameters():
            parameter.zero_()
        baseline.model.net[-1].bias.fill_(2 * np.log(score / (1 - score)))
    torch.save(baseline.model.state_dict(), root / "weights.pt")
    report["temperature"] = 2.0
    report["artifacts"]["weights"].update(
        sha256=sha256_file(root / "weights.pt"), size_bytes=(root / "weights.pt").stat().st_size
    )
    write_json_atomic(root / "bundle.json", report)
    monkeypatch.setenv("PREDICTION_API_TOKEN", "x" * 32)
    with TestClient(create_app(baseline_dir=root)) as client:
        response = client.post(
            "/predict",
            headers={"Authorization": "Bearer " + "x" * 32},
            json={
                "model_version": "baseline_v1",
                "representation": "scaled",
                "preprocessing_id": report["preprocessing_sha256"],
                "feature_schema_sha256": report["feature_schema_sha256"],
                "rows": [[0] * 2381 for _ in range(32)],
            },
        )
    assert response.status_code == 200
    result = response.json()
    assert result["model_version"] == "baseline_v1"
    assert result["threshold"] == 0.5
    assert result["preprocessing_id"] == report["preprocessing_sha256"]
    assert result["feature_schema_sha256"] == report["feature_schema_sha256"]
    assert result["score_type"] == "temperature_calibrated_probability"
    assert len(result["predictions"]) == 32
    for prediction in result["predictions"]:
        assert prediction == {"label": label, "score": pytest.approx(score, abs=1e-7)}
    assert np.isfinite(result["latency_ms"]) and result["latency_ms"] >= 0
