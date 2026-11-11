# Project structure

The stable placement reference for contributors and coding agents. Start with
[the documentation index](README.md); [architecture](architecture.md) explains
the components and data flows, and [testing](testing.md) maps individual suites.
This tree highlights boundaries and entry points, not every file.

## Repository tree

```text
Adversarial-Resilient/
├── README.md, AGENTS.md          # orientation and agent navigation
├── CONTRIBUTING.md, LICENSE      # contribution workflow and MIT license
├── Makefile                     # canonical setup/check/service/data commands
├── pyproject.toml               # Ruff, pytest and coverage; no package build
├── requirements*.txt            # runtime, dev, CPU torch, isolated CleverHans
├── Dockerfile, docker-compose.yml
├── .env.example                 # safe local/Compose settings template
├── .gitignore, .dockerignore, .gitattributes
├── .pre-commit-config.yaml       # formatting and hygiene hooks
├── .github/                     # CI workflow, issue and PR templates
├── api/
│   ├── main.py                  # app factory, middleware, /dashboard mount
│   ├── artifacts.py             # read-only /v1 research routes
│   └── prediction.py            # authenticated metadata/inference and budgets
├── dashboard/
│   ├── web/                     # primary HTML/CSS/JS and logo; no build step
│   ├── app.py                   # supported legacy Streamlit reference
│   └── client.py                # bounded/validated legacy HTTP client
├── src/                         # shared library, imported as src.*
│   ├── config.py                # central paths, default seed, dataset resolvers
│   ├── utils/seed.py            # deterministic Python/NumPy/torch seeding
│   ├── data/
│   │   ├── ember.py             # EMBER v2 vectorization and time split
│   │   ├── cicids2017.py        # CSV cleaning, labels, deduplication and split
│   │   ├── preprocessing.py     # atomic writes, hashes/manifests, scalers/splits
│   │   └── loader.py            # processed data interfaces
│   ├── models/
│   │   ├── baseline_mlp.py      # demo-era BaselineMLP and MNIST SmallCNN
│   │   ├── tabular.py           # binary TabularMLP and TabularCNN logits
│   │   ├── sampling.py          # shared stratified indices/rows and index hashes
│   │   ├── training.py          # classical/MLP validation-only comparison
│   │   ├── tuning.py            # CPU search, calibration and held-out test gate
│   │   └── frozen.py            # verified bundles and raw/scaled inference
│   ├── evaluation/              # binary metrics and bounded artifact readers
│   ├── attacks/                 # reserved boundary; no real-detector attacks yet
│   └── defenses/                # reserved boundary; no defense implementation yet
├── scripts/                     # runnable operator entry points
│   ├── setup_environment.py     # synchronize/check .venv; no data or hooks
│   ├── art_quickstart.py        # ART MNIST environment demo
│   ├── preprocess.py            # dataset pipeline and verification CLI
│   ├── eda_datasets.py          # EDA JSON/figures/report generator
│   ├── train_baselines.py       # Sprint 3 comparison CLI
│   └── tune_baseline.py         # Sprint 4 tune/calibrate/evaluate/freeze CLI
├── tests/                       # flat pytest suite; see docs/testing.md
│   ├── conftest.py              # Windows torch import-order workaround
│   └── data_fixtures.py         # reusable synthetic inputs
├── docs/                        # indexed guides, contracts and dated evidence
│   ├── data/                   # guide, feature layout, generated EDA/manifests
│   ├── data_cards/             # dataset composition, license and limitations
│   ├── literature/             # linked paper notes and templates
│   ├── security/               # dated audit and residual risks
│   ├── figures/                # intentionally committed reference PNGs
│   └── results/                # committed reference JSON; local baselines/ ignored
├── data/                        # runtime data, contents ignored except .gitkeep
│   ├── raw/                    # downloaded MNIST and optional dataset links
│   ├── processed/              # derived arrays, metadata, scalers and manifests
│   ├── adversarial/            # reserved later-sprint outputs
│   └── external/               # optional third-party data
├── models/                      # ignored checkpoints/bundles, tracked .gitkeep only
└── notebooks/                   # reserved exploration directory; .gitkeep only
```

Each application/library component has a local README linked from the index.
The repository is **not installed as a Python package**. Run commands from the
root; direct script entry points bootstrap the root import path. Keep that small
bootstrap exception local to CLIs, not reusable modules. `setup_environment.py`
uses only the standard library so it can run before dependencies are installed.

## Ownership and where new work belongs

| Location | Owns | Does not own |
|---|---|---|
| `src/data/` | Reusable parsing, preprocessing, loaders, artifact integrity | Training/model choice or HTTP |
| `src/models/` | Architectures, shared experiment sampling, training, tuning, verified inference | Routes, browser UI or CLI parsing |
| `src/evaluation/` | Metrics, thresholds, bounded research-artifact readers | API transport or training orchestration |
| `src/utils/` | Small genuinely shared helpers such as seeding | A catch-all for domain logic |
| `api/` | HTTP routing, validation, authentication, middleware, static serving | Training or dataset processing |
| `dashboard/web/` | Primary browser UI, static assets and same-origin HTTP calls | Local model/array loading or a frontend build |
| `dashboard/app.py`, `client.py` | Legacy Streamlit views and HTTP client | Primary UI entry point |
| `scripts/` | Runnable operator tools and CLI orchestration | Shared library APIs; extract only demonstrated reuse |
| `tests/` | Flat `test_<area>.py`, synthetic fixtures and helpers | Runtime outputs or production logic |
| `docs/` | Guides, references, decisions and compact research evidence | Datasets, weights, secrets or local tracking stores |
| `data/`, `models/`, `mlruns/` | Ignored runtime artifacts | Source code or hand-maintained documentation |
| `notebooks/` | Optional exploration | Anything a supported workflow depends on |

- **Paths/defaults:** `src/config.py`; random seeding: `src/utils/seed.py`.
  Keep settings in the existing [configuration reference](configuration.md) and
  add safe placeholders to `.env.example` when applicable.
- **Tests:** add `tests/test_<area>.py`, not a parallel nested test hierarchy.
  Share synthetic data through `tests/data_fixtures.py`; write only to `tmp_path`.
- **Documentation:** operations in `development.md`, settings in
  `configuration.md`, verification in `testing.md`, data work in `docs/data/`,
  paper notes in `docs/literature/`, API contracts in `api/README.md`.
  Link new pages from the index or an already indexed guide.
- **Status vs evidence:** change [progress](progress.md) for status,
  [the plan](project_plan.md) only for deliberate scope/schedule changes,
  [decisions](DECISIONS.md) for rationale, and dated reports for measured results.

## Important root configuration

| File | Purpose |
|---|---|
| `Makefile` | Canonical commands; CI calls `lint`, `coverage`, `security`, `docker-scan` |
| `pyproject.toml` | Ruff lint/format, pytest discovery and line/branch coverage; no separate type checker |
| `requirements.txt` | Pinned non-torch runtime requirements; not a transitive lockfile |
| `requirements-dev.txt` | Runtime plus tests, formatting, hooks and security tooling |
| `requirements-torch.txt` | CPU-only wheels with the PyTorch index scoped to this file |
| `requirements-cleverhans.txt` | Optional isolated legacy cross-check; not default setup |
| `Dockerfile`, `docker-compose.yml` | Non-root app image; two same-app instances plus local MLflow |
| `.env.example` | Local settings template; `.env` and local `.env.*` remain ignored |
| `.gitignore`, `.dockerignore` | Separate version-control and container-build-context policies |
| `.gitattributes` | Text normalization and binary/runtime-data diff policy |
| `.pre-commit-config.yaml` | Existing Ruff and file-hygiene hooks |

Dependency-update automation is not configured: `.github/dependabot.yml` was
intentionally removed in `557b34b`. Dated reports mention its earlier presence;
do not assume automatic version-update PRs are currently enabled.

## Generated vs maintained

| Path | Producer / handling |
|---|---|
| `docs/results/art_quickstart_results.json`, `docs/figures/art_*.png` | `scripts/art_quickstart.py` / `make demo`; intentionally committed, never hand-edit |
| `docs/data/manifests/*.json` | Full default-output `scripts/preprocess.py` runs; intentionally committed |
| `docs/data/eda_report.md`, `docs/results/data_eda.json`, `docs/figures/data_*.png` | `scripts/eda_datasets.py` / `make eda`; intentionally committed |
| `docs/results/baseline_reference.json` | Compact measured Sprint 3 snapshot; preserve scores/provenance, see [handoff](team_handoff.md) |
| `docs/results/baselines/` | Ignored local Sprint 3 comparison JSON |
| `data/`, `models/`, `mlruns/`, `mlartifacts/` contents | Ignored runtime data/checkpoints/tracking; retain tracked directory placeholders |
| `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, coverage outputs | Local environment/tool artifacts, not source |

Everything else is maintained by developers, including the generator scripts.
The demo CLI has no output-redirection flag: use its isolated pytest smoke test
or Python `run_demo(output_dir=...)` for checks that must not replace evidence.
`make clean` removes caches **and `mlruns/`**; it is not a harmless validation step.

## Dependency and naming conventions

- `src/` must not import `api/`, `dashboard/`, `scripts/` or `tests/`.
  API/dashboard/CLI layers may import `src/`; API and dashboard communicate over
  HTTP, never mutual Python imports. Static asset serving is not a Python import.
- Share sampling through `src/models/sampling.py`, not private helpers in a
  sibling training pipeline. Keep integrity verification in `src/data/preprocessing.py`.
- Python modules use `snake_case`; tests use `test_<area>.py`. Preserve existing
  document names/URLs (including `project-structure.md`, uppercase READMEs,
  `DECISIONS.md` and historical `PR_sprint1.md`); new general docs use
  `lower_snake_case.md`. Avoid cosmetic renames of stable links.
- Ruff is the formatter (`line-length = 100`); use logging in library code.
  Python 3.11–3.12 and CPU-only operation remain required.
- [Contribution rules](../CONTRIBUTING.md) own branching/commits/PR review.
  `main` receives changes through PRs, not direct pushes.

## Deliberate exceptions and retained history

The legacy Streamlit UI still has documented commands and real process tests;
it is not unused code. `src/attacks/`, `src/defenses/` and `notebooks/` reserve
explicit plan boundaries; do not implement speculative abstractions to fill them.
Historical reports/PR snapshots remain evidence, not current setup manuals.
The original project-plan HTML export is available in Git history (`c8a9d0a`);
the maintained scope document is Markdown. Existing runtime bundle directories
do not prove that a qualifying freeze exists or that M1 passed.

The [repository audit](repository_audit.md) records cleanup evidence and retained
exceptions. Boundary, navigation and ignore-policy regression checks are part
of the normal pytest suite; see [testing](testing.md).
