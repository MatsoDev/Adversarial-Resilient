# Architecture overview

This document describes how the repository is actually built today (Sprint 2
state) and the rules that keep it coherent as the project grows.

## What the system is

Machine-learning detectors for malware (EMBER) and network intrusion
(CIC-IDS-2017) that are attacked with adversarial examples (FGSM, PGD,
Carlini-Wagner) and later hardened with defenses. Sprint 1 proved the attack
tooling works end to end on an MNIST demo; Sprint 2 adds the cleaned, versioned
EMBER2018 and CIC-IDS-2017 datasets, reusable loaders, EDA, and manifests.
Baselines, attacks on real data, and defenses land in later sprints (see the
module READMEs under [`../src/`](../src/)).

## Components

```text
  +-------------------------------+   +-------------------------------+
  | scripts/art_quickstart.py     |   | scripts/preprocess.py         |
  | (ART demo on MNIST)           |   | scripts/eda_datasets.py       |
  +---------------+---------------+   +---------------+---------------+
                  | imports                           | imports
                  v                                   v
  +-----------+   +-------------------------------------------+   +----------------+
  | api/      |   |  src/  (shared library, importable as     |   | data/processed |
  | FastAPI   |-->|  `src.*`)                                 |-->| (gitignored)   |
  | /health   |   |  config.py  utils/seed  models/           |   +----------------+
  +-----------+   |  data/ attacks/ defenses/ evaluation/     |
        ^         |                                           |
        | calls   +-------------------------------------------+
  +-----------+                 | manifests / EDA
  | dashboard/|                 v
  | Streamlit |      +---------------------------+   +------------------+
  +-----------+      | docs/data/manifests/      |   | mlruns/          |
                     | docs/data/eda_report.md   |   | MLflow tracking  |
                     | docs/figures/data_*.png   |   | (gitignored)     |
                     +---------------------------+   +------------------+
```

### `src/` — shared library

The single home for reusable code. Everything else imports from here, never
the other way around.

- [`src/config.py`](../src/config.py) — central paths (`ROOT`, `DATA_DIR`,
  `FIGURES_DIR`, ...), the default `SEED`, and demo constants. All modules are
  expected to import paths from here instead of constructing their own so the
  project stays portable across Windows/Linux/macOS. `ensure_dirs()` creates
  the gitignored runtime directories.
- [`src/utils/seed.py`](../src/utils/seed.py) — `set_seed()` seeds
  `random`, numpy, and torch, and enables deterministic torch settings where
  possible. Every experiment should call it first.
- [`src/models/baseline_mlp.py`](../src/models/baseline_mlp.py) —
  `BaselineMLP` (tabular baseline skeleton) and `SmallCNN` (the MNIST demo
  model).
- [`src/data/`](../src/data/README.md) — Sprint 2 data layer (usage guide:
  [`docs/data/README.md`](data/README.md)):
  `ember.py` (clean-room EMBER v2 vectoriser, metadata scan, time split),
  `cicids2017.py` (cleaning, canonical labels, dedup, stratified split),
  `preprocessing.py` (atomic writes, hashing/manifests, scalers, split
  utilities), and `loader.py` (`load_ember` / `load_cicids2017`).
- `src/attacks/`, `src/defenses/`, `src/evaluation/` — placeholder packages
  whose READMEs describe the planned contents; they contain no logic yet.

### `scripts/` — runnable entry points

One-off and demo scripts that wire the library together. `scripts/` may import
`src/`; `src/` must never import `scripts/`.

- [`scripts/art_quickstart.py`](../scripts/art_quickstart.py) — the Sprint 1
  deliverable: downloads MNIST via torchvision into `data/raw/`, trains
  `SmallCNN`, wraps it with ART's `PyTorchClassifier`, runs FGSM/PGD/CW-L2,
  computes an accuracy-vs-epsilon table, then writes the JSON report,
  the two figures, and MLflow data. `--synthetic` runs on random data for
  tests, and `run_demo(args, output_dir=...)` redirects all outputs (the smoke
  test uses pytest's `tmp_path` so committed artifacts are never overwritten).
- [`scripts/preprocess.py`](../scripts/preprocess.py) — one-command
  reproducible EMBER/CICIDS preprocessing, `--verify-only` manifest checks,
  deterministic subsets, and `--dataset all`.
- [`scripts/eda_datasets.py`](../scripts/eda_datasets.py) — EDA JSON, compact
  PNG figures, and a generated Markdown report; `--output-dir` keeps tests out
  of `docs/`.

### `api/` — FastAPI service

[`api/main.py`](../api/main.py) exposes `GET /health` (used by the dashboard's
API check and `tests/test_api_health.py`) and `GET /`. FastAPI also serves
`/docs`, `/redoc`, and `/openapi.json` (disable with `API_DOCS_ENABLED=false`).
It validates Host headers, sends browser security headers, and runs with
`--no-server-header` in the image/Compose stack. Semester 2 adds the real
`/predict`, `/attack`, and `/defend` endpoints, which must also add
authentication, authorization, and rate limiting. The Docker image
(`Dockerfile`) runs this app as a non-root user with uvicorn. The endpoint
contract is documented in [`api/README.md`](../api/README.md).

### `dashboard/` — Streamlit UI

[`dashboard/app.py`](../dashboard/app.py) is a placeholder page with a button
that calls the API's `/health` endpoint. It reads `API_URL` from the
environment, defaulting to `http://localhost:8000` for local runs; compose sets
it to `http://api:8000`.

### Deployment stack

[`docker-compose.yml`](../docker-compose.yml) defines three services:

- `api` — built from the repo `Dockerfile`, served on `${API_PORT:-8000}`;
- `dashboard` — same image, runs Streamlit on `${DASHBOARD_PORT:-8501}`;
- `mlflow` — the official MLflow image, serving `./mlruns` on
  `${MLFLOW_PORT:-5000}`.

The stack reads `.env` (copied from [`.env.example`](../.env.example)) and
publishes ports on `127.0.0.1` by default. API and dashboard drop all Linux
capabilities and set `no-new-privileges`; MLflow has no authentication, so it
must stay on loopback or sit behind a TLS reverse proxy with auth.
`.dockerignore` keeps the build context small. The image is CPU-only, runs as
a non-root user, and pins its base image and pip version.

### CI

[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs on every push
and pull request:

- `lint-test` — Python 3.11, `make lint` (ruff check + format check), then
  `make test`.
- `security` — `make security` (pip-audit + Bandit).
- `docker` — `docker build` plus a pinned Trivy scan of fixed
  HIGH/CRITICAL findings (no push).

## Dependency rules

1. `src/` is the base layer: it may depend only on third-party packages
   (torch, numpy, ART, ...), never on `api/`, `dashboard/`, `scripts/`, or
   `tests/`.
2. `api/`, `dashboard/`, and `scripts/` may import `src/`.
3. `api/` and `dashboard/` are independent of each other; the dashboard talks
   to the API over HTTP.
4. `tests/` may import anything.
5. Paths come from `src/config.py`; seeds come from `src/utils/seed.py`.
6. New reusable code goes in `src/`; new runnable demos go in `scripts/`.

## Key data flows

**ART demo (`make demo`):**

```text
torchvision MNIST --> data/raw/MNIST/ --> SmallCNN (train) --> ART PyTorchClassifier
        --> FGSM / PGD / CW-L2 --> metrics (adv accuracy, ASR, L2/Linf)
        --> docs/results/art_quickstart_results.json
        --> docs/figures/art_samples.png, art_accuracy_vs_eps.png
        --> mlruns/ (MLflow file store)
```

**Data pipeline (`make data` / `make eda`):**

```text
resolved EMBER/CICIDS source (CLI > env var > data/raw/ > ~/Documents; read in place)
    --> src/data/ember.py / cicids2017.py (validate, clean, vectorise, split)
    --> data/processed/{ember2018,cicids2017}/ (gitignored .npy + metadata + scalers)
    --> docs/data/manifests/*.json (committed compact manifests)
    --> scripts/eda_datasets.py --> docs/results/data_eda.json
                                  docs/figures/data_*.png
                                  docs/data/eda_report.md
```

**API + dashboard:**

```text
Streamlit (dashboard/) --HTTP GET /health--> FastAPI (api/) --> {"status": "ok"}
```

## Constraints and invariants

- Python 3.11–3.12 (CI and Docker use 3.11; Python 3.10 support ends in October 2026).
- CPU-only; torch/torchvision CPU wheels from the PyTorch index
  (`requirements-torch.txt`, scoped index).
- Deterministic runs: fixed seeds (`SEED = 42` default) and
  `set_seed()`; the demo also records the seed in its JSON output.
- Raw datasets, processed arrays, scalers, model weights, `.env`, and `mlruns/`
  are never committed (`.gitignore`). Committed generated artifacts are the
  Sprint 1 demo files in `docs/results/` + `docs/figures/`, the compact data
  manifests in `docs/data/manifests/`, and the generated EDA report/figures.
- Data versioning is manifest-based (SHA-256 + sizes + counts + config + seed);
  DVC/Git LFS are deliberately not used in Sprint 2 (see `DECISIONS.md`).
- Defensive research only: public feature datasets, no live malware, no
  weaponized tooling (see [`threat_model_v0.1.md`](threat_model_v0.1.md)).

## Where future components fit

| Planned work | Sprint | Location | Module README |
|---|---|---|---|
| EMBER / CIC-IDS-2017 loaders, preprocessing, splits | 2 (done) | `src/data/` | [`src/data/README.md`](../src/data/README.md) |
| Baseline detectors | 3–4 | `src/models/` | [`src/models/README.md`](../src/models/README.md) |
| FGSM/PGD/CW wrappers over ART | 5–6 | `src/attacks/` | [`src/attacks/README.md`](../src/attacks/README.md) |
| Adversarial training, distillation, ensembles, sanitization, detector | 9–11 | `src/defenses/` | [`src/defenses/README.md`](../src/defenses/README.md) |
| Metrics and plots | 5, 7 | `src/evaluation/` | [`src/evaluation/README.md`](../src/evaluation/README.md) |
| REST endpoints (/predict, /attack, /defend) | 13 | `api/` | [`api/README.md`](../api/README.md) |
| Real dashboard | 13 | `dashboard/` | [`dashboard/README.md`](../dashboard/README.md) |

Non-obvious choices are logged in [`DECISIONS.md`](DECISIONS.md); sprint
reports record what was actually run and measured.
