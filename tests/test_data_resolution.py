"""Dataset directory resolution contract (CLI > env > repo > home)."""

from __future__ import annotations

from pathlib import Path

import pytest
from src import config
from src.config import resolve_cicids_source, resolve_ember_source, resolve_source_dir

ENV_VAR = "TEST_DATASET_SOURCE_DIR"
DATASET = "TestDataset"


def _resolve(*, cli_source=None, env_var: str = ENV_VAR, dataset_name: str = DATASET) -> Path:
    return resolve_source_dir(cli_source=cli_source, env_var=env_var, dataset_name=dataset_name)


def test_explicit_cli_source_wins_over_environment_and_falls_back_locally(monkeypatch, tmp_path):
    env_dir = tmp_path / "env"
    cli_dir = tmp_path / "cli"
    monkeypatch.setenv(ENV_VAR, str(env_dir))
    assert _resolve(cli_source=cli_dir) == cli_dir
    assert _resolve(cli_source=str(cli_dir)) == cli_dir

    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    assert _resolve(cli_source="~/datasets/demo") == home / "datasets" / "demo"


def test_environment_source_wins_over_repo_local_and_empty_values_are_ignored(
    monkeypatch, tmp_path
):
    raw_dir = tmp_path / "raw"
    (raw_dir / DATASET).mkdir(parents=True)
    monkeypatch.setattr(config, "RAW_DIR", raw_dir)

    env_dir = tmp_path / "env"
    monkeypatch.setenv(ENV_VAR, str(env_dir))
    assert _resolve() == env_dir

    monkeypatch.setenv(ENV_VAR, "")
    assert _resolve() == raw_dir / DATASET

    monkeypatch.delenv(ENV_VAR)
    assert _resolve() == raw_dir / DATASET


def test_home_documents_directory_is_the_last_existing_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "RAW_DIR", tmp_path / "raw")
    home = tmp_path / "home"
    home_dataset = home / "Documents" / DATASET
    home_dataset.mkdir(parents=True)
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.setattr(Path, "home", lambda: home)

    assert _resolve() == home_dataset


def test_missing_dataset_falls_back_to_local_path_for_a_clear_error(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "RAW_DIR", tmp_path / "raw")
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.setattr(Path, "home", lambda: home)

    resolved = _resolve()
    assert resolved == tmp_path / "raw" / DATASET
    assert not resolved.exists()


def test_ember_and_cicids_wrappers_use_their_environment_variables(monkeypatch, tmp_path):
    ember_dir = tmp_path / "ember"
    cicids_dir = tmp_path / "cicids"
    monkeypatch.setenv(config.EMBER_ENV_VAR, str(ember_dir))
    monkeypatch.setenv(config.CICIDS_ENV_VAR, str(cicids_dir))

    assert resolve_ember_source() == ember_dir
    assert resolve_cicids_source() == cicids_dir
    assert resolve_ember_source(tmp_path / "explicit-ember") == tmp_path / "explicit-ember"


@pytest.mark.parametrize("name", ["EMBER-Dataset", "CIC-IDS-Dataset"])
def test_default_dataset_names_are_documented(monkeypatch, tmp_path, name):
    monkeypatch.setattr(config, "RAW_DIR", tmp_path / "raw")
    monkeypatch.delenv(config.EMBER_ENV_VAR, raising=False)
    monkeypatch.delenv(config.CICIDS_ENV_VAR, raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "empty-home")

    resolver = resolve_ember_source if name == "EMBER-Dataset" else resolve_cicids_source
    assert resolver() == tmp_path / "raw" / name
