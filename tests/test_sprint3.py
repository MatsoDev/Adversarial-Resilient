"""Sprint 3 training integrity, metric correctness and HTTP contracts."""

import json
from pathlib import Path

import numpy as np
import pytest
from api.main import create_app
from fastapi.testclient import TestClient
from src.data.preprocessing import sha256_file
from src.evaluation.artifacts import ArtifactStore, ArtifactUnavailable
from src.evaluation.binary import binary_metrics, threshold_at_tpr
from src.models.training import MODEL_NAMES, TrainingConfig, train_baselines


@pytest.fixture
def processed(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    rng = np.random.default_rng(42)
    for split, rows in (("train", 40), ("val", 20)):
        y = np.tile([0, 1], rows // 2).astype(np.int8)
        X = rng.normal(size=(rows, 6)).astype(np.float32)
        X[:, 0] = y * 5
        np.save(root / f"{split}_X.npy", X)
        np.save(root / f"{split}_y.npy", y)
    (root / "feature_names.json").write_text(json.dumps([f"f{i}" for i in range(6)]))
    (root / "label_mapping.json").write_text('{"0": "benign", "1": "malicious"}')
    artifacts = {
        p.stem: {"file": p.name, "sha256": sha256_file(p), "size_bytes": p.stat().st_size}
        for p in root.iterdir()
    }
    (root / "manifest.json").write_text(
        json.dumps({"dataset": "ember2018", "subset": True, "artifacts": artifacts})
    )
    return root


@pytest.fixture
def trained(processed, tmp_path):
    docs = tmp_path / "docs"
    report = train_baselines(
        processed,
        config=TrainingConfig(
            max_train=24, max_val=16, hidden=(8,), epochs=2, trees=5, batch_size=8
        ),
        results_dir=docs / "results/baselines",
        model_dir=tmp_path / "models",
        log_mlflow=False,
    )
    return docs, report


def test_four_models_train_without_test_files_and_reproduce(trained, processed, tmp_path):
    docs, result = trained
    assert {r["model"] for r in result["runs"]} == set(MODEL_NAMES)
    assert len(ArtifactStore(docs).runs()["runs"]) == 4
    for run in result["runs"]:
        assert run["test_evaluated"] is False
        assert run["evaluation_split"] == "val"
        assert run["train_rows"] == 24 and run["val_rows"] == 16
        assert 0 <= run["metrics"]["accuracy"] <= 1
    again = train_baselines(
        processed,
        config=TrainingConfig(
            max_train=24, max_val=16, hidden=(8,), epochs=2, trees=5, batch_size=8
        ),
        results_dir=tmp_path / "again",
        model_dir=tmp_path / "again_models",
        log_mlflow=False,
    )
    assert [r["metrics"] for r in result["runs"]] == [r["metrics"] for r in again["runs"]]
    # Scaler uses selected training rows only, independent of validation shifts.
    from src.models.training import _sample

    selected, _, _ = _sample(
        np.load(processed / "train_X.npy"), np.load(processed / "train_y.npy"), 24, 42
    )
    stats = np.load(tmp_path / "models" / result["batch_id"] / "scaler.npz")
    np.testing.assert_allclose(stats["mean"], selected.mean(axis=0), atol=1e-6)


def test_tampered_data_is_rejected_before_training(processed, tmp_path):
    with (processed / "train_X.npy").open("ab") as handle:
        handle.write(b"tampered")
    with pytest.raises(ValueError, match="verification failed"):
        train_baselines(processed, results_dir=tmp_path / "results", model_dir=tmp_path / "models")
    assert not (tmp_path / "models").exists()


def test_metrics_and_validation_threshold():
    y = np.array([0, 0, 1, 1])
    scores = np.array([0.1, 0.6, 0.4, 0.9])
    metrics = binary_metrics(y, scores, 0.5)
    assert metrics["confusion_matrix"] == [[1, 1], [1, 1]]
    assert metrics["accuracy"] == 0.5
    assert metrics["roc_auc"] == 0.75
    assert threshold_at_tpr(y, scores, 1) == 0.4
    assert binary_metrics(np.array([0, 0]), np.array([0.2, 0.1]), 0.5)["roc_auc"] is None
    with pytest.raises(ValueError):
        binary_metrics(y, np.array([0, np.nan, 1, 1]), 0.5)


def test_http_routes_isolated_and_safe(trained):
    docs, result = trained
    client = TestClient(create_app(ArtifactStore(docs)))
    response = client.get("/v1/runs")
    assert response.status_code == 200
    assert response.json()["runs"] == json.loads(json.dumps(result["runs"]))
    assert response.headers["cache-control"] == "no-store"
    assert client.get("/v1/datasets/no-such-dataset").status_code == 404
    assert client.get("/v1/datasets/ember2018").status_code == 503
    assert client.get("/v1/reports/unknown").status_code == 404
    assert "Traceback" not in client.get("/v1/demo").text


def test_invalid_batches_and_outside_paths_are_rejected(trained, tmp_path):
    docs, result = trained
    result["runs"][0]["metrics"]["accuracy"] = 20
    (docs / "results/baselines/bad.json").write_text(json.dumps(result))
    assert ArtifactStore(docs).runs()["unavailable_batches"] == 1
    outside = tmp_path / "private.txt"
    outside.write_text("private")
    with pytest.raises(ArtifactUnavailable):
        ArtifactStore(docs).read("../private.txt")
    (docs / "results/baselines/nan.json").write_text('{"value":NaN}')
    with pytest.raises(ArtifactUnavailable):
        ArtifactStore(docs).json("results/baselines/nan.json")


def test_real_committed_report_contracts():
    store = ArtifactStore()
    for name in ("ember2018", "cicids2017"):
        assert store.dataset(name)["local_verification"] == "not_checked"
    assert store.demo()["dataset"] == "MNIST"
    assert store.figure("art_samples")["png_base64"]


def test_models_page_renders_measured_results(trained, monkeypatch):
    import dashboard.client as client
    from streamlit.testing.v1 import AppTest

    docs, result = trained
    monkeypatch.setattr(client, "fetch_json", lambda url, endpoint: ArtifactStore(docs).runs())
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "dashboard/app.py"), default_timeout=15
    ).run()
    app.radio[0].set_value("Models").run()
    assert not app.exception
    assert app.metric[0].value == f"{result['runs'][0]['metrics']['accuracy']:.2%}"
    app.selectbox[1].set_value("mlp").run()
    assert not app.exception
    assert any(h.value == "MLP learning curve" for h in app.subheader)


def test_mlflow_run_and_checkpoint_written(processed, tmp_path):
    import os

    import mlflow

    tracking = tmp_path / "tracking"
    result = train_baselines(
        processed,
        config=TrainingConfig(max_train=24, max_val=16),
        models=("logistic_regression",),
        results_dir=tmp_path / "results",
        model_dir=tmp_path / "models",
        tracking_uri=tracking.as_uri(),
    )
    run_id = result["runs"][0]["mlflow_run_id"]
    assert run_id
    client = mlflow.tracking.MlflowClient(tracking_uri=tracking.as_uri())
    assert client.get_run(run_id).info.status == "FINISHED"
    assert (tmp_path / "models" / result["batch_id"] / "logistic_regression.joblib").is_file()
    os.environ.pop("MLFLOW_TRACKING_URI", None)


def test_training_cli_success_and_missing_inputs(processed, tmp_path):
    from scripts.train_baselines import main

    args = [
        "--data-dir",
        str(processed),
        "--models",
        "logistic_regression",
        "--no-mlflow",
        "--results-dir",
        str(tmp_path / "cli_results"),
        "--model-dir",
        str(tmp_path / "cli_models"),
    ]
    assert main(args) == 0
    reports = list((tmp_path / "cli_results").glob("*.json"))
    assert len(reports) == 1
    assert json.loads(reports[0].read_text())["runs"][0]["test_evaluated"] is False
    assert main(["--data-dir", str(tmp_path / "missing"), "--no-mlflow"]) == 1
