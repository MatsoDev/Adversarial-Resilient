"""Direct tests for shared preprocessing, split, hashing and atomic-write helpers."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import UTC
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from src.data import preprocessing
from src.data.preprocessing import (
    apply_standardization,
    artifact_record,
    atomic_save_npy,
    atomic_write_dataframe,
    atomic_write_text,
    code_revision,
    compute_scaler_stats,
    ensure_finite,
    finalize_atomic_memmap,
    load_json,
    open_atomic_memmap,
    remove_rows_with_ids,
    sha256_bytes,
    sha256_file,
    stratified_split_indices,
    time_based_split,
    utc_now_iso,
    verify_manifest_artifacts,
    write_json_atomic,
)


def _temp_siblings(path: Path) -> list[Path]:
    return list(path.parent.glob(f".{path.name}.*.tmp"))


def test_sha256_helpers_match_hashlib_and_stream_across_chunks(tmp_path):
    payload = bytes(range(256)) * 20
    path = tmp_path / "payload.bin"
    path.write_bytes(payload)

    assert sha256_bytes(payload) == hashlib.sha256(payload).hexdigest()
    assert sha256_file(path, chunk_size=7) == hashlib.sha256(payload).hexdigest()
    assert sha256_file(path) == hashlib.sha256(payload).hexdigest()


def test_atomic_text_json_npy_and_dataframe_round_trip(tmp_path):
    text_path = tmp_path / "nested" / "note.txt"
    atomic_write_text(text_path, "hello\n")
    assert text_path.read_text(encoding="utf-8") == "hello\n"

    json_path = tmp_path / "nested" / "payload.json"
    write_json_atomic(
        json_path,
        {
            "z": np.int64(3),
            "a": np.float32(1.5),
            "array": np.asarray([1, 2], dtype=np.int64),
            "path": Path("relative/file.txt"),
        },
    )
    payload = load_json(json_path)
    assert payload == {
        "a": 1.5,
        "array": [1, 2],
        "path": "relative/file.txt",
        "z": 3,
    }
    text = json_path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert list(payload) == ["a", "array", "path", "z"]
    assert text == json.dumps(payload, indent=2, sort_keys=True) + "\n"

    npy_path = tmp_path / "nested" / "array.npy"
    array = np.asarray([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    atomic_save_npy(npy_path, array)
    np.testing.assert_array_equal(np.load(npy_path), array)

    frame = pd.DataFrame({"a": [1, 2], "b": [3, 4], "ignored": [5, 6]})
    csv_path = tmp_path / "nested" / "table.csv"
    atomic_write_dataframe(frame, csv_path, columns=["b", "a"])
    loaded = pd.read_csv(csv_path)
    assert list(loaded.columns) == ["b", "a"]
    pd.testing.assert_frame_equal(loaded, pd.DataFrame({"b": [3, 4], "a": [1, 2]}))

    assert not _temp_siblings(text_path)
    assert not _temp_siblings(json_path)
    assert not _temp_siblings(npy_path)
    assert not _temp_siblings(csv_path)


def test_atomic_writes_preserve_the_old_file_when_serialization_fails(tmp_path):
    json_path = tmp_path / "payload.json"
    write_json_atomic(json_path, {"ok": True})
    original_json = json_path.read_bytes()
    with pytest.raises(TypeError, match="not JSON serializable"):
        write_json_atomic(json_path, {"bad": object()})
    assert json_path.read_bytes() == original_json
    assert not _temp_siblings(json_path)

    csv_path = tmp_path / "table.csv"
    frame = pd.DataFrame({"a": [1]})
    atomic_write_dataframe(frame, csv_path, columns=["a"])
    original_csv = csv_path.read_bytes()
    with pytest.raises(KeyError):
        atomic_write_dataframe(frame, csv_path, columns=["missing"])
    assert csv_path.read_bytes() == original_csv
    assert not _temp_siblings(csv_path)


def test_atomic_memmap_publishes_only_after_finalize(tmp_path):
    final = tmp_path / "published.npy"
    final.write_bytes(b"old-content")
    memmap, tmp = open_atomic_memmap(final, shape=(2, 3), dtype="float32")
    assert tmp.exists()
    memmap[:] = np.arange(6, dtype=np.float32).reshape(2, 3)
    memmap.flush()
    assert final.read_bytes() == b"old-content"

    finalize_atomic_memmap(memmap, tmp, final)
    assert not tmp.exists()
    np.testing.assert_array_equal(np.load(final), np.arange(6, dtype=np.float32).reshape(2, 3))


def test_compute_scaler_stats_matches_numpy_and_handles_zero_variance(tmp_path):
    rng = np.random.default_rng(4)
    X = rng.normal(size=(203, 5)).astype(np.float32)
    X[:, 2] = 7.5
    mean, scale = compute_scaler_stats(X, chunk_size=17)

    expected_mean = X.astype(np.float64).mean(axis=0)
    expected_scale = X.astype(np.float64).std(axis=0)
    expected_scale[2] = 1.0
    np.testing.assert_allclose(mean, expected_mean, rtol=0, atol=1e-12)
    np.testing.assert_allclose(scale, expected_scale, rtol=0, atol=1e-12)
    assert scale[2] == 1.0

    path = tmp_path / "features.npy"
    np.save(path, X)
    path_mean, path_scale = compute_scaler_stats(path, chunk_size=50)
    np.testing.assert_allclose(path_mean, mean, rtol=0, atol=1e-12)
    np.testing.assert_allclose(path_scale, scale, rtol=0, atol=1e-12)


@pytest.mark.parametrize(
    ("array", "message"),
    [
        (np.arange(4, dtype=np.float32), "2-D array"),
        (np.empty((0, 3), dtype=np.float32), "zero rows"),
        (np.asarray([[1.0, np.nan]], dtype=np.float32), "non-finite"),
        (np.asarray([[1.0, np.inf]], dtype=np.float32), "non-finite"),
    ],
)
def test_compute_scaler_stats_rejects_invalid_input(array, message):
    with pytest.raises(ValueError, match=message):
        compute_scaler_stats(array)


def test_apply_standardization_chunking_is_equivalent_and_float32():
    rng = np.random.default_rng(9)
    X = rng.normal(size=(19, 4)).astype(np.float32)
    X[:, 3] = 7.0
    original = X.copy()
    mean = np.asarray([0.5, -1.0, 2.0, 7.0], dtype=np.float64)
    scale = np.asarray([2.0, 4.0, 0.5, 1.0], dtype=np.float64)

    small_chunks = apply_standardization(X, mean, scale, chunk_size=3)
    one_chunk = apply_standardization(X, mean, scale, chunk_size=10_000)
    assert small_chunks.dtype == np.float32
    np.testing.assert_array_equal(small_chunks, one_chunk)
    np.testing.assert_allclose(
        small_chunks[:, 3], np.zeros(len(X), dtype=np.float32), rtol=0, atol=1e-6
    )
    expected = (X.astype(np.float64) - mean) / scale
    np.testing.assert_allclose(small_chunks, expected, rtol=0, atol=1e-6)
    np.testing.assert_array_equal(X, original)


def test_ensure_finite_rejects_nan_and_inf_with_a_context_name():
    ensure_finite(np.asarray([[1.0, 2.0]]))
    with pytest.raises(ValueError, match="iris contains NaN or infinite"):
        ensure_finite(np.asarray([[1.0, np.nan]]), name="iris")
    with pytest.raises(ValueError, match="iris contains NaN or infinite"):
        ensure_finite(np.asarray([[np.inf, 2.0]]), name="iris")


def test_stratified_split_indices_are_deterministic_disjoint_and_complete():
    rng = np.random.default_rng(7)
    y = np.concatenate([np.zeros(120, dtype=np.int8), np.ones(80, dtype=np.int8)])
    rng.shuffle(y)

    first = stratified_split_indices(y, seed=13)
    second = stratified_split_indices(y, seed=13)
    for split in ("train", "val", "test"):
        np.testing.assert_array_equal(first[split], second[split])

    combined = np.concatenate([first["train"], first["val"], first["test"]])
    np.testing.assert_array_equal(np.sort(combined), np.arange(len(y)))
    assert len(set(first["train"]) & set(first["val"])) == 0
    assert len(set(first["train"]) & set(first["test"])) == 0
    assert len(set(first["val"]) & set(first["test"])) == 0
    assert len(first["train"]) == 140
    assert len(first["val"]) == 30
    assert len(first["test"]) == 30
    for split in ("train", "val", "test"):
        assert set(y[first[split]]) == {0, 1}

    different_seed = stratified_split_indices(y, seed=14)
    assert not np.array_equal(first["train"], different_seed["train"])


@pytest.mark.parametrize(
    ("labels", "fractions"),
    [
        (np.zeros(10, dtype=np.int8), (0.8, 0.1, 0.0)),
        (np.asarray([], dtype=np.int8), (0.7, 0.15, 0.15)),
        (np.zeros((10, 2), dtype=np.int8), (0.7, 0.15, 0.15)),
    ],
)
def test_stratified_split_indices_rejects_invalid_input(labels, fractions):
    with pytest.raises(ValueError):
        stratified_split_indices(
            labels,
            seed=1,
            train_fraction=fractions[0],
            val_fraction=fractions[1],
            test_fraction=fractions[2],
        )


def _time_frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["sha256", "appeared", "label"])


def test_time_based_split_rejects_invalid_inputs():
    frame = _time_frame(
        [
            {"sha256": "a", "appeared": "2018-01", "label": 0},
            {"sha256": "b", "appeared": "2018-02", "label": 1},
        ]
    )
    with pytest.raises(ValueError, match="val_fraction"):
        time_based_split(frame, val_fraction=0.0)
    with pytest.raises(ValueError, match="val_fraction"):
        time_based_split(frame, val_fraction=1.0)
    with pytest.raises(ValueError, match="empty frame"):
        time_based_split(_time_frame([]))
    with pytest.raises(KeyError, match="missing column 'label'"):
        time_based_split(frame.drop(columns=["label"]))


def test_time_based_split_raises_when_a_duplicate_group_blocks_a_train_set():
    rows = [
        {"sha256": "same", "appeared": f"2018-{index % 9 + 1:02d}", "label": index % 2}
        for index in range(10)
    ]
    with pytest.raises(RuntimeError, match="non-degenerate"):
        time_based_split(_time_frame(rows), val_fraction=0.2, min_val_per_class=1)


def test_time_based_split_reports_conflicting_labels_for_one_identifier():
    rows = [
        {"sha256": "dup", "appeared": "2018-01", "label": 0},
        {"sha256": "dup", "appeared": "2018-12", "label": 1},
    ]
    for index in range(12):
        rows.append({"sha256": f"a-{index}", "appeared": f"2018-{index % 6 + 1:02d}", "label": 0})
        rows.append({"sha256": f"b-{index}", "appeared": f"2018-{index % 6 + 7:02d}", "label": 1})
    frame = _time_frame(rows)
    split, info = time_based_split(frame, val_fraction=0.2, min_val_per_class=1)

    assert info["label_conflicts"] == 1
    duplicate_positions = np.flatnonzero(frame["sha256"].to_numpy() == "dup")
    assert len(set(split[duplicate_positions])) == 1


def test_remove_rows_with_ids_casts_identifiers_and_reports_count():
    frame = pd.DataFrame({"id": [1, 2, 3, 4], "value": ["a", "b", "c", "d"]})
    filtered, removed = remove_rows_with_ids(frame, id_col="id", blocked_ids={"2", "4"})
    assert removed == 2
    assert filtered["id"].tolist() == [1, 3]
    assert frame["id"].tolist() == [1, 2, 3, 4]

    unchanged, removed = remove_rows_with_ids(frame, id_col="id", blocked_ids=set())
    assert removed == 0
    assert unchanged is frame


def test_artifact_record_and_verification_detect_size_hash_and_missing_files(tmp_path):
    root = tmp_path / "root"
    (root / "sub").mkdir(parents=True)
    path = root / "sub" / "data.bin"
    path.write_bytes(b"artifact")

    record = artifact_record(path, root=root, shape=(2, 3), dtype="float32")
    assert record["file"] == "sub/data.bin"
    assert record["size_bytes"] == len(b"artifact")
    assert record["sha256"] == hashlib.sha256(b"artifact").hexdigest()
    assert record["shape"] == [2, 3]
    assert record["dtype"] == "float32"

    manifest = {"artifacts": {"data": record}}
    assert verify_manifest_artifacts(manifest, root) == []

    size_record = dict(record, size_bytes=record["size_bytes"] + 1)
    errors = verify_manifest_artifacts({"artifacts": {"data": size_record}}, root)
    assert any("size mismatch" in error for error in errors)

    hash_record = dict(record, sha256="0" * 64)
    errors = verify_manifest_artifacts({"artifacts": {"data": hash_record}}, root)
    assert any("sha256 mismatch" in error for error in errors)

    hash_record = dict(record)
    path.unlink()
    errors = verify_manifest_artifacts({"artifacts": {"data": hash_record}}, root)
    assert any("missing file" in error for error in errors)


def test_artifact_record_rejects_a_path_outside_the_manifest_root(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"x")
    with pytest.raises(ValueError):
        artifact_record(outside, root=root)


def test_utc_now_iso_is_second_precision_utc():
    timestamp = utc_now_iso()
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00", timestamp)
    parsed = pd.Timestamp(timestamp).to_pydatetime()
    assert parsed.tzinfo == UTC
    assert parsed.microsecond == 0


def test_code_revision_returns_none_without_git(monkeypatch):
    monkeypatch.setattr(preprocessing.shutil, "which", lambda name: None)
    assert code_revision() is None


def test_code_revision_uses_git_when_available(monkeypatch):
    class Result:
        returncode = 0
        stdout = "abc123\n"

    monkeypatch.setattr(preprocessing.shutil, "which", lambda name: "/usr/bin/git")
    monkeypatch.setattr(preprocessing.subprocess, "run", lambda *args, **kwargs: Result())
    assert code_revision() == "abc123"


def test_code_revision_returns_none_when_git_times_out(monkeypatch):
    monkeypatch.setattr(preprocessing.shutil, "which", lambda name: "/usr/bin/git")

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="git", timeout=5)

    monkeypatch.setattr(preprocessing.subprocess, "run", timeout)
    assert code_revision() is None


def test_atomic_write_cleans_up_when_publishing_fails(tmp_path, monkeypatch):
    target = tmp_path / "note.txt"
    target.write_text("old", encoding="utf-8")

    def failing_replace(source, destination):
        raise OSError("publish failed")

    monkeypatch.setattr(preprocessing.os, "replace", failing_replace)
    with pytest.raises(OSError, match="publish failed"):
        atomic_write_text(target, "new")

    assert target.read_text(encoding="utf-8") == "old"
    assert not _temp_siblings(target)
