"""Synthetic tests for CIC-IDS-2017 cleaning, dedup, splits and scaling."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest
from src.data.cicids2017 import (
    _dedupe_columns,
    binary_label,
    normalize_label,
    run_cicids_preprocessing,
)
from src.data.preprocessing import verify_manifest_artifacts

from tests.data_fixtures import cicids_rows, write_cicids_source


def _synthetic_source(tmp_path):
    monday = cicids_rows(count_benign=30, count_attack=15)
    monday.append(list(monday[0]))  # within-file exact duplicate
    monday.append([3000, 999, 60, 60, float("inf"), "DDoS"])
    monday.append([3001, 1000, 61, 61, float("nan"), "PortScan"])
    monday.append([3002, 1001, 62, 62, 300.0, "Heartbleed"])
    tuesday = cicids_rows(count_benign=10, count_attack=5, offset=10_000)
    tuesday.append(list(monday[1]))  # cross-file exact duplicate
    return write_cicids_source(
        tmp_path / "source",
        files={
            "Monday-WorkingHours.pcap_ISCX.csv": monday,
            "Tuesday-WorkingHours.pcap_ISCX.csv": tuesday,
        },
    )


def test_label_canonicalisation():
    assert normalize_label("  BENIGN  ") == "BENIGN"
    assert normalize_label("Web Attack \ufffd Brute Force") == "Web Attack - Brute Force"
    assert normalize_label("Web Attack \ufffd Sql Injection") == "Web Attack - SQL Injection"
    assert normalize_label("Web Attack \ufffd XSS") == "Web Attack - XSS"
    assert binary_label("BENIGN") == 0
    assert binary_label("DDoS") == 1
    with pytest.raises(ValueError, match="unknown CICIDS label"):
        normalize_label("Mystery Attack")


def test_duplicate_column_mismatch_is_rejected():
    frame = pd.DataFrame(
        {
            "Fwd Header Length": [1, 2],
            "Fwd Header Length.1": [1, 3],
            "Label": ["BENIGN", "BENIGN"],
        }
    )
    with pytest.raises(ValueError, match="differs"):
        _dedupe_columns(frame)


def test_cicids_pipeline_cleaning_dedup_split_and_scaler(tmp_path):
    source = _synthetic_source(tmp_path)
    output_a = tmp_path / "out_a"
    manifest_a = run_cicids_preprocessing(
        source, output_a, seed=11, verify_source=False, force=True, scaler=True
    )
    output_b = tmp_path / "out_b"
    manifest_b = run_cicids_preprocessing(
        source, output_b, seed=11, verify_source=False, force=True, scaler=True
    )

    assert manifest_a["cleaning"]["feature_dim"] == 4
    assert manifest_a["cleaning"]["inf_values"] == 1
    assert manifest_a["cleaning"]["nan_values_before_inf_replacement"] == 1
    assert manifest_a["cleaning"]["nan_values_after_inf_replacement"] == 2
    assert manifest_a["cleaning"]["duplicate_rows"]["total_dropped"] == 2
    assert manifest_a["cleaning"]["duplicate_rows"]["within_file"] == 1
    assert manifest_a["cleaning"]["duplicate_rows"]["cross_file"] == 1
    assert manifest_a["cleaning"]["label_conflicts_for_identical_rows"] == 0
    assert "Heartbleed" in manifest_a["labels"]["multiclass"]
    assert manifest_a["subset"] is False

    feature_names = json.loads((output_a / "feature_names.json").read_text())
    assert feature_names == [
        "Destination Port",
        "Flow Duration",
        "Fwd Header Length",
        "Flow Bytes/s",
    ]
    assert "Label" not in feature_names
    assert "Fwd Header Length.1" not in feature_names

    split_hashes = []
    for split in ("train", "val", "test"):
        X = np.load(output_a / f"{split}_X.npy")
        y_binary = np.load(output_a / f"{split}_y_binary.npy")
        y_multi = np.load(output_a / f"{split}_y_multiclass.npy")
        assert X.shape == (len(y_binary), 4)
        assert X.dtype == np.float32
        assert np.isfinite(X).all()
        assert len(y_multi) == len(y_binary)
        np.testing.assert_array_equal(X, np.load(output_b / f"{split}_X.npy"))
        np.testing.assert_array_equal(y_binary, np.load(output_b / f"{split}_y_binary.npy"))
        np.testing.assert_array_equal(y_multi, np.load(output_b / f"{split}_y_multiclass.npy"))
        hashes = pd.util.hash_pandas_object(pd.DataFrame(X), index=False).to_numpy()
        split_hashes.append(set(hashes.tolist()))

    assert not (split_hashes[0] & split_hashes[1])
    assert not (split_hashes[0] & split_hashes[2])
    assert not (split_hashes[1] & split_hashes[2])

    train_X = np.load(output_a / "train_X.npy").astype(np.float64)
    mean = np.load(output_a / "scaler_mean.npy")
    scale = np.load(output_a / "scaler_scale.npy")
    np.testing.assert_allclose(mean, train_X.mean(axis=0), rtol=1e-9, atol=1e-9)
    expected_scale = train_X.std(axis=0)
    expected_scale[expected_scale == 0] = 1.0
    np.testing.assert_allclose(scale, expected_scale, rtol=1e-9, atol=1e-9)

    without_timestamp_a = {key: value for key, value in manifest_a.items() if key != "generated_at"}
    without_timestamp_b = {key: value for key, value in manifest_b.items() if key != "generated_at"}
    assert json.dumps(without_timestamp_a, sort_keys=True) == json.dumps(
        without_timestamp_b, sort_keys=True
    )
    assert verify_manifest_artifacts(manifest_a, output_a) == []


def test_cicids_subset_refuses_to_overwrite_full_run(tmp_path):
    source = _synthetic_source(tmp_path)
    output = tmp_path / "full"
    run_cicids_preprocessing(source, output, seed=5, verify_source=False, force=True, scaler=False)
    with pytest.raises(RuntimeError, match="refusing to overwrite full-run artifacts"):
        run_cicids_preprocessing(
            source,
            output,
            seed=5,
            max_samples=10,
            verify_source=False,
            force=True,
            scaler=False,
        )


def test_cicids_subset_manifest(tmp_path):
    source = _synthetic_source(tmp_path)
    output = tmp_path / "subset"
    manifest = run_cicids_preprocessing(
        source,
        output,
        seed=5,
        max_samples=20,
        verify_source=False,
        force=True,
        scaler=True,
    )
    assert manifest["subset"] is True
    assert manifest["sampling"]["rows_used"] == 20
    total = sum(manifest["splits"][name]["rows"] for name in ("train", "val", "test"))
    assert total == 20
    assert "subset=true" in " ".join(manifest["notes"])
    assert verify_manifest_artifacts(manifest, output) == []
