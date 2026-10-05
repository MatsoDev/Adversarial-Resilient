"""Paths exist or are creatable."""

from src.config import MODELS_DIR, RAW_DIR, ensure_dirs


def test_ensure_dirs_creates():
    ensure_dirs()
    assert RAW_DIR.exists()
    assert MODELS_DIR.exists()
