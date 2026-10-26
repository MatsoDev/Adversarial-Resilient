# Development guide

Local setup, verification, demos, and services. Start with the root
[`README.md`](../README.md) for the project overview and
[`project-structure.md`](project-structure.md) for where code belongs.
Environment variables are listed in [`configuration.md`](configuration.md);
test organization is in [`testing.md`](testing.md). Security checks, findings,
and residual risks are in [`security/SECURITY_AUDIT.md`](security/SECURITY_AUDIT.md).

## Prerequisites

- Git.
- Python 3.11–3.12. Tested with Python 3.12.1 on Windows and Python 3.11 in
  CI; the pins in `requirements*.txt` support 3.11–3.12 (Python 3.10 support ends in October 2026).
- About 3 GB free disk for the Python environment and MNIST demo. Full
  preprocessing additionally needs roughly 9 GB for EMBER processed arrays
  (7.6 GB of arrays plus headroom) and 1 GB for CICIDS (stored under gitignored
  `data/processed/`); the pipeline checks for headroom before a full run.
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

This creates `.venv`, installs `requirements-dev.txt` (which includes
`requirements.txt`) and the separate CPU torch requirements, and installs the
pre-commit hooks. If `python` is not on `PATH` (common on Linux
distributions that only install `python3`), run `make setup PY=python3`.

### Manual setup

Windows (PowerShell):

```powershell
git clone https://github.com/MatsoDev/Adversarial-Resilient.git
cd Adversarial-Resilient
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
pip install -r requirements-torch.txt
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
pip install -r requirements-dev.txt
pip install -r requirements-torch.txt
pre-commit install
```

All commands below assume the virtual environment is active and that you are
in the repository root.

## Verification and quality checks

```bash
make lint      # ruff check + ruff format --check (same as CI)
make test      # pytest; synthetic fixtures, no datasets required
make coverage  # same suite + line/branch coverage (CI runs this)
make security  # pip-audit + bandit (same as CI)
make docker-scan  # Trivy scan of adversarial-resilient:dev (after docker-build)
make format    # rewrite files with ruff format
make check     # lint + test
make clean     # remove caches and mlruns/ (committed demo/EDA artifacts stay)
```

Without Make, use the equivalent commands:

```bash
python -m ruff check src scripts tests api dashboard
python -m ruff format --check src scripts tests api dashboard
python -m pytest
python -m pytest --cov=src --cov=api --cov=dashboard --cov=scripts \
  --cov-report=term-missing
python -m pip_audit -r requirements-dev.txt
python -m bandit -q -r src scripts api dashboard -ll
```

The `pytest` run takes under a minute. Fast tests use synthetic fixtures; two
optional local-dataset checks are skipped unless `RUN_REAL_DATA_TESTS=1`.
Tests write only to pytest temporary directories, never to committed
`docs/results/`, `docs/figures/`, or `docs/data/` artifacts. Test layout,
single-test commands, and the optional real-data checks are documented in
[`testing.md`](testing.md).

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
MLFLOW_ALLOW_FILE_STORE=true python -m mlflow ui
```

Then open http://127.0.0.1:5000 in your browser.

## Run the API and dashboard without Docker

Both commands below block until stopped, so use two separate terminal sessions
and keep both running while testing.

Terminal 1:

```bash
python -m uvicorn api.main:app --reload --port 8000
```

Open http://127.0.0.1:8000/health — expect `{"status": "ok"}`.

Terminal 2 (same folder, virtual environment activated):

```bash
python -m streamlit run dashboard/app.py
# or: make dashboard
```

Open http://localhost:8501 — expect the placeholder page with a button that
calls the API `/health`. The dashboard defaults to `http://localhost:8000`;
set `API_URL` to point it elsewhere.

## Run the Docker stack

The image builds in CI on every push and pull request. The 2026-10 security
audit rebuilt the image and started the full three-service stack on loopback;
API, dashboard, and MLflow health endpoints returned 200. Browser/MLflow
artifact workflows and sustained load were not exercised; see
[`security/SECURITY_AUDIT.md`](security/SECURITY_AUDIT.md).

```bash
cp .env.example .env
docker compose up --build
```

Ports come from `.env` (defaults: api 8000, dashboard 8501, mlflow 5000).
Published ports bind to `127.0.0.1` by default, so the stack is not reachable
from other hosts. Once the containers are up, check
http://127.0.0.1:8000/health, http://localhost:8501, and
http://localhost:5000. Stop with `Ctrl+C`, then `docker compose down`.

Do not set `BIND_ADDR=0.0.0.0` unless you put a TLS reverse proxy with
authentication in front of the stack. MLflow and the placeholder dashboard
have no built-in authentication.

The compose stack sets `API_URL=http://api:8000` for the dashboard container,
so the same app works inside Docker and locally.

## Data pipeline and EDA

See the data guide: [`data/README.md`](data/README.md). It covers dataset
locations, preprocessing/EDA commands, expected runtime and outputs, and the
processed-data loaders.

## Troubleshooting

| Problem | Fix |
|---|---|
| `python --version` shows 3.10 or older, or install fails on your Python | Install Python 3.11–3.12 (CI uses 3.11). Then recreate `.venv` from scratch. |
| `make setup` fails with `python: No such file or directory` | Only `python3` is installed. Run `make setup PY=python3` (or create the venv manually as shown above). |
| `ModuleNotFoundError: No module named 'pkg_resources'` when importing mlflow | Your environment predates the current pins. Recreate `.venv` with `make setup` (mlflow 3.17.2 + setuptools 84.2.1). |
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
| EMBER preprocessing is killed or runs out of disk | Plan for about 9–10 GB (arrays plus headroom). Use `--max-samples` for smoke work or free space under `data/processed/`; the pipeline preallocates `.npy.tmp` files and only publishes them after success. |
| CICIDS duplicate/NaN counts differ from an older notebook | This pipeline reads the original eight CSVs, deduplicates at saved float32 precision, and reports raw-float64 counts too. See the data card and Sprint 2 report rather than assuming a Kaggle-cleaned copy. |
