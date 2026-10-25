"""Small reusable loaders for the processed Sprint 2 datasets.

Sprint 3+ should import these instead of guessing artifact names. The loaders
never download data and raise a clear error when the preprocessing step has not
been run yet.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.config import CICIDS_PROCESSED_DIR, EMBER_PROCESSED_DIR
from src.data.preprocessing import apply_standardization

SPLITS = ("train", "val", "test")
CICIDS_TARGETS = ("binary", "multiclass")


@dataclass
class ProcessedDataset:
    """A cleaned split returned by :func:`load_ember` / :func:`load_cicids2017`."""

    X: np.ndarray
    y: np.ndarray
    metadata: pd.DataFrame | None
    feature_names: list[str]
    split: str
    dataset: str
    target: str | None = None
    label_mapping: dict[str, Any] | None = None

    def __len__(self) -> int:
        return len(self.X)


def _require(path: Path, *, dataset: str, artifact: str, root: Path) -> Path:
    if not path.is_file():
        example = {
            "ember2018": "python scripts/preprocess.py --dataset ember",
            "cicids2017": "python scripts/preprocess.py --dataset cicids2017",
        }[dataset]
        raise FileNotFoundError(
            f"missing processed {artifact} for {dataset} at {path}. "
            f"Run the preprocessing pipeline first, e.g.: {example} "
            f"(current root: {root})"
        )
    return path


def _load_json(path: Path, *, dataset: str, artifact: str, root: Path) -> Any:
    _require(path, dataset=dataset, artifact=artifact, root=root)
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _validate_split(split: str) -> None:
    if split not in SPLITS:
        raise ValueError(f"split must be one of {SPLITS}, got {split!r}")


def _load_metadata(root: Path, split: str, *, dataset: str) -> pd.DataFrame | None:
    path = root / f"{split}_metadata.csv"
    if not path.is_file():
        return None
    return pd.read_csv(path)


def _standardize(
    X: np.ndarray,
    *,
    root: Path,
    dataset: str,
    standardize: bool,
) -> np.ndarray:
    if not standardize:
        return np.asarray(X, dtype=np.float32)
    mean = np.load(
        _require(
            root / "scaler_mean.npy",
            dataset=dataset,
            artifact="scaler_mean.npy",
            root=root,
        ),
        allow_pickle=False,
    )
    scale = np.load(
        _require(
            root / "scaler_scale.npy",
            dataset=dataset,
            artifact="scaler_scale.npy",
            root=root,
        ),
        allow_pickle=False,
    )
    if X.shape[1] != mean.shape[0] or X.shape[1] != scale.shape[0]:
        raise ValueError(f"scaler dimension {mean.shape[0]} does not match features {X.shape[1]}")
    return apply_standardization(np.asarray(X), mean, scale)


def load_ember(
    split: str = "train",
    root: str | Path = EMBER_PROCESSED_DIR,
    standardize: bool = False,
) -> ProcessedDataset:
    """Load one processed EMBER split (X float32, y int8 0/1).

    Parameters
    ----------
    split:
        ``"train"``, ``"val"`` or ``"test"``.
    root:
        Directory written by ``scripts/preprocess.py --dataset ember``.
    standardize:
        Apply the saved train-only mean/scale statistics when True.
    """
    _validate_split(split)
    root = Path(root).expanduser()
    dataset = "ember2018"
    X = np.load(
        _require(root / f"{split}_X.npy", dataset=dataset, artifact=f"{split}_X.npy", root=root),
        allow_pickle=False,
    )
    y = np.load(
        _require(root / f"{split}_y.npy", dataset=dataset, artifact=f"{split}_y.npy", root=root),
        allow_pickle=False,
    )
    feature_names = _load_json(
        root / "feature_names.json",
        dataset=dataset,
        artifact="feature_names.json",
        root=root,
    )
    label_mapping = _load_json(
        root / "label_mapping.json",
        dataset=dataset,
        artifact="label_mapping.json",
        root=root,
    )
    if X.ndim != 2 or X.shape[1] != len(feature_names):
        raise ValueError(f"{split}_X has shape {X.shape}, expected (N, {len(feature_names)})")
    if len(X) != len(y):
        raise ValueError(f"{split}_X has {len(X)} rows but {split}_y has {len(y)}")
    X = _standardize(X, root=root, dataset=dataset, standardize=standardize)
    return ProcessedDataset(
        X=X,
        y=np.asarray(y),
        metadata=_load_metadata(root, split, dataset=dataset),
        feature_names=list(feature_names),
        split=split,
        dataset=dataset,
        target="binary",
        label_mapping=label_mapping,
    )


def load_cicids2017(
    split: str = "train",
    target: str = "binary",
    root: str | Path = CICIDS_PROCESSED_DIR,
    standardize: bool = False,
) -> ProcessedDataset:
    """Load one processed CIC-IDS-2017 split.

    ``target`` is ``"binary"`` (BENIGN=0, attack=1) or ``"multiclass"`` (the
    sorted label-to-integer mapping is returned in ``label_mapping``).
    """
    _validate_split(split)
    if target not in CICIDS_TARGETS:
        raise ValueError(f"target must be one of {CICIDS_TARGETS}, got {target!r}")
    root = Path(root).expanduser()
    dataset = "cicids2017"
    y_name = f"{split}_y_{target}.npy"
    X = np.load(
        _require(root / f"{split}_X.npy", dataset=dataset, artifact=f"{split}_X.npy", root=root),
        allow_pickle=False,
    )
    y = np.load(
        _require(root / y_name, dataset=dataset, artifact=y_name, root=root),
        allow_pickle=False,
    )
    feature_names = _load_json(
        root / "feature_names.json",
        dataset=dataset,
        artifact="feature_names.json",
        root=root,
    )
    label_mapping = _load_json(
        root / "label_mapping.json",
        dataset=dataset,
        artifact="label_mapping.json",
        root=root,
    )
    if X.ndim != 2 or X.shape[1] != len(feature_names):
        raise ValueError(f"{split}_X has shape {X.shape}, expected (N, {len(feature_names)})")
    if len(X) != len(y):
        raise ValueError(f"{split}_X has {len(X)} rows but {y_name} has {len(y)}")
    X = _standardize(X, root=root, dataset=dataset, standardize=standardize)
    return ProcessedDataset(
        X=X,
        y=np.asarray(y),
        metadata=_load_metadata(root, split, dataset=dataset),
        feature_names=list(feature_names),
        split=split,
        dataset=dataset,
        target=target,
        label_mapping=label_mapping,
    )
