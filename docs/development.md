# Development guide

Local setup, verification, demos, and services. Start with the root
[`README.md`](../README.md) for the project overview and
[`project-structure.md`](project-structure.md) for where code belongs.

## Prerequisites

- Git.
- Python 3.10–3.12. Tested with Python 3.12.1 on Windows and Python 3.11 in
  CI; the pins in `requirements.txt` support 3.10–3.12.
- About 3 GB free disk for the Python environment and MNIST demo. Full
  preprocessing additionally needs roughly 8 GB for EMBER processed arrays and
  1 GB for CICIDS (stored under gitignored `data/processed/`); the pipeline
  checks for headroom before a full run.
- Internet access for the first install and the MNIST download.
- Docker (optional, only for the container stack).
- GNU Make (optional; the commands below also run directly with `python`).

Check your versions:

```bash
python --version
git --version
```

## Setup

### Linux / macOS (Makefile shortcut)

```bash
make setup
```

This creates `.venv`, installs `requirements.txt` + `requirements-dev.txt`, and
installs the pre-commit hooks.

### Manual setup

Windows (PowerShell):

```powershell
git clone https://github.com/MatsoDev/Adversarial-Resilient.git
cd Adversarial-Resilient
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
```

If activation is blocked with an "execution of scripts is disabled" error, run
this once, then retry activation:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Linux / macOS:

```bash
git clone https://github.com/MatsoDev/Adversarial-Resilient.git
cd Adversarial-Resilient
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
```

All commands below assume the virtual environment is active and that you are
in the repository root.

## Verification and quality checks

```bash
make lint      # ruff check + ruff format --check (same as CI)
make test      # pytest; synthetic fixtures, no datasets required
make format    # rewrite files with ruff format
make check     # lint + test
```

Without Make, use the equivalent commands:

```bash
python -m ruff check src scripts tests api dashboard
python -m ruff format --check src scripts tests api dashboard
python -m pytest
```

The `pytest` run takes under a minute. Fast tests use synthetic fixtures; two
optional local-dataset checks are skipped unless `RUN_REAL_DATA_TESTS=1`.
Tests write only to pytest temporary directories, never to committed
`docs/results/`, `docs/figures/`, or `docs/data/` artifacts.

## Run the ART demo

The demo proves the FGSM/PGD/CW tooling works end to end on MNIST (CPU only).
It is an environment check, not a security result.

Fast version first (recommended). After the one-time MNIST download (about
60 MB into `data/raw/`), it takes a few minutes on a CPU laptop:

```bash
python scripts/art_quickstart.py --fast
# or: make demo
```

What to expect: clean test accuracy around 0.92 on the subset, FGSM and PGD
adversarial accuracy near 0.05 at epsilon 0.3, and CW-L2 evaluated on
20 samples. Exact numbers differ slightly by machine.

Full version (trains on all of MNIST for 3 epochs, CW on 200 samples; takes
10 minutes or more on CPU):

```bash
python scripts/art_quickstart.py --epochs 3
```

What to expect: clean accuracy around 0.99. The accuracy-vs-epsilon grid is
the slowest part; `--cw-samples 20` keeps CW tractable.

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

The JSON and figures are committed reference outputs; regenerate them with the
demo rather than editing them by hand. Browse the logged run with:

```bash
python -m mlflow ui
```

Then open http://127.0.0.1:5000 in your browser.

## Run the API and dashboard without Docker

Terminal 1:

```bash
python -m uvicorn api.main:app --reload --port 8000
```

Open http://127.0.0.1:8000/health — expect `{"status": "ok"}`.

Terminal 2 (same folder, virtual environment activated):

```bash
streamlit run dashboard/app.py
```

Open http://localhost:8501 — expect the placeholder page with a button that
calls the API `/health`. The dashboard defaults to `http://localhost:8000`;
set `API_URL` to point it elsewhere.

## Run the Docker stack

The image builds in CI on every push; the stack below was smoke-tested on
Linux.

```bash
cp .env.example .env
docker compose up --build
```

Ports come from `.env` (defaults: api 8000, dashboard 8501, mlflow 5000).
Once the containers are up, check http://127.0.0.1:8000/health,
http://localhost:8501, and http://localhost:5000. Stop with `Ctrl+C`, then
`docker compose down`.

The compose stack sets `API_URL=http://api:8000` for the dashboard container,
so the same app works inside Docker and locally.

## Data pipeline and EDA

See the data guide: [`data/README.md`](data/README.md). It covers dataset
locations, preprocessing/EDA commands, expected runtime and outputs, and the
processed-data loaders.

## Troubleshooting

| Problem | Fix |
|---|---|
| `python --version` shows 3.9 or older, or install fails on your Python | Install Python 3.10–3.12 (CI uses 3.11). Then recreate `.venv` from scratch. |
| `ModuleNotFoundError: No module named 'pkg_resources'` when importing mlflow | Your setuptools is too new. `requirements.txt` already pins `setuptools==75.8.0`; if you still see it, run `pip install "setuptools==75.8.0"`. |
| `ruff` or `pytest` not found | The venv is not activated, or dev requirements are missing. Activate `.venv` and run `pip install -r requirements-dev.txt`. |
| torch download is very slow or fails | The CPU wheel is about 200 MB. Check disk space and connection, then rerun the same `pip install` command; pip resumes. |
| PowerShell refuses to activate the venv | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`, then activate again. |
| `python -m uvicorn ...` says address already in use | Port 8000 is taken. Use another port, e.g. `--port 8001`, and open that URL instead. Same for Streamlit (`--server.port 8502`). |
| The local dashboard says the API is unreachable | Start the API first, or set `API_URL` (default `http://localhost:8000`). In Compose it is `http://api:8000`. |
| `docker compose up` fails with `env file ... not found` | Run `cp .env.example .env` first; compose uses it for host ports. |
| MNIST download shows `HTTP Error 404` for `yann.lecun.com` | Expected: torchvision automatically retries its mirror and continues. No action needed. |
| `--cleverhans` prints `CleverHans not available, skipping` | Expected: CleverHans lives in the separate `requirements-cleverhans.txt` because version 4.0.0 conflicts with the ART/torch stack. Only install it in an isolated env if you need the cross-check. |
| `git clone` fails on Windows with filename-too-long errors | Enable long paths once: `git config --system core.longpaths true` (needs an elevated prompt), then clone again. |
| `scripts/preprocess.py` says the source directory is missing | Set `EMBER_DATA_DIR` / `CICIDS_DATA_DIR`, pass `--source`, or place the dataset under `data/raw/` or `~/Documents/`. The pipeline never downloads data. |
| EMBER preprocessing is killed or runs out of disk | Full arrays need ~10 GB. Use `--max-samples` for smoke work or free space under `data/processed/`; the pipeline preallocates `.npy.tmp` files and only publishes them after success. |
| CICIDS duplicate/NaN counts differ from an older notebook | This pipeline reads the original eight CSVs, deduplicates at saved float32 precision, and reports raw-float64 counts too. See the data card and Sprint 2 report rather than assuming a Kaggle-cleaned copy. |
