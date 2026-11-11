# Adversarial-Resilient Security Models

Defensive ML research for developers and researchers building malware and
network-intrusion detectors. The repository implements dataset preprocessing,
baseline training, evaluation, and a research dashboard. Attacks against the
real detectors and adversarial defenses are planned, not implemented.

The MNIST demo in this repo is only an environment check that proves the attack
tooling works — it is not the project's security result.

The primary UI is plain **HTML, CSS and JavaScript** served by FastAPI; no
frontend build or Streamlit process is needed. A fresh checkout includes recorded
comparison results, not datasets or trained models. Start with [Quick start](#quick-start),
or follow [the team handoff](docs/team_handoff.md) to synchronize an existing checkout.

## Current status

Works today:

- ART demo on MNIST with FGSM, PGD, and CW-L2 (`scripts/art_quickstart.py`),
  including accuracy-vs-epsilon plots, a JSON report, and local MLflow logging.
- Test suite (`pytest`) and lint/format checks (`ruff`).
- FastAPI service with liveness, read-only research artifacts, and gated,
  bearer-token-protected feature prediction. See the [API reference](api/README.md).
- HTML research dashboard with Overview, Datasets, Models, MNIST demo and
  Methodology pages; baseline comparisons use recorded validation artifacts.
  The earlier Streamlit implementation is retained as a legacy reference.
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

Sprint 3 adds Logistic Regression, Random Forest, Linear SVM and PyTorch MLP
training with reproducible validation reports and MLflow tracking. Follow
[`docs/sprint3.md`](docs/sprint3.md) for local data setup and commands.
Sprint 4 adds CPU MLP/CNN tuning, calibration, gated freezing and authenticated
feature prediction. See [`docs/sprint4.md`](docs/sprint4.md) and the
[Sprint 4 report](docs/sprint4_report.md) for measured results and M1 status.
Attacks must wait until M1 passes; defenses remain later-sprint work.
Sprint-by-sprint status is tracked in
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
Run these commands from the cloned repository root:

```bash
make setup     # .venv, pinned dependencies, pre-commit hooks
make lint      # ruff check + format check (same as CI)
make test      # pytest, synthetic fixtures only
make coverage  # pytest with line/branch coverage
make security  # dependency + static security checks
source .venv/bin/activate  # Linux/macOS; Make uses .venv automatically, Python does not
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Open <http://localhost:8000/dashboard/>. Viewing the recorded results needs no
datasets, trained models, token, database, or `.env`. Prediction remains disabled
without both a qualifying frozen bundle and a local token; implementation is
not evidence that M1 has passed. See [current status](docs/progress.md).

Expected: lint is clean and all tests pass; the three optional real-data checks
are skipped unless `RUN_REAL_DATA_TESTS=1`. Node.js is optional for running the
JavaScript component test (skipped when unavailable); it is not a UI runtime dependency.

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
| `make dashboard` | Run FastAPI + HTML dashboard at http://localhost:8501/dashboard/ |
| `make docker-build` / `make docker-up` | Build the image / start the compose stack (`cp .env.example .env` first) |
| `make docker-scan` | Scan the built image for fixed HIGH/CRITICAL vulnerabilities |
| `make format` | Rewrite files with `ruff format` |
| `make coverage` | Full test suite with line/branch coverage (CI uses this) |
| `make security` | Dependency audit (`pip-audit`) + static security scan (`bandit`) |
| `make check` | `make lint` + `make test` |
| `make clean` | Remove caches and `mlruns/` (committed demo/EDA artifacts stay) |

The API and HTML dashboard share one process; choose the uvicorn command above
or `make dashboard`, not both. Full setup, legacy Streamlit instructions,
demo flags, service details, and troubleshooting are in
[`docs/development.md`](docs/development.md).

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
- [`docs/repository_audit.md`](docs/repository_audit.md) — maintenance findings,
  cleanup evidence, verification and intentionally retained files.
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
api/            FastAPI health/artifact routes, authenticated feature prediction
dashboard/      web/ HTML/CSS/JS (primary), app.py + client.py (legacy Streamlit)
data/           raw/, processed/, adversarial/, external/ runtime data (gitignored)
docs/           documentation (index at docs/README.md), data guides, reports
docs/data/      feature layout, data guide, generated EDA report, manifests
docs/figures/   demo + EDA plots (generated, committed on purpose)
docs/results/   demo + EDA JSON (generated, committed on purpose)
models/         local baseline checkpoints and Sprint 4 bundles (gitignored)
notebooks/      exploratory notebooks (later)
scripts/        environment setup, demo, preprocessing, EDA, training and tuning CLIs
src/            config.py paths/seeds, utils/, data/, models/, attacks/, defenses/, evaluation/
tests/          seed, config, API, data (synthetic), docs links, and smoke tests
```

Full reference: [`docs/project-structure.md`](docs/project-structure.md).

## Working with Git

- Branch names: `feat/<topic>`, `fix/<topic>`, `docs/<topic>`, `chore/<topic>` (or
  `sprint<N>/<topic>`).
- Commits use Conventional Commits: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`,
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

- Backend: extend the existing gated feature prediction with attack/defense endpoints.
- Frontend: extend the research dashboard with robustness comparisons.
- Hardening: containers, CI checks, and the final evaluation.

## Safety and ethics

Defensive research only. This repo works with public feature datasets and the
MNIST demo images — no malware samples and no weaponized tooling are included
or accepted here.
