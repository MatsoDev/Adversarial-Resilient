"""Loader API tests against synthetic processed artifacts."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest
from src.data import load_cicids2017, load_ember
from src.data.cicids2017 import run_cicids_preprocessing
from src.data.ember import run_ember_preprocessing

from tests.test_data_cicids import _synthetic_source
from tests.test_data_ember import _pipeline_source


def _write_artifacts(
    root,
    *,
    X,
    feature_names,
    labels,
    metadata: bool = True,
    scaler=None,
):
    root.mkdir(parents=True)
    np.save(root / "train_X.npy", X)
    for name, array in labels.items():
        np.save(root / f"train_{name}.npy", array)
    (root / "feature_names.json").write_text(json.dumps(feature_names), encoding="utf-8")
    (root / "label_mapping.json").write_text(
        json.dumps({"dataset": "synthetic", "labels": ["benign", "attack"]}),
        encoding="utf-8",
    )
    if metadata:
        pd.DataFrame({"split": ["train"] * len(X)}).to_csv(root / "train_metadata.csv", index=False)
    if scaler is not None:
        mean, scale = scaler
        np.save(root / "scaler_mean.npy", mean)
        np.save(root / "scaler_scale.npy", scale)
    return root


def test_load_ember_splits_and_standardize(tmp_path):
    source = _pipeline_source(tmp_path)
    output = tmp_path / "ember"
    run_ember_preprocessing(source, output, seed=2, jobs=1, verify_source=False, scaler=True)

    train = load_ember("train", root=output)
    assert train.dataset == "ember2018"
    assert train.X.dtype == np.float32
    assert train.X.shape[1] == 2381
    assert len(train.feature_names) == 2381
    assert len(train.X) == len(train.y)
    assert train.metadata is not None
    assert train.metadata["split"].eq("train").all()

    standardized = load_ember("train", root=output, standardize=True)
    nonzero_scale = np.load(output / "scaler_scale.npy") != 1.0
    np.testing.assert_allclose(
        standardized.X[:, nonzero_scale].mean(axis=0), 0.0, rtol=0, atol=2e-4
    )
    np.testing.assert_allclose(standardized.X[:, nonzero_scale].std(axis=0), 1.0, rtol=0, atol=2e-4)

    val = load_ember("val", root=output)
    test = load_ember("test", root=output)
    assert len(val.X) > 0 and len(test.X) > 0
    with pytest.raises(ValueError, match="split must be"):
        load_ember("validation", root=output)


def test_load_ember_missing_artifacts_has_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="preprocess.py --dataset ember"):
        load_ember("train", root=tmp_path / "does-not-exist")


def test_load_cicids_binary_and_multiclass(tmp_path):
    source = _synthetic_source(tmp_path)
    output = tmp_path / "cicids"
    run_cicids_preprocessing(source, output, seed=2, verify_source=False, force=True, scaler=True)

    binary = load_cicids2017("train", target="binary", root=output)
    multiclass = load_cicids2017("train", target="multiclass", root=output)
    assert binary.dataset == "cicids2017"
    assert binary.X.shape[1] == 4
    assert binary.target == "binary"
    assert set(np.unique(binary.y)).issubset({0, 1})
    assert multiclass.target == "multiclass"
    np.testing.assert_array_equal(binary.X, multiclass.X)
    assert "multiclass" in multiclass.label_mapping
    assert "Heartbleed" in multiclass.label_mapping["multiclass"]

    standardized = load_cicids2017("train", root=output, standardize=True)
    assert standardized.X.dtype == np.float32
    assert np.isfinite(standardized.X).all()

    with pytest.raises(ValueError, match="target must be"):
        load_cicids2017("train", target="unknown", root=output)
    with pytest.raises(FileNotFoundError, match="preprocess.py --dataset cicids2017"):
        load_cicids2017("train", root=tmp_path / "missing")


def test_load_ember_minimal_artifacts_without_metadata(tmp_path):
    features = np.asarray([[0.0, 1.0, 2.0], [3.0, 4.0, 5.0]], dtype=np.float32)
    root = _write_artifacts(
        tmp_path / "ember",
        X=features,
        feature_names=["alpha", "beta", "gamma"],
        labels={"y": np.asarray([0, 1], dtype=np.int8)},
        metadata=False,
    )

    dataset = load_ember("train", root=root)
    assert dataset.dataset == "ember2018"
    assert dataset.split == "train"
    assert dataset.target == "binary"
    assert dataset.metadata is None
    assert dataset.feature_names == ["alpha", "beta", "gamma"]
    assert dataset.label_mapping == {
        "dataset": "synthetic",
        "labels": ["benign", "attack"],
    }
    assert len(dataset) == 2
    np.testing.assert_array_equal(dataset.X, features)
    np.testing.assert_array_equal(dataset.y, np.asarray([0, 1]))


def test_load_ember_standardize_requires_both_scaler_files(tmp_path):
    root = _write_artifacts(
        tmp_path / "ember",
        X=np.zeros((2, 3), dtype=np.float32),
        feature_names=["a", "b", "c"],
        labels={"y": np.asarray([0, 1], dtype=np.int8)},
        metadata=False,
    )
    with pytest.raises(FileNotFoundError, match="scaler_mean.npy"):
        load_ember("train", root=root, standardize=True)
    with pytest.raises(FileNotFoundError, match="preprocess.py --dataset ember"):
        load_ember("train", root=root, standardize=True)


def test_load_ember_validates_shapes_and_scaler_dimensions(tmp_path):
    feature_names = ["a", "b", "c"]
    labels = {"y": np.asarray([0, 1], dtype=np.int8)}

    one_dimensional = _write_artifacts(
        tmp_path / "one-dim",
        X=np.zeros((2,), dtype=np.float32),
        feature_names=feature_names,
        labels=labels,
        metadata=False,
    )
    with pytest.raises(ValueError, match="has shape"):
        load_ember(root=one_dimensional)

    wrong_width = _write_artifacts(
        tmp_path / "wrong-width",
        X=np.zeros((2, 2), dtype=np.float32),
        feature_names=feature_names,
        labels=labels,
        metadata=False,
    )
    with pytest.raises(ValueError, match="expected \\(N, 3\\)"):
        load_ember(root=wrong_width)

    row_mismatch = _write_artifacts(
        tmp_path / "row-mismatch",
        X=np.zeros((3, 3), dtype=np.float32),
        feature_names=feature_names,
        labels={"y": np.asarray([0, 1], dtype=np.int8)},
        metadata=False,
    )
    with pytest.raises(ValueError, match="3 rows"):
        load_ember(root=row_mismatch)

    bad_scaler = _write_artifacts(
        tmp_path / "bad-scaler",
        X=np.zeros((2, 3), dtype=np.float32),
        feature_names=feature_names,
        labels={"y": np.asarray([0, 1], dtype=np.int8)},
        metadata=False,
        scaler=(np.zeros(2, dtype=np.float64), np.ones(3, dtype=np.float64)),
    )
    with pytest.raises(ValueError, match="scaler dimension 2 does not match features 3"):
        load_ember(root=bad_scaler, standardize=True)


def test_load_cicids_minimal_binary_and_multiclass_artifacts(tmp_path):
    features = np.asarray([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]], dtype=np.float32)
    root = _write_artifacts(
        tmp_path / "cicids",
        X=features,
        feature_names=["f0", "f1"],
        labels={
            "y_binary": np.asarray([0, 1, 0], dtype=np.int8),
            "y_multiclass": np.asarray([0, 1, 2], dtype=np.int16),
        },
    )

    binary = load_cicids2017("train", target="binary", root=root)
    multiclass = load_cicids2017("train", target="multiclass", root=root)
    assert binary.target == "binary"
    assert multiclass.target == "multiclass"
    assert binary.metadata is not None
    assert binary.metadata["split"].eq("train").all()
    np.testing.assert_array_equal(binary.X, features)
    np.testing.assert_array_equal(multiclass.X, features)
    np.testing.assert_array_equal(binary.y, np.asarray([0, 1, 0]))
    np.testing.assert_array_equal(multiclass.y, np.asarray([0, 1, 2]))
    assert binary.label_mapping["dataset"] == "synthetic"
    assert len(binary) == 3
