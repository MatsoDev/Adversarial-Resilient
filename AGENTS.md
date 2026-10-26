# AGENTS.md — repository map

Adversarial-Resilient Security Models: ML malware/network detectors attacked
with adversarial examples (FGSM/PGD/CW) and hardened with defenses. Current
state (Sprint 2 complete): pinned CPU environment, ART demo on MNIST, FastAPI
`/health`, Streamlit placeholder, Docker stack, CI, plus cleaned/versioned
EMBER2018 + CIC-IDS-2017 datasets, reusable loaders, EDA, and manifests.
Baselines, attacks, and defenses land in later sprints.

## Read first

1. [`README.md`](README.md) — overview, status, quick start.
2. [`docs/README.md`](docs/README.md) — documentation index.
3. [`docs/development.md`](docs/development.md) — setup, verification, demo,
   services, troubleshooting.
4. [`docs/configuration.md`](docs/configuration.md) — environment variables,
   dataset resolution, Compose ports.
5. [`docs/testing.md`](docs/testing.md) — test layout, conventions, optional
   real-data checks.
6. [`docs/project-structure.md`](docs/project-structure.md) — directory
   responsibilities, "where do I put ...?", conventions.
7. [`docs/architecture.md`](docs/architecture.md) — components, dependency
   rules, data flows, constraints.
8. [`docs/data/README.md`](docs/data/README.md) — dataset locations,
   preprocessing/EDA commands, loaders.
9. [`docs/DECISIONS.md`](docs/DECISIONS.md) — why non-obvious choices were
   made; check before re-litigating them.
10. [`docs/project_plan.md`](docs/project_plan.md) — scope/schedule baseline;
    [`docs/progress.md`](docs/progress.md) — current sprint status and
    checklist. Update `progress.md` when status changes, not the plan.
11. [`docs/security/SECURITY_AUDIT.md`](docs/security/SECURITY_AUDIT.md) —
    security baseline, fixed findings, verification, and residual risks.

## Commands (run from the repo root)

```bash
make setup              # create .venv, install deps, install pre-commit hooks
make lint               # ruff check + ruff format --check (mirrors CI)
make test               # pytest (synthetic fixtures; no datasets needed)
make coverage           # pytest + line/branch coverage (CI runs this)
make check              # lint + test
make security           # pip-audit + bandit (also a CI job)
make docker-build docker-scan  # build + Trivy scan of fixed HIGH/CRITICAL
make format             # rewrite files with ruff format
make demo               # scripts/art_quickstart.py --fast (real MNIST, minutes)
python scripts/art_quickstart.py --synthetic   # fast demo pipeline check
make data               # full EMBER + CICIDS preprocessing (needs local raw data)
make data-smoke         # deterministic 2000-row subset into /tmp
make eda                # regenerate docs/results/data_eda.json + figures/report
python scripts/preprocess.py --dataset all --verify-only
python -m uvicorn api.main:app --port 8000     # API (blocking; terminal 1)
python -m streamlit run dashboard/app.py       # dashboard (separate terminal 2)
docker compose up --build                      # api + dashboard + mlflow (.env first)
```

CI (`.github/workflows/ci.yml`) runs `make lint`, `make coverage`, `make security`
on Python 3.11, plus `docker build`; keep all green. `make lint` includes
formatting, so run it before every commit.

## Architectural rules (do not violate)

- **Dependency direction:** `api/`, `dashboard/`, `scripts/`, `tests/` may
  import `src/`; `src/` must never import them. `api/` and `dashboard/` do not
  import each other (HTTP only).
- **Paths/constants** come from `src/config.py`; **seeds** from
  `src/utils/seed.py`. Do not hard-code relative paths in modules.
- **New reusable code** → `src/<concern>/` (`data`, `models`, `attacks`,
  `defenses`, `evaluation`, `utils`). **New runnable demos** → `scripts/`.
  **New tests** → `tests/test_<area>.py` (flat), use `tmp_path` for outputs.
- **Docs** → `docs/`; link new documents from `docs/README.md`. Relative
  Markdown links are checked by `tests/test_docs_links.py`, so update links
  when moving files.
- Stay within the sprint scope: do not implement speculative abstractions in
  placeholder packages.

## Hard constraints

- **Python 3.11–3.12 only** (CI: 3.11); CPU-only, no CUDA assumptions.
- **Never commit** datasets, model weights, `.env`, or `mlruns/`; check
  `git status` before committing.
- **Generated files — never hand-edit:** `docs/results/art_quickstart_results.json`
  and `docs/figures/art_*.png` are produced by `scripts/art_quickstart.py`
  (`make demo`). `docs/results/data_eda.json`, `docs/figures/data_*.png`,
  `docs/data/eda_report.md`, and `docs/data/manifests/*.json` are produced by
  `scripts/eda_datasets.py` / full `scripts/preprocess.py` runs. All are
  intentionally committed; regenerate, don't edit.
- **Tests must not write into `docs/`**: pass `output_dir` to
  `run_demo()`, `--output-dir` to the data CLIs, and use synthetic fixtures.
  Real-data tests are skipped unless `RUN_REAL_DATA_TESTS=1`.
- **Style:** ruff (`line-length = 100`), `ruff format`, logging instead of
  print in library code; Windows/Linux/macOS compatible paths.
- **Git:** Conventional Commits; branch naming and PR rules in
  [`CONTRIBUTING.md`](CONTRIBUTING.md). Never push to `main` directly.
- **Data:** raw datasets are read in place (CLI `--source` > `EMBER_DATA_DIR` /
  `CICIDS_DATA_DIR` > `data/raw/<name>` > `~/Documents/<name>`); never copy or
  commit them. Versioning is manifest-based (SHA-256/counts/config), not
  DVC/LFS. See [`docs/data/README.md`](docs/data/README.md),
  [`docs/data/ember_feature_layout.md`](docs/data/ember_feature_layout.md), and
  [`docs/data_cards/`](docs/data_cards/).
- **Safety:** defensive research only — no live malware, no weaponized
  tooling, public feature datasets only (see
  [`docs/threat_model_v0.1.md`](docs/threat_model_v0.1.md)).

## Environment quirks

- CPU torch/torchvision wheels are installed from `requirements-torch.txt`;
  the PyTorch index is scoped there so normal PyPI packages cannot be
  shadowed. Install runtime/dev requirements first, then that file.
- `mlflow==3.17.2` keeps the local `mlruns/` file store behind an explicit
  opt-in (`MLFLOW_ALLOW_FILE_STORE=true`); the demo and Compose set it.
- CleverHans is deliberately isolated in `requirements-cleverhans.txt`.
- Compose binds published ports to `127.0.0.1` by default; do not set
  `BIND_ADDR=0.0.0.0` without TLS/authentication in front of MLflow and the
  dashboard (they have no built-in auth).
