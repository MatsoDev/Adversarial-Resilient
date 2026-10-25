"""Deterministic EDA for EMBER2018 and CIC-IDS-2017 (Sprint 2).

Default outputs:
  docs/results/data_eda.json
  docs/figures/data_ember_*.png
  docs/figures/data_cicids_*.png
  docs/data/eda_report.md

Pass ``--output-dir`` (e.g. pytest ``tmp_path`` or ``/tmp/eda_smoke``) to
redirect every output and leave the committed docs untouched.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import (  # noqa: E402
    CICIDS_PROCESSED_DIR,
    DATA_DOCS_DIR,
    EMBER_PROCESSED_DIR,
    FIGURES_DIR,
    RESULTS_DIR,
    resolve_cicids_source,
    resolve_ember_source,
)
from src.data.cicids2017 import (  # noqa: E402
    EXPECTED_TOTAL_ROWS,
    _dedupe_columns,
    _iter_chunks,
    _row_keys,
    binary_label,
    discover_cicids_files,
    normalize_label,
)
from src.data.ember import (  # noqa: E402
    FEATURE_GROUPS,
    EmberVectorizer,
    discover_ember_files,
    scan_ember_metadata,
)
from src.data.preprocessing import (  # noqa: E402
    atomic_write_text,
    load_json,
    write_json_atomic,
)
from src.utils.seed import set_seed  # noqa: E402

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deterministic EDA for Sprint 2 datasets")
    parser.add_argument("--dataset", choices=("ember", "cicids2017", "all"), required=True)
    parser.add_argument("--source", default=None)
    parser.add_argument("--ember-source", default=None)
    parser.add_argument("--cicids-source", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--max-samples",
        type=int,
        default=5000,
        help="Rows retained for feature-distribution summaries (default 5000)",
    )
    parser.add_argument("--jobs", type=int, default=min(4, os.cpu_count() or 1))
    parser.add_argument(
        "--no-processed",
        action="store_true",
        help="Do not read processed manifests under data/processed",
    )
    parser.add_argument("--ember-processed-dir", default=None)
    parser.add_argument("--cicids-processed-dir", default=None)
    return parser.parse_args(argv)


def _output_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    if args.output_dir:
        base = Path(args.output_dir)
        return (
            base / "results" / "data_eda.json",
            base / "figures",
            base / "data" / "eda_report.md",
        )
    return RESULTS_DIR / "data_eda.json", FIGURES_DIR, DATA_DOCS_DIR / "eda_report.md"


def _save_figure(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120, bbox_inches="tight", metadata={"Software": "matplotlib"})
    import matplotlib.pyplot as plt

    plt.close(fig)


def _sample_frame(frame: pd.DataFrame, *, max_samples: int, seed: int) -> pd.DataFrame:
    if max_samples >= len(frame) or len(frame) == 0:
        return frame.reset_index(drop=True)
    from sklearn.model_selection import train_test_split

    labels = frame["label"].to_numpy()
    if len(np.unique(labels)) > 1 and max_samples >= len(np.unique(labels)):
        chosen, _ = train_test_split(
            np.arange(len(frame)), train_size=max_samples, random_state=seed, stratify=labels
        )
        return frame.iloc[np.sort(chosen)].reset_index(drop=True)
    rng = np.random.default_rng(seed)
    chosen = np.sort(rng.choice(len(frame), size=max_samples, replace=False))
    return frame.iloc[chosen].reset_index(drop=True)


def _ember_feature_stats(
    files, sample_meta: pd.DataFrame, *, seed: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    vectorizer = EmberVectorizer()
    vectors: list[np.ndarray] = []
    histogram_sums: list[float] = []
    byteentropy_sums: list[float] = []
    for file_name, group in sample_meta.groupby("source_file", sort=False):
        candidates = [candidate for candidate in files.all if candidate.name == file_name]
        if not candidates:
            continue
        path = candidates[0]
        with open(path, "rb") as handle:
            for row in group.itertuples():
                handle.seek(int(row.source_offset))
                line = handle.readline()
                record = json.loads(line)
                vector = vectorizer.transform(record, context=f"{file_name}:{row.source_index + 1}")
                vectors.append(vector)
                histogram_sums.append(float(vector[0:256].sum()))
                byteentropy_sums.append(float(vector[256:512].sum()))

    if not vectors:
        return {}, {}
    matrix = np.stack(vectors)
    groups: dict[str, Any] = {}
    for name, (start, stop) in FEATURE_GROUPS.items():
        block = matrix[:, start:stop]
        groups[name] = {
            "dim": int(stop - start),
            "nonzero_fraction": round(float(np.mean(block != 0)), 6),
            "mean_variance": float(np.mean(block.var(axis=0))),
            "mean_abs": float(np.mean(np.abs(block))),
        }
    normalization = {
        "rows_checked": int(len(matrix)),
        "histogram_sum_min": float(np.min(histogram_sums)),
        "histogram_sum_max": float(np.max(histogram_sums)),
        "byteentropy_sum_min": float(np.min(byteentropy_sums)),
        "byteentropy_sum_max": float(np.max(byteentropy_sums)),
        "histogram_all_close_to_one": bool(np.allclose(histogram_sums, 1.0, atol=1e-5, rtol=0.0)),
        "byteentropy_all_close_to_one": bool(
            np.allclose(byteentropy_sums, 1.0, atol=1e-5, rtol=0.0)
        ),
    }
    return groups, normalization


def _ember_eda(
    source: Path,
    processed_dir: Path,
    *,
    seed: int,
    max_samples: int,
    jobs: int,
    figures_dir: Path,
    use_processed: bool,
) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    files = discover_ember_files(source, strict=False)
    train_meta, test_meta, file_stats = scan_ember_metadata(
        files, jobs=max(1, jobs), show_progress=True
    )
    metadata = pd.concat([train_meta, test_meta], ignore_index=True)
    label_counts = {
        str(int(key)): int(value) for key, value in sorted(metadata["label"].value_counts().items())
    }
    duplicate_rows = int(len(metadata) - metadata["sha256"].nunique())
    duplicate_groups = int((metadata.groupby("sha256").size() > 1).sum())
    appeared = metadata.groupby(["appeared", "label"]).size().unstack(fill_value=0).sort_index()
    appeared_by_label = {
        str(period): {str(int(label)): int(count) for label, count in row.items()}
        for period, row in appeared.iterrows()
    }
    missing_keys: Counter[str] = Counter()
    for stat in file_stats:
        missing_keys.update(stat["missing_keys"])

    sample_meta = _sample_frame(metadata, max_samples=min(max_samples, 20_000), seed=seed)
    feature_groups, normalization = _ember_feature_stats(files, sample_meta, seed=seed)

    processed: dict[str, Any] = {"available": False}
    manifest_path = processed_dir / "manifest.json"
    if use_processed and manifest_path.is_file():
        manifest = load_json(manifest_path)
        processed = {
            "available": True,
            "subset": manifest.get("subset"),
            "manifest": _relative_manifest_path(manifest_path),
            "feature_dim": manifest.get("preprocessing", {}).get("feature_dim"),
            "splits": manifest.get("splits", {}),
            "split_strategy": manifest.get("split_strategy", {}),
            "duplicates": manifest.get("duplicates", {}),
        }

    labels = sorted(label_counts)
    counts = [label_counts[label] for label in labels]
    fig, ax = plt.subplots(figsize=(6, 3.5))
    positions = np.arange(len(labels))
    ax.bar(positions, counts, color=["#4c72b0", "#55a868", "#c44e52"][: len(labels)])
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.set_yscale("log")
    ax.set_xlabel("label (-1 unlabelled, 0 benign, 1 malicious)")
    ax.set_ylabel("rows (log scale)")
    ax.set_title("EMBER2018 source label counts")
    for index, value in enumerate(counts):
        ax.text(index, value, f"{value:,}", ha="center", va="bottom", fontsize=8)
    _save_figure(fig, figures_dir / "data_ember_label_counts.png")

    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(appeared.index))
    for label in appeared.columns:
        ax.plot(x, appeared[label].to_numpy(), marker="o", markersize=2, label=f"label {label}")
    ax.set_yscale("log")
    ax.set_xlabel("appeared month (index)")
    ax.set_ylabel("rows (log scale)")
    ax.set_title("EMBER2018 appeared-by-label distribution")
    ax.legend()
    ax.grid(alpha=0.25)
    tick_step = max(1, len(appeared.index) // 8)
    ax.set_xticks(x[::tick_step])
    ax.set_xticklabels(appeared.index[::tick_step], rotation=45, ha="right", fontsize=7)
    _save_figure(fig, figures_dir / "data_ember_appeared_by_label.png")

    if feature_groups:
        names = list(feature_groups)
        fractions = [feature_groups[name]["nonzero_fraction"] for name in names]
        fig, ax = plt.subplots(figsize=(7, 3.5))
        ax.bar(names, fractions, color="#4c72b0")
        ax.set_ylabel("fraction of entries non-zero")
        ax.set_title(f"EMBER feature-group sparsity (sample n={len(sample_meta):,})")
        ax.tick_params(axis="x", rotation=35)
        ax.set_ylim(0, 1.05)
        _save_figure(fig, figures_dir / "data_ember_feature_groups.png")

    return {
        "source": {
            "files": [
                {
                    "name": stat["name"],
                    "partition": stat["partition"],
                    "rows": stat["rows"],
                    "label_counts": {
                        str(key): value for key, value in sorted(stat["label_counts"].items())
                    },
                }
                for stat in file_stats
            ],
            "rows": int(len(metadata)),
            "label_counts": label_counts,
            "missing_required_keys": dict(sorted(missing_keys.items())),
        },
        "duplicate_sha256": {
            "duplicate_rows": duplicate_rows,
            "duplicate_groups": duplicate_groups,
        },
        "appeared_by_label": appeared_by_label,
        "feature_sample": {
            "rows": int(len(sample_meta)),
            "group_stats": feature_groups,
            "normalization": normalization,
        },
        "processed": processed,
    }


def _cicids_eda(
    source: Path,
    processed_dir: Path,
    *,
    seed: int,
    max_samples: int,
    figures_dir: Path,
    use_processed: bool,
) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    files = discover_cicids_files(source, strict=False)
    total_rows = 0
    per_file: dict[str, Any] = {}
    overall_labels: Counter[str] = Counter()
    inf_counts: Counter[str] = Counter()
    nan_counts: Counter[str] = Counter()
    duplicate_rows = 0
    duplicate_within = 0
    duplicate_cross = 0
    label_conflicts = 0
    duplicate_rows_raw = 0
    label_conflicts_raw = 0
    duplicate_column_checked = 0
    duplicate_column_mismatches = 0
    seen: dict[int, tuple[str, str]] = {}
    seen_raw: dict[int, tuple[str, str]] = {}
    feature_names: list[str] | None = None
    sample_features: list[np.ndarray] = []
    sample_labels: list[str] = []
    sample_binary: list[int] = []
    sample_cap = max(1, max_samples)
    stride = max(1, EXPECTED_TOTAL_ROWS // sample_cap)
    global_row = 0

    for path in files:
        file_rows = 0
        file_labels: Counter[str] = Counter()
        file_duplicates = 0
        for chunk in _iter_chunks(path, chunk_size=200_000):
            chunk, checked, mismatches = _dedupe_columns(chunk)
            duplicate_column_checked += checked
            duplicate_column_mismatches += mismatches
            if feature_names is None:
                feature_names = [column for column in chunk.columns if column != "Label"]
            labels = np.asarray(
                [normalize_label(value) for value in chunk["Label"].astype(str)], dtype=object
            )
            file_rows += len(chunk)
            file_labels.update(labels.tolist())
            overall_labels.update(labels.tolist())
            features = chunk[feature_names].apply(pd.to_numeric, errors="coerce")
            inf_mask = np.isinf(features.to_numpy())
            if inf_mask.any():
                for column, count in zip(feature_names, inf_mask.sum(axis=0), strict=True):
                    if count:
                        inf_counts[column] += int(count)
            features = features.replace([np.inf, -np.inf], np.nan)
            nan_mask = features.isna().to_numpy()
            if nan_mask.any():
                for column, count in zip(feature_names, nan_mask.sum(axis=0), strict=True):
                    if count:
                        nan_counts[column] += int(count)
            valid = ~nan_mask.any(axis=1)
            row_numbers = np.arange(global_row, global_row + len(chunk), dtype=np.int64)
            global_row += len(chunk)
            if len(features) != len(labels):
                raise AssertionError("row alignment lost")
            if not valid.any():
                continue
            features_raw = features.loc[valid].reset_index(drop=True)
            features = features_raw.astype(np.float32)
            labels_valid = labels[valid]
            rows_valid = row_numbers[valid]

            take = rows_valid % stride == 0
            if len(sample_features) < sample_cap and take.any():
                indices = np.flatnonzero(take)[: sample_cap - len(sample_features)]
                sample_features.extend(features.iloc[indices].to_numpy(dtype=np.float32, copy=True))
                sample_labels.extend(labels_valid[indices].tolist())
                sample_binary.extend(binary_label(str(label)) for label in labels_valid[indices])

            keys_raw = _row_keys(features_raw)
            for position, key in enumerate(keys_raw):
                label = str(labels_valid[position])
                if key in seen_raw:
                    duplicate_rows_raw += 1
                    if seen_raw[key][0] != label:
                        label_conflicts_raw += 1
                else:
                    seen_raw[key] = (label, path.name)

            keys = _row_keys(features)
            for position, key in enumerate(keys):
                label = str(labels_valid[position])
                if key in seen:
                    previous_label, previous_file = seen[key]
                    duplicate_rows += 1
                    file_duplicates += 1
                    if previous_file == path.name:
                        duplicate_within += 1
                    else:
                        duplicate_cross += 1
                    if previous_label != label:
                        label_conflicts += 1
                else:
                    seen[key] = (label, path.name)
        total_rows += file_rows
        per_file[path.name] = {
            "rows": file_rows,
            "label_counts": dict(sorted(file_labels.items())),
            "duplicates_dropped": file_duplicates,
        }
        logger.info("EDA scanned %s: %d rows", path.name, file_rows)

    overflow = total_rows - int(overall_labels.get("BENIGN", 0))
    overall_counts = dict(sorted(overall_labels.items()))
    rare_threshold = 100
    rare_classes = {
        label: count for label, count in overall_counts.items() if count < rare_threshold
    }

    processed: dict[str, Any] = {"available": False}
    manifest_path = processed_dir / "manifest.json"
    if use_processed and manifest_path.is_file():
        manifest = load_json(manifest_path)
        processed = {
            "available": True,
            "subset": manifest.get("subset"),
            "manifest": _relative_manifest_path(manifest_path),
            "cleaning": manifest.get("cleaning", {}),
            "splits": manifest.get("splits", {}),
            "labels": manifest.get("labels", {}),
        }

    feature_summary: dict[str, Any] = {}
    selected_features = [
        name
        for name in (
            "Destination Port",
            "Flow Duration",
            "Flow Bytes/s",
            "Flow Packets/s",
            "Packet Length Mean",
            "Average Packet Size",
        )
        if feature_names and name in feature_names
    ]
    sample_matrix = (
        np.stack(sample_features) if sample_features else np.empty((0, len(feature_names or [])))
    )
    if sample_matrix.size:
        for index, name in enumerate(feature_names or []):
            column = sample_matrix[:, index]
            feature_summary[name] = {
                "mean": float(np.mean(column)),
                "std": float(np.std(column)),
                "min": float(np.min(column)),
                "max": float(np.max(column)),
            }
        binary_sample = np.asarray(sample_binary)
        fig, axes = plt.subplots(2, 2, figsize=(10, 6.5))
        for axis, name in zip(axes.ravel(), selected_features[:4], strict=False):
            index = feature_names.index(name)
            values = sample_matrix[:, index]
            if name in ("Flow Bytes/s", "Flow Packets/s", "Flow Duration"):
                values = np.log1p(np.maximum(values, 0))
                axis.set_xlabel(f"log1p({name})")
            else:
                axis.set_xlabel(name)
            axis.hist(
                values[binary_sample == 0],
                bins=40,
                alpha=0.6,
                label="BENIGN",
                color="#55a868",
            )
            axis.hist(
                values[binary_sample == 1],
                bins=40,
                alpha=0.6,
                label="ATTACK",
                color="#c44e52",
            )
            axis.set_ylabel("rows")
            axis.legend(fontsize=7)
            axis.tick_params(labelsize=7)
        fig.suptitle(f"CIC-IDS-2017 sample feature distributions (n={len(sample_features):,})")
        fig.tight_layout()
        _save_figure(fig, figures_dir / "data_cicids_feature_histograms.png")

    class_labels = list(overall_counts)
    class_counts = [overall_counts[label] for label in class_labels]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(class_labels[::-1], class_counts[::-1], color="#4c72b0")
    ax.set_xscale("log")
    ax.set_xlabel("rows (log scale)")
    ax.set_title("CIC-IDS-2017 class distribution (all source rows)")
    for index, value in enumerate(class_counts[::-1]):
        ax.text(value, index, f" {value:,}", va="center", fontsize=7)
    _save_figure(fig, figures_dir / "data_cicids_class_counts.png")

    fig, ax = plt.subplots(figsize=(9, 4))
    names = list(per_file)
    benign = [per_file[name]["label_counts"].get("BENIGN", 0) for name in names]
    attack = [
        per_file[name]["rows"] - per_file[name]["label_counts"].get("BENIGN", 0) for name in names
    ]
    x = np.arange(len(names))
    ax.bar(x, benign, label="BENIGN", color="#55a868")
    ax.bar(x, attack, bottom=benign, label="ATTACK", color="#c44e52")
    ax.set_xticks(x)
    ax.set_xticklabels(
        [name.replace(".pcap_ISCX.csv", "") for name in names], rotation=35, ha="right"
    )
    ax.set_ylabel("rows")
    ax.set_title("CIC-IDS-2017 rows per source file")
    ax.legend()
    _save_figure(fig, figures_dir / "data_cicids_per_file.png")

    affected = sorted(set(inf_counts) | set(nan_counts))
    if affected:
        fig, ax = plt.subplots(figsize=(7, 3.5))
        x = np.arange(len(affected))
        inf_values = [inf_counts.get(name, 0) for name in affected]
        nan_values = [nan_counts.get(name, 0) for name in affected]
        ax.bar(x - 0.18, inf_values, width=0.36, label="inf", color="#c44e52")
        ax.bar(x + 0.18, nan_values, width=0.36, label="NaN", color="#8172b2")
        ax.set_xticks(x)
        ax.set_xticklabels(affected, rotation=20, ha="right")
        ax.set_ylabel("values")
        ax.set_title("CIC-IDS-2017 non-finite values per column")
        ax.legend()
        _save_figure(fig, figures_dir / "data_cicids_inf_nan.png")

    return {
        "source": {
            "files": {name: per_file[name] for name in per_file},
            "rows": int(total_rows),
            "class_counts": overall_counts,
            "binary_balance": {
                "BENIGN": int(overall_labels.get("BENIGN", 0)),
                "ATTACK": int(overflow),
                "benign_fraction": round(float(overall_labels.get("BENIGN", 0)) / total_rows, 6)
                if total_rows
                else None,
            },
            "rare_classes_below_100": rare_classes,
        },
        "cleaning": {
            "feature_dim": int(len(feature_names or [])),
            "duplicate_column": {
                "rows_checked": int(duplicate_column_checked),
                "mismatches": int(duplicate_column_mismatches),
            },
            "inf_values": int(sum(inf_counts.values())),
            "inf_counts_per_column": dict(sorted(inf_counts.items())),
            "nan_values": int(sum(nan_counts.values())),
            "nan_counts_per_column": dict(sorted(nan_counts.items())),
            "duplicate_rows": {
                "total": int(duplicate_rows),
                "within_file": int(duplicate_within),
                "cross_file": int(duplicate_cross),
                "key_precision": "float32 (stored feature precision)",
            },
            "duplicate_rows_raw_float64": int(duplicate_rows_raw),
            "label_conflicts_for_identical_rows": int(label_conflicts),
            "label_conflicts_raw_float64": int(label_conflicts_raw),
        },
        "feature_sample": {
            "rows": int(len(sample_features)),
            "stride": stride,
            "features": feature_summary,
            "plotted_features": selected_features,
        },
        "processed": processed,
    }


def _relative_manifest_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def _format_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def _build_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Dataset EDA report (Sprint 2)",
        "",
        "> Generated by `scripts/eda_datasets.py` from the local raw datasets and,",
        "> when available, the processed manifests. Do not hand-edit numbers;",
        "> regenerate the report instead.",
        "",
        f"- Seed: `{payload['seed']}`",
        f"- Generated at (UTC): `{payload['generated_at']}`",
        f"- Feature-summary sample cap: `{payload['max_samples']}` rows per dataset",
        "",
    ]
    ember = payload.get("datasets", {}).get("ember2018")
    if ember:
        source = ember["source"]
        lines += [
            "## EMBER2018 v2",
            "",
            f"Source rows: **{source['rows']:,}**.",
            "",
            _format_table(
                ["Label", "Rows"],
                [[key, f"{value:,}"] for key, value in source["label_counts"].items()],
            ),
            "",
            f"Duplicate sha256 rows: **{ember['duplicate_sha256']['duplicate_rows']:,}** "
            f"({ember['duplicate_sha256']['duplicate_groups']:,} groups). "
            f"Missing required keys: "
            f"`{ember['source']['missing_required_keys'] or 'none'}`.",
            "",
        ]
        normalization = ember["feature_sample"]["normalization"]
        lines += [
            "Feature-group summary on the deterministic sample "
            f"(n={ember['feature_sample']['rows']:,}):",
            "",
            _format_table(
                ["Group", "Dim", "Non-zero fraction", "Mean variance"],
                [
                    [
                        name,
                        stats["dim"],
                        f"{stats['nonzero_fraction']:.4f}",
                        f"{stats['mean_variance']:.6g}",
                    ]
                    for name, stats in ember["feature_sample"]["group_stats"].items()
                ],
            ),
            "",
            f"- Histogram sums close to 1: **{normalization.get('histogram_all_close_to_one')}** "
            f"(range {normalization.get('histogram_sum_min')} to "
            f"{normalization.get('histogram_sum_max')}).",
            f"- Byte-entropy sums close to 1: "
            f"**{normalization.get('byteentropy_all_close_to_one')}** "
            f"(range {normalization.get('byteentropy_sum_min')} to "
            f"{normalization.get('byteentropy_sum_max')}).",
            "",
        ]
        processed = ember.get("processed", {})
        if processed.get("available"):
            splits = processed.get("splits", {})
            lines += [
                "Processed split counts (from manifest):",
                "",
                _format_table(
                    ["Split", "Rows", "Label counts", "Appeared range"],
                    [
                        [
                            name,
                            f"{stats.get('rows', 0):,}",
                            stats.get("label_counts", {}),
                            f"{stats.get('min_appeared')} .. {stats.get('max_appeared')}",
                        ]
                        for name, stats in splits.items()
                    ],
                ),
                "",
                f"Validation strategy: `{processed.get('split_strategy', {}).get('strategy')}`; "
                f"cross-split duplicates: "
                f"`{processed.get('duplicates', {}).get('cross_split_sha256')}`.",
                "",
            ]

    cicids = payload.get("datasets", {}).get("cicids2017")
    if cicids:
        source = cicids["source"]
        cleaning = cicids["cleaning"]
        lines += [
            "## CIC-IDS-2017",
            "",
            f"Source rows: **{source['rows']:,}**. Feature dimension after removing the "
            f"duplicate column: **{cleaning['feature_dim']}**.",
            "",
            _format_table(
                ["File", "Rows", "BENIGN", "ATTACK", "Duplicates dropped"],
                [
                    [
                        name,
                        f"{stats['rows']:,}",
                        f"{stats['label_counts'].get('BENIGN', 0):,}",
                        f"{stats['rows'] - stats['label_counts'].get('BENIGN', 0):,}",
                        f"{stats['duplicates_dropped']:,}",
                    ]
                    for name, stats in source["files"].items()
                ],
            ),
            "",
            f"Binary balance: **{source['binary_balance']['BENIGN']:,} BENIGN** "
            f"({source['binary_balance']['benign_fraction']:.4%}) and "
            f"**{source['binary_balance']['ATTACK']:,} ATTACK**.",
            "",
            _format_table(
                ["Class", "Rows"],
                [[label, f"{count:,}"] for label, count in source["class_counts"].items()],
            ),
            "",
            f"- Inf values: **{cleaning['inf_values']:,}**; NaN values: "
            f"**{cleaning['nan_values']:,}**.",
            f"- Duplicate rows dropped at stored float32 precision: "
            f"**{cleaning['duplicate_rows']['total']:,}** "
            f"(within file {cleaning['duplicate_rows']['within_file']:,}, "
            f"cross file {cleaning['duplicate_rows']['cross_file']:,}). "
            f"At raw float64 precision: **{cleaning['duplicate_rows_raw_float64']:,}**.",
            f"- Identical rows with conflicting labels (float32 / float64): "
            f"**{cleaning['label_conflicts_for_identical_rows']:,}** / "
            f"**{cleaning['label_conflicts_raw_float64']:,}**.",
            f"- Duplicate-column equality check: "
            f"{cleaning['duplicate_column']['rows_checked']:,} rows, "
            f"{cleaning['duplicate_column']['mismatches']} mismatches.",
            f"- Rare classes (<100 rows): `{source['rare_classes_below_100']}`.",
            "",
        ]
        processed = cicids.get("processed", {})
        if processed.get("available"):
            splits = processed.get("splits", {})
            lines += [
                "Processed split counts (from manifest):",
                "",
                _format_table(
                    ["Split", "Rows", "Fraction"],
                    [
                        [
                            name,
                            f"{stats.get('rows', 0):,}",
                            stats.get("fraction"),
                        ]
                        for name, stats in splits.items()
                        if name in ("train", "val", "test")
                    ],
                ),
                "",
                "Multiclass classes absent from a split: "
                f"`{splits.get('multiclass_absent_from_split', {})}`.",
                "",
            ]
        sample = cicids["feature_sample"]
        lines += [
            f"Feature distributions use a systematic sample of **{sample['rows']:,}** rows "
            f"(stride {sample['stride']}); the source/cleaning counts above cover all rows.",
            "",
        ]

    lines += [
        "## Notes and limitations",
        "",
        "- EMBER2018 v2 is not EMBER2024; the official 200k test set is never moved into train/val.",
        "- EMBER validation is time-based (latest ~15%); the official test split is untouched.",
        "- CIC-IDS-2017 is lab/simulated traffic from 2017; exact duplicates are removed before",
        "  the stratified split to reduce leakage, but near-duplicates and label errors remain.",
        "- No resampling or class weighting is applied in Sprint 2; rare classes may be absent",
        "  from validation/test splits because splits are stratified on the binary target only.",
        "- Figures use compact summaries only; no pairplots over the 2381 EMBER features.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args(argv)
    set_seed(args.seed)
    if args.max_samples < 1:
        logger.error("--max-samples must be positive")
        return 2
    if args.dataset == "all" and args.source:
        logger.error("--source is ambiguous with --dataset all; use --ember-source/--cicids-source")
        return 2
    if args.dataset != "all" and (args.ember_source or args.cicids_source):
        logger.error("--ember-source/--cicids-source require --dataset all")
        return 2

    results_path, figures_dir, report_path = _output_paths(args)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()  # noqa: UP017
    payload: dict[str, Any] = {
        "generated_at": generated_at,
        "seed": args.seed,
        "max_samples": args.max_samples,
        "datasets": {},
    }

    try:
        if args.dataset in ("ember", "all"):
            source = resolve_ember_source(
                args.source if args.dataset == "ember" else args.ember_source
            )
            processed = (
                Path(args.ember_processed_dir) if args.ember_processed_dir else EMBER_PROCESSED_DIR
            )
            logger.info("EDA EMBER source %s", source)
            payload["datasets"]["ember2018"] = _ember_eda(
                source,
                processed,
                seed=args.seed,
                max_samples=args.max_samples,
                jobs=args.jobs,
                figures_dir=figures_dir,
                use_processed=not args.no_processed,
            )
        if args.dataset in ("cicids2017", "all"):
            source = resolve_cicids_source(
                args.source if args.dataset == "cicids2017" else args.cicids_source
            )
            processed = (
                Path(args.cicids_processed_dir)
                if args.cicids_processed_dir
                else CICIDS_PROCESSED_DIR
            )
            logger.info("EDA CICIDS source %s", source)
            payload["datasets"]["cicids2017"] = _cicids_eda(
                source,
                processed,
                seed=args.seed,
                max_samples=args.max_samples,
                figures_dir=figures_dir,
                use_processed=not args.no_processed,
            )
    except Exception as error:
        logger.error("EDA failed: %s", error)
        raise

    results_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    write_json_atomic(results_path, payload)
    atomic_write_text(report_path, _build_report(payload))
    logger.info("wrote %s", results_path)
    logger.info("wrote %s", report_path)
    logger.info("wrote figures to %s", figures_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
