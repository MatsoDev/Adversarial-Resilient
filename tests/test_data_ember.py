"""Synthetic tests for EMBER vectorisation, splits and manifests (no real data)."""

from __future__ import annotations

import copy
import json

import numpy as np
import pandas as pd
import pytest
from src.data.ember import (
    FEATURE_DIM,
    TEST_FILE_NAME,
    TRAIN_FILE_NAMES,
    EmberVectorizer,
    _check_ember_source_counts,
    discover_ember_files,
    feature_names,
    iter_ember_records,
    run_ember_preprocessing,
)
from src.data.preprocessing import time_based_split, verify_manifest_artifacts

from tests.data_fixtures import ember_record, fake_sha, write_ember_source


def _set_path(record, path, value):
    target = record
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


def _delete_path(record, path):
    target = record
    for key in path[:-1]:
        target = target[key]
    del target[path[-1]]


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


def test_discover_ember_files_requires_directory_train_files_and_test_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="source directory not found"):
        discover_ember_files(tmp_path / "missing")

    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(FileNotFoundError, match="no train_features"):
        discover_ember_files(empty)

    no_test = tmp_path / "no-test"
    no_test.mkdir()
    (no_test / "train_features_0.jsonl").write_text("", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match=TEST_FILE_NAME):
        discover_ember_files(no_test, strict=False)


def test_discover_ember_files_strict_order_and_non_strict_sorting(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    for name in reversed(TRAIN_FILE_NAMES):
        (source / name).write_text("", encoding="utf-8")
    (source / TEST_FILE_NAME).write_text("", encoding="utf-8")
    files = discover_ember_files(source)
    assert [path.name for path in files.train] == list(TRAIN_FILE_NAMES)
    assert files.test.name == TEST_FILE_NAME

    partial = tmp_path / "partial"
    partial.mkdir()
    (partial / "train_features_10.jsonl").write_text("", encoding="utf-8")
    (partial / "train_features_2.jsonl").write_text("", encoding="utf-8")
    (partial / TEST_FILE_NAME).write_text("", encoding="utf-8")
    ordered = discover_ember_files(partial, strict=False)
    assert [path.name for path in ordered.train] == [
        "train_features_2.jsonl",
        "train_features_10.jsonl",
    ]
    with pytest.raises(FileNotFoundError, match="expected EMBER train files"):
        discover_ember_files(partial)


def test_iter_ember_records_skips_blank_lines_and_returns_line_numbers(tmp_path):
    record_a = ember_record("iter-a", 0, "2018-01")
    record_b = ember_record("iter-b", 1, "2018-02")
    path = tmp_path / "records.jsonl"
    path.write_text(json.dumps(record_a) + "\n\n" + json.dumps(record_b) + "\n", encoding="utf-8")

    records = list(iter_ember_records(path))
    assert [line_number for line_number, _ in records] == [0, 2]
    assert [record["sha256"] for _, record in records] == [
        record_a["sha256"],
        record_b["sha256"],
    ]


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("histogram",), [1] * 255, "histogram must have 256"),
        (("byteentropy",), [1] * 255, "byteentropy must have 256"),
        (("strings", "printabledist"), [1] * 95, "printabledist must have 96"),
    ],
)
def test_ember_vectorizer_rejects_wrong_count_lengths(path, value, message):
    record = ember_record("bad-length", 0, "2018-01")
    _set_path(record, path, value)
    with pytest.raises(ValueError, match=message):
        EmberVectorizer().transform(record)


@pytest.mark.parametrize(
    "path",
    [
        ("strings", "MZ"),
        ("header", "coff", "machine"),
        ("header", "optional", "magic"),
        ("section", "entry"),
        ("section", "sections"),
    ],
)
def test_ember_vectorizer_rejects_missing_nested_fields(path):
    record = ember_record("missing-field", 0, "2018-01")
    _delete_path(record, path)
    with pytest.raises(ValueError):
        EmberVectorizer().transform(record)


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("general",), [], "general must contain"),
        (("header", "coff"), [], "header.coff/header.optional must be objects"),
        (("section", "entry"), 5, "section.entry must be a string"),
        (("section", "sections"), {}, "section.sections must be a list"),
        (("imports",), [], "imports must be an object"),
        (("exports",), {}, "exports must be a list"),
        (("datadirectories",), {}, "datadirectories must be a list"),
        (("appeared",), "2018-13", "invalid appeared"),
        (("appeared",), "2018-1", "invalid appeared"),
    ],
)
def test_ember_vectorizer_rejects_wrong_types_and_dates(path, value, message):
    record = ember_record("bad-type", 0, "2018-01")
    _set_path(record, path, value)
    with pytest.raises(ValueError, match=message):
        EmberVectorizer().transform(record)


def test_ember_general_fields_must_keep_the_official_order():
    record = ember_record("general-order", 0, "2018-01")
    record["general"] = dict(reversed(list(record["general"].items())))
    with pytest.raises(ValueError, match="official order"):
        EmberVectorizer().transform(record)


def test_ember_vectorizer_zero_histograms_normalize_to_zero_blocks():
    record = ember_record(
        "zero-histogram",
        0,
        "2018-01",
        histogram=[0] * 256,
        byteentropy=[0] * 256,
    )
    vector = EmberVectorizer().transform(record)
    assert np.all(vector[0:256] == 0)
    assert np.all(vector[256:512] == 0)


def test_ember_vectorizer_keeps_only_the_first_fifteen_datadirectories():
    directories = [{"size": index, "virtual_address": index * 10} for index in range(20)]
    record = ember_record("datadirs", 0, "2018-01", datadirectories=directories)
    vector = EmberVectorizer().transform(record)
    expected = np.zeros(30, dtype=np.float32)
    expected[0::2] = np.arange(15)
    expected[1::2] = np.arange(15) * 10
    np.testing.assert_array_equal(vector[2351:], expected)


def test_ember_source_count_guard_reports_mismatches_and_force_overrides():
    file_stats = [
        {
            "name": "train_features_0.jsonl",
            "partition": "train",
            "rows": 800_000,
            "label_counts": {-1: 200_000, 0: 300_000, 1: 300_000},
        },
        {
            "name": "test_features.jsonl",
            "partition": "test",
            "rows": 200_000,
            "label_counts": {0: 100_000, 1: 100_000},
        },
    ]
    assert _check_ember_source_counts(file_stats, force=False) is None

    wrong = copy.deepcopy(file_stats)
    wrong[0]["rows"] = 799_999
    with pytest.raises(ValueError, match="train rows"):
        _check_ember_source_counts(wrong, force=False)
    assert _check_ember_source_counts(wrong, force=True) is None


def test_ember_pipeline_rejects_source_files_with_wrong_hashes(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    for name in TRAIN_FILE_NAMES:
        (source / name).write_text("{}\n", encoding="utf-8")
    (source / TEST_FILE_NAME).write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="sha256 mismatch"):
        run_ember_preprocessing(source, tmp_path / "out", jobs=1, verify_source=True)


def test_ember_pipeline_can_skip_scaler_artifacts(tmp_path):
    source = _pipeline_source(tmp_path)
    output = tmp_path / "no-scaler"
    manifest = run_ember_preprocessing(
        source, output, seed=3, jobs=1, verify_source=False, scaler=False
    )
    for name in ("scaler_mean.npy", "scaler_scale.npy", "scaler.json"):
        assert not (output / name).exists(), name
    for name in ("scaler_mean", "scaler_scale", "scaler"):
        assert name not in manifest["artifacts"]
    assert verify_manifest_artifacts(manifest, output) == []


def test_ember_pipeline_parallel_vectorisation_matches_serial(tmp_path):
    source = _pipeline_source(tmp_path)
    serial_output = tmp_path / "serial"
    parallel_output = tmp_path / "parallel"
    serial = run_ember_preprocessing(
        source, serial_output, seed=9, jobs=1, verify_source=False, scaler=False
    )
    parallel = run_ember_preprocessing(
        source, parallel_output, seed=9, jobs=2, verify_source=False, scaler=False
    )

    for split in ("train", "val", "test"):
        np.testing.assert_array_equal(
            np.load(serial_output / f"{split}_X.npy"),
            np.load(parallel_output / f"{split}_X.npy"),
        )
        np.testing.assert_array_equal(
            np.load(serial_output / f"{split}_y.npy"),
            np.load(parallel_output / f"{split}_y.npy"),
        )
    serial.pop("generated_at")
    parallel.pop("generated_at")
    assert json.dumps(serial, sort_keys=True) == json.dumps(parallel, sort_keys=True)


def test_ember_pipeline_rejects_records_missing_required_keys(tmp_path):
    bad = ember_record("missing-header", 0, "2018-01")
    bad.pop("header")
    source = write_ember_source(
        tmp_path / "source",
        train_files=[[bad]],
        test_records=[ember_record("test", 0, "2018-06")],
    )
    with pytest.raises(ValueError, match="missing required keys"):
        run_ember_preprocessing(source, tmp_path / "out", jobs=1, verify_source=False, scaler=False)


def test_ember_pipeline_rejects_unexpected_labels(tmp_path):
    source = write_ember_source(
        tmp_path / "source",
        train_files=[[ember_record("bad-label", 2, "2018-01")]],
        test_records=[ember_record("test", 0, "2018-06")],
    )
    with pytest.raises(ValueError, match="unexpected EMBER labels"):
        run_ember_preprocessing(source, tmp_path / "out", jobs=1, verify_source=False, scaler=False)


def test_ember_pipeline_requires_at_least_one_labeled_training_row(tmp_path):
    source = write_ember_source(
        tmp_path / "source",
        train_files=[[ember_record(f"unlabeled-{index}", -1, "2018-01") for index in range(3)]],
        test_records=[ember_record("test", 0, "2018-06")],
    )
    with pytest.raises(RuntimeError, match="no labeled EMBER training rows"):
        run_ember_preprocessing(source, tmp_path / "out", jobs=1, verify_source=False, scaler=False)


def test_ember_subset_must_cover_every_class(tmp_path):
    source = _pipeline_source(tmp_path)
    with pytest.raises(ValueError, match="at least the number of classes"):
        run_ember_preprocessing(
            source,
            tmp_path / "tiny",
            seed=1,
            max_samples=1,
            jobs=1,
            verify_source=False,
            scaler=False,
        )
