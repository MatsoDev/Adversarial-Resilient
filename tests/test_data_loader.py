"""Loader API tests against synthetic processed artifacts."""

from __future__ import annotations

import numpy as np
import pytest
from src.data import load_cicids2017, load_ember
from src.data.cicids2017 import run_cicids_preprocessing
from src.data.ember import run_ember_preprocessing

from tests.test_data_cicids import _synthetic_source
from tests.test_data_ember import _pipeline_source


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
