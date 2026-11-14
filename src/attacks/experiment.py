"""Offline gated EMBER attack experiments; writes summaries, never exposes arrays."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError
from pathlib import Path

import numpy as np

from src.attacks.constraints import FeaturePolicy
from src.attacks.runner import BinaryLogits, generate, library_version
from src.config import ROOT, SEED
from src.data.loader import load_ember
from src.data.preprocessing import (
    code_revision,
    sha256_file,
    verify_manifest_artifacts,
    write_json_atomic,
)
from src.evaluation.attack_results import validate_attack_report
from src.evaluation.attacks import attack_metrics, labels
from src.models.frozen import FrozenBaseline, transform
from src.models.sampling import index_hash, sample_indices


def run_experiment(
    data_dir,
    bundle_dir,
    policy_path,
    configs,
    output,
    *,
    samples=128,
    split="test",
    seed=SEED,
    cleverhans=False,
):
    """Require M1, exact dataset/schema identity, and a reviewed explicit policy.

    Missing/unsupported optional cross-checks remain not_run. Other runtime
    failures are errors, not silently swallowed or replaced with zero ASR.
    """
    if split not in {"val", "test"} or type(samples) is not int or not 2 <= samples <= 4096:
        raise ValueError("Use val/test and 2–4096 rows for bounded offline runs")
    if not configs or len(configs) > 100:
        raise ValueError("Expected 1–100 attack configurations")
    output, data_dir, bundle_dir = map(Path, (output, data_dir, bundle_dir))
    if output.exists():
        raise ValueError("Refusing to overwrite an existing experiment")
    baseline = FrozenBaseline(bundle_dir)
    record = baseline.record
    manifest_path = data_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("dataset") != "ember2018" or manifest.get("subset"):
        raise ValueError("Expected full EMBER manifest")
    if sha256_file(manifest_path) != record["manifest_sha256"]:
        raise ValueError("Frozen model dataset manifest mismatch")
    required = [f"{split}_X", f"{split}_y", "feature_names"]
    artifacts = manifest["artifacts"]
    for key in required:
        suffix = ".json" if key == "feature_names" else ".npy"
        if artifacts[key]["file"] != key + suffix:
            raise ValueError("Incompatible dataset artifact filename")
    if verify_manifest_artifacts(
        {"artifacts": {k: artifacts[k] for k in required}}, data_dir, require_hashes=True
    ):
        raise ValueError("Dataset artifact verification failed")
    if sha256_file(data_dir / "feature_names.json") != record["feature_schema_sha256"]:
        raise ValueError("Feature schema mismatch")
    policy_record = json.loads(Path(policy_path).read_text(encoding="utf-8"))
    if policy_record.get("feature_schema_sha256") != record["feature_schema_sha256"]:
        raise ValueError("Policy feature schema mismatch")
    policy = FeaturePolicy(policy_record, 2381)
    # This box/integer projector cannot enforce normalized groups, hash
    # collisions, loader semantics or coupled derived structural fields.
    supported = {
        512,
        513,
        514,
        611,
        612,
        613,
        614,
        615,
        616,
        617,
        619,
        620,
        625,
        688,
        689,
        690,
        691,
        692,
    }
    if any(f["index"] not in supported for f in policy.record["features"]):
        raise ValueError("Policy requires a coupled or structural projector not implemented yet")
    if any(f["index"] not in {513, 611} and not f["integer"] for f in policy.record["features"]):
        raise ValueError("Count features must use integral projection")
    dataset = load_ember(split, root=data_dir, mmap_mode="r")
    if not np.isin(dataset.y, [0, 1]).all():
        raise ValueError("Expected binary labels")
    indices = sample_indices(dataset.y, samples, seed)
    raw, y = np.asarray(dataset.X[indices]), dataset.y[indices]
    clean = transform(raw, baseline.mean, baseline.scale)
    model = BinaryLogits(baseline.model, record["temperature"])
    before = labels(model, clean)
    identity = {
        "dataset": "ember2018",
        "manifest_sha256": record["manifest_sha256"],
        "model_sha256": sha256_file(bundle_dir / "bundle.json"),
        "model_version": record["model_version"],
        "split": split,
        "indices_sha256": index_hash(indices),
        "samples": len(y),
        "seed": seed,
        "feature_schema_sha256": record["feature_schema_sha256"],
        "preprocessing_sha256": record["preprocessing_sha256"],
        "constraint_sha256": policy.digest,
        "threshold": 0.5,
        "representation": "signed-log1p-standardized",
        "targeted": False,
        "cohort": "stratified_all_classes",
        "norm_l0_tolerance": 1e-6,
    }
    # Identity includes exact rows, policy and model, not just a human version tag.
    group = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    rows = []
    for config in configs:
        row = {
            "attack": config.attack,
            "norm": config.norm,
            "parameters": config.parameters(),
            "projection": "after_generation" if config.attack == "CW-L2" else "each_step",
            "library": "ART",
            "library_version": library_version("ART"),
        }
        attacked = generate(model, raw, y, baseline.mean, baseline.scale, policy, config, seed=seed)
        after = labels(model, attacked)
        row["metrics"] = attack_metrics(y, before, after, clean, attacked)
        cross = {"status": "not_run", "reason": "Optional isolated CleverHans check not requested"}
        if cleverhans:
            try:
                cross_version = library_version("CleverHans")
                other = generate(
                    model,
                    raw,
                    y,
                    baseline.mean,
                    baseline.scale,
                    policy,
                    config,
                    library="CleverHans",
                    seed=seed,
                )
                other_labels = labels(model, other)
                cross = {
                    "status": "completed",
                    "library": "CleverHans",
                    "version": cross_version,
                    "metrics": attack_metrics(y, before, other_labels, clean, other),
                    "prediction_agreement": float(np.mean(after == other_labels)),
                    "mean_candidate_l2_difference": float(
                        np.linalg.norm(attacked.astype(np.float64) - other, axis=1).mean()
                    ),
                    "interpretation": "Independent implementations; agreement is not equivalence",
                }
            except (ImportError, PackageNotFoundError, NotImplementedError) as error:
                cross = {"status": "not_run", "reason": str(error)}
        row["cross_check"] = cross
        rows.append(row)
    result = {
        "schema_version": 1,
        "status": "completed",
        "compatibility_id": group,
        "generated_at": datetime.now(UTC).isoformat(),
        "identity": identity,
        "constraint": {
            "status": "reviewed_feature_space",
            "reviewer": policy.record["reviewer"],
            "problem_space_validated": False,
            "policy": policy.record,
        },
        "asr_definition": "Clean-correct rows made incorrect / clean-correct rows (all classes)",
        "norm_units": "Signed-log1p standardized model coordinates; L0 tolerance 1e-6",
        "code_revision": code_revision(),
        "source_sha256": {
            str(p.relative_to(ROOT)).replace("\\", "/"): sha256_file(p)
            for p in (ROOT / "src/attacks").glob("*.py")
        },
        "results": rows,
    }
    validate_attack_report(result)
    write_json_atomic(output, result)
    return result
