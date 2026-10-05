# Adversarial-Resilient Security Models

Machine-learning detectors for malware and network intrusion, attacked with
adversarial examples (FGSM, PGD, Carlini-Wagner) and then hardened with
adversarial training, distillation, ensembles, input sanitization, and detectors.
The MNIST demo in this repo is only an environment check that proves the attack
tooling works — it is not the project's security result.

## Current status

Works today:

- ART demo on MNIST with FGSM, PGD, and CW-L2 (`scripts/art_quickstart.py`),
  including accuracy-vs-epsilon plots, a JSON report, and local MLflow logging.
- Test suite (`pytest`) and lint (`ruff`).
- FastAPI service with `GET /health` returning `{"status": "ok"}`.
- Streamlit dashboard page (early placeholder that can ping the API).
- `Dockerfile` and `docker-compose.yml` for api, dashboard, and mlflow services.

Next:

- Real datasets (EMBER for malware, CIC-IDS-2017 for network traffic).
- Baseline detectors and their clean-accuracy benchmarks.
- FGSM/PGD/CW attacks against the real detectors.
- Defenses (adversarial training, distillation, ensembles, sanitization, detector).
- A real dashboard with robustness charts.

Honestly not verified: Docker images were never built or run here (no Docker
daemon on this machine), and the CleverHans cross-check was only tested as a
graceful skip (library not installed). See the troubleshooting section for why
CleverHans is optional.

## Prerequisites

- Git.
- Python 3.10 or 3.11. Tested with Python 3.12.1 on Windows and Python 3.11 in
  CI; the pins in `requirements.txt` support 3.10–3.12.
- About 3 GB free disk (PyTorch CPU wheel plus dependencies and the MNIST
  download).
- Internet access for the first install and the MNIST download.
- Docker (optional, only for the container option).

Check your versions:

```bash
python --version
git --version
```

## Setup

### Windows (PowerShell)

```powershell
git clone https://github.com/MatsoDev/Adversarial-Resilient.git
cd Adversarial-Resilient
git checkout sprint1/foundations
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```

(The `git checkout` line is needed until the open pull request is merged;
after that, `main` will contain everything.)

If activation is blocked with an "execution of scripts is disabled" error, run
this once, then retry activation:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Linux / macOS

```bash
git clone https://github.com/MatsoDev/Adversarial-Resilient.git
cd Adversarial-Resilient
git checkout sprint1/foundations
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```

Shortcut on Linux/macOS (requires `make`):

```bash
make setup
```

## Verify the install

```bash
python -m ruff check src scripts tests api dashboard
```

Expected output:

```text
All checks passed!
```

```bash
python -m pytest
```

Expected output (takes about 40 seconds, uses tiny synthetic data):

```text
4 passed in ...
```

Note: the test suite runs the demo pipeline on synthetic data and overwrites
`docs/results/art_quickstart_results.json` and `docs/figures/`. Running the
real demo below restores the real outputs.

## Run the ART demo

Fast version first (recommended). After the one-time MNIST download
(about 60 MB into `data/raw/`), it takes roughly 3–5 minutes on a CPU laptop:

```bash
python scripts/art_quickstart.py --fast
```

What to expect: clean test accuracy around 0.92 on the subset, FGSM and PGD
adversarial accuracy near 0.05 at epsilon 0.3, and CW-L2 evaluated on
20 samples. Your exact numbers will differ slightly by machine.

Full version (trains on all of MNIST for 3 epochs, CW on 200 samples;
takes 10 minutes or more on CPU):

```bash
python scripts/art_quickstart.py --epochs 3
```

What to expect: clean accuracy around 0.99. The accuracy-vs-epsilon grid is
the slowest part; a `--cw-samples 20` flag keeps CW tractable.

Flags:

- `--fast`: small training subset (5000) and small CW sample (20).
- `--epochs N`: training epochs (default 2 with `--fast`, else 3).
- `--eps E`: epsilon for FGSM/PGD (default 0.3).
- `--seed N`: random seed (default 42).
- `--cw-samples N`: override the CW evaluation sample count.
- `--synthetic`: tiny random data, no download (used by the tests).
- `--cleverhans`: optional CleverHans FGSM/PGD cross-check; skips gracefully
  with a warning if CleverHans is not installed.

Outputs:

- `docs/results/art_quickstart_results.json`: clean/adversarial accuracy,
  attack success rate, mean L2/Linf perturbation, and the epsilon table.
- `docs/figures/art_samples.png`: original vs FGSM vs PGD image grid.
- `docs/figures/art_accuracy_vs_eps.png`: accuracy-vs-epsilon curves.
- `mlruns/`: local MLflow tracking data (gitignored).

Browse the logged run:

```bash
python -m mlflow ui
```

Then open http://127.0.0.1:5000 in your browser.

## Run the API and dashboard

Without Docker (with the virtual environment activated):

```bash
python -m uvicorn api.main:app --reload --port 8000
```

Open http://127.0.0.1:8000/health — expect `{"status": "ok"}`.

In a second terminal (same folder, venv activated):

```bash
streamlit run dashboard/app.py
```

Open http://localhost:8501 — expect the placeholder page with a button that
calls the API `/health`.

With Docker (not tested here — there was no Docker daemon on this machine):

```bash
docker compose up --build
```

Ports come from `.env` (defaults: api 8000, dashboard 8501, mlflow 5000).
Stop with `Ctrl+C`, then `docker compose down`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `python --version` shows 3.9 or older, or install fails on your Python | Install Python 3.10 or 3.11 (3.12 also worked here); CI uses 3.11. Then recreate `.venv` from scratch. |
| `ModuleNotFoundError: No module named 'pkg_resources'` when importing mlflow | Your setuptools is too new. `requirements.txt` already pins `setuptools==75.8.0`; if you still see it, run `pip install "setuptools==75.8.0"`. |
| `ruff` or `pytest` not found | The venv is not activated, or dev requirements are missing. Activate `.venv` and run `pip install -r requirements-dev.txt`. |
| torch download is very slow or fails | The CPU wheel is about 200 MB. Check disk space and connection, then rerun the same `pip install` command; pip resumes. |
| PowerShell refuses to activate the venv | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`, then activate again. |
| `python -m uvicorn ...` says address already in use | Port 8000 is taken. Use another port, e.g. `--port 8001`, and open that URL instead. Same for Streamlit (`--server.port 8502`). |
| MNIST download shows `HTTP Error 404` for `yann.lecun.com` | Expected: torchvision automatically retries its mirror and continues. No action needed. |
| `--cleverhans` prints `CleverHans not available, skipping` | Expected: CleverHans lives in the separate `requirements-cleverhans.txt` because version 4.0.0 conflicts with the ART/torch stack. Only install it in an isolated env if you need the cross-check. |
| `git clone` fails on Windows with filename-too-long errors | Enable long paths once: `git config --system core.longpaths true` (needs an elevated prompt), then clone again. |

## Project structure

```text
api/            FastAPI service (/health today)
dashboard/      Streamlit app (early page today)
data/           raw/, processed/, adversarial/ runtime data (gitignored, .gitkeep only)
docs/           threat model, reading list, literature templates, decisions, reports
docs/figures/   demo plots (generated)
docs/results/   demo JSON report (generated)
models/         trained weights (gitignored, .gitkeep only)
notebooks/      exploratory notebooks (later)
scripts/        art_quickstart.py demo
src/            config.py paths/seeds, utils/, data/, models/, attacks/, defenses/, evaluation/
tests/          seed, config, and smoke tests
```

## Working with Git

- Branch names: `feat/<topic>`, `fix/<topic>`, `docs/<topic>` (or `sprint<N>/<topic>`).
- Commits use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `test:`, `ci:`.
- Open a pull request into `main`; never push directly to `main`.
- Never commit datasets, model weights, `.env`, or `mlruns/`. Check `git status`
  before every commit.

## Data policy

Datasets and model weights are not in this repo. When the real datasets arrive,
raw downloads go in `data/raw/`, cleaned splits in `data/processed/`,
generated adversarial sets in `data/adversarial/`, and checkpoints in `models/`.
Download and verification instructions will be added alongside the loading code.

## Roadmap

Semester 1:

- Foundations: environment, ART demo on MNIST, threat model draft.
- Data: EMBER and CIC-IDS-2017 download, EDA, preprocessing pipeline.
- Attacks: FGSM, PGD, and CW against the real detectors.
- Defenses: adversarial training, distillation, ensembles, sanitization, detector.

Semester 2:

- Backend: FastAPI prediction, attack, and defense endpoints.
- Frontend: dashboard with robustness charts and MLflow links.
- Hardening: containers, CI checks, and the final evaluation.

## Safety and ethics

Defensive research only. This repo works with public feature datasets and the
MNIST demo images — no malware samples and no weaponized tooling are included
or accepted here.
