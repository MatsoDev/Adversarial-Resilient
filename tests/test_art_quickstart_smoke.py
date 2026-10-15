"""Smoke test: tiny synthetic run, FGSM only path, finishes <60s.

Outputs go to pytest's ``tmp_path`` so the test never touches the committed
demo artifacts in ``docs/`` (regression test for the Sprint 1 known issue).
"""

import math


def test_quickstart_synthetic_smoke(tmp_path):
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
