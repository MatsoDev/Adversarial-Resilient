# PR: sprint1/foundations → main

## What
Sprint 1 foundations: repo skeleton, pinned CPU env (torch 2.4.1, ART 1.18.1,
numpy 1.26.4, setuptools 75.8.0), `src/config` + `set_seed` + BaselineMLP/SmallCNN,
ART MNIST demo (FGSM/PGD/CW-L2 + eps plots + JSON + MLflow), Docker placeholders
(api/health, dashboard, mlflow), CI (ruff + pytest + docker build), docs
(threat_model v0.1, reading_list, 2 literature templates, DECISIONS, sprint1_report).

## Why
Semester 1 Weeks 1–2 deliverable; unblocks Sprint 2 (EMBER/CIC-IDS-2017 EDA).

## Verification (real runs, Windows, Python 3.12.1)
- `python -m ruff check src scripts tests api dashboard` → All checks passed!
- `python -m pytest -q` → 4 passed.
- `python scripts/art_quickstart.py --fast --seed 42` → clean 0.92, FGSM adv
  0.066 ASR 0.934, PGD adv 0.045 ASR 0.955, CW adv 0.25 ASR 0.75; figures + JSON + mlruns written.
- Full 60k×3 epochs (partial, eps grid timed out): clean 0.9880, FGSM 0.127,
  PGD 0.012, CW 0.05 — see sprint1_report.
- `health()` → `{'status': 'ok'}`; compose YAML parses (api/dashboard/mlflow).
- `--cleverhans` → graceful skip (not installed, isolated by design).

## Not verified
Docker build/up (no daemon), `make` binary (used `python -m` equivalents),
CleverHans full install, EMBER/CIC data (Sprint 2).

## Checklist
- [x] Conventional Commits (to be applied on squash/merge)
- [x] No datasets/weights/.env/mlruns committed (`data/raw`, `mlruns` gitignored)
- [x] Docs updated
