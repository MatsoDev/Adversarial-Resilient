"""Small measured case studies, not executable samples or full feature arrays."""

from __future__ import annotations

import numpy as np
import torch


def measured_examples(model, clean, attacked, raw, y, indices, mean, scale, policy):
    """Choose one broken, one unchanged-correct and one preexisting-error row.

    Selection is deliberately illustrative, never a representative sample.
    Scores are calibrated model outputs, not probabilities of file safety.
    """
    with torch.inference_mode():
        before_scores = torch.softmax(model(torch.from_numpy(clean)), dim=1)[:, 1].numpy()
        after_scores = torch.softmax(model(torch.from_numpy(attacked)), dim=1)[:, 1].numpy()
    before, after = (before_scores >= 0.5).astype(int), (after_scores >= 0.5).astype(int)
    groups = (
        ("successful_attack", (before == y) & (after != y)),
        ("remained_correct", (before == y) & (after == y)),
        ("preexisting_error", before != y),
    )
    examples = []
    for outcome, mask in groups:
        positions = np.flatnonzero(mask)
        if not len(positions):
            continue
        j = int(positions[0])
        delta = attacked[j].astype(np.float64) - clean[j]
        changes = []
        for feature in policy.record["features"]:
            i = feature["index"]
            if abs(delta[i]) <= 1e-6:
                continue
            signed_log = float(attacked[j, i]) * scale[i] + mean[i]
            value = float(np.sign(signed_log) * np.expm1(abs(signed_log)))
            if feature["integer"]:
                value = int(round(value))
            changes.append(
                {
                    "index": i,
                    "operation": feature["operation"],
                    "raw_before": float(raw[j, i]),
                    "raw_after_approx": value,
                    "model_before": float(clean[j, i]),
                    "model_after": float(attacked[j, i]),
                }
            )
        examples.append(
            {
                "cohort_position": j,
                "split_row_index": int(indices[j]),
                "true_label": int(y[j]),
                "clean_prediction": int(before[j]),
                "attacked_prediction": int(after[j]),
                "clean_malicious_score": float(before_scores[j]),
                "attacked_malicious_score": float(after_scores[j]),
                "outcome": outcome,
                "norms": {
                    "L0": int(np.count_nonzero(abs(delta) > 1e-6)),
                    "L2": float(np.linalg.norm(delta)),
                    "Linf": float(np.max(abs(delta))),
                },
                "changes": changes,
            }
        )
    return examples
