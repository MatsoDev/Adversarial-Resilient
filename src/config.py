"""Central paths, seeds and constants.

All modules should import paths from here so the project stays
reproducible on Windows / Linux / macOS and CPU-only laptops.
"""

from __future__ import annotations

from pathlib import Path

# Repo root = parent of src/
ROOT: Path = Path(__file__).resolve().parent.parent

DATA_DIR: Path = ROOT / "data"
RAW_DIR: Path = DATA_DIR / "raw"
PROCESSED_DIR: Path = DATA_DIR / "processed"
ADVERSARIAL_DIR: Path = DATA_DIR / "adversarial"

MODELS_DIR: Path = ROOT / "models"
NOTEBOOKS_DIR: Path = ROOT / "notebooks"
DOCS_DIR: Path = ROOT / "docs"
FIGURES_DIR: Path = DOCS_DIR / "figures"
RESULTS_DIR: Path = DOCS_DIR / "results"

SEED: int = 42

# MNIST demo defaults (scripts/art_quickstart.py)
MNIST_MEAN: float = 0.1307
MNIST_STD: float = 0.3081

# EMBER / CICIDS2017 placeholders (Sprint 2 fills the download + EDA)
EMBER_URL: str = "https://ember.elastic.co/"
CICIDS2017_URL: str = "https://www.unb.ca/cic/datasets/ids-2017.html"


def ensure_dirs() -> None:
    """Create gitignored runtime dirs if missing (safe to call repeatedly)."""
    for d in (RAW_DIR, PROCESSED_DIR, ADVERSARIAL_DIR, MODELS_DIR, FIGURES_DIR, RESULTS_DIR):
        d.mkdir(parents=True, exist_ok=True)
