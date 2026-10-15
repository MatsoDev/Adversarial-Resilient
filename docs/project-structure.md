# Project structure

Reference for how this repository is organized and where new work belongs.
For component behavior and dependency rules see [`architecture.md`](architecture.md).

## Repository tree

```text
Adversarial-Resilient/
├── README.md                    # entry point: setup, verification, demo, troubleshooting
├── CONTRIBUTING.md              # branching, commit style, PR checklist
├── AGENTS.md                    # short navigation map for AI agents
├── LICENSE                      # MIT
├── Makefile                     # setup / lint / test / demo / docker-build / docker-up / clean
├── pyproject.toml               # ruff + pytest configuration (tooling only, no packaging)
├── requirements.txt             # pinned runtime dependencies (CPU-only)
├── requirements-dev.txt         # runtime + pytest/ruff/pre-commit
├── requirements-cleverhans.txt  # optional isolated env for the CH cross-check
├── Dockerfile                   # dev image; CMD runs the FastAPI app
├── docker-compose.yml           # api + dashboard + mlflow services
├── .env.example                 # ports and MLflow/PYTHONPATH template
├── .pre-commit-config.yaml      # ruff + whitespace/hygiene hooks
├── .github/
│   ├── workflows/ci.yml         # lint + tests (py3.11), docker build
│   ├── ISSUE_TEMPLATE/          # bug.md, task.md
│   └── PULL_REQUEST_TEMPLATE.md
├── api/                         # FastAPI service (importable as `api.*`)
│   ├── main.py                  # app, GET /health, GET /
│   └── README.md
├── dashboard/                   # Streamlit UI
│   ├── app.py                   # placeholder page calling the API
│   └── README.md
├── src/                         # shared library (importable as `src.*`)
│   ├── config.py                # central paths, seed, demo constants
│   ├── utils/seed.py            # deterministic seeding (python/numpy/torch)
│   ├── models/baseline_mlp.py   # BaselineMLP, SmallCNN
│   ├── data/                    # dataset loaders + preprocessing (later sprints)
│   ├── attacks/                 # FGSM/PGD/CW wrappers (later sprints)
│   ├── defenses/                # hardening methods (later sprints)
│   └── evaluation/              # metrics + plots (later sprints)
├── scripts/                     # runnable demos / utilities
│   └── art_quickstart.py        # end-to-end ART demo on MNIST
├── tests/                       # pytest suite (flat, one file per area)
│   ├── test_config.py
│   ├── test_seed.py
│   ├── test_api_health.py
│   └── test_art_quickstart_smoke.py
├── docs/                        # see docs/README.md for the documentation index
│   ├── README.md                # documentation index
│   ├── architecture.md          # components, data flows, dependency rules
│   ├── project-structure.md     # this file
│   ├── threat_model_v0.1.md     # security scope and attacker model
│   ├── DECISIONS.md             # log of non-obvious decisions
│   ├── reading_list.md          # papers and why they matter
│   ├── sprint1_report.md        # Sprint 1 report (history)
│   ├── PR_sprint1.md            # Sprint 1 PR description snapshot (history)
│   ├── literature/              # paper notes + templates
│   ├── figures/                 # generated demo plots (committed on purpose)
│   └── results/                 # generated demo JSON (committed on purpose)
├── data/                        # runtime datasets; gitignored except .gitkeep
│   ├── raw/                     # downloads (MNIST lives here after first run)
│   ├── processed/               # cleaned/split datasets (later sprints)
│   └── adversarial/             # generated adversarial datasets (later sprints)
├── models/                      # trained weights; gitignored except .gitkeep
└── notebooks/                   # exploratory notebooks (empty for now)
```

## Directory responsibilities

| Directory | Contains | Must not contain |
|---|---|---|
| `src/` | Reusable library code, grouped by concern; importable as `src.*` | Scripts with side effects, notebooks, tests |
| `scripts/` | Runnable entry points (`python scripts/<name>.py`) | Reusable library code (put it in `src/`) |
| `api/` | FastAPI app and HTTP concerns | Model/training logic (import it from `src/`) |
| `dashboard/` | Streamlit UI code | Business logic (call the API instead) |
| `tests/` | pytest tests, fixtures, helpers | Production code |
| `docs/` | Documentation + intentionally committed demo artifacts | Runtime data, model weights |
| `data/` | Runtime datasets and derived data (gitignored) | Code, docs, committed data files |
| `models/` | Trained checkpoints (gitignored) | Code |
| `notebooks/` | Exploratory notebooks | Anything the project depends on |

## Root files

| File | Purpose |
|---|---|
| `Makefile` | Canonical developer commands; mirrors what CI runs |
| `pyproject.toml` | ruff (lint/format) and pytest settings; the project is not packaged |
| `requirements*.txt` | Pinned dependencies; `-dev` adds test/lint tooling, `-cleverhans` is isolated |
| `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.env.example` | Container stack and its configuration template |
| `.pre-commit-config.yaml` | Formatting/hygiene hooks installed by `make setup` |
| `.gitattributes`, `.gitignore` | Line-ending normalization and ignore policy |

## Where do I put ...?

- **New reusable code:** a module or package under `src/<concern>/`
  (`data`, `models`, `attacks`, `defenses`, `evaluation`, or `utils`). Add it
  only when it is actually used; do not create speculative abstractions.
- **New runnable demo or one-off tool:** `scripts/<name>.py`, importable by
  tests as `scripts.<name>`.
- **New tests:** `tests/test_<area>.py`, flat in the tests directory. Use
  `tmp_path` for any file output so the committed `docs/` artifacts are never
  touched by test runs. Fast, dependency-light tests are preferred; the
  ART smoke test uses `--synthetic` data.
- **Paths or seeds:** add to `src/config.py` / use `src/utils/seed.py` rather
  than hard-coding relative paths in modules.
- **Documentation:** general docs in `docs/`, paper notes in
  `docs/literature/` (copy a template there), non-obvious decisions logged in
  `docs/DECISIONS.md`, then link new docs from `docs/README.md`.
- **Datasets / weights:** never commit; they go to `data/` / `models/`
  (gitignored) at runtime.
- **Configuration for the stack:** `.env.example` + `docker-compose.yml`;
  do not commit a real `.env`.

## Generated vs maintained files

**Generated (do not hand-edit):**

- `docs/results/art_quickstart_results.json`, `docs/figures/art_*.png` —
  written by `scripts/art_quickstart.py` (`make demo`); committed on purpose
  as the reference demo output.
- `mlruns/`, `data/raw/MNIST/`, `models/*.pt` — runtime outputs, gitignored.
- `__pycache__/`, `.pytest_cache/`, `.ruff_cache/` — tool caches, gitignored;
  `make clean` removes them.

**Maintained by developers:** everything else, including the committed demo
artifacts' generator (`scripts/art_quickstart.py`).

## Conventions

- **Naming:** `snake_case` for Python modules, `test_<area>.py` for tests, and
  `lower_snake_case.md` for docs (with two established exceptions:
  `DECISIONS.md` and the `sprint<N>_report.md` pattern).
- **Imports:** `from src.config import ...`, `from scripts.art_quickstart
  import ...` (the repo root works as the import base because tests and
  scripts run from the root).
- **Style:** ruff with `line-length = 100`; `ruff format` is the formatter
  (enforced by pre-commit). No `print` in library code — use `logging`.
- **Commits/branches:** see [`../CONTRIBUTING.md`](../CONTRIBUTING.md).
- **Generated demo artifacts:** regenerate with `make demo`; never edit them
  by hand.

## Notes and exceptions

- `data/raw/MNIST/` appears after the first demo run; it is downloaded by
  torchvision and is not part of the repository.
- `docs/PR_sprint1.md` is a historical snapshot of the merged Sprint 1 pull
  request; it is kept for the project record, not as live documentation.
- The `src/data`, `src/attacks`, `src/defenses`, and `src/evaluation` packages
  currently contain only `__init__.py` and a README describing planned
  contents; they reserve the module boundaries for later sprints.
- `notebooks/` and `models/` are intentionally empty (`.gitkeep` only) until
  the dataset/sprint work needs them.
