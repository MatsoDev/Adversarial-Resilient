"""End-to-end CLI tests for scripts/preprocess.py using synthetic sources."""

from __future__ import annotations

import json

from scripts.preprocess import main

from tests.data_fixtures import (
    ember_record,
    standard_cicids_source,
    write_ember_source,
)


def _ember_source(tmp_path):
    train_0 = []
    train_1 = []
    for index in range(20):
        month = f"2018-{index % 6 + 1:02d}"
        label = index % 2
        record = ember_record(f"cli-{index}", label, month, size=1000 + index)
        (train_0 if label == 0 else train_1).append(record)
    test = [
        ember_record(f"cli-test-{index}", index % 2, "2018-06", size=5000 + index)
        for index in range(20)
    ]
    return write_ember_source(
        tmp_path / "source", train_files=[train_0, train_1], test_records=test
    )


def test_ember_cli_subset_verify_and_force(tmp_path):
    source = _ember_source(tmp_path)
    output = tmp_path / "ember_out"
    common = [
        "--dataset",
        "ember",
        "--source",
        str(source),
        "--max-samples",
        "50",
        "--output-dir",
        str(output),
        "--force",
        "--jobs",
        "1",
        "--skip-source-check",
    ]
    assert main(common) == 0
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["subset"] is True
    assert manifest["sampling"]["max_samples"] == 50
    for name in (
        "train_X.npy",
        "val_X.npy",
        "test_X.npy",
        "train_y.npy",
        "feature_names.json",
        "label_mapping.json",
        "scaler_mean.npy",
        "train_metadata.csv",
    ):
        assert (output / name).is_file(), name

    assert main(["--dataset", "ember", "--output-dir", str(output), "--verify-only"]) == 0

    with open(output / "test_X.npy", "ab") as handle:
        handle.write(b"corrupt")
    assert main(["--dataset", "ember", "--output-dir", str(output), "--verify-only"]) == 1

    assert main(common) == 0
    assert main(["--dataset", "ember", "--output-dir", str(output), "--verify-only"]) == 0


def test_cicids_cli_subset_and_verify(tmp_path):
    source = standard_cicids_source(tmp_path / "source")
    output = tmp_path / "cicids_out"
    args = [
        "--dataset",
        "cicids2017",
        "--source",
        str(source),
        "--max-samples",
        "40",
        "--output-dir",
        str(output),
        "--force",
        "--skip-source-check",
    ]
    assert main(args) == 0
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["dataset"] == "cicids2017"
    assert manifest["subset"] is True
    assert (output / "train_y_binary.npy").is_file()
    assert (output / "train_y_multiclass.npy").is_file()
    assert main(["--dataset", "cicids2017", "--output-dir", str(output), "--verify-only"]) == 0
