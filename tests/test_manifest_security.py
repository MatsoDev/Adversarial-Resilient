"""Manifest path-containment regression tests."""

from __future__ import annotations

import hashlib
import os

import pytest
from src.data.preprocessing import verify_manifest_artifacts


def _manifest(relative: str, payload: bytes) -> dict:
    return {
        "artifacts": {
            "artifact": {
                "file": relative,
                "size_bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        }
    }


def test_valid_manifest_artifact_is_accepted(tmp_path):
    root = tmp_path / "unit" / "generated"
    root.mkdir(parents=True)
    payload = b"valid-artifact"
    (root / "data.bin").write_bytes(payload)
    assert verify_manifest_artifacts(_manifest("data.bin", payload), root) == []


def test_nested_valid_artifact_is_accepted(tmp_path):
    root = tmp_path / "generated"
    (root / "sub").mkdir(parents=True)
    payload = b"nested"
    (root / "sub" / "data.bin").write_bytes(payload)
    assert verify_manifest_artifacts(_manifest("sub/data.bin", payload), root) == []


@pytest.mark.parametrize("relative", ["../secret.txt", "../../etc/passwd", "/etc/passwd"])
def test_manifest_rejects_paths_outside_root(tmp_path, relative):
    root = tmp_path / "generated"
    root.mkdir()
    (tmp_path / "secret.txt").write_text("secret")
    errors = verify_manifest_artifacts(_manifest(relative, b"secret"), root)
    assert errors
    assert "escapes the manifest root" in errors[0]


def test_manifest_rejects_symlink_escape(tmp_path):
    root = tmp_path / "generated"
    root.mkdir()
    outside = tmp_path / "secret.txt"
    outside.write_text("secret")
    link = root / "linked"
    try:
        os.symlink(outside, link)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available on this platform")
    errors = verify_manifest_artifacts(_manifest("linked", b"secret"), root)
    assert errors
    assert "escapes the manifest root" in errors[0]


def test_manifest_rejects_malformed_records(tmp_path):
    root = tmp_path / "generated"
    root.mkdir()
    assert verify_manifest_artifacts({"artifacts": {"bad": "not-an-object"}}, root)
    assert verify_manifest_artifacts({"artifacts": {"bad": {"file": ""}}}, root)
    (root / "data.bin").write_bytes(b"data")
    bad_size = {"artifacts": {"bad": {"file": "data.bin", "size_bytes": "nope"}}}
    errors = verify_manifest_artifacts(bad_size, root)
    assert errors and "could not read" in errors[0]
