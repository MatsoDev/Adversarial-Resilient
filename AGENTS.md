# AGENTS.md — repository map

Adversarial-Resilient Security Models: ML malware/network detectors attacked
with adversarial examples (FGSM/PGD/CW) and hardened with defenses. Current
state (Sprint 1): pinned CPU environment, ART demo on MNIST, FastAPI
`/health`, Streamlit placeholder, Docker stack, CI. Real datasets, baselines,
attacks, and defenses land in later sprints.

## Read first

1. [`README.md`](README.md) — setup, verification, demo, troubleshooting.
2. [`docs/README.md`](docs/README.md) — documentation index.
3. [`docs/architecture.md`](docs/architecture.md) — components, dependency
   rules, data flows, constraints.
4. [`docs/project-structure.md`](docs/project-structure.md) — directory
   responsibilities, "where do I put ...?", conventions.
5. [`docs/DECISIONS.md`](docs/DECISIONS.md) — why non-obvious choices were
   made; check before re-litigating them.
6. [`docs/project_plan.md`](docs/project_plan.md) — scope/schedule baseline;
   [`docs/progress.md`](docs/progress.md) — current sprint status and
   checklist. Update `progress.md` when status changes, not the plan.

## Commands (run from the repo root)

```bash
make setup              # create .venv, install deps, install pre-commit hooks
make lint               # ruff check src scripts tests api dashboard
make test               # pytest (6 tests, ~40 s; smoke test is synthetic)
make demo               # scripts/art_quickstart.py --fast (real MNIST, minutes)
python scripts/art_quickstart.py --synthetic   # fast demo pipeline check
python -m uvicorn api.main:app --port 8000     # API
streamlit run dashboard/app.py                 # dashboard
docker compose up --build                      # api + dashboard + mlflow (.env first)
```

CI (`.github/workflows/ci.yml`) runs `ruff check` and `pytest` on Python 3.11
plus `docker build`; keep both green.

## Architectural rules (do not violate)

- **Dependency direction:** `api/`, `dashboard/`, `scripts/`, `tests/` may
  import `src/`; `src/` must never import them. `api/` and `dashboard/` do not
  import each other (HTTP only).
- **Paths/constants** come from `src/config.py`; **seeds** from
  `src/utils/seed.py`. Do not hard-code relative paths in modules.
- **New reusable code** → `src/<concern>/` (`data`, `models`, `attacks`,
  `defenses`, `evaluation`, `utils`). **New runnable demos** → `scripts/`.
  **New tests** → `tests/test_<area>.py` (flat), use `tmp_path` for outputs.
- Stay within the sprint scope: do not implement speculative abstractions in
  placeholder packages.

## Hard constraints

- **Python 3.10–3.12 only** (CI: 3.11); CPU-only, no CUDA assumptions.
- **Never commit** datasets, model weights, `.env`, or `mlruns/`; check
  `git status` before committing.
- **Generated files — never hand-edit:** `docs/results/art_quickstart_results.json`
  and `docs/figures/art_*.png` are produced by `scripts/art_quickstart.py`
  (`make demo`), then intentionally committed. Regenerate, don't edit.
- **Tests must not write into `docs/`**: pass `output_dir` to
  `run_demo()` (see `tests/test_art_quickstart_smoke.py`).
- **Style:** ruff (`line-length = 100`), `ruff format`, logging instead of
  print in library code; Windows/Linux/macOS compatible paths.
- **Git:** Conventional Commits; branch naming and PR rules in
  [`CONTRIBUTING.md`](CONTRIBUTING.md). Never push to `main` directly.
- **Safety:** defensive research only — no live malware, no weaponized
  tooling, public feature datasets only (see
  [`docs/threat_model_v0.1.md`](docs/threat_model_v0.1.md)).

## Environment quirk

`mlflow==2.15.1` needs `pkg_resources`, so `setuptools` is pinned to `75.8.0`
in `requirements.txt`. Do not "modernize" the pin without verifying MLflow
still imports. CleverHans is deliberately isolated in
`requirements-cleverhans.txt`.
