"""Regression tests for the read-only artifact service's resource boundaries."""

import json
import os
from pathlib import Path

import pytest
from api.main import create_app
from fastapi.testclient import TestClient
from src.config import ROOT
from src.evaluation.artifacts import ArtifactStore, ArtifactUnavailable


@pytest.mark.parametrize("value", ["1e999", "-1e999", "NaN", "Infinity"])
def test_nonfinite_numbers_rejected_anywhere_in_artifact(tmp_path, value):
    target = tmp_path / "results"
    target.mkdir()
    (target / "art_quickstart_results.json").write_text(
        '{"attacks":{},"accuracy_vs_eps":[],"nested":{"value":' + value + "}}"
    )
    response = TestClient(create_app(ArtifactStore(tmp_path))).get("/v1/demo")
    assert response.status_code == 503
    assert response.json() == {"detail": "Artifact is unavailable or invalid"}


def test_run_response_has_aggregate_budget(tmp_path):
    folder = tmp_path / "results/baselines"
    folder.mkdir(parents=True)
    reference = json.loads((ROOT / "docs/results/baseline_reference.json").read_bytes())
    for index in range(5):
        report = json.loads(json.dumps(reference))
        for run in report["runs"]:
            run["run_id"] = f"{index}-{run['run_id']}"
        report["runs"][0]["padding"] = "x" * 900_000
        (folder / f"{index}.json").write_text(json.dumps(report))
    response = TestClient(create_app(ArtifactStore(tmp_path))).get("/v1/runs")
    assert response.status_code == 200
    assert len(response.content) <= 4 * 1024 * 1024
    assert response.json()["truncated"] is True
    assert response.json()["runs"]


def test_symlink_loop_is_unavailable(tmp_path):
    path = tmp_path / "loop"
    try:
        path.symlink_to(path)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(ArtifactUnavailable):
        ArtifactStore(tmp_path).read("loop")


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="POSIX named pipes only")
def test_named_pipe_rejected_before_open(tmp_path, monkeypatch):
    path = tmp_path / "pipe"
    os.mkfifo(path)
    original = Path.open

    def guarded_open(self, *args, **kwargs):
        if self == path:
            pytest.fail("must not perform a blocking open of a named pipe")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    with pytest.raises(ArtifactUnavailable):
        ArtifactStore(tmp_path).read("pipe")
