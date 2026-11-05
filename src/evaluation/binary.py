"""Binary classification metrics with explicit score/threshold semantics."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
    roc_curve,
)


def binary_metrics(y: np.ndarray, scores: np.ndarray, threshold: float) -> dict:
    """Evaluate positive-class scores; undefined AUC/FPR is null, not zero."""
    y, scores = np.asarray(y), np.asarray(scores)
    if y.ndim != 1 or scores.shape != y.shape or not len(y):
        raise ValueError("Expected nonempty matching one-dimensional labels and scores")
    if not np.isin(y, [0, 1]).all() or not np.isfinite(scores).all():
        raise ValueError("Expected binary labels and finite scores")
    if not np.isfinite(threshold):
        raise ValueError("Threshold must be finite")
    predicted = (scores >= threshold).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y, predicted, average="binary", zero_division=0
    )
    matrix = confusion_matrix(y, predicted, labels=[0, 1])
    tn, fp, fn, tp = matrix.ravel()
    two_classes = len(np.unique(y)) == 2
    return {
        "n_samples": len(y),
        "accuracy": float(accuracy_score(y, predicted)),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "roc_auc": float(roc_auc_score(y, scores)) if two_classes else None,
        "false_positive_rate": float(fp / (tn + fp)) if tn + fp else None,
        "confusion_matrix": matrix.tolist(),
        "confusion_matrix_labels": [0, 1],
        "threshold": threshold,
    }


def threshold_at_tpr(y: np.ndarray, scores: np.ndarray, target: float = 0.95) -> float:
    """Select the highest threshold reaching target TPR on validation only."""
    if not 0 < target <= 1 or len(np.unique(y)) != 2:
        raise ValueError("TPR selection requires both classes and target in (0, 1]")
    _, tpr, thresholds = roc_curve(y, scores)
    return float(thresholds[np.flatnonzero(tpr >= target)[0]])
