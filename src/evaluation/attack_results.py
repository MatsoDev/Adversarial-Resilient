"""Validate compact completed attack reports before exposing them over HTTP."""

from __future__ import annotations

import hashlib
import json
import math


def validate_attack_report(report):
    """Reject inconsistent counts, identities, mislabeled CW and nonfinite values."""

    def require(condition):
        if not condition:
            raise ValueError("Invalid attack report")

    def finite_tree(value):
        if isinstance(value, float):
            require(math.isfinite(value))
        elif isinstance(value, dict):
            for v in value.values():
                finite_tree(v)
        elif isinstance(value, list):
            for v in value:
                finite_tree(v)

    finite_tree(report)
    require(report["schema_version"] == 1 and report["status"] == "completed")
    identity = report["identity"]
    for k in (
        "manifest_sha256",
        "model_sha256",
        "indices_sha256",
        "constraint_sha256",
        "feature_schema_sha256",
        "preprocessing_sha256",
    ):
        require(isinstance(identity[k], str) and len(identity[k]) == 64)
        require(all(c in "0123456789abcdef" for c in identity[k]))
    require(identity["dataset"] == "ember2018" and identity["model_version"] == "baseline_v1")
    require(identity["split"] in {"val", "test"} and identity["threshold"] == 0.5)
    require(identity["targeted"] is False and identity["cohort"] == "stratified_all_classes")
    require(identity["representation"] == "signed-log1p-standardized")
    require(identity["norm_l0_tolerance"] == 1e-6)
    require(type(identity["samples"]) is int and 2 <= identity["samples"] <= 4096)
    expected = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    require(report["compatibility_id"] == expected)
    constraint = report["constraint"]
    require(constraint["status"] in {"reviewed_feature_space", "owner_authorized_feature_space"})
    require(constraint["problem_space_validated"] is False)
    require(isinstance(report["generated_at"], str) and bool(report["generated_at"]))
    require(constraint["policy"]["status"] == constraint["status"])
    if constraint["status"] == "owner_authorized_feature_space":
        require(
            constraint["security_review"] == constraint["policy"]["security_review"] == "pending"
        )
    require(constraint["reviewer"] == constraint["policy"]["reviewer"])
    policy_hash = hashlib.sha256(
        json.dumps(constraint["policy"], sort_keys=True, allow_nan=False).encode()
    ).hexdigest()
    require(policy_hash == identity["constraint_sha256"])

    def metrics(m):
        n = identity["samples"]
        require(m["samples"] == n)
        for key in ("clean_correct", "attacked_correct", "successful_attacks", "asr_denominator"):
            require(type(m[key]) is int and 0 <= m[key] <= n)
        d = m["clean_correct"]
        require(d == m["asr_denominator"] and m["successful_attacks"] <= d)
        require(m["successful_attacks"] <= n - m["attacked_correct"])
        require(m["attacked_correct"] >= d - m["successful_attacks"])
        require(m["attacked_correct"] <= n - m["successful_attacks"])
        require(math.isclose(m["clean_accuracy"], d / n, abs_tol=1e-12))
        require(math.isclose(m["attacked_accuracy"], m["attacked_correct"] / n, abs_tol=1e-12))
        if d:
            require(
                math.isclose(m["attack_success_rate"], m["successful_attacks"] / d, abs_tol=1e-12)
            )
        else:
            require(m["attack_success_rate"] is None)
        for norm in ("L0", "L2", "Linf"):
            require(isinstance(m["mean_norms"][norm], int | float) and m["mean_norms"][norm] >= 0)
        require(m["mean_norms"]["L0"] <= 2381)

    rows = report["results"]
    require(isinstance(rows, list) and 1 <= len(rows) <= 100)
    seen = set()
    for row in rows:
        require(row["library"] == "ART" and isinstance(row["library_version"], str))
        attack, params = row["attack"], row["parameters"]
        require(attack in {"FGSM", "PGD", "CW-L2"})
        require(row["norm"] == ("L2" if attack == "CW-L2" else "Linf"))
        require(row["projection"] == ("after_generation" if attack == "CW-L2" else "each_step"))
        if attack == "CW-L2":
            require("epsilon" not in params)
            require(params["learning_rate"] > 0 and params["binary_search_steps"] > 0)
        else:
            require(params["epsilon"] >= 0 and params["random_start"] is False)
        if attack in {"PGD", "CW-L2"}:
            require(type(params["iterations"]) is int and params["iterations"] > 0)
        if attack == "PGD":
            require(params["step_size"] > 0)
        unique = json.dumps([attack, params], sort_keys=True)
        require(unique not in seen)
        seen.add(unique)
        metrics(row["metrics"])
        require(row["metrics"]["clean_correct"] == rows[0]["metrics"]["clean_correct"])
        check = row["cross_check"]
        require(check["status"] in {"not_run", "completed"})
        if check["status"] == "completed":
            require(check["library"] == "CleverHans" and isinstance(check["version"], str))
            metrics(check["metrics"])
            require(check["metrics"]["clean_correct"] == row["metrics"]["clean_correct"])
            require(0 <= check["prediction_agreement"] <= 1)
            require(check["mean_candidate_l2_difference"] >= 0)
        else:
            require(isinstance(check["reason"], str) and bool(check["reason"]))
    return report
