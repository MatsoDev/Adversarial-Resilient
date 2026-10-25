"""Central paths, seeds and constants.

All modules should import paths from here so the project stays
reproducible on Windows / Linux / macOS and CPU-only laptops.
"""

from __future__ import annotations

import os
from pathlib import Path

# Repo root = parent of src/
ROOT: Path = Path(__file__).resolve().parent.parent

DATA_DIR: Path = ROOT / "data"
RAW_DIR: Path = DATA_DIR / "raw"
PROCESSED_DIR: Path = DATA_DIR / "processed"
ADVERSARIAL_DIR: Path = DATA_DIR / "adversarial"
EXTERNAL_DIR: Path = DATA_DIR / "external"

MODELS_DIR: Path = ROOT / "models"
NOTEBOOKS_DIR: Path = ROOT / "notebooks"
DOCS_DIR: Path = ROOT / "docs"
FIGURES_DIR: Path = DOCS_DIR / "figures"
RESULTS_DIR: Path = DOCS_DIR / "results"
DATA_DOCS_DIR: Path = DOCS_DIR / "data"
DATA_MANIFESTS_DIR: Path = DATA_DOCS_DIR / "manifests"
DATA_CARDS_DIR: Path = DOCS_DIR / "data_cards"

SEED: int = 42

# MNIST demo defaults (scripts/art_quickstart.py)
MNIST_MEAN: float = 0.1307
MNIST_STD: float = 0.3081

# Dataset locations. Raw data is never copied into the repository; it is read
# in place from the first location that resolves. See resolve_source_dir().
EMBER_DATASET_NAME: str = "EMBER-Dataset"
CICIDS_DATASET_NAME: str = "CIC-IDS-Dataset"
EMBER_ENV_VAR: str = "EMBER_DATA_DIR"
CICIDS_ENV_VAR: str = "CICIDS_DATA_DIR"

EMBER_PROCESSED_DIR: Path = PROCESSED_DIR / "ember2018"
CICIDS_PROCESSED_DIR: Path = PROCESSED_DIR / "cicids2017"

# Reference URLs (documentation only; nothing is downloaded by the code).
EMBER_URL: str = "https://ember.elastic.co/"
EMBER_PAPER_URL: str = "https://arxiv.org/abs/1804.04637"
CICIDS2017_URL: str = "https://www.unb.ca/cic/datasets/ids-2017.html"


def resolve_source_dir(
    *,
    cli_source: str | Path | None,
    env_var: str,
    dataset_name: str,
) -> Path:
    """Resolve a local dataset directory without using personal absolute paths.

    Order: explicit CLI argument > environment variable > repo-local
    ``data/raw/<name>`` > ``~/Documents/<name>``. The final fallback is the
    repo-local path even if it does not exist, so callers can produce a useful
    error message.
    """
    if cli_source is not None:
        return Path(cli_source).expanduser()

    env_value = os.environ.get(env_var)
    if env_value:
        return Path(env_value).expanduser()

    local = RAW_DIR / dataset_name
    if local.exists():
        return local

    home = Path.home() / "Documents" / dataset_name
    if home.exists():
        return home

    return local


def resolve_ember_source(cli_source: str | Path | None = None) -> Path:
    """Resolve the EMBER 2018 v2 directory (see resolve_source_dir)."""
    return resolve_source_dir(
        cli_source=cli_source, env_var=EMBER_ENV_VAR, dataset_name=EMBER_DATASET_NAME
    )


def resolve_cicids_source(cli_source: str | Path | None = None) -> Path:
    """Resolve the CIC-IDS-2017 directory (see resolve_source_dir)."""
    return resolve_source_dir(
        cli_source=cli_source, env_var=CICIDS_ENV_VAR, dataset_name=CICIDS_DATASET_NAME
    )


# Resolved once at import for convenience. Prefer the functions above in code
# that may run after an environment variable changes.
EMBER_SOURCE_DIR: Path = resolve_ember_source()
CICIDS_SOURCE_DIR: Path = resolve_cicids_source()


def ensure_dirs() -> None:
    """Create gitignored runtime dirs if missing (safe to call repeatedly)."""
    for d in (
        RAW_DIR,
        PROCESSED_DIR,
        ADVERSARIAL_DIR,
        EXTERNAL_DIR,
        MODELS_DIR,
        FIGURES_DIR,
        RESULTS_DIR,
        DATA_DOCS_DIR,
        DATA_MANIFESTS_DIR,
        DATA_CARDS_DIR,
        EMBER_PROCESSED_DIR,
        CICIDS_PROCESSED_DIR,
    ):
        d.mkdir(parents=True, exist_ok=True)
