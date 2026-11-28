# Development guide

Run commands from the repository root. See [configuration](configuration.md)
for environment variables and [testing](testing.md) for test conventions and
optional checks.

## Prerequisites

Use Git and Python 3.11 or 3.12 on Linux or Windows. The exact CPU torch and
torchvision pins have no native macOS wheels on the configured index. Allow
about 3 GB for the environment and MNIST demo, and internet access for the
initial install. Full dataset storage requirements are in the
[data guide](data/README.md). GNU Make and Docker are optional.

## Setup

On Linux with Make, run `make setup PY=python3.11` (or use `PY=python3.12`).
It creates `.venv`, installs the pinned dependencies, and attempts to install
pre-commit hooks.

On Windows or Linux without Make, select Python 3.11 or 3.12 and run:

```bash
python scripts/setup_environment.py
```

Use `python3.11` or `python3.12` on Linux if needed. The bootstrap creates or
reuses `.venv`, synchronizes runtime, development, and CPU torch packages,
then checks the pins and dependency consistency. It skips Git hooks and
optional CleverHans packages. Add `--check-only` to verify an existing
environment without installing anything.

Activate with `source .venv/bin/activate` on Linux or
`.\.venv\Scripts\Activate.ps1` in PowerShell. You can also run
`.venv/bin/python` or `.\.venv\Scripts\python.exe` directly.

## Verification and quality checks

| Command | Purpose |
|---|---|
| `make check` | Run Ruff lint and format checks, then pytest |
| `make coverage` | Run the suite with line and branch coverage |
| `make security` | Run pip-audit and Bandit |
| `make docker-build docker-scan` | Build the local image and scan for fixed high and critical findings |

Without Make, use these commands with the virtual environment active:

```bash
python -m ruff check src scripts tests api dashboard
python -m ruff format --check src scripts tests api dashboard
python -m pytest
```

See [testing](testing.md) for focused runs, coverage commands, and skip reasons.
`make format` applies Ruff formatting. `make clean` deletes caches and local
MLflow history in `mlruns/`.

## Run the ART demo

The CPU-only MNIST demo checks the research tooling. The first run downloads
about 60 MB of MNIST data. Run `make demo` or
`python scripts/art_quickstart.py --fast` with the virtual environment active.
Use `python scripts/art_quickstart.py --help` for flags and the
[Sprint 1 report](sprint1_report.md) for historical measurements.

The demo writes [JSON results](results/art_quickstart_results.json),
[example images](figures/art_samples.png), [accuracy curves](figures/art_accuracy_vs_eps.png),
and local MLflow runs. Inspect the JSON `failed` field for failed CW evaluations.
Regenerate the committed JSON and figures with the demo. Even `--synthetic`
writes to the committed paths when run from the CLI. For an isolated check,
run `python -m pytest tests/test_art_quickstart_smoke.py`. Python callers can
set `output_dir` on `run_demo()` to redirect all outputs.

Current ASR measures the fraction of clean-correct rows made incorrect.
An empty denominator yields JSON `null` and omits ASR from MLflow. Pass paired
clean predictions as `y_pred_clean` when calling `eval_attack()`. The committed
Sprint 1 results retain the historical overall adversarial error rate under the
ASR label.

On Linux, run `MLFLOW_ALLOW_FILE_STORE=true python -m mlflow ui` to browse
local runs at <http://127.0.0.1:5000>. See the
[testing guide](testing.md#optional-cleverhans-checks) for optional backend setup.

## Run the API and dashboard without Docker

On Linux, `make dashboard` serves the API and HTML dashboard together at
<http://localhost:8501/dashboard/>. With the virtual environment active, you can
also run the service on port 8000 on Linux or Windows:

```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Open <http://localhost:8000/dashboard/>, confirm **v0.8.0 · Sprint 08**, and
expand **Recorded case catalogue**. The legacy Streamlit entry point is
documented in the [dashboard reference](../dashboard/README.md#legacy-streamlit-interface).

`/health` checks process liveness. Use `/v1/runs` to verify recorded comparisons
and the authenticated `/v1/baseline` route to check prediction readiness.
Check local processed data with `python scripts/preprocess.py --dataset all --verify-only`.
See the [API reference](../api/README.md) and [freeze protocol](sprint4.md).

## Run the Docker stack

Create `.env` from `.env.example` if needed, then run:

```bash
docker compose up --build
```

Check the API at <http://127.0.0.1:8000/health>, the dashboard at
<http://localhost:8501/dashboard/>, and MLflow at <http://localhost:5000>.
Use `docker compose ps` and `docker compose logs api dashboard mlflow` to inspect
the stack. Stop it with `docker compose down`.

The API and dashboard are separate processes running the same FastAPI app,
each with its own prediction cache and query budget. Both mount reports and
Sprint 4 model bundles read-only. Published ports default to loopback. Keep
that binding unless you have a TLS reverse proxy with authentication for the
dashboard and MLflow. See [Compose configuration](configuration.md#env-and-docker).

## Data pipeline and EDA

The [data guide](data/README.md) covers sources, commands, storage estimates,
and generated outputs. Follow the [Sprint 4 protocol](sprint4.md) for training
and freezing a baseline.

## Troubleshooting

| Problem | Fix |
|---|---|
| Setup cannot find Python or rejects its version | Select an installed Python 3.11 or 3.12 explicitly, for example `make setup PY=python3.11`. |
| Ruff, pytest, or MLflow imports fail | Use the project venv and run the setup bootstrap to synchronize its pins. |
| Port 8000 is in use | Pass `--port 8001` and open <http://localhost:8001/dashboard/>. |
| Dashboard reports an API error | Check `/health`, `/v1/runs`, and the server logs. The HTML client uses its own origin. |
| API returns 400 for the Host header | Use localhost or list the intended hostname in `API_ALLOWED_HOSTS`. |
| Prediction returns 503 | Check the verified frozen bundle at `models/sprint4/baseline_v1` and a process token of at least 32 characters. Export settings or pass `--env-file .env` for native uvicorn. Restart after replacing a loaded bundle. |
| Prediction returns 401, 422, or 429 | See [prediction errors](../api/README.md#prediction-errors) for tokens, feature validation, and query limits. |
| Windows clone fails with paths that are too long | Run `git config --system core.longpaths true` from an elevated prompt, then clone again. |
| MNIST's first download mirror returns 404 | Torchvision retries with its fallback mirror. |
| Preprocessing cannot find files or runs out of space | Check source resolution and disk estimates in the [data guide](data/README.md). |
