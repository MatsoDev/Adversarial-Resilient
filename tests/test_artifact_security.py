"""Regression tests for the read-only artifact service's resource boundaries."""

import hashlib
import json
import os
from pathlib import Path

import pytest
from api.main import create_app
from fastapi.testclient import TestClient
from src.config import ROOT
from src.evaluation.artifacts import ArtifactStore, ArtifactUnavailable


def test_dataset_manifest_and_digest_use_one_read(tmp_path, monkeypatch):
    name = "ember2018"
    relative = f"data/manifests/{name}.json"
    manifest = tmp_path / relative
    manifest.parent.mkdir(parents=True)
    original = {"dataset": name, "subset": False, "splits": {}}
    original_bytes = json.dumps(original).encode()
    manifest.write_bytes(original_bytes)
    eda = tmp_path / "results/data_eda.json"
    eda.parent.mkdir()
    eda.write_text(json.dumps({"datasets": {name: {"source": {"rows": 1}}}}), encoding="utf-8")
    store = ArtifactStore(tmp_path)
    read = store.read
    manifest_reads = 0

    def read_and_replace(path):
        nonlocal manifest_reads
        content = read(path)
        if path == relative:
            manifest_reads += 1
            replacement = manifest.with_suffix(".tmp")
            replacement.write_text(json.dumps({**original, "subset": True}), encoding="utf-8")
            replacement.replace(manifest)
        return content

    monkeypatch.setattr(store, "read", read_and_replace)
    response = TestClient(create_app(store)).get(f"/v1/datasets/{name}")

    assert response.status_code == 200
    assert response.json()["manifest"] == original
    assert response.json()["manifest_sha256"] == hashlib.sha256(original_bytes).hexdigest()
    assert manifest_reads == 1


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
