"""Shared deterministic preprocessing helpers for the Sprint 2 datasets.

The helpers here are deliberately small and framework-free (numpy, pandas,
scikit-learn): atomic writes, hashing/manifest utilities, train-only scaler
statistics, stratified splits, and the EMBER time-based validation split.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.config import ROOT

HASH_CHUNK_SIZE = 1 << 20


def utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp (seconds precision)."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()  # noqa: UP017


def sha256_file(path: str | Path, chunk_size: int = HASH_CHUNK_SIZE) -> str:
    """Stream a file through SHA-256 without loading it into memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def code_revision() -> str | None:
    """Best-effort git revision of the working tree, or None outside git."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    revision = result.stdout.strip()
    return revision if result.returncode == 0 and revision else None


def atomic_write_bytes(path: str | Path, data: bytes) -> None:
    """Write bytes to a sibling .tmp file, then atomically replace the target."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def atomic_write_text(path: str | Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def write_json_atomic(path: str | Path, payload: Any) -> None:
    """Write deterministic JSON (sorted keys, trailing newline) atomically."""
    text = json.dumps(payload, indent=2, sort_keys=True, default=_json_default)
    atomic_write_text(path, text + "\n")


def _json_default(value: Any) -> Any:
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def load_json(path: str | Path) -> Any:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def atomic_save_npy(path: str | Path, array: np.ndarray) -> None:
    """Save a numpy array atomically (write .tmp, fsync, os.replace)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as handle:
        np.save(handle, array, allow_pickle=False)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def open_atomic_memmap(
    path: str | Path, *, shape: tuple[int, ...], dtype: str | np.dtype = "float32"
) -> tuple[np.memmap, Path]:
    """Open a preallocated ``.npy`` memmap under a ``.tmp`` name.

    Call :func:`finalize_atomic_memmap` after all writes to atomically publish
    the completed array. On failure the final path is never touched.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    memmap = np.lib.format.open_memmap(tmp, mode="w+", dtype=dtype, shape=shape)
    return memmap, tmp


def finalize_atomic_memmap(memmap: np.memmap, tmp: Path, final: Path) -> None:
    memmap.flush()
    del memmap
    os.replace(tmp, final)


def ensure_finite(array: np.ndarray, *, name: str = "features") -> None:
    """Raise ValueError if any value is NaN or +/-inf."""
    if not np.isfinite(array).all():
        raise ValueError(f"{name} contains NaN or infinite values")


def _as_array(source: np.ndarray | str | Path, *, mmap_mode: str = "r") -> np.ndarray:
    if isinstance(source, str | Path):
        return np.load(source, mmap_mode=mmap_mode)
    return source


def compute_scaler_stats(
    source: np.ndarray | str | Path, *, chunk_size: int = 50_000
) -> tuple[np.ndarray, np.ndarray]:
    """Compute train-only mean/scale (population std) in bounded memory.

    Zero-variance columns get ``scale = 1`` so standardisation is a no-op for
    them. The source may be an in-memory array or a path to a ``.npy`` file.
    """
    array = _as_array(source)
    if array.ndim != 2:
        raise ValueError(f"expected a 2-D array, got shape {array.shape}")
    n_rows, n_features = array.shape
    if n_rows == 0:
        raise ValueError("cannot compute scaler statistics from zero rows")

    sums = np.zeros(n_features, dtype=np.float64)
    sums_sq = np.zeros(n_features, dtype=np.float64)
    for start in range(0, n_rows, chunk_size):
        block = np.asarray(array[start : start + chunk_size], dtype=np.float64)
        if not np.isfinite(block).all():
            raise ValueError("cannot compute scaler statistics from non-finite features")
        sums += block.sum(axis=0)
        sums_sq += np.square(block).sum(axis=0)

    mean = sums / n_rows
    variance = sums_sq / n_rows - np.square(mean)
    variance[variance < 0] = 0.0
    scale = np.sqrt(variance)
    scale[scale == 0] = 1.0
    return mean.astype(np.float64), scale.astype(np.float64)


def apply_standardization(
    array: np.ndarray, mean: np.ndarray, scale: np.ndarray, *, chunk_size: int = 50_000
) -> np.ndarray:
    """Return a float32 copy standardised with precomputed train-only stats."""
    mean32 = np.asarray(mean, dtype=np.float32)
    scale32 = np.asarray(scale, dtype=np.float32)
    output = np.empty(array.shape, dtype=np.float32)
    for start in range(0, array.shape[0], chunk_size):
        stop = start + chunk_size
        output[start:stop] = (np.asarray(array[start:stop], dtype=np.float32) - mean32) / scale32
    return output


def stratified_split_indices(
    y_binary: np.ndarray,
    *,
    seed: int,
    train_fraction: float = 0.70,
    val_fraction: float = 0.15,
    test_fraction: float = 0.15,
) -> dict[str, np.ndarray]:
    """Deterministic stratified 70/15/15 split on the binary target."""
    from sklearn.model_selection import train_test_split

    fractions = train_fraction + val_fraction + test_fraction
    if not np.isclose(fractions, 1.0):
        raise ValueError("train/val/test fractions must sum to 1")
    y_binary = np.asarray(y_binary)
    if y_binary.ndim != 1 or len(y_binary) == 0:
        raise ValueError("y_binary must be a non-empty 1-D array")
    indices = np.arange(len(y_binary), dtype=np.int64)
    train_idx, temp_idx = train_test_split(
        indices,
        train_size=train_fraction,
        random_state=seed,
        stratify=y_binary,
    )
    temp_y = y_binary[temp_idx]
    if len(temp_idx) < 2 or len(np.unique(temp_y)) < len(np.unique(y_binary)):
        raise ValueError("not enough samples per class for a stratified val/test split")
    val_share = val_fraction / (val_fraction + test_fraction)
    val_idx, test_idx = train_test_split(
        temp_idx,
        train_size=val_share,
        random_state=seed,
        stratify=temp_y,
    )
    return {
        "train": np.sort(train_idx),
        "val": np.sort(val_idx),
        "test": np.sort(test_idx),
    }


def remove_rows_with_ids(
    frame: pd.DataFrame, *, id_col: str, blocked_ids: set[str]
) -> tuple[pd.DataFrame, int]:
    """Drop rows whose identifier appears in ``blocked_ids``."""
    if not blocked_ids:
        return frame, 0
    mask = frame[id_col].astype(str).isin(blocked_ids)
    removed = int(mask.sum())
    return frame.loc[~mask].copy(), removed


def time_based_split(
    frame: pd.DataFrame,
    *,
    val_fraction: float = 0.15,
    label_col: str = "label",
    time_col: str = "appeared",
    id_col: str = "sha256",
    min_val_per_class: int = 50,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Hold out the latest ``val_fraction`` of rows as validation.

    A global time split is tried first. If any class ends up missing or too
    small in train/val, the function falls back to a per-class time split (the
    latest fraction within each class). Rows sharing an identifier always land
    in the same split, so duplicate hashes never cross train/val.

    Returns ``(split, info)`` where ``split`` is an int8 array aligned with
    ``frame`` (0 = train, 1 = val).
    """
    if not 0.0 < val_fraction < 1.0:
        raise ValueError("val_fraction must be between 0 and 1")
    if frame.empty:
        raise ValueError("cannot split an empty frame")
    for column in (label_col, time_col, id_col):
        if column not in frame.columns:
            raise KeyError(f"missing column {column!r}")

    work = frame[[id_col, time_col, label_col]].copy()
    work[id_col] = work[id_col].astype(str)
    work[time_col] = work[time_col].astype(str)

    groups = (
        work.groupby(id_col, sort=False)
        .agg(
            group_time=(time_col, "max"),
            group_label=(label_col, "first"),
            group_size=(label_col, "size"),
            distinct_labels=(label_col, "nunique"),
        )
        .reset_index()
    )
    label_conflicts = int((groups["distinct_labels"] > 1).sum())
    n_rows = len(work)
    target_val_rows = max(1, int(round(val_fraction * n_rows)))
    work_labels = work[label_col].to_numpy()
    work_ids = work[id_col].to_numpy()

    def _assign(chosen_ids: set[str]) -> np.ndarray:
        is_val = np.fromiter(
            (value in chosen_ids for value in work_ids), dtype=np.int8, count=n_rows
        )
        return is_val

    def _counts(split: np.ndarray) -> dict[str, dict[str, int]]:
        counts: dict[str, dict[str, int]] = {}
        for label in sorted(pd.unique(work_labels).tolist()):
            mask = work_labels == label
            train_count = int(np.sum(mask & (split == 0)))
            val_count = int(np.sum(mask & (split == 1)))
            counts[str(label)] = {
                "train": train_count,
                "val": val_count,
                "total": train_count + val_count,
            }
        return counts

    def _acceptable(counts: dict[str, dict[str, int]]) -> bool:
        for stats in counts.values():
            total = stats["total"]
            if total < 2:
                continue
            required_val = min(min_val_per_class, max(1, total // 10))
            if stats["val"] < required_val or stats["train"] == 0:
                return False
        return True

    ordered = groups.sort_values(["group_time", id_col], ascending=[False, True], kind="mergesort")
    chosen_global: set[str] = set()
    accumulated = 0
    for group_id, group_size in zip(ordered[id_col], ordered["group_size"], strict=True):
        if accumulated >= target_val_rows:
            break
        chosen_global.add(str(group_id))
        accumulated += int(group_size)

    global_split = _assign(chosen_global)
    global_counts = _counts(global_split)
    strategy = "global_time"
    chosen = chosen_global
    chosen_counts = global_counts
    if not _acceptable(global_counts):
        strategy = "per_class_time"
        chosen = set()
        for label in pd.unique(groups["group_label"]).tolist():
            subset = groups.loc[groups["group_label"] == label].sort_values(
                ["group_time", id_col], ascending=[False, True], kind="mergesort"
            )
            class_target = max(1, int(round(val_fraction * int(subset["group_size"].sum()))))
            accumulated = 0
            for group_id, group_size in zip(subset[id_col], subset["group_size"], strict=True):
                if accumulated >= class_target:
                    break
                chosen.add(str(group_id))
                accumulated += int(group_size)
        chosen_counts = _counts(_assign(chosen))
        if not _acceptable(chosen_counts):
            raise RuntimeError(
                "could not produce a non-degenerate time-based train/val split for every class"
            )

    split = _assign(chosen)
    val_times = work.loc[split == 1, time_col]
    train_times = work.loc[split == 0, time_col]
    info: dict[str, Any] = {
        "strategy": strategy,
        "val_fraction_requested": val_fraction,
        "target_val_rows": target_val_rows,
        "actual_val_rows": int(split.sum()),
        "actual_val_fraction": round(float(split.mean()), 6),
        "class_counts": chosen_counts,
        "duplicate_sha256_groups": int((groups["group_size"] > 1).sum()),
        "duplicate_sha256_rows": int((groups["group_size"] - 1).clip(lower=0).sum()),
        "label_conflicts": label_conflicts,
        "min_train_time": str(train_times.min()) if not train_times.empty else None,
        "max_train_time": str(train_times.max()) if not train_times.empty else None,
        "min_val_time": str(val_times.min()) if not val_times.empty else None,
        "max_val_time": str(val_times.max()) if not val_times.empty else None,
    }
    return split, info


def artifact_record(
    path: str | Path,
    *,
    root: str | Path,
    shape: tuple[int, ...] | None = None,
    dtype: str | None = None,
) -> dict[str, Any]:
    """Describe an output artifact for a manifest (relative name + hash)."""
    path = Path(path)
    root = Path(root)
    record: dict[str, Any] = {
        "file": path.relative_to(root).as_posix(),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if shape is not None:
        record["shape"] = [int(value) for value in shape]
    if dtype is not None:
        record["dtype"] = str(dtype)
    return record


def verify_manifest_artifacts(manifest: dict[str, Any], root: str | Path) -> list[str]:
    """Check every artifact in a manifest; return a list of human-readable errors."""
    root = Path(root)
    errors: list[str] = []
    artifacts = manifest.get("artifacts", {})
    if not isinstance(artifacts, dict) or not artifacts:
        return ["manifest has no artifacts"]
    for name, record in sorted(artifacts.items()):
        relative = record.get("file")
        if not relative:
            errors.append(f"{name}: missing 'file' in manifest")
            continue
        path = root / relative
        if not path.is_file():
            errors.append(f"{name}: missing file {relative}")
            continue
        size = path.stat().st_size
        if "size_bytes" in record and size != int(record["size_bytes"]):
            errors.append(f"{name}: size mismatch (expected {record['size_bytes']}, found {size})")
        expected_hash = record.get("sha256")
        if expected_hash and sha256_file(path) != expected_hash:
            errors.append(f"{name}: sha256 mismatch for {relative}")
    return errors
