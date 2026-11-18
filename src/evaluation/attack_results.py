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
    require(identity["dataset"] == "ember2018")
    if identity["model_version"] == "sprint4_candidate":
        require(report["experiment_stage"] == "development_candidate_not_frozen")
        require(
            identity["model_status"] in {"blocked_validation_accuracy", "blocked_test_accuracy"}
        )
        require(identity["split"] == "val" and identity["cohort"] == "operating_validation")
        require(
            isinstance(report["candidate_reason"], str) and bool(report["candidate_reason"].strip())
        )
        require(report["baseline_qualification"]["status"] == identity["model_status"])
    else:
        require(identity["model_version"] == "baseline_v1")
        require(report.get("experiment_stage", "frozen_baseline") == "frozen_baseline")
        require(identity["cohort"] == "stratified_all_classes")
    require(identity["split"] in {"val", "test"} and identity["threshold"] == 0.5)
    require(identity["targeted"] is False)
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
    # Imported reports bypass the attack runner's FeaturePolicy constructor.
    # Validate indices here too: they are used as identities and displayed by the UI.
    features = {}
    require(isinstance(constraint["policy"]["features"], list))
    for feature in constraint["policy"]["features"]:
        index = feature["index"]
        require(type(index) is int and 0 <= index < 2381 and index not in features)
        features[index] = feature

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
        examples = row.get("examples", [])
        require(isinstance(examples, list) and len(examples) <= 3)
        positions = set()
        outcomes = set()
        for example in examples:
            position = example["cohort_position"]
            require(type(position) is int and 0 <= position < identity["samples"])
            require(position not in positions)
            positions.add(position)
            require(type(example["split_row_index"]) is int and example["split_row_index"] >= 0)
            truth, before, after = (
                example[k] for k in ("true_label", "clean_prediction", "attacked_prediction")
            )
            require(all(type(v) is int and v in {0, 1} for v in (truth, before, after)))
            outcome = (
                "preexisting_error"
                if before != truth
                else "successful_attack"
                if after != truth
                else "remained_correct"
            )
            require(example["outcome"] == outcome and outcome not in outcomes)
            outcomes.add(outcome)
            if outcome == "successful_attack":
                require(row["metrics"]["successful_attacks"] > 0)
            if outcome == "preexisting_error":
                require(row["metrics"]["clean_correct"] < identity["samples"])
            for key, prediction in (
                ("clean_malicious_score", before),
                ("attacked_malicious_score", after),
            ):
                score = example[key]
                require(type(score) in {int, float} and 0 <= score <= 1)
                require(int(score >= 0.5) == prediction)
            changes = example["changes"]
            require(isinstance(changes, list) and len(changes) <= len(features))
            changed = set()
            deltas = []
            for change in changes:
                i = change["index"]
                require(type(i) is int and i in features and i not in changed)
                changed.add(i)
                require(change["operation"] == features[i]["operation"])
                for key in ("raw_before", "raw_after_approx", "model_before", "model_after"):
                    require(type(change[key]) in {int, float})
                delta = abs(change["model_after"] - change["model_before"])
                require(delta > 1e-6)
                deltas.append(delta)
            norms = example["norms"]
            require(type(norms["L0"]) is int and norms["L0"] == len(changes))
            require(norms["L2"] >= 0 and norms["Linf"] >= 0)
            require(math.isclose(norms["Linf"], max(deltas, default=0), abs_tol=1e-6))
            require(math.isclose(norms["L2"], math.sqrt(sum(d * d for d in deltas)), abs_tol=1e-4))
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
