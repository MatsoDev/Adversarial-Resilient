# Adversarial-Resilient Security Models

Machine-learning detectors for malware and network intrusion, attacked with
adversarial examples (FGSM, PGD, Carlini-Wagner) and then hardened with
adversarial training, distillation, ensembles, input sanitization, and detectors.
The MNIST demo in this repo is only an environment check that proves the attack
tooling works — it is not the project's security result.

## Current status

Works today:

- ART demo on MNIST with FGSM, PGD, and CW-L2 (`scripts/art_quickstart.py`),
  including accuracy-vs-epsilon plots, a JSON report, and local MLflow logging.
- Test suite (`pytest`) and lint (`ruff`).
- FastAPI service with `GET /health` returning `{"status": "ok"}`.
- Streamlit dashboard page (early placeholder that can ping the API).
- `Dockerfile` and `docker-compose.yml` for api, dashboard, and mlflow services
  (the image is built in CI; the compose stack was smoke-tested on Linux).
- Cleaned/versioned EMBER2018 v2 and CIC-IDS-2017 datasets with manifest-based
  versioning, reusable loaders, EDA, data cards, and a reproducible
  `scripts/preprocess.py` pipeline.

Next: baseline detectors, FGSM/PGD/CW attacks on the real datasets, defenses,
and the full dashboard.
Sprint-by-sprint status is tracked in
[`docs/progress.md`](docs/progress.md); scope and schedule are in
[`docs/project_plan.md`](docs/project_plan.md).

Honestly not verified: the CleverHans cross-check was only tested as a graceful
skip (library not installed). Docker is covered differently: the image builds
in CI on every push, and the compose stack (api, dashboard, mlflow) was
smoke-tested on Linux — see the troubleshooting section for why CleverHans is
optional.

## Documentation

Start with the documentation index: [`docs/README.md`](docs/README.md).
Highlights:

- [`docs/architecture.md`](docs/architecture.md) — components, dependency
  rules, and data flows.
- [`docs/project-structure.md`](docs/project-structure.md) — directory
  responsibilities and where new code belongs.
- [`docs/progress.md`](docs/progress.md) — where we are now: sprint and
  milestone status (living tracker; baseline is
  [`docs/project_plan.md`](docs/project_plan.md)).
- [`AGENTS.md`](AGENTS.md) — quick navigation map for AI coding agents.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — branching, commit style, PR rules.
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — non-obvious technical decisions.
- [`docs/threat_model_v0.1.md`](docs/threat_model_v0.1.md) — security scope
  and attacker model.

## Prerequisites

- Git.
- Python 3.10 or 3.11. Tested with Python 3.12.1 on Windows and Python 3.11 in
  CI; the pins in `requirements.txt` support 3.10–3.12.
- About 3 GB free disk for the Python environment and MNIST demo. Full
  preprocessing additionally needs roughly 8 GB for EMBER processed arrays and
  1 GB for CICIDS (stored under gitignored `data/processed/`); the pipeline
  checks for headroom before a full run.
- Internet access for the first install and the MNIST download.
- Docker (optional, only for the container option).

Check your versions:

```bash
python --version
git --version
```

## Setup

### Windows (PowerShell)

```powershell
git clone https://github.com/MatsoDev/Adversarial-Resilient.git
cd Adversarial-Resilient
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```

If activation is blocked with an "execution of scripts is disabled" error, run
this once, then retry activation:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Linux / macOS

```bash
git clone https://github.com/MatsoDev/Adversarial-Resilient.git
cd Adversarial-Resilient
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```

Shortcut on Linux/macOS (requires `make`):

```bash
make setup
```

## Verify the install

```bash
python -m ruff check src scripts tests api dashboard
```

Expected output:

```text
All checks passed!
```

```bash
python -m pytest
```

Expected output (takes about 45 seconds; data/ART tests use tiny synthetic
fixtures, and real-data checks are skipped by default):

```text
26 passed, 2 skipped in ...
```

Tests write to pytest temporary directories, so the committed results in
`docs/results/`, `docs/figures/`, and `docs/data/` are never overwritten. Set
`RUN_REAL_DATA_TESTS=1` to enable the optional local-dataset availability
checks.

## Run the ART demo

Fast version first (recommended). After the one-time MNIST download
(about 60 MB into `data/raw/`), it takes roughly 3–5 minutes on a CPU laptop:

```bash
python scripts/art_quickstart.py --fast
```

What to expect: clean test accuracy around 0.92 on the subset, FGSM and PGD
adversarial accuracy near 0.05 at epsilon 0.3, and CW-L2 evaluated on
20 samples. Your exact numbers will differ slightly by machine.

Full version (trains on all of MNIST for 3 epochs, CW on 200 samples;
takes 10 minutes or more on CPU):

```bash
python scripts/art_quickstart.py --epochs 3
```

What to expect: clean accuracy around 0.99. The accuracy-vs-epsilon grid is
the slowest part; a `--cw-samples 20` flag keeps CW tractable.

Flags:

- `--fast`: small training subset (5000) and small CW sample (20).
- `--epochs N`: training epochs (default 2 with `--fast`, else 3).
- `--eps E`: epsilon for FGSM/PGD (default 0.3).
- `--seed N`: random seed (default 42).
- `--cw-samples N`: override the CW evaluation sample count.
- `--synthetic`: tiny random data, no download (used by the tests).
- `--cleverhans`: optional CleverHans FGSM/PGD cross-check; skips gracefully
  with a warning if CleverHans is not installed.

Outputs:

- `docs/results/art_quickstart_results.json`: clean/adversarial accuracy,
  attack success rate, mean L2/Linf perturbation, and the epsilon table.
- `docs/figures/art_samples.png`: original vs FGSM vs PGD image grid.
- `docs/figures/art_accuracy_vs_eps.png`: accuracy-vs-epsilon curves.
- `mlruns/`: local MLflow tracking data (gitignored).

Browse the logged run:

```bash
python -m mlflow ui
```

Then open http://127.0.0.1:5000 in your browser.

## Run the API and dashboard

Without Docker (with the virtual environment activated):

```bash
python -m uvicorn api.main:app --reload --port 8000
```

Open http://127.0.0.1:8000/health — expect `{"status": "ok"}`.

In a second terminal (same folder, venv activated):

```bash
streamlit run dashboard/app.py
```

Open http://localhost:8501 — expect the placeholder page with a button that
calls the API `/health`.

With Docker (the image builds in CI on every push; the stack below was
smoke-tested on Linux):

```bash
cp .env.example .env
docker compose up --build
```

Ports come from `.env` (defaults: api 8000, dashboard 8501, mlflow 5000).
Once the containers are up, check http://127.0.0.1:8000/health,
http://localhost:8501, and http://localhost:5000. Stop with `Ctrl+C`, then
`docker compose down`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `python --version` shows 3.9 or older, or install fails on your Python | Install Python 3.10 or 3.11 (3.12 also worked here); CI uses 3.11. Then recreate `.venv` from scratch. |
| `ModuleNotFoundError: No module named 'pkg_resources'` when importing mlflow | Your setuptools is too new. `requirements.txt` already pins `setuptools==75.8.0`; if you still see it, run `pip install "setuptools==75.8.0"`. |
| `ruff` or `pytest` not found | The venv is not activated, or dev requirements are missing. Activate `.venv` and run `pip install -r requirements-dev.txt`. |
| torch download is very slow or fails | The CPU wheel is about 200 MB. Check disk space and connection, then rerun the same `pip install` command; pip resumes. |
| PowerShell refuses to activate the venv | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`, then activate again. |
| `python -m uvicorn ...` says address already in use | Port 8000 is taken. Use another port, e.g. `--port 8001`, and open that URL instead. Same for Streamlit (`--server.port 8502`). |
| `docker compose up` fails with `env file ... not found` | Run `cp .env.example .env` first; compose reads it for ports and settings. |
| MNIST download shows `HTTP Error 404` for `yann.lecun.com` | Expected: torchvision automatically retries its mirror and continues. No action needed. |
| `--cleverhans` prints `CleverHans not available, skipping` | Expected: CleverHans lives in the separate `requirements-cleverhans.txt` because version 4.0.0 conflicts with the ART/torch stack. Only install it in an isolated env if you need the cross-check. |
| `git clone` fails on Windows with filename-too-long errors | Enable long paths once: `git config --system core.longpaths true` (needs an elevated prompt), then clone again. |
| `scripts/preprocess.py` says the source directory is missing | Set `EMBER_DATA_DIR` / `CICIDS_DATA_DIR`, pass `--source`, or place the dataset under `data/raw/` or `~/Documents/`. The pipeline never downloads data. |
| EMBER preprocessing is killed or runs out of disk | Full arrays need ~10 GB. Use `--max-samples` for smoke work or free space under `data/processed/`; the pipeline preallocates `.npy.tmp` files and only publishes them after success. |
| CICIDS duplicate/NaN counts differ from an older notebook | This pipeline reads the original eight CSVs, deduplicates at saved float32 precision, and reports raw-float64 counts too. See the data card and Sprint 2 report rather than assuming a Kaggle-cleaned copy. |

## Project structure

```text
api/            FastAPI service (/health today)
dashboard/      Streamlit app (early page today)
data/           raw/, processed/, adversarial/ runtime data (gitignored, .gitkeep only)
docs/           documentation (index at docs/README.md), data cards, decisions, reports
docs/data/      feature layout, generated EDA report, committed manifests
docs/figures/   demo + EDA plots (generated, committed on purpose)
docs/results/   demo + EDA JSON (generated, committed on purpose)
models/         trained weights (gitignored, .gitkeep only)
notebooks/      exploratory notebooks (later)
scripts/        art_quickstart.py, preprocess.py, eda_datasets.py
src/            config.py paths/seeds, utils/, data/ (Sprint 2), models/, attacks/, defenses/, evaluation/
tests/          seed, config, API, data (synthetic), and smoke tests
```

Full reference: [`docs/project-structure.md`](docs/project-structure.md).

## Working with Git

- Branch names: `feat/<topic>`, `fix/<topic>`, `docs/<topic>` (or `sprint<N>/<topic>`).
- Commits use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `test:`, `ci:`.
- Open a pull request into `main`; never push directly to `main`.
- Never commit datasets, model weights, `.env`, or `mlruns/`. Check `git status`
  before every commit.

## Data

Raw datasets are **read in place** from outside the repository and are never
committed. Processed arrays/scalers also stay out of Git
(`data/processed/` is gitignored); only compact manifests, data cards, reports,
and EDA figures are committed.

### Locations and resolution order

| Dataset | Local files |
|---|---|
| EMBER2018 v2 | `~/Documents/EMBER-Dataset/` (6 train JSONL files + `test_features.jsonl`) |
| CIC-IDS-2017 | `~/Documents/CIC-IDS-Dataset/` (8 original UNB/CIC CSVs) |

Code resolves sources in this order:

```text
CLI --source
  > EMBER_DATA_DIR / CICIDS_DATA_DIR
  > data/raw/EMBER-Dataset or data/raw/CIC-IDS-Dataset
  > ~/Documents/EMBER-Dataset or ~/Documents/CIC-IDS-Dataset
```

No download is performed by the pipeline. Do not copy the datasets into the
repository; if you symlink them under `data/raw/`, they remain ignored.

### Commands

```bash
# Full pipeline (default source locations; publishes manifests)
python scripts/preprocess.py --dataset all

# Explicit sources/outputs (same commands as the Sprint 2 verification)
python scripts/preprocess.py --dataset ember \
  --source ~/Documents/EMBER-Dataset \
  --output-dir data/processed/ember2018
python scripts/preprocess.py --dataset cicids2017 \
  --source ~/Documents/CIC-IDS-Dataset \
  --output-dir data/processed/cicids2017

# Verify artifacts against the manifests without reprocessing
python scripts/preprocess.py --dataset all --verify-only

# Fast deterministic subset (writes subset=true; /tmp only)
python scripts/preprocess.py --dataset ember --max-samples 2000 \
  --output-dir /tmp/ember_smoke --force --jobs 1
python scripts/preprocess.py --dataset cicids2017 --max-samples 2000 \
  --output-dir /tmp/cicids_smoke --force

# EDA (default outputs in docs/; --output-dir for tests)
python scripts/eda_datasets.py --dataset all
python scripts/eda_datasets.py --dataset all --max-samples 5000 \
  --output-dir /tmp/eda_smoke
```

Or `make data`, `make data-smoke`, and `make eda`.

### Expected runtime and outputs

On this Linux machine (12 CPU cores, 14 GB RAM, Python 3.11):

- Full EMBER: about 10 minutes with `--jobs 6` (source hashing, metadata scan,
  vectorisation, scaler, artifact hashing), ~7.6 GB of arrays.
- Full CICIDS2017: about 1.5 minutes, ~0.8 GB of arrays.
- Subset smoke runs: about 1–2.5 minutes each (EMBER also hashes the 9.4 GB
  source even for a subset).
- `make test` stays dataset-free and runs in under a minute.

Full manifests are committed under [`docs/data/manifests/`](docs/data/manifests/);
processed arrays live in gitignored `data/processed/`. See:

- [`docs/data/ember_feature_layout.md`](docs/data/ember_feature_layout.md) — 2381-dim layout.
- [`docs/data/eda_report.md`](docs/data/eda_report.md) — generated EDA report.
- [`docs/data_cards/`](docs/data_cards/) — datasheets, licenses, limitations.
- [`docs/sprint2_report.md`](docs/sprint2_report.md) — commands and actual results.

### Loading processed data

```python
from src.data import load_ember, load_cicids2017

X_train, y_train = load_ember("train").X, load_ember("train").y
cicids_val = load_cicids2017("val", target="binary", standardize=True)
```

`load_ember` / `load_cicids2017` raise a clear error if artifacts are missing and
never download data.

## Roadmap

Semester 1:

- Foundations: environment, ART demo on MNIST, threat model draft.
- Data: EMBER and CIC-IDS-2017 download, EDA, preprocessing pipeline.
- Attacks: FGSM, PGD, and CW against the real detectors.
- Defenses: adversarial training, distillation, ensembles, sanitization, detector.

Semester 2:

- Backend: FastAPI prediction, attack, and defense endpoints.
- Frontend: dashboard with robustness charts and MLflow links.
- Hardening: containers, CI checks, and the final evaluation.

## Safety and ethics

Defensive research only. This repo works with public feature datasets and the
MNIST demo images — no malware samples and no weaponized tooling are included
or accepted here.
