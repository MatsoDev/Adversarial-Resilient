"""Synthetic tests for EMBER vectorisation, splits and manifests (no real data)."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest
from src.data.ember import (
    FEATURE_DIM,
    EmberVectorizer,
    feature_names,
    run_ember_preprocessing,
)
from src.data.preprocessing import time_based_split, verify_manifest_artifacts

from tests.data_fixtures import ember_record, fake_sha, write_ember_source


def test_ember_vectorizer_layout_and_normalization():
    record = ember_record("layout", 0, "2018-01", size=4096)
    vector = EmberVectorizer().transform(record)

    assert vector.shape == (FEATURE_DIM,)
    assert vector.dtype == np.float32
    assert np.isfinite(vector).all()

    np.testing.assert_allclose(vector[0:256].sum(), 1.0, rtol=0, atol=1e-6)
    np.testing.assert_allclose(vector[256:512].sum(), 1.0, rtol=0, atol=1e-6)
    np.testing.assert_allclose(vector[0], 1.0 / 256, rtol=0, atol=1e-6)

    assert vector[512] == pytest.approx(10.0)
    assert vector[513] == pytest.approx(5.5)
    assert vector[514] == pytest.approx(96.0)
    np.testing.assert_allclose(vector[515:611].sum(), 1.0, rtol=0, atol=1e-6)
    assert vector[611] == pytest.approx(3.2)
    assert vector[612] == pytest.approx(1.0)
    assert vector[613] == pytest.approx(2.0)
    assert vector[615] == pytest.approx(1.0)

    assert vector[616] == pytest.approx(4096.0)
    assert vector[617] == pytest.approx(8192.0)
    assert vector[619] == pytest.approx(1.0)

    assert vector[626] == pytest.approx(1234567890.0)
    assert vector[677] == pytest.approx(0.0)
    assert vector[687] == pytest.approx(10.0)

    assert vector[688] == pytest.approx(2.0)
    assert vector[689] == pytest.approx(0.0)
    assert vector[690] == pytest.approx(0.0)
    assert vector[691] == pytest.approx(1.0)
    assert vector[692] == pytest.approx(1.0)

    assert vector[2351] == pytest.approx(0.0)
    assert vector[2352] == pytest.approx(0.0)
    assert vector[2353] == pytest.approx(10.0)
    assert vector[2354] == pytest.approx(100.0)


def test_ember_vectorizer_empty_groups_are_zero_vectors():
    record = ember_record(
        "empty-groups",
        1,
        "2018-02",
        sections=[],
        imports={},
        exports=[],
        datadirectories=[],
    )
    vector = EmberVectorizer().transform(record)
    assert np.isfinite(vector).all()
    assert np.all(vector[693:843] == 0)
    assert np.all(vector[893:943] == 0)
    assert np.all(vector[943:2351] == 0)
    assert np.all(vector[2351:2381] == 0)


def test_ember_vectorizer_deterministic_and_validates():
    record = ember_record("deterministic", 0, "2018-03")
    vectorizer = EmberVectorizer()
    first = vectorizer.transform(record)
    second = vectorizer.transform(record)
    np.testing.assert_array_equal(first, second)

    missing = dict(record)
    missing.pop("header")
    with pytest.raises(ValueError, match="missing required keys"):
        vectorizer.transform(missing)

    bad_sha = dict(record)
    bad_sha["sha256"] = "not-a-sha"
    with pytest.raises(ValueError, match="invalid sha256"):
        vectorizer.transform(bad_sha)

    bad_label = dict(record)
    bad_label["label"] = 2
    with pytest.raises(ValueError, match="label must be"):
        vectorizer.transform(bad_label)


def test_ember_feature_names_cover_2381_dimensions():
    names = feature_names()
    assert len(names) == FEATURE_DIM
    assert names[0] == "histogram_0"
    assert names[512] == "strings_numstrings"
    assert names[616] == "general_size"
    assert names[626] == "header_0"
    assert names[-1] == "datadirectories_29"


def _pipeline_source(tmp_path):
    train_file_0 = []
    train_file_1 = []
    for index in range(30):
        month = f"2018-{index % 6 + 1:02d}"
        train_file_0.append(ember_record(f"benign-{index}", 0, month, size=1000 + index))
        train_file_1.append(ember_record(f"malicious-{index}", 1, month, size=2000 + index))
    for index in range(5):
        train_file_1.append(ember_record(f"unlabeled-{index}", -1, "2018-05", size=3000 + index))
    # Duplicate sha256 inside supervised train: same record appended twice.
    train_file_1.append(ember_record("benign-0", 0, "2018-01", size=1000))
    # Duplicate of a test sample inside train (must be removed from train/val).
    train_file_1.append(ember_record("test-overlap", 0, "2018-06", size=5000))

    test_records = []
    for index in range(10):
        test_records.append(ember_record(f"test-benign-{index}", 0, "2018-06", size=4000 + index))
        test_records.append(
            ember_record(f"test-malicious-{index}", 1, "2018-06", size=6000 + index)
        )
    test_records.append(ember_record("test-overlap", 0, "2018-06", size=5000))
    return write_ember_source(
        tmp_path / "source",
        train_files=[train_file_0, train_file_1],
        test_records=test_records,
    )


def test_ember_pipeline_split_duplicates_and_determinism(tmp_path):
    source = _pipeline_source(tmp_path)
    output_a = tmp_path / "out_a"
    manifest_a = run_ember_preprocessing(
        source, output_a, seed=7, jobs=1, verify_source=False, scaler=True
    )
    output_b = tmp_path / "out_b"
    manifest_b = run_ember_preprocessing(
        source, output_b, seed=7, jobs=1, verify_source=False, scaler=True
    )

    for split in ("train", "val", "test"):
        X = np.load(output_a / f"{split}_X.npy")
        y = np.load(output_a / f"{split}_y.npy")
        assert X.shape == (len(y), FEATURE_DIM)
        assert X.dtype == np.float32
        assert y.dtype == np.int8
        assert np.isfinite(X).all()
        np.testing.assert_array_equal(X, np.load(output_b / f"{split}_X.npy"))
        np.testing.assert_array_equal(y, np.load(output_b / f"{split}_y.npy"))

    assert manifest_a["duplicates"]["removed_train_or_val_rows_duplicating_test"] == 1
    assert manifest_a["duplicates"]["cross_split_sha256"] == 0
    assert manifest_a["subset"] is False
    assert manifest_a["splits"]["train"]["rows"] > 0
    assert manifest_a["splits"]["val"]["rows"] > 0
    assert manifest_a["splits"]["test"]["rows"] == 21
    assert manifest_a["split_strategy"]["strategy"] == "global_time"
    assert manifest_a["splits"]["val"]["max_appeared"] == "2018-06"
    assert (
        manifest_a["splits"]["val"]["min_appeared"] >= manifest_a["splits"]["train"]["max_appeared"]
    )

    train_meta = pd.read_csv(output_a / "train_metadata.csv")
    val_meta = pd.read_csv(output_a / "val_metadata.csv")
    test_meta = pd.read_csv(output_a / "test_metadata.csv")
    assert not (set(train_meta["sha256"]) & set(val_meta["sha256"]))
    assert not (set(train_meta["sha256"]) & set(test_meta["sha256"]))
    assert "test-overlap" not in set(train_meta["sha256"].map(lambda value: value[:12]))

    without_timestamp_a = {key: value for key, value in manifest_a.items() if key != "generated_at"}
    without_timestamp_b = {key: value for key, value in manifest_b.items() if key != "generated_at"}
    assert json.dumps(without_timestamp_a, sort_keys=True) == json.dumps(
        without_timestamp_b, sort_keys=True
    )


def test_ember_subset_refuses_to_overwrite_full_run(tmp_path):
    source = _pipeline_source(tmp_path)
    output = tmp_path / "full"
    run_ember_preprocessing(source, output, seed=3, jobs=1, verify_source=False, scaler=False)
    with pytest.raises(RuntimeError, match="refusing to overwrite full-run artifacts"):
        run_ember_preprocessing(
            source,
            output,
            seed=3,
            max_samples=10,
            jobs=1,
            verify_source=False,
            scaler=False,
        )


def test_ember_manifest_detects_tampering(tmp_path):
    source = _pipeline_source(tmp_path)
    output = tmp_path / "out"
    manifest = run_ember_preprocessing(
        source, output, seed=3, jobs=1, verify_source=False, scaler=False
    )
    assert verify_manifest_artifacts(manifest, output) == []
    damaged = output / "train_X.npy"
    with open(damaged, "ab") as handle:
        handle.write(b"tampered")
    errors = verify_manifest_artifacts(manifest, output)
    assert any("train_X" in error for error in errors)


def test_time_split_holds_out_latest_rows():
    rows = []
    for index in range(100):
        rows.append(
            {
                "sha256": fake_sha(f"monthly-{index}"),
                "appeared": f"2018-{index % 10 + 1:02d}",
                "label": index % 2,
            }
        )
    frame = pd.DataFrame(rows)
    split, info = time_based_split(frame, val_fraction=0.15, min_val_per_class=1)
    assert info["strategy"] == "global_time"
    assert info["actual_val_rows"] == 15
    assert info["min_val_time"] >= info["max_train_time"]
    val_months = frame.loc[split == 1, "appeared"]
    assert val_months.max() == "2018-10"
    assert set(frame.loc[split == 1, "label"]) == {0, 1}


def test_time_split_falls_back_to_per_class():
    rows = []
    for index in range(50):
        rows.append(
            {
                "sha256": fake_sha(f"early-{index}"),
                "appeared": f"2018-{index % 3 + 1:02d}",
                "label": 0,
            }
        )
    for index in range(50):
        rows.append(
            {
                "sha256": fake_sha(f"late-{index}"),
                "appeared": f"2018-{index % 2 + 9:02d}",
                "label": 1,
            }
        )
    frame = pd.DataFrame(rows)
    split, info = time_based_split(frame, val_fraction=0.15, min_val_per_class=1)
    assert info["strategy"] == "per_class_time"
    assert info["class_counts"]["0"]["val"] > 0
    assert info["class_counts"]["1"]["val"] > 0
    for label in (0, 1):
        class_rows = frame.loc[frame["label"] == label]
        class_val = class_rows.loc[split[frame["label"].to_numpy() == label] == 1]
        class_train = class_rows.loc[split[frame["label"].to_numpy() == label] == 0]
        assert class_val["appeared"].max() == class_rows["appeared"].max()
        assert class_val["appeared"].min() >= class_train["appeared"].max()


def test_time_split_keeps_duplicate_hashes_together():
    rows = [
        {"sha256": "dup", "appeared": "2018-01", "label": 0},
        {"sha256": "dup", "appeared": "2018-12", "label": 0},
        {"sha256": "b", "appeared": "2018-02", "label": 0},
        {"sha256": "c", "appeared": "2018-03", "label": 0},
        {"sha256": "d", "appeared": "2018-04", "label": 0},
        {"sha256": "e", "appeared": "2018-05", "label": 0},
        {"sha256": "f", "appeared": "2018-06", "label": 0},
        {"sha256": "g", "appeared": "2018-07", "label": 0},
        {"sha256": "h", "appeared": "2018-08", "label": 0},
        {"sha256": "i", "appeared": "2018-09", "label": 0},
    ]
    frame = pd.DataFrame(rows)
    split, _ = time_based_split(frame, val_fraction=0.2, min_val_per_class=1)
    duplicate_positions = np.flatnonzero(frame["sha256"].to_numpy() == "dup")
    assert len(set(split[duplicate_positions])) == 1
