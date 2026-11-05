"""Opt-in checks on the real processed EMBER dataset; no model test-set evaluation."""

import json
import os

import numpy as np
import pytest
from src.config import EMBER_PROCESSED_DIR


@pytest.mark.skipif(os.environ.get("RUN_REAL_DATA_TESTS") != "1", reason="Real data opt-in")
def test_processed_ember_counts_schema_labels_and_normalization():
    root = EMBER_PROCESSED_DIR
    if not (root / "manifest.json").is_file():
        pytest.skip("Processed EMBER is not installed")
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["subset"] is False
    assert manifest["preprocessing"]["scaler_fit_split"] == "train"
    for split, rows in [("train", 510000), ("val", 90000), ("test", 200000)]:
        X = np.load(root / f"{split}_X.npy", mmap_mode="r", allow_pickle=False)
        y = np.load(root / f"{split}_y.npy", allow_pickle=False)
        assert X.shape == (rows, 2381)
        assert len(y) == rows
        assert set(np.unique(y)) == {0, 1}
        sample = X[np.linspace(0, rows - 1, 100, dtype=int)]
        assert np.isfinite(sample).all()
        np.testing.assert_allclose(sample[:, :256].sum(axis=1), 1, atol=1e-5)
    assert manifest["splits"]["val"]["max_appeared"] <= manifest["splits"]["test"]["min_appeared"]
