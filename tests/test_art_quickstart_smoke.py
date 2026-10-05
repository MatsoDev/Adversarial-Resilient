"""Smoke test: tiny synthetic run, FGSM only path, finishes <60s."""

import math


def test_quickstart_synthetic_smoke():
    from scripts.art_quickstart import parse_args, run_demo

    args = parse_args(["--synthetic", "--epochs", "1", "--eps", "0.1", "--seed", "0"])
    results = run_demo(args)
    assert math.isfinite(results["clean_accuracy"])
    assert "fgsm" in results["attacks"]
    fgsm = results["attacks"]["fgsm"]
    for k in ("adv_accuracy", "attack_success_rate", "mean_l2", "mean_linf"):
        assert math.isfinite(fgsm[k]), k
    assert len(results["accuracy_vs_eps"]) >= 2
