"""Attack metrics with explicit counts and model-space perturbation units."""

from __future__ import annotations

import numpy as np
import torch


def labels(model, x):
    with torch.inference_mode():
        output = model(torch.from_numpy(np.asarray(x, dtype=np.float32))).numpy()
    if output.shape != (len(x), 2) or not np.isfinite(output).all():
        raise ValueError("Expected finite two-class logits")
    return (output[:, 1] >= output[:, 0]).astype(np.int64)


def attack_metrics(y, clean_labels, attacked_labels, clean, attacked):
    y, before, after = map(np.asarray, (y, clean_labels, attacked_labels))
    clean, attacked = map(np.asarray, (clean, attacked))
    if (
        y.ndim != 1
        or not len(y)
        or before.shape != y.shape
        or after.shape != y.shape
        or clean.ndim != 2
        or clean.shape != attacked.shape
        or len(clean) != len(y)
        or not np.isfinite(clean).all()
        or not np.isfinite(attacked).all()
        or any(not np.isin(v, [0, 1]).all() for v in (y, before, after))
    ):
        raise ValueError("Invalid paired attack evaluation")
    correct = before == y
    successes = int(np.sum(correct & (after != y)))
    denominator = int(correct.sum())
    delta = attacked.astype(np.float64) - clean.astype(np.float64)
    return {
        "samples": len(y),
        "clean_correct": denominator,
        "attacked_correct": int(np.sum(after == y)),
        "successful_attacks": successes,
        "asr_denominator": denominator,
        "attack_success_rate": successes / denominator if denominator else None,
        "clean_accuracy": float(np.mean(correct)),
        "attacked_accuracy": float(np.mean(after == y)),
        "mean_norms": {
            "L0": float(np.mean(np.count_nonzero(np.abs(delta) > 1e-6, axis=1))),
            "L2": float(np.mean(np.linalg.norm(delta, axis=1))),
            "Linf": float(np.mean(np.max(np.abs(delta), axis=1))),
        },
    }
