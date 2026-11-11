"""Preserve row selection and provenance across the shared sampling refactor."""

import hashlib

import numpy as np
import pytest
from sklearn.model_selection import train_test_split
from src.models.sampling import index_hash, sample_indices, sample_rows


@pytest.mark.parametrize("limit", [None, 20, 30])
def test_no_reduction_keeps_all_rows_in_order(limit):
    y = np.tile([0, 1], 10)
    np.testing.assert_array_equal(sample_indices(y, limit, 42), np.arange(len(y)))


def test_sampling_preserves_previous_stratified_selection():
    y = np.repeat([0, 1], [80, 20])
    expected, _ = train_test_split(np.arange(len(y)), train_size=30, stratify=y, random_state=42)
    actual = sample_indices(y, 30, 42)
    np.testing.assert_array_equal(actual, np.sort(expected))
    np.testing.assert_array_equal(actual, sample_indices(y, 30, 42))
    np.testing.assert_array_equal(np.bincount(y[actual]), [24, 6])
    assert not np.array_equal(actual, sample_indices(y, 30, 43))


def test_sample_rows_only_reads_selected_features_and_retains_label_dtype():
    y = np.tile([0, 1], 20).astype(np.int8)
    indices = sample_indices(y, 12, 42)
    features = np.arange(120, dtype=np.float64).reshape(40, 3)

    class SelectedRowsOnly:
        def __getitem__(self, selected):
            np.testing.assert_array_equal(selected, indices)
            return features[selected]

    X, labels, selected = sample_rows(SelectedRowsOnly(), y, 12, 42)
    np.testing.assert_array_equal(X, features[indices].astype(np.float32))
    np.testing.assert_array_equal(labels, y[indices])
    np.testing.assert_array_equal(selected, indices)
    assert X.dtype == np.float32
    assert labels.dtype == y.dtype


def test_index_hash_preserves_order_and_little_endian_int64_format():
    indices = np.array([1, 3, 258], dtype=">i4")
    expected_bytes = b"".join(int(value).to_bytes(8, "little", signed=True) for value in indices)
    assert index_hash(indices) == hashlib.sha256(expected_bytes).hexdigest()
    assert index_hash(indices) == index_hash(indices.astype("<i8"))
    assert index_hash(indices) != index_hash(indices[::-1])
