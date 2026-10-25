# Adversarial-Resilient Security Models

Machine-learning detectors for malware and network intrusion, attacked with
adversarial examples (FGSM, PGD, Carlini-Wagner) and then hardened with
adversarial training, distillation, ensembles, input sanitization, and
detectors.

The MNIST demo in this repo is only an environment check that proves the attack
tooling works — it is not the project's security result.

## Current status

Works today:

- ART demo on MNIST with FGSM, PGD, and CW-L2 (`scripts/art_quickstart.py`),
  including accuracy-vs-epsilon plots, a JSON report, and local MLflow logging.
- Test suite (`pytest`) and lint/format checks (`ruff`).
- FastAPI service with `GET /health` returning `{"status": "ok"}`.
- Streamlit dashboard page (early placeholder that can ping the API).
- `Dockerfile` and `docker-compose.yml` for api, dashboard, and mlflow services
  (the image is built in CI; Compose publishes ports on localhost by default and
  runs the API/dashboard with dropped capabilities).
- Cleaned/versioned EMBER2018 v2 and CIC-IDS-2017 datasets with manifest-based
  versioning, reusable loaders, EDA, data cards, and a reproducible
  `scripts/preprocess.py` pipeline.
- Security baseline: upgraded vulnerable dependencies, API host/header
  hardening, defensive dashboard URL handling, manifest path containment,
  loopback-only Compose defaults, and CI dependency/static checks. Evidence
  and residual risks are in [`docs/security/SECURITY_AUDIT.md`](docs/security/SECURITY_AUDIT.md).

Next: baseline detectors, FGSM/PGD/CW attacks on the real datasets, defenses,
and the full dashboard. Sprint-by-sprint status is tracked in
[`docs/progress.md`](docs/progress.md); scope and schedule are in
[`docs/project_plan.md`](docs/project_plan.md).

Honestly not verified: the CleverHans cross-check was only tested as a graceful
skip (library not installed). Docker is covered differently: the image builds
in CI on every push; the 2026-10 security audit rebuilt the image, started the
full three-service stack on loopback, and health-checked the API, dashboard,
and MLflow. Browser/MLflow artifact workflows and sustained load were not
exercised, and the official MLflow container runs as root. See the
[security audit](docs/security/SECURITY_AUDIT.md) and the
[troubleshooting section](docs/development.md#troubleshooting) for details.

## Quick start

Prerequisites: Git and Python 3.11–3.12. Docker is optional. The first install
and the MNIST demo need internet access.

```bash
make setup     # .venv, pinned dependencies, pre-commit hooks
make lint      # ruff check + format check (same as CI)
make test      # pytest, synthetic fixtures only
make security  # dependency + static security checks
```

Expected: lint is clean and all tests pass; the two optional real-data checks
are skipped unless `RUN_REAL_DATA_TESTS=1`.

Windows and non-Make setups are documented in the
[development guide](docs/development.md). If your system only provides
`python3`, run `make setup PY=python3`. The same commands without `make` are:

```bash
python -m ruff check src scripts tests api dashboard
python -m ruff format --check src scripts tests api dashboard
python -m pytest
```

## Common commands

| Command | What it does |
|---|---|
| `make demo` | Run the fast ART MNIST demo (downloads MNIST, takes a few minutes) |
| `make data` | Full EMBER + CICIDS preprocessing (needs local raw datasets) |
| `make data-smoke` | Deterministic 2000-row subsets into `/tmp` |
| `make eda` | Regenerate EDA JSON, figures, and report under `docs/` |
| `make docker-build` / `make docker-up` | Build the image / start the compose stack (`cp .env.example .env` first) |
| `make docker-scan` | Scan the built image for fixed HIGH/CRITICAL vulnerabilities |
| `make format` | Rewrite files with `ruff format` |
| `make security` | Dependency audit (`pip-audit`) + static security scan (`bandit`) |
| `make check` | `make lint` + `make test` |
| `make clean` | Remove caches and `mlruns/` (committed demo/EDA artifacts stay) |

API locally: `python -m uvicorn api.main:app --port 8000`; dashboard:
`streamlit run dashboard/app.py`. Full setup, demo flags, service details, and
troubleshooting are in [`docs/development.md`](docs/development.md).

## Documentation

Start with the documentation index: [`docs/README.md`](docs/README.md).
Highlights:

- [`docs/development.md`](docs/development.md) — setup, verification, ART demo,
  API/dashboard, Docker, troubleshooting.
- [`docs/configuration.md`](docs/configuration.md) — environment variables,
  dataset resolution, Compose ports, paths, and seeds.
- [`docs/testing.md`](docs/testing.md) — test layout, commands, fixtures, and
  optional real-data checks.
- [`docs/architecture.md`](docs/architecture.md) — components, dependency
  rules, and data flows.
- [`docs/project-structure.md`](docs/project-structure.md) — directory
  responsibilities and where new code belongs.
- [`docs/data/README.md`](docs/data/README.md) — dataset locations,
  preprocessing/EDA commands, and loaders.
- [`api/README.md`](api/README.md) — HTTP endpoints, responses, and OpenAPI
  URLs.
- [`docs/progress.md`](docs/progress.md) — current sprint and milestone status
  (scope baseline: [`docs/project_plan.md`](docs/project_plan.md)).
- [`AGENTS.md`](AGENTS.md) — quick navigation map for AI coding agents.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — branching, commit style, PR rules.
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — non-obvious technical decisions.
- [`docs/threat_model_v0.1.md`](docs/threat_model_v0.1.md) — security scope
  and attacker model.
- [`docs/security/SECURITY_AUDIT.md`](docs/security/SECURITY_AUDIT.md) —
  application security audit, fixes, verification, and remaining risks.

## Project structure

```text
api/            FastAPI service (/health today)
dashboard/      Streamlit app (early page today)
data/           raw/, processed/, adversarial/, external/ runtime data (gitignored)
docs/           documentation (index at docs/README.md), data guides, reports
docs/data/      feature layout, data guide, generated EDA report, manifests
docs/figures/   demo + EDA plots (generated, committed on purpose)
docs/results/   demo + EDA JSON (generated, committed on purpose)
models/         trained weights (gitignored, .gitkeep only)
notebooks/      exploratory notebooks (later)
scripts/        art_quickstart.py, preprocess.py, eda_datasets.py
src/            config.py paths/seeds, utils/, data/, models/, attacks/, defenses/, evaluation/
tests/          seed, config, API, data (synthetic), docs links, and smoke tests
```

Full reference: [`docs/project-structure.md`](docs/project-structure.md).

## Working with Git

- Branch names: `feat/<topic>`, `fix/<topic>`, `docs/<topic>` (or
  `sprint<N>/<topic>`).
- Commits use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`,
  `test:`, `ci:`.
- Open a pull request into `main`; never push directly to `main`.
- Never commit datasets, model weights, `.env`, or `mlruns/`. Check `git status`
  before every commit.

## Roadmap

Semester 1:

- Foundations: environment, ART demo on MNIST, threat model draft.
- Data: EMBER and CIC-IDS-2017 download, EDA, preprocessing pipeline.
- Attacks: FGSM, PGD, and CW against the real detectors.
- Defenses: adversarial training, distillation, ensembles, sanitization,
  detector.

Semester 2:

- Backend: FastAPI prediction, attack, and defense endpoints.
- Frontend: dashboard with robustness charts and MLflow links.
- Hardening: containers, CI checks, and the final evaluation.

## Safety and ethics

Defensive research only. This repo works with public feature datasets and the
MNIST demo images — no malware samples and no weaponized tooling are included
or accepted here.
