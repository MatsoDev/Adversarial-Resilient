"""Synthetic tests for CIC-IDS-2017 cleaning, dedup, splits and scaling."""

from __future__ import annotations

import hashlib
import json
from collections import Counter

import numpy as np
import pandas as pd
import pytest
from src.data.cicids2017 import (
    FILE_ORDER,
    SOURCE_SHA256,
    _check_source_composition,
    _dedupe_columns,
    _source_file_info,
    _stratified_subset_indices,
    binary_label,
    discover_cicids_files,
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

    binary_counts = manifest_a["splits"]["class_counts"]["binary"]
    used_binary = manifest_a["sampling"]["used_binary_counts"]
    for label, used_name in (("0", "BENIGN"), ("1", "ATTACK")):
        assert sum(binary_counts[label].values()) == used_binary[used_name]
    multiclass_counts = manifest_a["splits"]["class_counts"]["multiclass"]
    for label, counts in multiclass_counts.items():
        class_name = manifest_a["labels"]["multiclass_names"][label]
        assert sum(counts.values()) == manifest_a["labels"]["overall_counts"][class_name]


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


def test_label_canonicalisation_handles_unicode_dashes_and_whitespace():
    assert normalize_label("Web Attack \u2013 Brute Force") == "Web Attack - Brute Force"
    assert normalize_label("Web Attack \u2014 xss") == "Web Attack - XSS"
    assert (
        normalize_label("  Web   Attack \ufffd   SQL   Injection ") == "Web Attack - SQL Injection"
    )


def test_discover_cicids_files_order_and_strictness(tmp_path):
    with pytest.raises(FileNotFoundError, match="source directory not found"):
        discover_cicids_files(tmp_path / "missing")

    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(FileNotFoundError, match="no CSV files"):
        discover_cicids_files(empty)

    partial = write_cicids_source(
        tmp_path / "partial",
        files={
            "Tuesday-WorkingHours.pcap_ISCX.csv": [],
            "Monday-WorkingHours.pcap_ISCX.csv": [],
        },
    )
    found = discover_cicids_files(partial, strict=False)
    assert [path.name for path in found] == [
        "Monday-WorkingHours.pcap_ISCX.csv",
        "Tuesday-WorkingHours.pcap_ISCX.csv",
    ]
    with pytest.raises(FileNotFoundError, match="expected the eight"):
        discover_cicids_files(partial)

    complete = write_cicids_source(tmp_path / "complete", files={name: [] for name in FILE_ORDER})
    assert [path.name for path in discover_cicids_files(complete)] == list(FILE_ORDER)


def test_dedupe_columns_removes_identical_duplicate_and_rejects_bad_frames():
    frame = pd.DataFrame(
        {
            "Fwd Header Length": [40, 41],
            "Fwd Header Length.1": [40, 41],
            "Label": ["BENIGN", "BENIGN"],
        }
    )
    cleaned, rows_checked, mismatches = _dedupe_columns(frame)
    assert "Fwd Header Length.1" not in cleaned.columns
    assert rows_checked == 2
    assert mismatches == 0

    with pytest.raises(ValueError, match="missing 'Label'"):
        _dedupe_columns(pd.DataFrame({"value": [1]}))
    with pytest.raises(ValueError, match="unexpected duplicate column names"):
        _dedupe_columns(pd.DataFrame([[1, 2]], columns=["Label", "Label"]))


def test_stratified_subset_indices_validate_size_and_are_deterministic():
    binary = np.asarray([0] * 60 + [1] * 40, dtype=np.int8)
    with pytest.raises(ValueError, match="at least the number of binary classes"):
        _stratified_subset_indices(binary, max_samples=1, seed=1)

    complete = _stratified_subset_indices(binary, max_samples=len(binary), seed=1)
    np.testing.assert_array_equal(complete, np.arange(len(binary)))

    first = _stratified_subset_indices(binary, max_samples=20, seed=3)
    second = _stratified_subset_indices(binary, max_samples=20, seed=3)
    np.testing.assert_array_equal(first, second)
    assert np.all(np.diff(first) > 0)
    assert set(binary[first]) == {0, 1}


def test_cicids_invalid_row_threshold_requires_force(tmp_path):
    source = _synthetic_source(tmp_path)
    with pytest.raises(RuntimeError, match="exceeds"):
        run_cicids_preprocessing(
            source,
            tmp_path / "blocked",
            seed=1,
            verify_source=False,
            force=False,
            scaler=False,
        )

    manifest = run_cicids_preprocessing(
        source,
        tmp_path / "forced",
        seed=1,
        verify_source=False,
        force=True,
        scaler=False,
    )
    assert manifest["cleaning"]["rows_dropped_invalid"] == 2


def test_cicids_pipeline_reports_duplicate_rows_with_conflicting_labels(tmp_path):
    monday = cicids_rows(count_benign=30, count_attack=15)
    conflict = list(monday[0])
    conflict[-1] = "DDoS"
    monday.append(conflict)
    tuesday = cicids_rows(count_benign=10, count_attack=5, offset=10_000)
    source = write_cicids_source(
        tmp_path / "source",
        files={
            "Monday-WorkingHours.pcap_ISCX.csv": monday,
            "Tuesday-WorkingHours.pcap_ISCX.csv": tuesday,
        },
    )
    output = tmp_path / "out"
    manifest = run_cicids_preprocessing(
        source, output, seed=5, verify_source=False, force=True, scaler=False
    )

    assert manifest["cleaning"]["duplicate_rows"]["total_dropped"] == 1
    assert manifest["cleaning"]["label_conflicts_for_identical_rows"] == 1
    assert any("conflicting labels" in note for note in manifest["notes"])
    assert verify_manifest_artifacts(manifest, output) == []


def test_cicids_pipeline_can_skip_scaler_artifacts(tmp_path):
    source = _synthetic_source(tmp_path)
    output = tmp_path / "no-scaler"
    manifest = run_cicids_preprocessing(
        source, output, seed=5, verify_source=False, force=True, scaler=False
    )
    for name in ("scaler_mean.npy", "scaler_scale.npy", "scaler.json"):
        assert not (output / name).exists(), name
    for name in ("scaler_mean", "scaler_scale", "scaler"):
        assert name not in manifest["artifacts"]


def test_cicids_subset_must_cover_every_binary_class(tmp_path):
    source = _synthetic_source(tmp_path)
    with pytest.raises(ValueError, match="at least the number of binary classes"):
        run_cicids_preprocessing(
            source,
            tmp_path / "tiny",
            seed=5,
            max_samples=1,
            verify_source=False,
            force=True,
            scaler=False,
        )


def test_cicids_pipeline_rejects_a_source_without_usable_rows(tmp_path):
    source = write_cicids_source(
        tmp_path / "source",
        files={
            "Monday-WorkingHours.pcap_ISCX.csv": [
                [1, float("nan"), 40, 40, 100.0, "BENIGN"],
                [2, 100, 50, 50, float("inf"), "DDoS"],
            ]
        },
    )
    with pytest.raises(RuntimeError, match="no usable CICIDS rows"):
        run_cicids_preprocessing(
            source,
            tmp_path / "out",
            verify_source=False,
            force=True,
            scaler=False,
        )


def test_source_composition_guard_reports_mismatch_and_force_overrides():
    file_stats = [{"name": "Monday-WorkingHours.pcap_ISCX.csv", "rows": 1}]
    labels = Counter({"BENIGN": 1})
    with pytest.raises(ValueError, match="total rows"):
        _check_source_composition(file_stats, labels, total_rows=1, force=False)
    assert _check_source_composition(file_stats, labels, total_rows=1, force=True) is None


def test_source_hash_guard_rejects_tampering(tmp_path, monkeypatch):
    path = tmp_path / "Monday-WorkingHours.pcap_ISCX.csv"
    path.write_text("tampered", encoding="utf-8")
    monkeypatch.setitem(SOURCE_SHA256, path.name, "0" * 64)

    with pytest.raises(ValueError, match="sha256 mismatch"):
        _source_file_info([path], verify_hashes=True, force=False)

    info = _source_file_info([path], verify_hashes=True, force=True)
    assert info[path.name]["sha256"] == hashlib.sha256(b"tampered").hexdigest()
