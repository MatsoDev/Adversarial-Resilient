"""Reconstruct aggregate charts from recorded outcomes and clean inference only."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch  # Load native torch libraries first on Windows.
from matplotlib import pyplot as plt
from src.config import EMBER_PROCESSED_DIR, EXTERNAL_DIR, FROZEN_BASELINE_DIR, RESULTS_DIR
from src.data.loader import load_ember
from src.data.preprocessing import sha256_file, verify_manifest_artifacts, write_json_atomic
from src.evaluation.attack_results import validate_attack_report
from src.models.frozen import FrozenBaseline, transform
from src.models.sampling import index_hash, sample_indices, validation_partitions


def confusion(truth, predictions):
    return np.bincount(2 * truth + predictions, minlength=4).reshape(2, 2).tolist()


def recover_after(indices, truth, before, configuration):
    """Return a matrix only when the stored cases account for every binary flip."""
    counts = configuration["metrics"]
    correct = before == truth
    if len(truth) != counts["samples"] or int(correct.sum()) != counts["clean_correct"]:
        raise ValueError("Clean inference does not match the recorded cohort counts")
    expected_errors = counts["successful_attacks"]
    expected_repairs = counts["attacked_correct"] - counts["clean_correct"] + expected_errors
    after = before.copy()
    seen = set()
    for example in configuration.get("examples", []):
        position = example["cohort_position"]
        if (
            not 0 <= position < len(indices)
            or position in seen
            or indices[position] != example["split_row_index"]
            or truth[position] != example["true_label"]
            or before[position] != example["clean_prediction"]
        ):
            raise ValueError("Recorded case disagrees with verified clean inference")
        seen.add(position)
        after[position] = example["attacked_prediction"]
    errors = int(np.sum(correct & (after != truth)))
    repairs = int(np.sum(~correct & (after == truth)))
    if errors > expected_errors or repairs > expected_repairs:
        raise ValueError("Recorded cases contradict the cohort's decision counts")
    if (errors, repairs) != (expected_errors, expected_repairs):
        return None
    return confusion(truth, after)


def one_coordinate_histogram(metrics):
    """Recover counts for L0 in {0, 1} from its cohort-wide arithmetic mean."""
    total = metrics["samples"]
    changed = metrics["mean_norms"]["L0"] * total
    rounded = round(changed)
    if not 0 <= rounded <= total or not math.isclose(changed, rounded, abs_tol=1e-7):
        raise ValueError("The mean L0 is incompatible with a one-coordinate cohort")
    return [total - rounded, rounded]


def analyze(report_path, bundle_dir, data_dir):
    report = validate_attack_report(json.loads(report_path.read_text(encoding="utf-8")))
    identity = report["identity"]
    if (identity["split"], identity["cohort"]) != ("val", "operating_validation"):
        raise ValueError("This analysis only reads recorded operating-validation cohorts")
    if sha256_file(bundle_dir / "bundle.json") != identity["model_sha256"]:
        raise ValueError("The selected bundle does not match the original experiment")
    bundle = FrozenBaseline(bundle_dir, require_frozen=False)
    manifest_path = data_dir / "manifest.json"
    for key in ("manifest_sha256", "feature_schema_sha256", "preprocessing_sha256"):
        if bundle.record[key] != identity[key]:
            raise ValueError(f"Model provenance mismatch: {key}")
    if (
        bundle.record.get("subset") is not False
        or sha256_file(manifest_path) != identity["manifest_sha256"]
    ):
        raise ValueError("Expected the original full EMBER manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = {"val_X": "val_X.npy", "val_y": "val_y.npy", "feature_names": "feature_names.json"}
    artifacts = {key: manifest["artifacts"][key] for key in files}
    if any(artifacts[key]["file"] != name for key, name in files.items()):
        raise ValueError("Unexpected validation artifact filenames")
    if verify_manifest_artifacts({"artifacts": artifacts}, data_dir, require_hashes=True):
        raise ValueError("Validation artifact verification failed")
    if sha256_file(data_dir / files["feature_names"]) != identity["feature_schema_sha256"]:
        raise ValueError("Validation feature schema mismatch")
    data = load_ember("val", root=data_dir, mmap_mode="r")
    if not np.isin(data.y, [0, 1]).all():
        raise ValueError("Expected binary validation labels")
    _, _, pool = validation_partitions(data.y, bundle.record["seed"])
    operating = bundle.record["partitions"]["operating"]
    if operating != {"rows": len(pool), "indices_sha256": index_hash(pool)}:
        raise ValueError("Operating partition mismatch")
    indices = pool[sample_indices(data.y[pool], identity["samples"], identity["seed"])]
    if len(indices) != identity["samples"] or index_hash(indices) != identity["indices_sha256"]:
        raise ValueError("Ordered cohort mismatch")
    truth = data.y[indices].astype(np.int64)
    clean = transform(data.X[indices], bundle.mean, bundle.scale)
    with torch.inference_mode():
        logits = bundle.model(torch.from_numpy(clean)).reshape(-1) / bundle.record["temperature"]
    if logits.shape != truth.shape or not torch.isfinite(logits).all():
        raise ValueError("Expected one finite logit per row")
    before = (logits.numpy() >= 0).astype(np.int64)
    one_coordinate = len(report["constraint"]["policy"]["features"]) == 1
    return {
        "schema_version": 1,
        "source_report_sha256": hashlib.sha256(
            json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest(),
        "compatibility_id": report["compatibility_id"],
        "identity": identity,
        "class_order": ["benign", "malicious"],
        "before": confusion(truth, before),
        "l0_bins": [0, 1] if one_coordinate else None,
        "results": [
            {
                "method": row["attack"],
                "parameters": row["parameters"],
                "after": recover_after(indices, truth, before, row),
                "l0_counts": one_coordinate_histogram(row["metrics"]) if one_coordinate else None,
            }
            for row in report["results"]
        ],
    }


def plot_example(summary, path):
    row = next(
        (
            r
            for r in summary["results"]
            if r["after"] is not None and r["after"] != summary["before"]
        ),
        None,
    )
    if row is None or row["l0_counts"] is None:
        return False
    labels = ["Benign", "Malicious"]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2), layout="constrained")
    vmax = max(max(max(line) for line in matrix) for matrix in (summary["before"], row["after"]))
    for ax, title, matrix in zip(
        axes[:2],
        ("Before: clean replay", "After: recovered counts"),
        (summary["before"], row["after"]),
        strict=True,
    ):
        ax.imshow(matrix, cmap="Blues", vmin=0, vmax=vmax)
        ax.set(title=title, xlabel="Predicted class", ylabel="True class")
        ax.set_xticks([0, 1], labels)
        ax.set_yticks([0, 1], labels)
        for i, counts in enumerate(matrix):
            for j, count in enumerate(counts):
                ax.text(
                    j,
                    i,
                    count,
                    ha="center",
                    va="center",
                    color="white" if count > vmax * 0.6 else "#172238",
                )
    ax = axes[2]
    bars = ax.bar(["None", "One"], row["l0_counts"], color=["#526782", "#216b9a"])
    ax.bar_label(bars, padding=3)
    ax.margins(y=0.18)
    ax.set(title="L0 distribution", xlabel="Changed coordinates per row", ylabel="Rows")
    setting = row["parameters"].get("epsilon")
    suffix = f" (ε = {setting:g})" if setting is not None else ""
    fig.suptitle(
        f"Recorded EMBER validation cohort · {summary['identity']['samples']} rows · {row['method']}{suffix}"
    )
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=RESULTS_DIR / "attack_reference.json")
    parser.add_argument("--bundle-dir", type=Path, default=FROZEN_BASELINE_DIR)
    parser.add_argument("--data-dir", type=Path, default=EMBER_PROCESSED_DIR)
    parser.add_argument("--output-dir", type=Path, default=EXTERNAL_DIR / "sprint7-cohort-analysis")
    args = parser.parse_args()
    torch.set_num_threads(2)
    summary = analyze(args.report, args.bundle_dir, args.data_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json_atomic(args.output_dir / "cohort_summary.json", summary)
    plot_example(summary, args.output_dir / "cohort_example.png")
    print(
        f"Recovered {sum(row['after'] is not None for row in summary['results'])} "
        f"of {len(summary['results'])} post-change matrices in {args.output_dir}"
    )


if __name__ == "__main__":
    main()
