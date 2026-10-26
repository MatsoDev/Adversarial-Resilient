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
| Environment variables | Dataset locations, dashboard API URL, Compose host ports, optional real-data tests |
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
| `API_URL` | No | `http://localhost:8000` | `dashboard/app.py`, `dashboard/client.py` | Base URL the Streamlit page uses for `GET /health`; must be absolute http/https with no credentials, query string, or fragment; read at import time, so restart Streamlit after changing it |
| `API_ALLOWED_HOSTS` | No | `localhost,127.0.0.1,api,testserver` | `api/main.py` | Comma-separated `Host` header allowlist; `*` disables validation (not recommended) |
| `API_DOCS_ENABLED` | No | `true` | `api/main.py` | Serve `/docs`, `/redoc`, and `/openapi.json`; set `false` to hide them |
| `BIND_ADDR` | No | `127.0.0.1` | Docker Compose | Host interface for all published ports; do not use `0.0.0.0` without TLS/authentication |
| `API_PORT` | No | `8000` | Docker Compose | Host port mapped to the API container; not read by Python |
| `DASHBOARD_PORT` | No | `8501` | Docker Compose | Host port mapped to the dashboard container; not read by Python |
| `MLFLOW_PORT` | No | `5000` | Docker Compose | Host port mapped to the MLflow container; not read by Python |
| `RUN_REAL_DATA_TESTS` | No | Unset (tests skip) | `tests/test_data_real_optional.py` | Set to `1` to run the two local-dataset availability checks |

Notes:

- `src/utils/seed.py` sets `PYTHONHASHSEED` internally from the seed argument;
  it is not a user-facing configuration option.
- No API keys or secrets are read by the current code. The API exposes only
  liveness/message endpoints, so there is nothing to authenticate yet. Future
  prediction/attack endpoints must add authentication, authorization, and
  rate limiting before they are exposed beyond localhost.
- MLflow and the dashboard have no built-in authentication. Compose binds all
  published ports to `127.0.0.1` by default; use a TLS reverse proxy with
  authentication before changing `BIND_ADDR`.
- The dashboard's `API_URL` is overridden to `http://api:8000` in
  [`../docker-compose.yml`](../docker-compose.yml); the environment value is
  what lets the same page work locally and in the container network.

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
- `.env` is gitignored. Never commit it or put real credentials in it.
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

Point the dashboard at a non-default API port:

```bash
API_URL=http://127.0.0.1:8001 python -m streamlit run dashboard/app.py
```

Run the optional real-data tests (requires both local datasets):

```bash
RUN_REAL_DATA_TESTS=1 python -m pytest tests/test_data_real_optional.py -q
```

The commands above assume the virtual environment is active. For equivalent
Make targets and troubleshooting see [`development.md`](development.md), for
the test layout and optional checks see [`testing.md`](testing.md), and for the
complete data CLI flags see [`data/README.md`](data/README.md).
