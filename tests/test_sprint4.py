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


def test_api_prediction_validation_and_auth(frozen, monkeypatch):
    root, report = frozen
    monkeypatch.delenv("PREDICTION_API_TOKEN", raising=False)
    client = TestClient(create_app(baseline_dir=root))
    assert client.post("/predict").status_code == 503
    monkeypatch.setenv("PREDICTION_API_TOKEN", "x" * 32)
    assert client.get("/v1/baseline").status_code == 401
    client.headers["Authorization"] = "Bearer " + "x" * 32
    identity = client.get("/v1/baseline")
    assert identity.status_code == 200
    payload = dict(
        model_version="baseline_v1",
        representation="raw",
        preprocessing_id=report["preprocessing_sha256"],
        feature_schema_sha256=report["feature_schema_sha256"],
        rows=[[0] * 2381],
    )
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert response.json()["score_type"] == "temperature_calibrated_probability"
    assert response.headers["cache-control"] == "no-store"
    for change in (
        {"rows": []},
        {"rows": [[0]]},
        {"rows": [[True] * 2381]},
        {"rows": [["0"] * 2381]},
        {"rows": [[1e31] * 2381]},
        {"preprocessing_id": "0" * 64},
        {"feature_schema_sha256": "0" * 64},
        {"representation": "unknown"},
        {"model_version": "candidate"},
        {"path": "/tmp/model.pt"},
        {"rows": [[0] * 2381] * 33},
    ):
        assert client.post("/predict", json={**payload, **change}).status_code == 422
    assert (
        client.post("/predict", content=b"{}", headers={"Content-Type": "text/plain"}).status_code
        == 415
    )
    assert (
        client.post(
            "/predict",
            content=b"x" * (2 * 1024 * 1024 + 1),
            headers={"Content-Type": "application/json"},
        ).status_code
        == 413
    )
    assert (
        client.post(
            "/predict", content=b'{"rows": NaN}', headers={"Content-Type": "application/json"}
        ).status_code
        == 422
    )
    for _ in range(31):
        response = client.get("/v1/baseline")
    assert response.status_code == 429


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
