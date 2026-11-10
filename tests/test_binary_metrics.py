"""Hand-computed metric contracts, including thresholds hidden by ROC simplification."""

import numpy as np
import pytest
from src.evaluation.binary import binary_metrics, threshold_at_tpr


@pytest.mark.parametrize(("target", "expected"), [(0.25, 0.8), (0.5, 0.7), (0.75, 0.6), (1, 0.5)])
def test_highest_threshold_is_not_lost_on_vertical_roc_segment(target, expected):
    y = np.array([0, 1, 1, 1, 1, 0])
    scores = np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.1])
    threshold = threshold_at_tpr(y, scores, target)
    assert threshold == expected
    assert binary_metrics(y, scores, threshold)["recall"] == target


def test_default_95_percent_tpr_does_not_round_up_to_all_positives():
    y = np.array([0] + [1] * 20 + [0])
    scores = np.array([100] + list(range(20, 0, -1)) + [0])
    assert threshold_at_tpr(y, scores) == 2


def test_tied_scores_are_included_together_and_threshold_is_order_independent():
    y = np.array([0, 1, 0, 1, 1])
    scores = np.array([0.9, 0.8, 0.8, 0.8, 0.2])
    for order in (np.arange(5), np.array([4, 2, 0, 3, 1])):
        threshold = threshold_at_tpr(y[order], scores[order], 0.5)
        assert threshold == 0.8
        metrics = binary_metrics(y[order], scores[order], threshold)
        assert metrics["recall"] == pytest.approx(2 / 3)
        assert metrics["confusion_matrix"] == [[0, 2], [1, 2]]


def test_metrics_include_threshold_equality_and_support_decision_margins():
    metrics = binary_metrics(np.array([0, 0, 0, 1, 1, 1]), np.array([-3, 0, -1, -2, 0, 2]), 0)
    assert metrics == {
        "n_samples": 6,
        "accuracy": pytest.approx(2 / 3),
        "precision": pytest.approx(2 / 3),
        "recall": pytest.approx(2 / 3),
        "f1": pytest.approx(2 / 3),
        "roc_auc": pytest.approx(13 / 18),
        "false_positive_rate": pytest.approx(1 / 3),
        "confusion_matrix": [[2, 1], [1, 2]],
        "confusion_matrix_labels": [0, 1],
        "threshold": 0,
    }


@pytest.mark.parametrize(
    ("labels", "expected_matrix", "expected_fpr"),
    [([0, 0], [[1, 1], [0, 0]], 0.5), ([1, 1], [[0, 0], [1, 1]], None)],
)
def test_single_class_metrics_keep_undefined_values_explicit(labels, expected_matrix, expected_fpr):
    metrics = binary_metrics(np.array(labels), np.array([0.2, 0.8]), 0.5)
    assert metrics["roc_auc"] is None
    assert metrics["false_positive_rate"] == expected_fpr
    assert metrics["confusion_matrix"] == expected_matrix


@pytest.mark.parametrize(
    ("y", "scores", "threshold"),
    [
        ([], [], 0.5),
        ([[0, 1]], [[0.1, 0.9]], 0.5),
        ([0, 1], [0.1], 0.5),
        ([0, 2], [0.1, 0.9], 0.5),
        ([0, 1], [0.1, np.inf], 0.5),
        ([0, 1], [0.1, 0.9], np.nan),
    ],
)
def test_invalid_metric_inputs_raise(y, scores, threshold):
    with pytest.raises(ValueError):
        binary_metrics(np.array(y), np.array(scores), threshold)


@pytest.mark.parametrize("target", [0, -0.1, 1.1, np.nan])
def test_invalid_target_tpr_is_rejected(target):
    with pytest.raises(ValueError):
        threshold_at_tpr(np.array([0, 1]), np.array([0.1, 0.9]), target)


def test_operating_point_requires_both_classes():
    with pytest.raises(ValueError):
        threshold_at_tpr(np.array([1, 1]), np.array([0.1, 0.9]))
