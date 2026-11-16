"""Synthetic ART demo with outputs isolated from committed artifacts via ``tmp_path``."""

import math

import pytest


def test_quickstart_synthetic_smoke(tmp_path):
    from mlflow.tracking import MlflowClient
    from scripts.art_quickstart import parse_args, run_demo

    args = parse_args(["--synthetic", "--epochs", "1", "--eps", "0.1", "--seed", "0"])
    results = run_demo(args, output_dir=tmp_path)
    assert math.isfinite(results["clean_accuracy"])
    assert "fgsm" in results["attacks"]
    fgsm = results["attacks"]["fgsm"]
    for k in ("adv_accuracy", "attack_success_rate", "mean_l2", "mean_linf"):
        assert math.isfinite(fgsm[k]), k
    assert len(results["accuracy_vs_eps"]) >= 2
    assert (tmp_path / "results" / "art_quickstart_results.json").exists()
    assert (tmp_path / "figures" / "art_samples.png").exists()
    assert (tmp_path / "figures" / "art_accuracy_vs_eps.png").exists()

    client = MlflowClient(tracking_uri=(tmp_path / "mlruns").as_uri())
    experiment = client.get_experiment_by_name("art_quickstart")
    runs = client.search_runs([experiment.experiment_id])
    assert len(runs) == 1
    for name, metrics in results["attacks"].items():
        if metrics.get("failed"):
            continue
        asr = metrics["attack_success_rate"]
        if metrics["clean_accuracy_subset"] == 0:
            assert asr is None
            assert f"{name}_asr" not in runs[0].data.metrics
        else:
            assert 0 <= asr <= 1
            assert runs[0].data.metrics[f"{name}_asr"] == pytest.approx(asr)
