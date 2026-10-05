# Sprint 1 report — foundations (Weeks 1–2)

Branch: `sprint1/foundations`. Remote was empty; started from scratch.
Env: Windows, Python 3.12.1 (`C:\Python312\python.exe`), `.venv` in repo root.
CI canonical Python is 3.11 (see `ci.yml`); pins verified on 3.12.1 here.

## What was done
- Skeleton per spec (README, CONTRIBUTING, LICENSE MIT, .gitignore/.gitattributes,
  .env.example, pyproject ruff+pytest, requirements.txt + -dev + -cleverhans,
  Makefile, pre-commit, data/models/notebooks .gitkeep, src/* placeholders,
  api `/health`, dashboard placeholder, Dockerfile + compose, CI, docs).
- Pinned CPU env: `torch==2.4.1+cpu`, `torchvision==0.19.1+cpu`,
  `numpy==1.26.4`, `adversarial-robustness-toolbox==1.18.1`, `mlflow==2.15.1`,
  `setuptools==75.8.0` (see Known issues), plus fastapi/uvicorn/streamlit.
- `src/config.py` (paths + `ensure_dirs()`), `src/utils/seed.py` (`set_seed()`),
  `src/models/baseline_mlp.py` (`BaselineMLP`, `SmallCNN`).
- `scripts/art_quickstart.py`: MNIST via torchvision to `data/raw/`, SmallCNN,
  ART `PyTorchClassifier` + FGSM/PGD/CW-L2, eps table/plots, JSON + MLflow,
  `--fast/--epochs/--eps/--seed/--cleverhans/--synthetic/--cw-samples`.
- Tests: `test_seed`, `test_config`, `test_art_quickstart_smoke` (synthetic, <60s).
- Docs: threat_model_v0.1 (STRIDE/attacker-centric, ATLAS/OWASP marked TODO),
  reading_list (7 items, no fake URLs), 2 literature templates, DECISIONS, this report.

## What was run (trimmed outputs)
- `python -m venv .venv && .venv\Scripts\pip install -r requirements.txt -r requirements-dev.txt`
  → Success (torch 201 MB CPU wheel). See DECISIONS for setuptools fix.
- `python -m ruff check src scripts tests api dashboard` → `All checks passed!`
- `python -m pytest -q` → `4 passed` (warnings only: matplotlib pyparsing,
  mlflow pkg_resources/pydantic deprecation).
- `python scripts/art_quickstart.py --fast --seed 42` → OK (MNIST download from
  `ossci-datasets`, train 5000 subset ×2 epochs, FGSM/PGD on 1000, CW on 20,
  eps grid 6 values). Wrote `docs/results/art_quickstart_results.json`,
  `docs/figures/art_samples.png`, `art_accuracy_vs_eps.png`, `mlruns/`.
- `python -c "from api.main import health; print(health())"` → `{'status': 'ok'}`
- `python -c "yaml.safe_load(open('docker-compose.yml'))"` → services
  `['api', 'dashboard', 'mlflow']`, `compose YAML ok`.
- `python scripts/art_quickstart.py --synthetic --epochs 1 --cleverhans`
  → `CleverHans not available, skipping: No module named 'cleverhans'` (graceful).

## Real results (art_quickstart, --fast, seed 42, eps 0.3)
- Clean test accuracy (10k): **0.92** (subset clean: 0.909 FGSM/PGD, 0.95 CW-20).
- FGSM (n=1000, eps=0.3): adv_acc **0.066**, ASR **0.934**,
  mean L2 **6.446**, mean Linf **0.300**.
- PGD (n=1000, eps=0.3, eps_step=0.1, max_iter=10): adv_acc **0.045**,
  ASR **0.955**, mean L2 **5.790**, mean Linf **0.300**.
- CW-L2 (n=20, confidence=0.0, max_iter=10): adv_acc **0.25**, ASR **0.75**,
  mean L2 **1.785**, mean Linf **0.505**, subset clean **0.95**.
- Accuracy vs eps (adv acc):
  eps 0.0: FGSM 0.909 / PGD 0.909; 0.05: 0.875/0.874; 0.10: 0.741/0.714;
  0.15: 0.538/0.412; 0.20: 0.308/0.143; 0.30: 0.066/0.046.
- Full-data check (60k, 3 epochs, --cw-samples 20, partial — eps grid timed out
  after 10 min): clean **0.9880** (>95% target met), FGSM adv **0.127** ASR 0.873,
  PGD adv **0.012** ASR 0.988, CW adv **0.05** ASR 0.95. Logs only; JSON still
  holds the --fast run (official `make demo` output).

## Not verified
- Docker: no daemon on this machine (`Get-Command docker` empty). Files written,
  YAML parsed via PyYAML, `api.health()` returns ok, but `docker build` /
  `docker compose up` NOT run.
- `make` targets: no `make` on Windows; Makefile present, but verified via
  direct `python -m ...` equivalents (see above). CI runs `ruff` + `pytest` +
  `docker build` on ubuntu.
- CleverHans full cross-check: library not installed (isolated on purpose);
  only graceful-skip path verified.
- EMBER / CIC-IDS-2017 download, EDA, preprocessing: Sprint 2.

## Known issues
- `mlflow==2.15.1` imports `pkg_resources`; `setuptools>=81` removed it.
  Pinned `setuptools==75.8.0` in requirements.txt. Verified.
- `set_seed()` called `torch.set_num_interop_threads(1)` twice → RuntimeError
  in tests; now wrapped in try/except RuntimeError.
- MNIST canonical `yann.lecun.com` URLs 404; torchvision falls back to
  `ossci-datasets` automatically (observed in logs, no action needed).
- `--fast` took ~4–5 min here (not <2 min) due to PGD×1000 + CW×20 + 6-eps grid
  on CPU. Acceptable for `make demo`; use `--synthetic` for <60s smoke.
- Smoke test overwrites `docs/results/*.json` + figures with synthetic data;
  re-ran `--fast` afterwards to restore real outputs.

## Suggested Sprint 2 tasks
1. EMBER + CIC-IDS-2017 download + SHA verify + license notes (`src/data/`).
2. EDA notebooks (class balance, feature stats, missing values).
3. Preprocessing pipeline (scaling, splits, `processed/` + tests).
4. Tabular baselines (LightGBM/MLP) + clean metrics before attacks.
5. Fix smoke-test artifact overwrite (write synthetic to temp dir).
