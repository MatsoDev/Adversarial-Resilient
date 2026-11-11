# Configuration reference

How the project is configured for local development, tests, and the Docker
stack. This page lists the settings that are actually read by the code and
Compose; paths and constants are defined in
[`../src/config.py`](../src/config.py). For setup steps see
[`development.md`](development.md), and for dataset locations see
[`data/README.md`](data/README.md).

## Configuration sources

| Source | Used for |
|---|---|
| CLI flags | One-off datasets, output directories, seeds, demo options |
| Environment variables | Dataset locations, legacy dashboard URL, API hardening/token, Compose ports, optional tests |
| `.env` | Compose host binding/ports, plus api/dashboard container environment via `env_file` (never commit it) |
| Python constants | Repository paths, default seed, dataset names, demo constants in [`../src/config.py`](../src/config.py) |

Precedence for raw dataset discovery (highest first):

```text
CLI --source (or --ember-source / --cicids-source)
  > EMBER_DATA_DIR / CICIDS_DATA_DIR
  > data/raw/EMBER-Dataset or data/raw/CIC-IDS-Dataset
  > ~/Documents/EMBER-Dataset or ~/Documents/CIC-IDS-Dataset
```

`src.config.resolve_ember_source()` and `resolve_cicids_source()` implement this
order. If no location exists, the repo-local path is returned so callers can
produce an actionable error instead of using a personal absolute path.

## Environment variables

| Variable | Required | Default | Read by | Purpose |
|---|---|---|---|---|
| `EMBER_DATA_DIR` | No | Resolution order above | `src.config.resolve_ember_source()` | Raw EMBER2018 v2 directory |
| `CICIDS_DATA_DIR` | No | Resolution order above | `src.config.resolve_cicids_source()` | Raw CIC-IDS-2017 directory (eight CSVs) |
| `API_URL` | No | `http://localhost:8000` | Legacy `dashboard/app.py` | Base URL for the Streamlit artifact/health client; absolute http/https without credentials, query, fragment, whitespace or backslashes. Initialized in session state; change the sidebar URL or start a new session after changing the environment. HTML ignores this variable. |
| `API_ALLOWED_HOSTS` | No | `localhost,127.0.0.1,api,testserver` | `api/main.py` | Comma-separated `Host` header allowlist; `*` disables validation (not recommended) |
| `API_DOCS_ENABLED` | No | `true` | `api/main.py` | Read at app creation. Accepts `1/true/yes/on` or `0/false/no/off` (case-insensitive); invalid values warn and use the default. Hiding docs does not disable API routes. |
| `PREDICTION_API_TOKEN` | For prediction | Unset (disabled) | `api/prediction.py` | Random local research bearer token, minimum 32 characters; never commit; required by `/predict` and `/v1/baseline` |
| `BIND_ADDR` | No | `127.0.0.1` | Docker Compose | Host interface for all published ports; do not use `0.0.0.0` without TLS/authentication |
| `API_PORT` | No | `8000` | Docker Compose | Host port mapped to the API container; not read by Python |
| `DASHBOARD_PORT` | No | `8501` | Docker Compose | Host port mapped to the dashboard container; not read by Python |
| `MLFLOW_PORT` | No | `5000` | Docker Compose | Host port mapped to the MLflow container; not read by Python |
| `RUN_REAL_DATA_TESTS` | No | Unset (tests skip) | `tests/test_data_real_optional.py` | Set to `1` to run the two local-dataset availability checks |
| `MLFLOW_ALLOW_FILE_STORE` | For local file tracking | Project scripts set `true` if absent | Demo, training/tuning scripts and MLflow | MLflow 3.17 requires opt-in for the local `mlruns/` store. Compose sets `true`; set it explicitly for `mlflow ui`. An existing value is not overridden by scripts. |

Notes:

- `src/utils/seed.py` sets `PYTHONHASHSEED` internally from the seed argument;
  it is not a user-facing configuration option.
- Sprint 4 prediction requires a local bearer token and enforces a per-peer
  query budget. Keep it on loopback; TLS and multi-user authorization remain
  external requirements. See [Sprint 4](sprint4.md).
- MLflow and the dashboard have no built-in authentication. Compose binds all
  published ports to `127.0.0.1` by default; use a TLS reverse proxy with
  authentication before changing `BIND_ADDR`.
- `RUN_REAL_DATA_TESTS=1` also enables the processed-EMBER check in
  `tests/test_sprint3_real.py` (three opt-in tests total).
- `API_ALLOWED_HOSTS` is read at app creation (restart after changes);
  `PREDICTION_API_TOKEN` is read on each authenticated request. The token is
  compared against the exact `Authorization: Bearer <token>` header.
- Compose's dashboard service runs FastAPI, not Streamlit, and no longer sets
  the unused `API_URL`. HTML always requests its own origin's `/v1/*` and
  `/predict`; there is no separate browser API URL or CORS configuration.
- Training/tuning use explicit `--tracking-uri` or the local `mlruns/` default,
  not `MLFLOW_TRACKING_URI`, to select tracking storage.

## `.env` and Docker

[`../.env.example`](../.env.example) is the template for Compose host ports:

```bash
cp .env.example .env
docker compose up --build
```

- Compose requires `.env` because the services declare `env_file: .env`.
- `BIND_ADDR` plus the three `*_PORT` variables control host binding/ports;
  the Python apps do not read them. Inside the containers the API always
  listens on 8000, the dashboard on 8501, and MLflow on 5000.
- `API_ALLOWED_HOSTS` and `API_DOCS_ENABLED` are optional API settings in the
  same file. The safe defaults are built into the app.
- `.env` and local `.env.*` variants are gitignored; only the root `.env.example`
  template is allowed. Never commit real credentials.
- Native Python entry points do not call `load_dotenv`. For local uvicorn,
  export settings first or pass `--env-file .env`; Compose loads it automatically.
- If you add a new variable, document it here and add a safe placeholder to
  `.env.example`; do not hard-code paths or secrets in application code.

## Security notes

The application security baseline and residual risks are documented in
[`security/SECURITY_AUDIT.md`](security/SECURITY_AUDIT.md). In short: keep the
Compose ports on loopback, do not expose MLflow without authentication/TLS,
keep `API_DOCS_ENABLED=false` on public deployments, and run `make security`
after dependency or HTTP changes.

## Data paths and seeds

Use imports from [`../src/config.py`](../src/config.py) instead of constructing
paths in modules. The main locations are:

| Constant | Location |
|---|---|
| `ROOT` | Repository root (parent of `src/`) |
| `RAW_DIR` | `data/raw/` (downloads and optional dataset symlinks) |
| `PROCESSED_DIR` | `data/processed/` (gitignored arrays, scalers, manifests) |
| `ADVERSARIAL_DIR` | `data/adversarial/` (reserved for later sprints) |
| `MODELS_DIR` | `models/` (gitignored checkpoints) |
| `BASELINE_MODELS_DIR` / `BASELINE_RESULTS_DIR` | `models/baselines/`, `docs/results/baselines/` (ignored development outputs) |
| `FROZEN_BASELINE_DIR` | `models/sprint4/baseline_v1/` (default trusted inference bundle; no environment override) |
| `FIGURES_DIR` / `RESULTS_DIR` | `docs/figures/`, `docs/results/` (committed demo/EDA outputs) |
| `DATA_MANIFESTS_DIR` | `docs/data/manifests/` (committed full-run manifests) |

`SEED = 42` is the default in `src/config.py`; `src.utils.seed.set_seed()`
seeds Python, numpy, and torch. CLI `--seed` overrides it for data and demo
runs.

## Examples

Resolve dataset directories explicitly without copying data into the repo:

```bash
export EMBER_DATA_DIR="$HOME/datasets/EMBER-Dataset"
export CICIDS_DATA_DIR="$HOME/datasets/CIC-IDS-Dataset"
python scripts/preprocess.py --dataset all
```

Run the primary dashboard on a non-default port (no `API_URL` needed):

```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8001
# Open http://localhost:8001/dashboard/
```

Run the optional real-data tests (requires both local datasets):

```bash
RUN_REAL_DATA_TESTS=1 python -m pytest tests/test_data_real_optional.py -q
```

The commands above assume the virtual environment is active. For equivalent
Make targets and troubleshooting see [`development.md`](development.md), for
the test layout and optional checks see [`testing.md`](testing.md), and for the
complete data CLI flags see [`data/README.md`](data/README.md).
