"""Offline transfer: the crafting function never receives the target model.

V1 deliberately requires identical preprocessing. Transferring standardized
coordinates between different scalers would silently change the raw sample.
"""

from __future__ import annotations

import hashlib

import numpy as np
import torch

from src.attacks.examples import measured_examples
from src.attacks.runner import BinaryLogits, generate
from src.data.preprocessing import sha256_file
from src.evaluation.attacks import attack_metrics, labels
from src.models.frozen import FrozenBaseline


def array_hash(values):
    """Ordered little-endian float32 bytes, shape supplied by report identity."""
    return hashlib.sha256(np.asarray(values, dtype="<f4").tobytes(order="C")).hexdigest()


def source_bundle(path, target, target_path, *, allow_candidate):
    source = FrozenBaseline(path, require_frozen=not allow_candidate)
    a, b = source.record, target.record
    for key in ("manifest_sha256", "feature_schema_sha256", "preprocessing_sha256", "seed"):
        if a[key] != b[key]:
            raise ValueError(f"Transfer requires matching {key}")
    if a["subset"] is not False or b["subset"] is not False:
        raise ValueError("Transfer requires full-training bundles")
    if allow_candidate and any(
        r["model_version"] != "sprint4_candidate"
        or r["status"] not in {"blocked_validation_accuracy", "blocked_test_accuracy"}
        for r in (a, b)
    ):
        raise ValueError("Transfer candidate mode requires two blocked candidates")
    if a["artifacts"]["weights"]["sha256"] == b["artifacts"]["weights"]["sha256"]:
        raise ValueError("Transfer requires distinct source and target weights")
    if a["partitions"] != b["partitions"]:
        raise ValueError("Transfer requires identical train/validation partitions")
    if not np.array_equal(source.mean, target.mean) or not np.array_equal(
        source.scale, target.scale
    ):
        raise ValueError("Transfer requires identical fitted scalers")
    return source, {
        "model_sha256": sha256_file(path / "bundle.json"),
        "target_model_sha256": sha256_file(target_path / "bundle.json"),
        "weights_sha256": a["artifacts"]["weights"]["sha256"],
        "target_weights_sha256": b["artifacts"]["weights"]["sha256"],
        "model_version": a["model_version"],
        "model_status": a["status"],
        "manifest_sha256": a["manifest_sha256"],
        "feature_schema_sha256": a["feature_schema_sha256"],
        "preprocessing_sha256": a["preprocessing_sha256"],
        "threshold": 0.5,
        "temperature": a["temperature"],
        "target_temperature": b["temperature"],
        "training_seed": a["seed"],
        "target_training_seed": b["seed"],
        "partitions": a["partitions"],
        "target_partitions": b["partitions"],
        "knowledge": "source_white_box_target_no_feedback",
        "labels": "public_ground_truth",
        "target_queries_during_crafting": 0,
        "selection": "predeclared_all_rows_no_target_filter",
    }


def directional_metrics(y, before, after):
    """Class-specific induced errors, never counting preexisting errors."""
    y, before, after = map(np.asarray, (y, before, after))
    result = {"preexisting_errors": int(np.sum(before != y))}
    for name, label in (("malware_evasion", 1), ("false_positive_induction", 0)):
        eligible = (y == label) & (before == y)
        denominator = int(eligible.sum())
        numerator = int(np.sum(eligible & (after != y)))
        result[name] = {
            "numerator": numerator,
            "denominator": denominator,
            "rate": numerator / denominator if denominator else None,
        }
    return result


def evaluate_transfer(source, target, raw, y, indices, policy, config, *, seed):
    """Craft once using ONLY source, then score identical bytes on both models."""
    from src.models.frozen import transform

    clean = transform(raw, source.mean, source.scale)
    source_model = BinaryLogits(source.model, source.record["temperature"]).eval()
    # This call has no target argument, score, decision or gradient.
    attacked = generate(source_model, raw, y, source.mean, source.scale, policy, config, seed=seed)
    source_before, source_after = labels(source_model, clean), labels(source_model, attacked)
    target_model = BinaryLogits(target.model, target.record["temperature"]).eval()
    target_before, target_after = labels(target_model, clean), labels(target_model, attacked)
    examples = measured_examples(
        target_model, clean, attacked, raw, y, indices, target.mean, target.scale, policy
    )
    with torch.inference_mode():
        source_scores = [
            torch.softmax(source_model(torch.from_numpy(x)), dim=1)[:, 1].numpy()
            for x in (clean, attacked)
        ]
    for example in examples:
        position = example["cohort_position"]
        example.update(
            source_clean_prediction=int(source_before[position]),
            source_attacked_prediction=int(source_after[position]),
            source_clean_malicious_score=float(source_scores[0][position]),
            source_attacked_malicious_score=float(source_scores[1][position]),
        )
    eligible = (source_before == y) & (target_before == y) & (source_after != y)
    denominator = int(eligible.sum())
    numerator = int(np.sum(eligible & (target_after != y)))
    return {
        "candidate_sha256": array_hash(attacked),
        "source_metrics": attack_metrics(y, source_before, source_after, clean, attacked),
        "target_metrics": attack_metrics(y, target_before, target_after, clean, attacked),
        "source_outcomes": directional_metrics(y, source_before, source_after),
        "target_outcomes": directional_metrics(y, target_before, target_after),
        "conditional_transfer": {
            "numerator": numerator,
            "denominator": denominator,
            "rate": numerator / denominator if denominator else None,
        },
        "examples": examples,
    }
