"""Validate the optional Sprint 6 extension without relaxing historical reports."""

from __future__ import annotations

import hashlib
import json
import math


def validate_outcomes(value, metrics):
    """Check directional denominators sum to the clean-correct cohort."""

    def require(condition):
        if not condition:
            raise ValueError("Invalid directional attack counts")

    require(type(value["preexisting_errors"]) is int)
    require(value["preexisting_errors"] == metrics["samples"] - metrics["clean_correct"])
    directions = [value[k] for k in ("malware_evasion", "false_positive_induction")]
    for direction in directions:
        n, d = direction["numerator"], direction["denominator"]
        require(type(n) is int and type(d) is int and 0 <= n <= d <= metrics["clean_correct"])
        require(
            math.isclose(direction["rate"], n / d, abs_tol=1e-12)
            if d
            else direction["rate"] is None
        )
    require(sum(v["denominator"] for v in directions) == metrics["clean_correct"])
    require(sum(v["numerator"] for v in directions) == metrics["successful_attacks"])


def validate_transfer(report, metrics):
    from src.evaluation.attack_results import validate_attack_report

    def require(value):
        if not value:
            raise ValueError("Invalid transfer evidence")

    def digest(value):
        require(isinstance(value, str) and len(value) == 64)
        require(all(c in "0123456789abcdef" for c in value))

    identity = report["identity"]
    source = identity["transfer_source"]
    for key in (
        "model_sha256",
        "target_model_sha256",
        "weights_sha256",
        "target_weights_sha256",
        "manifest_sha256",
        "feature_schema_sha256",
        "preprocessing_sha256",
    ):
        digest(source[key])
    for key in ("clean_sha256", "split_X_sha256", "split_y_sha256"):
        digest(identity[key])
    for key in ("manifest_sha256", "feature_schema_sha256", "preprocessing_sha256"):
        require(source[key] == identity[key])
    require(source["target_model_sha256"] == identity["model_sha256"])
    require(source["model_sha256"] != identity["model_sha256"])
    require(source["weights_sha256"] != source["target_weights_sha256"])
    require(source["threshold"] == 0.5 and source["temperature"] > 0)
    require(source["target_temperature"] > 0)
    require(type(source["training_seed"]) is int)
    require(source["target_training_seed"] == source["training_seed"])
    require(source["partitions"] == source["target_partitions"])
    require(source["knowledge"] == "source_white_box_target_no_feedback")
    require(source["labels"] == "public_ground_truth")
    require(type(source["target_queries_during_crafting"]) is int)
    require(source["target_queries_during_crafting"] == 0)
    require(source["selection"] == "predeclared_all_rows_no_target_filter")
    for name in ("train", "selection", "calibration", "operating"):
        partition = source["partitions"][name]
        digest(partition["indices_sha256"])
        require(type(partition["rows"]) is int and partition["rows"] > 0)
    require(source["model_version"] == identity["model_version"])
    if identity["model_version"] == "sprint4_candidate":
        require(source["model_status"] in {"blocked_validation_accuracy", "blocked_test_accuracy"})
        require(isinstance(report["transfer_authorization"], str))
        require(bool(report["transfer_authorization"].strip()))
    else:
        require(source["model_status"] == "frozen")

    def ratio(value, maximum):
        n, d = value["numerator"], value["denominator"]
        require(type(n) is int and type(d) is int and 0 <= n <= d <= maximum)
        require(math.isclose(value["rate"], n / d, abs_tol=1e-12) if d else value["rate"] is None)

    # Reuse the full existing case/score/policy/norm validator for transferred
    # target examples. Remove the extension to avoid recursive extension parsing.
    legacy_identity = {k: v for k, v in identity.items() if k != "transfer_source"}
    legacy = {
        **report,
        "identity": legacy_identity,
        "compatibility_id": hashlib.sha256(
            json.dumps(legacy_identity, sort_keys=True).encode()
        ).hexdigest(),
    }
    projected_rows = []
    first = report["results"][0]["transfer"]
    for row in report["results"]:
        transfer = row["transfer"]
        digest(transfer["candidate_sha256"])
        a, b = transfer["source_metrics"], transfer["target_metrics"]
        metrics(a)
        metrics(b)
        require(b["clean_correct"] == row["metrics"]["clean_correct"])
        require(a["mean_norms"] == b["mean_norms"])
        require(a["clean_correct"] == first["source_metrics"]["clean_correct"])
        validate_outcomes(transfer["source_outcomes"], a)
        validate_outcomes(transfer["target_outcomes"], b)
        for model in ("source", "target"):
            for direction in ("malware_evasion", "false_positive_induction"):
                require(
                    transfer[f"{model}_outcomes"][direction]["denominator"]
                    == first[f"{model}_outcomes"][direction]["denominator"]
                )
        if row["norm"] == "Linf":
            require(a["mean_norms"]["Linf"] <= row["parameters"]["epsilon"] + 1e-6)
        if row["parameters"].get("epsilon") == 0:
            require(transfer["candidate_sha256"] == identity["clean_sha256"])
            for m in (a, b):
                require(m["clean_correct"] == m["attacked_correct"])
                require(m["successful_attacks"] == 0)
                require(all(v == 0 for v in m["mean_norms"].values()))
        conditional = transfer["conditional_transfer"]
        ratio(conditional, min(a["successful_attacks"], b["clean_correct"]))
        require(conditional["numerator"] <= b["successful_attacks"])
        examples = transfer["examples"]
        for example in examples:
            for phase in ("clean", "attacked"):
                score = example[f"source_{phase}_malicious_score"]
                prediction = example[f"source_{phase}_prediction"]
                require(type(score) in {int, float} and 0 <= score <= 1)
                require(type(prediction) is int and prediction in {0, 1})
                require(int(score >= 0.5) == prediction)
        projected_rows.append(
            {
                **{k: v for k, v in row.items() if k != "transfer"},
                "metrics": b,
                "examples": examples,
                "cross_check": {"status": "not_run", "reason": "Transfer is not a cross-check"},
                "outcomes": transfer["target_outcomes"],
            }
        )
    legacy["results"] = projected_rows
    validate_attack_report(legacy)
