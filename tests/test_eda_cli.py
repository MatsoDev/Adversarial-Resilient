"""Tests for the deterministic EDA CLI and its report/output contract."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
from scripts import eda_datasets
from src import config

from tests.data_fixtures import (
    ember_record,
    standard_cicids_source,
    write_ember_source,
)


def _synthetic_ember_source(root: Path) -> Path:
    train = [
        ember_record(f"eda-{index}", index % 2, f"2018-{index % 6 + 1:02d}") for index in range(12)
    ]
    return write_ember_source(root, train_files=[train[:8]], test_records=train[8:])


def test_output_paths_default_to_docs_and_honor_an_override(tmp_path):
    args = eda_datasets.parse_args(["--dataset", "ember"])
    assert eda_datasets._output_paths(args) == (
        config.RESULTS_DIR / "data_eda.json",
        config.FIGURES_DIR,
        config.DATA_DOCS_DIR / "eda_report.md",
    )

    override = eda_datasets.parse_args(["--dataset", "all", "--output-dir", str(tmp_path)])
    results, figures, report = eda_datasets._output_paths(override)
    assert results == tmp_path / "results" / "data_eda.json"
    assert figures == tmp_path / "figures"
    assert report == tmp_path / "data" / "eda_report.md"


def test_sample_frame_is_deterministic_stratified_and_bounded():
    frame = pd.DataFrame({"label": [0, 1] * 100, "value": list(range(200))})
    first = eda_datasets._sample_frame(frame, max_samples=20, seed=3)
    second = eda_datasets._sample_frame(frame, max_samples=20, seed=3)
    assert first.equals(second)
    assert len(first) == 20
    assert set(first["label"]) == {0, 1}

    complete = eda_datasets._sample_frame(frame, max_samples=500, seed=3)
    assert complete.equals(frame.reset_index(drop=True))

    empty = eda_datasets._sample_frame(frame.iloc[:0], max_samples=5, seed=3)
    assert empty.empty


def test_eda_cli_writes_json_report_and_figures_for_both_datasets(tmp_path):
    ember_source = _synthetic_ember_source(tmp_path / "ember")
    cicids_source = standard_cicids_source(tmp_path / "cicids")
    output = tmp_path / "eda"

    exit_code = eda_datasets.main(
        [
            "--dataset",
            "all",
            "--ember-source",
            str(ember_source),
            "--cicids-source",
            str(cicids_source),
            "--output-dir",
            str(output),
            "--max-samples",
            "5",
            "--no-processed",
            "--jobs",
            "1",
        ]
    )
    assert exit_code == 0

    results_path = output / "results" / "data_eda.json"
    report_path = output / "data" / "eda_report.md"
    assert results_path.is_file()
    assert report_path.is_file()
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    assert payload["seed"] == 42
    assert payload["max_samples"] == 5
    assert set(payload["datasets"]) == {"ember2018", "cicids2017"}

    ember = payload["datasets"]["ember2018"]
    assert ember["source"]["rows"] == 12
    assert ember["source"]["label_counts"] == {"0": 6, "1": 6}
    assert ember["feature_sample"]["rows"] == 5
    assert ember["feature_sample"]["normalization"]["histogram_all_close_to_one"] is True
    assert ember["feature_sample"]["normalization"]["byteentropy_all_close_to_one"] is True

    cicids = payload["datasets"]["cicids2017"]
    assert cicids["source"]["rows"] == 62
    assert sum(cicids["source"]["class_counts"].values()) == 62
    assert cicids["cleaning"]["feature_dim"] == 4
    assert cicids["cleaning"]["duplicate_rows"]["total"] == 2
    assert cicids["cleaning"]["duplicate_rows"]["within_file"] == 1
    assert cicids["cleaning"]["duplicate_rows"]["cross_file"] == 1

    report = report_path.read_text(encoding="utf-8")
    for heading in (
        "# Dataset EDA report (Sprint 2)",
        "## EMBER2018 v2",
        "## CIC-IDS-2017",
        "## Notes and limitations",
    ):
        assert heading in report

    figures = {path.name for path in (output / "figures").glob("*.png")}
    assert {
        "data_ember_label_counts.png",
        "data_ember_appeared_by_label.png",
        "data_ember_feature_groups.png",
        "data_cicids_class_counts.png",
        "data_cicids_per_file.png",
        "data_cicids_feature_histograms.png",
    } <= figures


@pytest.mark.parametrize(
    "argv",
    [
        ["--dataset", "all", "--source", "somewhere"],
        ["--dataset", "ember", "--ember-source", "somewhere"],
        ["--dataset", "cicids2017", "--cicids-source", "somewhere"],
        ["--dataset", "ember", "--max-samples", "0"],
    ],
)
def test_eda_cli_rejects_ambiguous_or_invalid_arguments(argv):
    assert eda_datasets.main(argv) == 2
