"""Optional real-data checks. Skipped by default; never used by CI.

Run with:
  RUN_REAL_DATA_TESTS=1 .venv/bin/python -m pytest tests/test_data_real_optional.py -q
"""

from __future__ import annotations

import os

import pytest
from src.config import resolve_cicids_source, resolve_ember_source

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_REAL_DATA_TESTS") != "1",
    reason="set RUN_REAL_DATA_TESTS=1 to exercise local ~/Documents datasets",
)


def test_real_ember_source_exists():
    source = resolve_ember_source()
    assert source.is_dir(), source
    assert (source / "train_features_0.jsonl").is_file()
    assert (source / "test_features.jsonl").is_file()


def test_real_cicids_source_exists():
    source = resolve_cicids_source()
    assert source.is_dir(), source
    assert len(list(source.glob("*.csv"))) == 8
