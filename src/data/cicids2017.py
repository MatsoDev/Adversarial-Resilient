"""CIC-IDS-2017 loading, cleaning, deduplication and preprocessing.

This module reads the eight original UNB/CIC CSV files in place. It does not
use any third-party "cleaned" Kaggle copy. Known local quirks are handled and
recorded in the manifest: leading/trailing spaces in 65/79 column names, a
duplicate ``Fwd Header Length.1`` column, U+FFFD characters in web-attack
labels, infinities/NaNs, and exact duplicate rows.
"""

from __future__ import annotations

import logging
import re
import shutil
from collections import Counter
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.data.preprocessing import (
    artifact_record,
    atomic_save_npy,
    atomic_write_dataframe,
    code_revision,
    compute_scaler_stats,
    load_json,
    sha256_file,
    stratified_split_indices,
    utc_now_iso,
    verify_manifest_artifacts,
    write_json_atomic,
)
from src.utils.seed import set_seed

logger = logging.getLogger(__name__)

FILE_ORDER: tuple[str, ...] = (
    "Monday-WorkingHours.pcap_ISCX.csv",
    "Tuesday-WorkingHours.pcap_ISCX.csv",
    "Wednesday-workingHours.pcap_ISCX.csv",
    "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv",
    "Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv",
    "Friday-WorkingHours-Morning.pcap_ISCX.csv",
    "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
    "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv",
)

EXPECTED_FILE_ROWS: dict[str, int] = {
    "Monday-WorkingHours.pcap_ISCX.csv": 529_918,
    "Tuesday-WorkingHours.pcap_ISCX.csv": 445_909,
    "Wednesday-workingHours.pcap_ISCX.csv": 692_703,
    "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv": 170_366,
    "Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv": 288_602,
    "Friday-WorkingHours-Morning.pcap_ISCX.csv": 191_033,
    "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv": 225_745,
    "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv": 286_467,
}
EXPECTED_TOTAL_ROWS = 2_830_743
EXPECTED_BINARY_COUNTS = {"BENIGN": 2_273_097, "ATTACK": 557_646}
EXPECTED_FEATURE_DIM = 77

SOURCE_SHA256: dict[str, str] = {
    "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv": (
        "6ff1580f5f81c0ae28a26f7631721018577f5f7c5e0feac28b795fcfe7b411ee"
    ),
    "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv": (
        "ca1824c51bfbb7b3c72290a11be04366ba8815878c6a1cc5c44cb1cee269e99b"
    ),
    "Friday-WorkingHours-Morning.pcap_ISCX.csv": (
        "53a41c24d570ea83b7ac55b2e94df94e7a8216aeb80a2af0246b6bc8bb543000"
    ),
    "Monday-WorkingHours.pcap_ISCX.csv": (
        "852c4beb34eda186f32561fa79df7a0747e92e1a6535b01270820dd9ffe17f34"
    ),
    "Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv": (
        "6bcda3857c2504676034e3ea57762d38393cc734cb377a726bd5cb153961b1b5"
    ),
    "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv": (
        "d67066211fb1689c78406f1506f4c44704ecb92088353d5c96d96d6474eb819d"
    ),
    "Tuesday-WorkingHours.pcap_ISCX.csv": (
        "52b8692ae8c7d2ed04671fe2b98335693c0a92c7ab157d8c8b534d6523080851"
    ),
    "Wednesday-workingHours.pcap_ISCX.csv": (
        "893c27dc968bf7a8adef1689f90be55ca4a4dc3088fb63d6ff247ac56856df2a"
    ),
}

KNOWN_LABELS: tuple[str, ...] = (
    "BENIGN",
    "Bot",
    "DDoS",
    "DoS GoldenEye",
    "DoS Hulk",
    "DoS Slowhttptest",
    "DoS slowloris",
    "FTP-Patator",
    "Heartbleed",
    "Infiltration",
    "PortScan",
    "SSH-Patator",
    "Web Attack - Brute Force",
    "Web Attack - SQL Injection",
    "Web Attack - XSS",
)

_CANONICAL_BY_LOWER = {label.lower(): label for label in KNOWN_LABELS}
_DUPLICATE_COLUMN = "Fwd Header Length.1"
_ORIGINAL_DUPLICATE_COLUMN = "Fwd Header Length"
_WHITESPACE_RE = re.compile(r"\s+")


def _label_key(value: object) -> str:
    text = str(value).strip()
    text = text.replace("\ufffd", "-")
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = _WHITESPACE_RE.sub(" ", text)
    return text


def normalize_label(value: object) -> str:
    """Normalise a raw CICIDS label to one of the documented canonical names."""
    text = _label_key(value)
    canonical = _CANONICAL_BY_LOWER.get(text.lower())
    if canonical is None:
        raise ValueError(
            f"unknown CICIDS label {value!r} (normalised to {text!r}); "
            "add it to KNOWN_LABELS with a documented mapping"
        )
    return canonical


def binary_label(label: str) -> int:
    return 0 if label == "BENIGN" else 1


def discover_cicids_files(source_dir: str | Path, *, strict: bool = True) -> tuple[Path, ...]:
    """Discover the eight CIC-IDS-2017 CSV files in canonical day order."""
    source = Path(source_dir).expanduser()
    if not source.is_dir():
        raise FileNotFoundError(
            f"CIC-IDS-2017 source directory not found: {source}. "
            "Set CICIDS_DATA_DIR or pass --source."
        )
    found = list(source.glob("*.csv"))
    if not found:
        raise FileNotFoundError(f"no CSV files in {source}")
    order = {name: index for index, name in enumerate(FILE_ORDER)}
    files = tuple(sorted(found, key=lambda path: (order.get(path.name, 10**9), path.name)))
    if strict:
        names = [path.name for path in files]
        if names != list(FILE_ORDER):
            raise FileNotFoundError(
                f"expected the eight CIC-IDS-2017 files {list(FILE_ORDER)}, found {names}"
            )
    return files


def _detect_encoding(path: Path) -> str:
    """Try strict UTF-8 on a prefix; fall back to latin-1 when needed."""
    with open(path, "rb") as handle:
        sample = handle.read(1 << 20)
    try:
        sample.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        return "latin-1"


def _iter_chunks(path: Path, *, chunk_size: int) -> Iterator[pd.DataFrame]:
    encoding = _detect_encoding(path)
    yield from pd.read_csv(
        path,
        chunksize=chunk_size,
        low_memory=False,
        encoding=encoding,
        encoding_errors="replace",
    )


def _dedupe_columns(
    chunk: pd.DataFrame,
) -> tuple[pd.DataFrame, int, int]:
    """Strip column names, verify and drop the duplicate Fwd Header Length column."""
    chunk.columns = [str(column).strip() for column in chunk.columns]
    if "Label" not in chunk.columns:
        raise ValueError(f"missing 'Label' column; found {list(chunk.columns)[-5:]}")
    if chunk.columns.duplicated().any():
        duplicates = chunk.columns[chunk.columns.duplicated()].tolist()
        raise ValueError(f"unexpected duplicate column names after stripping: {duplicates}")

    rows_checked = 0
    mismatches = 0
    if _DUPLICATE_COLUMN in chunk.columns:
        if _ORIGINAL_DUPLICATE_COLUMN not in chunk.columns:
            raise ValueError(f"{_DUPLICATE_COLUMN} present without {_ORIGINAL_DUPLICATE_COLUMN}")
        left = pd.to_numeric(chunk[_ORIGINAL_DUPLICATE_COLUMN], errors="coerce")
        right = pd.to_numeric(chunk[_DUPLICATE_COLUMN], errors="coerce")
        equal = (left == right) | (left.isna() & right.isna())
        mismatches = int((~equal).sum())
        rows_checked = len(chunk)
        if mismatches:
            raise ValueError(
                f"{_DUPLICATE_COLUMN} differs from {_ORIGINAL_DUPLICATE_COLUMN} "
                f"in {mismatches} rows; refusing to drop a non-identical column"
            )
        chunk = chunk.drop(columns=[_DUPLICATE_COLUMN])
    return chunk, rows_checked, mismatches


def _row_keys(features: pd.DataFrame) -> list[int]:
    """128-bit exact-row keys for duplicate detection (two pandas hashes)."""
    first = pd.util.hash_pandas_object(features, index=False).to_numpy(dtype=np.uint64)
    reversed_columns = pd.util.hash_pandas_object(features.iloc[:, ::-1], index=False).to_numpy(
        dtype=np.uint64
    )
    return [
        (int(left) << 64) | int(right) for left, right in zip(first, reversed_columns, strict=True)
    ]


def _stratified_subset_indices(binary: np.ndarray, *, max_samples: int, seed: int) -> np.ndarray:
    if max_samples >= len(binary):
        return np.arange(len(binary), dtype=np.int64)
    from sklearn.model_selection import train_test_split

    if max_samples < len(np.unique(binary)):
        raise ValueError("max_samples must be at least the number of binary classes")
    chosen, _ = train_test_split(
        np.arange(len(binary)),
        train_size=max_samples,
        random_state=seed,
        stratify=binary,
    )
    return np.sort(chosen)


def _check_source_composition(
    file_stats: Sequence[dict[str, Any]],
    label_counts: Counter[str],
    total_rows: int,
    *,
    force: bool,
) -> None:
    if force:
        return
    problems: list[str] = []
    if total_rows != EXPECTED_TOTAL_ROWS:
        problems.append(f"total rows {total_rows} != {EXPECTED_TOTAL_ROWS}")
    for stat in file_stats:
        expected = EXPECTED_FILE_ROWS.get(stat["name"])
        if expected is not None and stat["rows"] != expected:
            problems.append(f"{stat['name']} rows {stat['rows']} != {expected}")
    benign = int(label_counts.get("BENIGN", 0))
    attack = int(total_rows - benign)
    if benign != EXPECTED_BINARY_COUNTS["BENIGN"] or attack != EXPECTED_BINARY_COUNTS["ATTACK"]:
        problems.append(
            f"binary counts BENIGN={benign}, ATTACK={attack} != {EXPECTED_BINARY_COUNTS}"
        )
    if problems:
        raise ValueError(
            "CIC-IDS-2017 source does not match the expected composition: "
            + "; ".join(problems)
            + " (use --force to override)"
        )


def _split_class_counts(
    labels: np.ndarray, multiclass: np.ndarray, split: np.ndarray
) -> dict[str, Any]:
    binary_counts: dict[str, dict[str, int]] = {}
    for label in (0, 1):
        mask = labels == label
        binary_counts[str(label)] = {
            "train": int(np.sum(mask & (split == 0))),
            "val": int(np.sum(mask & (split == 1))),
            "test": int(np.sum(mask & (split == 2))),
        }
    multiclass_counts: dict[str, dict[str, int]] = {}
    for label in sorted(set(multiclass.tolist())):
        mask = multiclass == label
        multiclass_counts[str(label)] = {
            "train": int(np.sum(mask & (split == 0))),
            "val": int(np.sum(mask & (split == 1))),
            "test": int(np.sum(mask & (split == 2))),
        }
    return {"binary": binary_counts, "multiclass": multiclass_counts}


def _source_file_info(
    paths: Sequence[Path], *, verify_hashes: bool, force: bool
) -> dict[str, dict[str, Any]]:
    infos: dict[str, dict[str, Any]] = {}
    for path in paths:
        info: dict[str, Any] = {"name": path.name, "size_bytes": path.stat().st_size}
        if verify_hashes:
            digest = sha256_file(path)
            info["sha256"] = digest
            expected = SOURCE_SHA256.get(path.name)
            if expected and digest != expected and not force:
                raise ValueError(
                    f"sha256 mismatch for {path.name}: expected {expected}, found {digest} "
                    "(use --force to override)"
                )
        infos[path.name] = info
    return infos


def _guard_subset_output(output: Path, *, subset: bool) -> None:
    if not subset:
        return
    manifest_path = output / "manifest.json"
    if not manifest_path.is_file():
        return
    existing = load_json(manifest_path)
    if not existing.get("subset", True):
        raise RuntimeError(
            f"refusing to overwrite full-run artifacts in {output} with a subset run; "
            "choose a different --output-dir"
        )


def run_cicids_preprocessing(
    source_dir: str | Path,
    output_dir: str | Path,
    *,
    seed: int = 42,
    max_samples: int | None = None,
    jobs: int = 1,
    force: bool = False,
    verify_source: bool = True,
    scaler: bool = True,
    chunk_size: int = 200_000,
    max_drop_fraction: float = 0.01,
) -> dict[str, Any]:
    """Run the complete CIC-IDS-2017 cleaning/splitting pipeline."""
    set_seed(seed)
    if jobs > 1:
        logger.info("CICIDS preprocessing is single-process (global dedup); --jobs ignored")
    source = Path(source_dir).expanduser()
    output = Path(output_dir).expanduser()
    output.mkdir(parents=True, exist_ok=True)
    subset = max_samples is not None
    _guard_subset_output(output, subset=subset)

    files = discover_cicids_files(source, strict=verify_source)
    source_infos = _source_file_info(files, verify_hashes=verify_source, force=force)
    logger.info("CICIDS source: %d CSV files under %s", len(files), source)

    file_stats: list[dict[str, Any]] = []
    feature_names: list[str] | None = None
    total_rows = 0
    rows_after_invalid = 0
    rows_dropped_invalid = 0
    inf_counts = Counter()
    nan_counts = Counter()
    nan_before_counts = Counter()
    duplicate_column_rows_checked = 0
    duplicate_column_mismatches = 0
    duplicate_rows_total = 0
    label_conflicts_total = 0
    duplicate_within_file = 0
    duplicate_cross_file = 0
    encodings: dict[str, str] = {}

    seen: dict[int, tuple[str, str]] = {}
    feature_parts: list[pd.DataFrame] = []
    metadata_parts: list[pd.DataFrame] = []
    all_label_counts: Counter[str] = Counter()

    for _file_index, path in enumerate(files):
        logger.info("cleaning %s", path.name)
        file_rows = 0
        file_label_counts: Counter[str] = Counter()
        file_invalid = 0
        file_duplicates = 0
        file_within_duplicates = 0
        file_cross_duplicates = 0
        file_conflicts = 0
        encodings[path.name] = _detect_encoding(path)

        for chunk in _iter_chunks(path, chunk_size=chunk_size):
            chunk, checked, mismatches = _dedupe_columns(chunk)
            duplicate_column_rows_checked += checked
            duplicate_column_mismatches += mismatches
            if feature_names is None:
                feature_names = [column for column in chunk.columns if column != "Label"]
                if verify_source and len(feature_names) != EXPECTED_FEATURE_DIM and not force:
                    raise ValueError(
                        f"expected {EXPECTED_FEATURE_DIM} numeric features, "
                        f"found {len(feature_names)}"
                    )
            elif [column for column in chunk.columns if column != "Label"] != feature_names:
                raise ValueError(f"column layout differs in {path.name}")

            base_row = total_rows
            source_rows = np.arange(base_row, base_row + len(chunk), dtype=np.int64)
            file_rows += len(chunk)
            total_rows += len(chunk)

            raw_labels = chunk["Label"].astype(str)
            labels = np.asarray([normalize_label(value) for value in raw_labels], dtype=object)
            file_label_counts.update(labels.tolist())
            all_label_counts.update(labels.tolist())

            features = chunk[feature_names].apply(pd.to_numeric, errors="coerce")
            inf_mask = np.isinf(features.to_numpy())
            nan_before_mask = features.isna().to_numpy()
            if inf_mask.any():
                columns = np.asarray(feature_names)
                for column, count in zip(columns, inf_mask.sum(axis=0), strict=True):
                    if count:
                        inf_counts[str(column)] += int(count)
            if nan_before_mask.any():
                columns = np.asarray(feature_names)
                for column, count in zip(columns, nan_before_mask.sum(axis=0), strict=True):
                    if count:
                        nan_before_counts[str(column)] += int(count)
            features = features.replace([np.inf, -np.inf], np.nan)
            nan_mask = features.isna().to_numpy()
            if nan_mask.any():
                columns = np.asarray(feature_names)
                for column, count in zip(columns, nan_mask.sum(axis=0), strict=True):
                    if count:
                        nan_counts[str(column)] += int(count)

            valid_mask = ~nan_mask.any(axis=1)
            invalid = int((~valid_mask).sum())
            file_invalid += invalid
            rows_dropped_invalid += invalid
            rows_after_invalid += int(valid_mask.sum())
            if invalid:
                features = features.loc[valid_mask]
                labels = labels[valid_mask]
                source_rows = source_rows[valid_mask]

            if features.empty:
                continue
            features = features.astype(np.float32).reset_index(drop=True)
            keys = _row_keys(features)
            keep = np.zeros(len(features), dtype=bool)
            for position, key in enumerate(keys):
                label = str(labels[position])
                if key in seen:
                    previous_label, previous_file = seen[key]
                    file_duplicates += 1
                    duplicate_rows_total += 1
                    if previous_file == path.name:
                        file_within_duplicates += 1
                        duplicate_within_file += 1
                    else:
                        file_cross_duplicates += 1
                        duplicate_cross_file += 1
                    if previous_label != label:
                        file_conflicts += 1
                        label_conflicts_total += 1
                else:
                    seen[key] = (label, path.name)
                    keep[position] = True
            if file_duplicates:
                features = features.loc[keep].reset_index(drop=True)
                labels = labels[keep]
                source_rows = source_rows[keep]
            if features.empty:
                continue
            feature_parts.append(features)
            metadata_parts.append(
                pd.DataFrame(
                    {
                        "source_file": path.name,
                        "source_row": source_rows,
                        "label": labels,
                    }
                )
            )

        file_stats.append(
            {
                "name": path.name,
                "size_bytes": source_infos[path.name]["size_bytes"],
                "sha256": source_infos[path.name].get("sha256"),
                "encoding": encodings[path.name],
                "rows": file_rows,
                "label_counts": dict(sorted(file_label_counts.items())),
                "rows_dropped_invalid": file_invalid,
                "duplicates_dropped": file_duplicates,
                "duplicates_within_file": file_within_duplicates,
                "duplicates_cross_file": file_cross_duplicates,
                "label_conflicts": file_conflicts,
            }
        )

    if feature_names is None or not feature_parts:
        raise RuntimeError("no usable CICIDS rows were found")
    if feature_names is None:
        raise RuntimeError("could not determine feature names")

    if verify_source:
        _check_source_composition(file_stats, all_label_counts, total_rows, force=force)

    drop_fraction = rows_dropped_invalid / total_rows if total_rows else 0.0
    if drop_fraction > max_drop_fraction and not force:
        raise RuntimeError(
            f"dropping {rows_dropped_invalid} invalid rows ({drop_fraction:.3%}) exceeds "
            f"the {max_drop_fraction:.1%} safety threshold; document instead of silently "
            "losing data (use --force to override)"
        )

    features_all = pd.concat(feature_parts, ignore_index=True)
    metadata_all = pd.concat(metadata_parts, ignore_index=True)
    del feature_parts, metadata_parts
    if len(features_all) != len(metadata_all):
        raise AssertionError("feature and metadata row counts diverged")

    labels_all = metadata_all["label"].to_numpy(dtype=object)
    binary_all = np.asarray([binary_label(label) for label in labels_all], dtype=np.int8)
    multiclass_names = sorted(set(labels_all.tolist()))
    multiclass_mapping = {label: index for index, label in enumerate(multiclass_names)}
    multiclass_all = np.asarray([multiclass_mapping[label] for label in labels_all], dtype=np.int16)
    rows_after_dedup = int(len(features_all))
    source_binary_counts = {
        "BENIGN": int(all_label_counts.get("BENIGN", 0)),
        "ATTACK": int(total_rows - all_label_counts.get("BENIGN", 0)),
    }

    if subset:
        selected = _stratified_subset_indices(binary_all, max_samples=max_samples, seed=seed)
        features_all = features_all.iloc[selected].reset_index(drop=True)
        metadata_all = metadata_all.iloc[selected].reset_index(drop=True)
        labels_all = labels_all[selected]
        binary_all = binary_all[selected]
        multiclass_all = multiclass_all[selected]

    split_indices = stratified_split_indices(binary_all, seed=seed)
    split_codes = np.empty(len(binary_all), dtype=np.int8)
    for code, split_name in enumerate(("train", "val", "test")):
        split_codes[split_indices[split_name]] = code

    split_frames: dict[str, dict[str, Any]] = {}
    for _code, split_name in enumerate(("train", "val", "test")):
        indices = split_indices[split_name]
        split_frames[split_name] = {
            "X": features_all.iloc[indices].reset_index(drop=True),
            "y_binary": binary_all[indices].astype(np.int8),
            "y_multiclass": multiclass_all[indices].astype(np.int16),
            "metadata": metadata_all.iloc[indices].reset_index(drop=True),
            "indices": indices,
        }

    class_counts = _split_class_counts(binary_all, multiclass_all, split_codes)
    multiclass_names_by_id = {str(index): label for label, index in multiclass_mapping.items()}
    absent = {
        split_name: [
            multiclass_names_by_id[key]
            for key, counts in class_counts["multiclass"].items()
            if counts[split_name] == 0
        ]
        for split_name in ("train", "val", "test")
    }

    feature_dim = len(feature_names)
    estimated_bytes = len(features_all) * feature_dim * 4
    free_bytes = shutil.disk_usage(output).free
    if free_bytes < int(estimated_bytes * 1.2) + 100_000_000:
        raise RuntimeError(
            f"not enough free disk under {output}: need about "
            f"{estimated_bytes * 1.2 / 1e9:.1f} GB, have {free_bytes / 1e9:.1f} GB"
        )

    for split_name, payload in split_frames.items():
        X = payload["X"].to_numpy(dtype=np.float32, copy=True)
        if not np.isfinite(X).all():
            raise AssertionError(f"{split_name} contains non-finite features after cleaning")
        atomic_save_npy(output / f"{split_name}_X.npy", X)
        atomic_save_npy(output / f"{split_name}_y_binary.npy", payload["y_binary"])
        atomic_save_npy(output / f"{split_name}_y_multiclass.npy", payload["y_multiclass"])
        metadata = payload["metadata"].copy()
        metadata["label_binary"] = payload["y_binary"]
        metadata["label_multiclass"] = payload["y_multiclass"]
        metadata["split"] = split_name
        atomic_write_dataframe(
            metadata,
            output / f"{split_name}_metadata.csv",
            columns=[
                "source_file",
                "source_row",
                "label",
                "label_binary",
                "label_multiclass",
                "split",
            ],
        )
        logger.info("wrote %s_X.npy (%d rows, %d features)", split_name, len(X), feature_dim)

    feature_names_path = output / "feature_names.json"
    write_json_atomic(feature_names_path, feature_names)
    label_mapping_path = output / "label_mapping.json"
    write_json_atomic(
        label_mapping_path,
        {
            "dataset": "cicids2017",
            "binary": {"BENIGN": 0, "ATTACK": 1},
            "multiclass": multiclass_mapping,
            "multiclass_names": multiclass_names_by_id,
            "raw_to_canonical": {
                "strip_whitespace": True,
                "replace_U+FFFD_with": "-",
                "collapse_whitespace": True,
            },
        },
    )

    scaler_files: list[Path] = []
    if scaler:
        mean, scale = compute_scaler_stats(split_frames["train"]["X"])
        mean_path = output / "scaler_mean.npy"
        scale_path = output / "scaler_scale.npy"
        atomic_save_npy(mean_path, mean)
        atomic_save_npy(scale_path, scale)
        scaler_files = [mean_path, scale_path]
        write_json_atomic(
            output / "scaler.json",
            {
                "dataset": "cicids2017",
                "fit_split": "train",
                "n_samples": int(len(split_frames["train"]["X"])),
                "n_features": feature_dim,
                "zero_variance_scale": 1.0,
            },
        )

    artifacts: dict[str, Any] = {}
    for split_name, payload in split_frames.items():
        artifacts[f"{split_name}_X"] = artifact_record(
            output / f"{split_name}_X.npy",
            root=output,
            shape=payload["X"].shape,
            dtype="float32",
        )
        artifacts[f"{split_name}_y_binary"] = artifact_record(
            output / f"{split_name}_y_binary.npy",
            root=output,
            shape=payload["y_binary"].shape,
            dtype="int8",
        )
        artifacts[f"{split_name}_y_multiclass"] = artifact_record(
            output / f"{split_name}_y_multiclass.npy",
            root=output,
            shape=payload["y_multiclass"].shape,
            dtype="int16",
        )
        artifacts[f"{split_name}_metadata"] = artifact_record(
            output / f"{split_name}_metadata.csv", root=output
        )
    artifacts["feature_names"] = artifact_record(feature_names_path, root=output)
    artifacts["label_mapping"] = artifact_record(label_mapping_path, root=output)
    for path in scaler_files:
        artifacts[path.stem] = artifact_record(path, root=output)
    if scaler:
        artifacts["scaler"] = artifact_record(output / "scaler.json", root=output)

    source_files = []
    for stat in file_stats:
        record = dict(stat)
        record["expected_rows"] = EXPECTED_FILE_ROWS.get(stat["name"])
        source_files.append(record)

    used_binary_counts = {
        "BENIGN": int(np.sum(binary_all == 0)),
        "ATTACK": int(np.sum(binary_all == 1)),
    }
    manifest: dict[str, Any] = {
        "dataset": "cicids2017",
        "dataset_version": "CIC-IDS-2017 original UNB/CIC CSV release (8 files)",
        "subset": subset,
        "seed": seed,
        "generated_at": utc_now_iso(),
        "code_revision": code_revision(),
        "source_resolution": (
            "CLI --source > CICIDS_DATA_DIR > data/raw/CIC-IDS-Dataset > "
            "~/Documents/CIC-IDS-Dataset"
        ),
        "source": {
            "files": source_files,
            "total_rows": int(total_rows),
            "total_label_counts": dict(sorted(all_label_counts.items())),
            "binary_counts": source_binary_counts,
        },
        "sampling": {
            "max_samples": max_samples,
            "rows_after_dedup": rows_after_dedup,
            "rows_used": int(len(features_all)),
            "used_binary_counts": used_binary_counts,
        },
        "cleaning": {
            "encoding": encodings,
            "column_names": "stripped leading/trailing whitespace",
            "duplicate_column": {
                "dropped": _DUPLICATE_COLUMN,
                "identical_to": _ORIGINAL_DUPLICATE_COLUMN,
                "rows_checked": int(duplicate_column_rows_checked),
                "mismatches": int(duplicate_column_mismatches),
            },
            "inf_values": int(sum(inf_counts.values())),
            "inf_counts_per_column": dict(sorted(inf_counts.items())),
            "nan_values_before_inf_replacement": int(sum(nan_before_counts.values())),
            "nan_counts_before_inf_replacement": dict(sorted(nan_before_counts.items())),
            "nan_values_after_inf_replacement": int(sum(nan_counts.values())),
            "nan_counts_after_inf_replacement": dict(sorted(nan_counts.items())),
            "rows_after_invalid_drop": int(rows_after_invalid),
            "rows_dropped_invalid": int(rows_dropped_invalid),
            "drop_fraction": round(float(drop_fraction), 6),
            "drop_threshold": max_drop_fraction,
            "duplicate_key_precision": "float32 (stored feature precision)",
            "duplicate_rows": {
                "total_dropped": int(duplicate_rows_total),
                "within_file": int(duplicate_within_file),
                "cross_file": int(duplicate_cross_file),
            },
            "label_conflicts_for_identical_rows": int(label_conflicts_total),
            "feature_dim": int(feature_dim),
            "feature_names_file": "feature_names.json",
            "coercion": "non-numeric feature values coerced to NaN before dropping",
        },
        "labels": {
            "binary": {"BENIGN": 0, "ATTACK": 1},
            "multiclass": multiclass_mapping,
            "multiclass_names": multiclass_names_by_id,
            "overall_counts": {
                label: int(np.sum(labels_all == label)) for label in multiclass_names
            },
        },
        "splits": {
            "train": {
                "rows": int(len(split_indices["train"])),
                "fraction": round(len(split_indices["train"]) / len(binary_all), 6),
            },
            "val": {
                "rows": int(len(split_indices["val"])),
                "fraction": round(len(split_indices["val"]) / len(binary_all), 6),
            },
            "test": {
                "rows": int(len(split_indices["test"])),
                "fraction": round(len(split_indices["test"]) / len(binary_all), 6),
            },
            "class_counts": class_counts,
            "multiclass_absent_from_split": absent,
        },
        "split_strategy": {
            "type": "stratified_on_binary_target",
            "fractions": {"train": 0.70, "val": 0.15, "test": 0.15},
            "seed": seed,
            "deduplicated_before_split": True,
            "resampling": None,
            "class_weights": None,
        },
        "preprocessing": {
            "raw_numeric_features": True,
            "scaler_fit_split": "train" if scaler else None,
            "scaler": "mean/population-std, zero-variance columns use scale=1",
            "shortcut_features_kept": [
                "Destination Port",
                "Flow Duration",
                "Flow Bytes/s",
                "Flow Packets/s",
                "Init_Win_bytes_forward",
                "Init_Win_bytes_backward",
            ],
        },
        "artifacts": artifacts,
        "notes": [
            "rare multiclass attacks may be absent from val/test; splits are stratified on "
            "the binary target only",
            "no resampling or class weighting is applied in Sprint 2",
            "random splits on CICIDS can overstate performance; duplicate rows are removed "
            "before splitting at the stored float32 precision",
            "rows that differ only beyond float32 precision are indistinguishable to the "
            "model and are collapsed by deduplication",
            "subset=true artifacts use a deterministic stratified sample of cleaned rows",
        ],
    }
    if label_conflicts_total:
        manifest["notes"].append(
            f"{label_conflicts_total} identical feature rows had conflicting labels; "
            "the first occurrence was kept and the conflict count is reported"
        )
    if subset:
        manifest["notes"].append(
            "subset=true: do not overwrite full-run artifacts with this manifest"
        )

    manifest_path = output / "manifest.json"
    write_json_atomic(manifest_path, manifest)
    errors = verify_manifest_artifacts(manifest, output)
    if errors:
        raise RuntimeError("manifest verification failed: " + "; ".join(errors))
    logger.info("wrote manifest %s", manifest_path)
    return manifest
