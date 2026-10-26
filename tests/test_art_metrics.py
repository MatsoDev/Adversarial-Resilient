"""Metric-contract tests for the ART demo (no training, no network)."""

from __future__ import annotations

import sys

import numpy as np
from scripts.art_quickstart import cleverhans_check, eval_attack, load_mnist, parse_args


def test_eval_attack_reports_accuracy_asr_and_perturbation_sizes():
    y_true = np.asarray([0, 1, 0, 1])
    y_pred = np.asarray([0, 0, 1, 1])
    x_orig = np.zeros((4, 1, 2, 2), dtype=np.float32)
    x_adv = x_orig.copy()
    x_adv[0, 0, 0, 0] = 3.0
    x_adv[0, 0, 0, 1] = 4.0
    x_adv[1, 0, 0, 0] = -2.0
    x_adv[3, 0, 1, 1] = 1.0
    original_adv = x_adv.copy()

    result = eval_attack(y_true, y_pred, x_orig, x_adv, eps=0.3)

    assert result["eps"] == 0.3
    assert result["adv_accuracy"] == 0.5
    assert result["attack_success_rate"] == 0.5
    assert result["mean_l2"] == 2.0
    assert result["mean_linf"] == 1.75
    np.testing.assert_array_equal(x_adv, original_adv)


def test_parse_args_defaults_match_the_documented_demo_contract():
    args = parse_args([])
    assert args.fast is False
    assert args.synthetic is False
    assert args.epochs is None
    assert args.eps == 0.3
    assert args.seed == 42
    assert args.cw_samples is None
    assert args.cleverhans is False


def test_synthetic_mnist_is_deterministic_and_shaped_without_downloading():
    train_loader, test_loader, x_test, y_test = load_mnist(fast=True, synthetic=True)
    _, _, x_test_again, y_test_again = load_mnist(fast=True, synthetic=True)

    np.testing.assert_array_equal(x_test, x_test_again)
    np.testing.assert_array_equal(y_test, y_test_again)
    assert x_test.shape == (64, 1, 28, 28)
    assert x_test.dtype == np.float32
    assert y_test.shape == (64,)
    assert set(np.unique(y_test)).issubset(set(range(10)))
    assert x_test.min() >= 0.0 and x_test.max() <= 1.0

    xb, yb = next(iter(train_loader))
    assert tuple(xb.shape) == (64, 1, 28, 28)
    assert tuple(yb.shape) == (64,)
    xb_test, yb_test = next(iter(test_loader))
    assert tuple(xb_test.shape) == (64, 1, 28, 28)
    assert tuple(yb_test.shape) == (64,)


def test_cleverhans_check_skips_gracefully_when_the_optional_dependency_is_missing(
    monkeypatch,
):
    monkeypatch.setitem(sys.modules, "cleverhans", None)
    result = cleverhans_check(None, np.zeros((1, 1, 28, 28)), np.zeros(1), 0.1)
    assert result["skipped"] is True
    assert "cleverhans" in result["reason"].lower()
