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
  Linux CI. Both older and newer Python releases are outside the supported range.
- Native Linux/Windows installation requires wheels compatible with your
  architecture. **Native macOS cannot install the current exact `+cpu` torch
  and torchvision pins:** neither has a macOS wheel on the configured index
  (checked 2026-11-17). The path handling is cross-platform, but that does not
  establish platform installation support. No alternative macOS pins or native
  macOS procedure have been validated; keep dependency changes separate.
- About 3 GB free disk for the Python environment and MNIST demo. Full
  preprocessing additionally needs roughly 9 GB for EMBER processed arrays
  (7.6 GB of arrays plus headroom) and 1 GB for CICIDS (stored under gitignored
  `data/processed/`); the pipeline checks for headroom before a full run.
- Internet access for the first install and the MNIST download.
- Docker (optional, only for the container stack).
- GNU Make (optional; the commands below also run directly with `python`).

Check the interpreter you will use to create the environment. On Linux:

```bash
python3.11 --version
git --version
```

The Python command must report `Python 3.11.x` (or select `python3.12` for
3.12.x); Git must exit successfully. In PowerShell use `python --version`
and confirm 3.11 or 3.12. Do not assume that an unversioned `python3` is supported.

## Setup

For both new and existing Linux/Windows team checkouts, the bootstrap is
`python scripts/setup_environment.py` (Python 3.11–3.12). It creates/reuses
`.venv`, synchronizes runtime/developer and CPU torch requirements (not optional
CleverHans), and checks the installed versions.
Use `--check-only` to verify without installing. This script does not activate
the venv or install Git hooks; `make setup` also attempts hook installation.
After activation (or using `.venv/bin/python` / `.venv\Scripts\python.exe`), the current HTML dashboard
runs with `python -m uvicorn api.main:app --port 8000`, at
<http://localhost:8000/dashboard/>. See [team_handoff.md](team_handoff.md).

### Linux (Makefile shortcut)

```bash
make setup PY=python3.11
```

This creates `.venv`, installs `requirements-dev.txt` (which includes
`requirements.txt`) and the separate CPU torch requirements, then attempts to
install pre-commit hooks. Hook-install failure is reported but does not fail
`make setup`. Substitute `PY=python3.12`, or `PY=python3` only after checking
that it is a supported version. Success means the dependency installs finish
and `.venv/bin/python` exists; verify the pins below rather than relying on
the Make target's exit code alone.

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

If activation is blocked by PowerShell policy, no policy change is necessary:
use the venv interpreter directly for each command, for example:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m uvicorn api.main:app --port 8000
```

Linux:

```bash
git clone https://github.com/MatsoDev/Adversarial-Resilient.git
cd Adversarial-Resilient
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
pip install -r requirements-torch.txt
pre-commit install
```

The fresh-install commands above were not rerun in the 2026-11-17 documentation
audit, nor was Windows installation repeated. Their success criterion is a
created venv, completed installs and the following existing-environment check:

```bash
python scripts/setup_environment.py --check-only
```

With the venv active, this was verified on Linux and printed:

```text
All direct requirements match the project pins.
No broken requirements found.
Ready: .venv Python -m uvicorn api.main:app --port 8000; open /dashboard/
```

In PowerShell, `.\.venv\Scripts\python.exe scripts/setup_environment.py --check-only`
checks the same contract without activation. All commands below assume the
virtual environment is active and that you are in the repository root.

## Verification and quality checks

```bash
make lint      # ruff check + ruff format --check (same as CI)
make test      # pytest; synthetic fixtures, no datasets required
make coverage  # same suite + line/branch coverage (CI runs this)
make security  # pip-audit + bandit (same as CI)
make docker-scan  # Trivy scan of adversarial-resilient:dev (after docker-build)
make check     # lint + test
```

These checks should exit 0; Ruff reports `All checks passed!`, pytest has no
failures, pip-audit reports no known vulnerabilities in its audited requirements,
and Bandit reports no medium/high findings. Docker scanning requires a built
image and was not rerun for this documentation pass. `make format` rewrites
Python formatting; `make clean` deletes caches **and `mlruns/`**. Neither is a
verification step.

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

Runtime depends on the machine. Fast tests use synthetic fixtures. Three
real-data checks skip unless `RUN_REAL_DATA_TESTS=1`; three optional CleverHans
cases skip without its torch backend. Four Node-backed component cases skip
when Node is absent. The 2026-11-17 Linux baseline had 468 passing cases and six
skips, with Node available and neither optional dataset checks nor CleverHans enabled.
Tests write only to pytest temporary directories, never to committed
`docs/results/`, `docs/figures/`, or `docs/data/` artifacts. Test layout,
single-test commands, and the optional real-data checks are documented in
[`testing.md`](testing.md).

## Run the ART demo

The demo proves the FGSM/PGD/CW tooling works end to end on MNIST (CPU only).
It is an environment check, not a security result. The real-MNIST commands below
were not rerun for this documentation pass; the numerical expectations come
from the dated [Sprint 1 report](sprint1_report.md), not a new measurement.

Fast version first (recommended). After the one-time MNIST download (about
60 MB into `data/raw/`), it takes a few minutes on a CPU laptop:

```bash
python scripts/art_quickstart.py --fast
# or: make demo
```

The historical fast run had clean test accuracy around 0.92, FGSM and PGD
adversarial accuracy near 0.05 at epsilon 0.3, and CW-L2 evaluated on
20 samples. Exact numbers differ slightly by machine.

Full version (trains on all of MNIST for 3 epochs, CW on 200 samples; takes
10 minutes or more on CPU):

```bash
python scripts/art_quickstart.py --epochs 3
```

The historical partial full-data check reached clean accuracy around 0.99;
its epsilon grid timed out. The accuracy-vs-epsilon grid is the slowest part;
`--cw-samples 20` limits CW work. A completed run writes the outputs listed below.
Inspect the CW result's `failed` field rather than assuming every attack completed.

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

ASR is the fraction of clean-correct rows made incorrect by the attack. It is
JSON `null` when none of the clean predictions is correct, and no ASR metric
is logged to MLflow for that cohort. Python callers of `eval_attack()` must
pass the paired clean predictions as `y_pred_clean=...`.

The committed Sprint 1 JSON and reports retain the older overall adversarial
error rate under the ASR label. They have not been regenerated and are not
measurements of the corrected conditional ASR.

The JSON and figures are committed reference outputs; regenerate them with the
demo rather than editing them by hand. **The demo CLI has no `--output-dir`
flag**: even `--synthetic` writes to the default committed output paths. For an
isolated synthetic check run `python -m pytest tests/test_art_quickstart_smoke.py`;
Python callers can instead pass `run_demo(args, output_dir=Path(...))` to redirect
results, figures and MLflow under a chosen directory. Browse a logged run with:

```bash
MLFLOW_ALLOW_FILE_STORE=true python -m mlflow ui
```

Then open http://127.0.0.1:5000 in your browser. Success means the local run and
its logged artifacts are visible; the MLflow UI was not started in this pass.

The demo's optional CleverHans path is separate from the measured Sprint 5
cross-checks. Sprint 5 uses an isolated torch-only install from
`requirements-cleverhans-torch.txt`, with explicit path flags; see
[Sprint 5 setup](sprint5.md#attack-adapters). The older
`requirements-cleverhans.txt` environment includes TensorFlow and recorded
advisory risks; it is neither required for normal setup nor the Sprint 5 overlay.
The MNIST helper's gradient-context concern remains
[flagged, not changed](documentation_audit.md); completed Sprint 5 checks do not
verify that helper.

## Run the API and dashboard without Docker

The HTML dashboard and API run in one service. The command blocks until stopped.

With the virtual environment active:

```bash
python -m uvicorn api.main:app --reload --port 8000
```

Open http://127.0.0.1:8000/health — expect `{"status": "ok"}`.

Open <http://localhost:8000/dashboard/>. Alternatively, `make dashboard` starts
the same application on port 8501; open <http://localhost:8501/dashboard/>.
`dashboard/app.py` is a legacy Streamlit reference, not the primary entry point.
Its separate API/client workflow is documented in [the dashboard README](../dashboard/README.md).

The `/health` response is liveness only: it does not verify data, reports,
MLflow, a token, or a frozen model. Check `/v1/runs` for recorded comparisons;
dataset routes always return `local_verification: "not_checked"`. Use the
preprocessing CLI's `--verify-only` for local arrays, and the authenticated
`/v1/baseline` route for prediction readiness. See [the API reference](../api/README.md).

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
http://127.0.0.1:8000/health, http://localhost:8501/dashboard/, and
http://localhost:5000. Stop with `Ctrl+C`, then `docker compose down`.

Do not set `BIND_ADDR=0.0.0.0` unless you put a TLS reverse proxy with
authentication in front of the stack. MLflow and the research dashboard
have no built-in authentication.

Both `api` and `dashboard` run the same FastAPI app on different ports. The
HTML client uses its own origin; no inter-service `API_URL` is needed.
Each process has its own prediction cache/query budget.
Compose mounts `docs/` and `models/sprint4/` read-only into both services;
raw/processed datasets are not required to browse reports. Check service state
and logs with `docker compose ps` and `docker compose logs api dashboard mlflow`.
The MLflow service has no Compose healthcheck; inspect its endpoint separately.
Compose startup was not rerun for this documentation pass; the historical smoke
test above does not establish a fresh installation or complete browser workflow.

Provision prediction only after a genuine freeze, following [Sprint 4](sprint4.md).
Native uvicorn does **not** load `.env` automatically: export settings before
startup or explicitly pass `--env-file .env`. Compose loads the file via
`env_file`. Restart API/dashboard processes after replacing a loaded bundle.

## Data pipeline and EDA

Sprint 4 training/freezing and feature prediction are documented in
[`sprint4.md`](sprint4.md), including the data-quality gate and fail-closed API.

See the data guide: [`data/README.md`](data/README.md). It covers dataset
locations, preprocessing/EDA commands, expected runtime and outputs, and the
processed-data loaders.

## Troubleshooting

| Problem | Fix |
|---|---|
| Python is outside 3.11–3.12, or install fails on your Python | Select Python 3.11 or 3.12 before creating the venv. A newer system Python is not a supported substitute. |
| `make setup` fails with `python: No such file or directory` | Select an installed supported interpreter, for example `make setup PY=python3.11`; use `PY=python3` only after checking its version. |
| macOS reports no matching `torch==...+cpu` distribution | The exact CPU pins have no macOS wheels on the configured index. Native macOS setup is not validated; do not replace pins as a troubleshooting shortcut. |
| `ModuleNotFoundError: No module named 'pkg_resources'` when importing mlflow | Your environment predates the current pins. Recreate `.venv` with `make setup` (mlflow 3.17.2 + setuptools 84.2.1). |
| `ruff` or `pytest` not found | The venv is not activated, or dev requirements are missing. Activate `.venv` and run `pip install -r requirements-dev.txt`. |
| torch download is very slow or fails | The CPU wheel is about 200 MB. Check disk space and connection, then rerun the same `pip install` command; pip resumes. |
| PowerShell refuses to activate the venv | Use `.\.venv\Scripts\python.exe` directly; activation is optional. |
| `python -m uvicorn ...` says address already in use | Port 8000 is taken. Use `--port 8001` and open `http://localhost:8001/dashboard/`; the HTML client follows the same origin automatically. |
| HTML dashboard reports an API error | Check `/health` and `/v1/runs` on the same host/port, then inspect uvicorn logs. `API_URL` affects only legacy Streamlit, not HTML. |
| `/` shows a Sprint 1 placeholder message | That root response is retained for compatibility; the current UI is `/dashboard/`, not `/`. |
| HTTP 400 `Invalid host header` | Use localhost or add the intended hostname to `API_ALLOWED_HOSTS` before startup; do not disable validation with `*`. |
| Prediction returns 503 while `/health` is OK | Confirm the API process receives a token of at least 32 characters and a valid frozen bundle exists at `models/sprint4/baseline_v1`. `.env` alone does not configure native uvicorn. Inspect server logs for bundle errors; do not bypass the M1 gate. |
| Prediction returns 401 / 422 / 429 | Check the exact bearer token / ordered features and bundle identities / wait for the 60-second per-peer window. See [API errors](../api/README.md#prediction-errors). |
| `docker compose up` fails with `env file ... not found` | Run `cp .env.example .env` first; compose uses it for host ports. |
| MNIST download shows `HTTP Error 404` for `yann.lecun.com` | Expected: torchvision automatically retries its mirror and continues. No action needed. |
| `--cleverhans` prints `CleverHans not available, skipping` | Normal without the optional library. For Sprint 5 use its documented torch-only overlay and explicit path flags, not the older TensorFlow environment; MNIST helper verification is separate. |
| `git clone` fails on Windows with filename-too-long errors | Enable long paths once: `git config --system core.longpaths true` (needs an elevated prompt), then clone again. |
| `scripts/preprocess.py` says the source directory is missing | Set `EMBER_DATA_DIR` / `CICIDS_DATA_DIR`, pass `--source`, or place the dataset under `data/raw/` or `~/Documents/`. The pipeline never downloads data. |
| EMBER preprocessing is killed or runs out of disk | Plan for about 9–10 GB (arrays plus headroom). Use `--max-samples` for smoke work or free space under `data/processed/`; the pipeline preallocates `.npy.tmp` files and only publishes them after success. |
| CICIDS duplicate/NaN counts differ from an older notebook | This pipeline reads the original eight CSVs, deduplicates at saved float32 precision, and reports raw-float64 counts too. See the data card and Sprint 2 report rather than assuming a Kaggle-cleaned copy. |
