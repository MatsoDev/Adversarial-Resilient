"""End-to-end CLI tests for scripts/preprocess.py using synthetic sources."""

from __future__ import annotations

import json

from scripts import preprocess
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


def test_dataset_all_rejects_ambiguous_source_and_output(tmp_path):
    assert main(["--dataset", "all", "--source", str(tmp_path)]) == 2
    assert main(["--dataset", "all", "--output-dir", str(tmp_path / "out")]) == 2


def test_dataset_all_runs_both_pipelines_and_verifies_them(monkeypatch, tmp_path):
    ember_output = tmp_path / "processed" / "ember2018"
    cicids_output = tmp_path / "processed" / "cicids2017"
    manifests = tmp_path / "manifests"
    monkeypatch.setattr(preprocess, "EMBER_PROCESSED_DIR", ember_output)
    monkeypatch.setattr(preprocess, "CICIDS_PROCESSED_DIR", cicids_output)
    monkeypatch.setattr(preprocess, "DATA_MANIFESTS_DIR", manifests)

    ember_source = _ember_source(tmp_path / "ember-case")
    cicids_source = standard_cicids_source(tmp_path / "cicids-case")
    exit_code = main(
        [
            "--dataset",
            "all",
            "--ember-source",
            str(ember_source),
            "--cicids-source",
            str(cicids_source),
            "--max-samples",
            "40",
            "--force",
            "--skip-source-check",
            "--jobs",
            "1",
        ]
    )
    assert exit_code == 0
    assert json.loads((ember_output / "manifest.json").read_text())["subset"] is True
    assert json.loads((cicids_output / "manifest.json").read_text())["subset"] is True
    assert not list(manifests.glob("*.json"))
    assert main(["--dataset", "all", "--verify-only"]) == 0


def test_full_run_publishes_the_manifest_for_the_default_output(monkeypatch, tmp_path):
    ember_output = tmp_path / "processed" / "ember2018"
    manifests = tmp_path / "manifests"
    monkeypatch.setattr(preprocess, "EMBER_PROCESSED_DIR", ember_output)
    monkeypatch.setattr(preprocess, "DATA_MANIFESTS_DIR", manifests)

    source = _ember_source(tmp_path / "source")
    assert (
        main(
            [
                "--dataset",
                "ember",
                "--source",
                str(source),
                "--force",
                "--skip-source-check",
                "--jobs",
                "1",
            ]
        )
        == 0
    )
    published = manifests / "ember2018.json"
    assert published.is_file()
    published_manifest = json.loads(published.read_text())
    assert published_manifest["dataset"] == "ember2018"
    assert published_manifest["subset"] is False
    assert main(["--dataset", "ember", "--verify-only"]) == 0


def test_no_scale_option_skips_scaler_artifacts(tmp_path):
    source = _ember_source(tmp_path / "source")
    output = tmp_path / "out"
    assert (
        main(
            [
                "--dataset",
                "ember",
                "--source",
                str(source),
                "--max-samples",
                "40",
                "--output-dir",
                str(output),
                "--force",
                "--skip-source-check",
                "--no-scale",
                "--jobs",
                "1",
            ]
        )
        == 0
    )
    for name in ("scaler_mean.npy", "scaler_scale.npy", "scaler.json"):
        assert not (output / name).exists(), name


def test_custom_output_does_not_publish_a_manifest(tmp_path):
    output = tmp_path / "custom"
    output.mkdir()
    preprocess._publish_manifest("ember", output, {"dataset": "ember2018", "subset": False})
    assert not list(tmp_path.rglob("*.json"))


def test_subset_run_does_not_publish_a_manifest(monkeypatch, tmp_path):
    manifests = tmp_path / "manifests"
    monkeypatch.setattr(preprocess, "DATA_MANIFESTS_DIR", manifests)
    preprocess._publish_manifest("ember", tmp_path, {"dataset": "ember2018", "subset": True})
    assert not list(manifests.glob("*.json"))


def test_verify_only_reports_missing_and_mismatched_manifests(tmp_path):
    output = tmp_path / "out"
    verify_args = ["--dataset", "ember", "--output-dir", str(output), "--verify-only"]
    assert main(verify_args) == 1

    output.mkdir()
    (output / "manifest.json").write_text(
        json.dumps({"dataset": "cicids2017", "artifacts": {}}), encoding="utf-8"
    )
    assert main(verify_args) == 1

    (output / "manifest.json").write_text(
        json.dumps({"dataset": "ember2018", "artifacts": {}}), encoding="utf-8"
    )
    assert main(verify_args) == 1
