"""Shared deterministic row selection and provenance for baseline experiments.

Index selection does not read feature matrices, so tuning can keep large arrays
memory-mapped. Keep this independent of either training implementation.
"""

from __future__ import annotations

import hashlib

import numpy as np
from sklearn.model_selection import train_test_split


def validation_partitions(y, seed):
    """Disjoint sorted selection/calibration/operating indices (50/25/25)."""
    indices = np.arange(len(y))
    selection, remainder = train_test_split(indices, test_size=0.5, stratify=y, random_state=seed)
    calibration, operating = train_test_split(
        remainder, test_size=0.5, stratify=y[remainder], random_state=seed
    )
    return tuple(np.sort(part) for part in (selection, calibration, operating))


def sample_indices(y: np.ndarray, limit: int | None, seed: int) -> np.ndarray:
    """Return sorted stratified row indices, or every row when no reduction is needed."""
    indices = np.arange(len(y))
    if limit is not None and limit < len(y):
        indices, _ = train_test_split(indices, train_size=limit, stratify=y, random_state=seed)
        indices.sort()
    return indices


def sample_rows(
    X: np.ndarray, y: np.ndarray, limit: int | None, seed: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Materialize only selected features (float32) and labels, retaining original indices."""
    indices = sample_indices(y, limit, seed)
    return np.asarray(X[indices], dtype=np.float32), np.asarray(y[indices]), indices


def index_hash(indices: np.ndarray) -> str:
    """Hash ordered original row indices using the existing little-endian int64 format."""
    return hashlib.sha256(indices.astype("<i8").tobytes()).hexdigest()
