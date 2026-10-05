# Adversarial-Resilient Security Models

Defensive research: build ML malware (EMBER, primary) + NIDS (CIC-IDS-2017,
secondary) detectors, attack them with FGSM / PGD / Carlini-Wagner (IBM ART +
CleverHans), then harden via adversarial training, distillation, ensembles,
input sanitization, and an adversarial detector.

Pipeline: `data → models → attacks → defenses → evaluation → api/dashboard`.

## Quick start (5 commands)

```bash
git checkout sprint1/foundations
make setup
make lint
make test
make demo
```

Windows (no `make`): `python -m venv .venv`, `.venv\\Scripts\\pip install -r requirements.txt -r requirements-dev.txt`, `python -m ruff check src scripts tests api dashboard`, `python -m pytest -q`, `python scripts/art_quickstart.py --fast`.

## Repo map
- `src/config.py`, `src/utils/seed.py` — paths, seeds.
- `src/data/`, `src/models/`, `src/attacks/`, `src/defenses/`, `src/evaluation/` — placeholders (see each README; sprints 2–4 fill them).
- `scripts/art_quickstart.py` — MNIST FGSM/PGD/CW demo (template for Phase 1).
- `api/main.py` (`/health`), `dashboard/app.py` — Semester 2 placeholders.
- `data/raw|processed|adversarial/`, `models/`, `mlruns/` — gitignored runtime dirs.
- `docs/` — threat model, reading list, literature templates, DECISIONS, sprint report.

## Roles
| Member | Focus |
|---|---|
| AI engineer | models, ART/CleverHans harness, hardening |
| Data scientist | EDA, preprocessing, metrics |
| CS ×2 | FastAPI, dashboard, Docker, CI |
| Security ×5 | threat model, literature notes, red-team eval |

## Roadmap
### Semester 1
- Sprint 1 (W1–2): foundations (this branch) — env, ART demo, threat model v0.1.
- Sprint 2: EMBER + CIC-IDS-2017 download, EDA, preprocessing pipeline.
- Sprint 3: FGSM/PGD/CW on real detectors (feature- + problem-space).
- Sprint 4: hardening + detector + robustness report.
### Semester 2
- FastAPI (`/predict`, `/attack`, `/defend`), dashboard, Docker hardening, final eval.

## ART demo
`python scripts/art_quickstart.py --fast` trains SmallCNN on MNIST (CPU),
runs FGSM/PGD/CW via ART, writes `docs/figures/*.png` +
`docs/results/art_quickstart_results.json`, logs to `mlruns/`.
`--cleverhans` adds a lazy FGSM/PGD cross-check (skips if not installed).

## Contributing
See `CONTRIBUTING.md`. Conventional Commits; `docs/DECISIONS.md` for non-obvious choices.
Defensive only — no real malware or weaponized tooling.
