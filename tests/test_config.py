"""Runtime directory creation contract (isolated from the repository tree)."""

from __future__ import annotations

from src import config

DIRECTORY_NAMES = (
    "RAW_DIR",
    "PROCESSED_DIR",
    "ADVERSARIAL_DIR",
    "EXTERNAL_DIR",
    "MODELS_DIR",
    "FIGURES_DIR",
    "RESULTS_DIR",
    "DATA_DOCS_DIR",
    "DATA_MANIFESTS_DIR",
    "DATA_CARDS_DIR",
    "EMBER_PROCESSED_DIR",
    "CICIDS_PROCESSED_DIR",
)


def test_ensure_dirs_creates_every_configured_directory_idempotently(monkeypatch, tmp_path):
    targets = {}
    for name in DIRECTORY_NAMES:
        target = tmp_path / "repo" / name.lower()
        targets[name] = target
        monkeypatch.setattr(config, name, target)

    config.ensure_dirs()
    config.ensure_dirs()

    for name, target in targets.items():
        assert target.is_dir(), name
