"""Filesystem privacy for native and container SQLite history."""

import os
import stat

import pytest
from src.evaluation.prediction_history import PredictionHistory


@pytest.mark.skipif(os.name != "posix", reason="POSIX file permission bits")
def test_history_restricts_permissions_on_create_and_on_read(tmp_path):
    path = tmp_path / "history?#.sqlite3"
    history = PredictionHistory(path)
    assert history.list() == []
    assert not path.exists()

    batch = history.append(
        {
            "model_version": "baseline_v1",
            "preprocessing_id": "0" * 64,
            "feature_schema_sha256": "1" * 64,
            "threshold": 0.5,
            "predictions": [{"label": 0, "score": 0.1}],
        },
        "raw",
    )
    assert stat.S_IMODE(path.stat().st_mode) == 0o600

    path.chmod(0o640)
    assert PredictionHistory(path).list() == [batch]
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
