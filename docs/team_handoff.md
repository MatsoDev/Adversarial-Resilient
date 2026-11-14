# Team handoff — recorded research results and current environment

## Sprint 5 on main

Sprint 5 was merged into `main` through [PR #19](https://github.com/MatsoDev/Adversarial-Resilient/pull/19).
From a clean checkout, on Windows:

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
python scripts/setup_environment.py
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Open <http://localhost:8000/dashboard/attacks.html>. The committed measured
reference includes 21 configurations and 21 completed CleverHans cross-checks;
viewing it requires no dataset, weights, optional CleverHans install or token.
It is explicitly a **development candidate, not frozen**, using 128 operating-
validation rows and an owner-authorized size-only probe. Full validation was
92.1778%, below the 93% gate. Prediction remains unavailable until M1 passes.

There are no new mandatory runtime dependencies. Git pull does not install
packages; the bootstrap above checks/synchronizes existing pins. For actual
retraining and attack reproduction, use [Sprint 4](sprint4.md) and
[Sprint 5](sprint5.md). Weights/datasets are not distributed in Git. GPU training
is optional and can reuse a trusted existing CUDA torch installation without
replacing the main environment. The experiment's runtime is recorded.

The remaining instructions cover environment setup and earlier recorded
baseline results, which remain available alongside the Sprint 5 explorer.

## Update your checkout and environment

Commit or stash your own local changes first, then from the repository root:

```powershell
git switch main
git pull --ff-only origin main
python scripts/setup_environment.py
```

Use Python **3.11 or 3.12** (`python3` on Linux/macOS if needed). The setup
command creates/reuses `.venv`, installs/synchronizes all runtime, developer
and CPU torch pins, verifies exact versions and runs `pip check`. Already
satisfied versions are reused. It may need internet for missing/changed
packages. Git pull updates source files; it does not execute installers.
No Git hooks or automatic downloads are installed by this command.

Handoff verification on 2026-11-06: full suite **275 passed, 3 opt-in skips**,
**89% total line/branch coverage**, lint/format and Bandit passed. Running
`setup_environment.py --check-only` confirmed every direct pin and `pip check`
on the installed project environment. GitHub CI is checked again before merge.

Verify an existing environment without installing anything:

```powershell
python scripts/setup_environment.py --check-only
```

## Open the HTML dashboard

Windows (no activation required):

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Linux/macOS:

```bash
.venv/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Open <http://localhost:8000/dashboard/>. FastAPI serves the HTML/CSS/JavaScript
and same-origin research API; no Streamlit or frontend build is required.

The checked-in `docs/results/baseline_reference.json` is the compact output of
the measured four-model experiment, not a synthetic demo. A fresh checkout
displays these recorded validation results immediately, plus committed EDA,
dataset cards and methodology. Results carry their original timestamp,
manifest hash, training/validation counts and subset label. Locally generated
runs are also shown; a duplicated reference run is displayed once.

## What stays local

Raw EMBER files, processed arrays, trained model weights, scalers, `.env` and
MLflow tracking are not included in Git. The reference results let everyone
inspect the UI; they do not install models or enable file scanning.

To reproduce training, follow [sprint3.md](sprint3.md): obtain/verify EMBER2018
v2, preprocess, verify artifacts, then run:

```powershell
.\.venv\Scripts\python.exe scripts/train_baselines.py --dataset ember2018 --max-train 10000 --max-val 90000 --threads 2
```

Budget about 25 GB of disk for archive/extraction/processing. The completed
run used 10,000 training rows and 90,000 validation rows. Official test-set
evaluation, tuning/freezing `baseline_v1` and gated feature prediction are
implemented in Sprint 4; see [the protocol](sprint4.md) and
[current M1 status](progress.md). The recorded Sprint 3 runs are still
validation-only and do not enable prediction. No application database is required.

The local MLflow IDs in the recorded snapshot refer to the original machine;
each teammate generates their own tracking store when reproducing training.
See [sprint3_report.md](sprint3_report.md) for exact results and limitations.
