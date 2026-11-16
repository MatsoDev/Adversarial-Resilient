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
        position = int(positions[0])
        delta = attacked[position].astype(np.float64) - clean[position]
        changes = []
        for feature in policy.record["features"]:
            feature_index = feature["index"]
            if abs(delta[feature_index]) <= 1e-6:
                continue
            signed_log = (
                float(attacked[position, feature_index]) * scale[feature_index]
                + mean[feature_index]
            )
            raw_after = float(np.sign(signed_log) * np.expm1(abs(signed_log)))
            if feature["integer"]:
                raw_after = int(round(raw_after))
            changes.append(
                {
                    "index": feature_index,
                    "operation": feature["operation"],
                    "raw_before": float(raw[position, feature_index]),
                    "raw_after_approx": raw_after,
                    "model_before": float(clean[position, feature_index]),
                    "model_after": float(attacked[position, feature_index]),
                }
            )
        examples.append(
            {
                "cohort_position": position,
                "split_row_index": int(indices[position]),
                "true_label": int(y[position]),
                "clean_prediction": int(before[position]),
                "attacked_prediction": int(after[position]),
                "clean_malicious_score": float(before_scores[position]),
                "attacked_malicious_score": float(after_scores[position]),
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
