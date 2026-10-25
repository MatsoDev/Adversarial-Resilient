# Documentation index

Start here. The root [`README.md`](../README.md) explains what the project is
and how to get it running; this page is the map to everything else.

## Getting oriented

| Document | What it covers |
|---|---|
| [`../README.md`](../README.md) | Project overview, current status, quick start, command summary |
| [`../AGENTS.md`](../AGENTS.md) | Short navigation map for AI coding agents and new contributors |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | Branching, commit style, PR checklist, code style |
| [`development.md`](development.md) | Setup, verification, ART demo, API/dashboard, Docker, troubleshooting |
| [`configuration.md`](configuration.md) | Environment variables, dataset resolution, Compose ports, paths/seeds |
| [`testing.md`](testing.md) | Test layout, commands, synthetic fixtures, optional real-data checks |
| [`progress.md`](progress.md) | Where are we now: sprint/milestone status, current checklist |

## Architecture and structure

| Document | What it covers |
|---|---|
| [`architecture.md`](architecture.md) | Components, entry points, dependency rules, data flows, constraints |
| [`project-structure.md`](project-structure.md) | Directory responsibilities, where new code/tests/docs belong, conventions |
| [`../api/README.md`](../api/README.md) | FastAPI endpoints, responses, run commands, OpenAPI URLs |
| [`../dashboard/README.md`](../dashboard/README.md) | Streamlit page, `API_URL`, run command |
| [`../src/data/README.md`](../src/data/README.md) | Data layer APIs: preprocessing entry points and loaders |
| [`../src/models/README.md`](../src/models/README.md) | Current model classes and planned baseline work |
| [`../src/attacks/README.md`](../src/attacks/README.md) | Planned FGSM/PGD/CW wrappers (placeholder) |
| [`../src/defenses/README.md`](../src/defenses/README.md) | Planned hardening methods (placeholder) |
| [`../src/evaluation/README.md`](../src/evaluation/README.md) | Planned metrics and plots (placeholder) |

## Data

| Document | What it covers |
|---|---|
| [`data/README.md`](data/README.md) | Dataset locations, preprocessing/EDA commands, outputs, and loaders |
| [`data/ember_feature_layout.md`](data/ember_feature_layout.md) | EMBER2018 v2 2381-dim group offsets and processing semantics |
| [`data/eda_report.md`](data/eda_report.md) | Generated EDA report for both datasets (do not hand-edit) |
| [`data/manifests/ember2018.json`](data/manifests/ember2018.json) | Full-run EMBER manifest: sources, counts, splits, artifact hashes |
| [`data/manifests/cicids2017.json`](data/manifests/cicids2017.json) | Full-run CICIDS manifest: cleaning, dedup, splits, artifact hashes |
| [`data_cards/ember2018.md`](data_cards/ember2018.md) | EMBER datasheet: composition, license, biases, safety |
| [`data_cards/cicids2017.md`](data_cards/cicids2017.md) | CICIDS datasheet: composition, license, known flaws, safety |

## Security research

| Document | What it covers |
|---|---|
| [`threat_model_v0.1.md`](threat_model_v0.1.md) | Assets, attacker goals/knowledge, scope, metrics (draft for review) |
| [`security/SECURITY_AUDIT.md`](security/SECURITY_AUDIT.md) | Application security audit: findings, fixes, verification, residual risks |
| [`reading_list.md`](reading_list.md) | Papers and why they matter to the project |
| [`literature/README.md`](literature/README.md) | Literature notes and note templates (malware + network tracks) |

## Project process and history

| Document | What it covers |
|---|---|
| [`project_plan.md`](project_plan.md) | Canonical project plan: scope, sprints, milestones, risks (baseline) |
| [`DECISIONS.md`](DECISIONS.md) | Log of non-obvious technical decisions, sprint by sprint |
| [`sprint1_report.md`](sprint1_report.md) | Sprint 1 report: what was done, run, measured, not verified |
| [`sprint2_report.md`](sprint2_report.md) | Sprint 2 report: data pipeline commands, counts, EDA, limitations |
| [`PR_sprint1.md`](PR_sprint1.md) | Snapshot of the Sprint 1 pull request description (historical) |

## Generated artifacts (do not edit by hand)

These are committed on purpose so results are visible without running anything:

| Path | Produced by |
|---|---|
| [`results/art_quickstart_results.json`](results/art_quickstart_results.json) | `scripts/art_quickstart.py` (`make demo`) |
| [`figures/art_samples.png`](figures/art_samples.png) | original vs FGSM vs PGD grid |
| [`figures/art_accuracy_vs_eps.png`](figures/art_accuracy_vs_eps.png) | accuracy-vs-epsilon curves |
| [`results/data_eda.json`](results/data_eda.json) | `scripts/eda_datasets.py` (`make eda`) |
| [`figures/data_*.png`](figures/) | EDA plots |
| [`data/eda_report.md`](data/eda_report.md) | generated EDA report |
| [`data/manifests/`](data/manifests/) | compact manifests from full `scripts/preprocess.py` runs |

To regenerate, run the corresponding command (see
[`development.md`](development.md) and [`data/README.md`](data/README.md)).
`mlruns/`, `data/raw/`, `data/processed/`, and `models/` are generated at
runtime but are gitignored, not committed.
