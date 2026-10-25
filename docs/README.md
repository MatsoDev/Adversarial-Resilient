# Documentation index

Start here. The root [`README.md`](../README.md) explains what the project is
and how to get it running; this page is the map to everything else.

## Getting oriented

| Document | What it covers |
|---|---|
| [`../README.md`](../README.md) | Project overview, setup, verification, ART demo, API/dashboard, troubleshooting |
| [`../AGENTS.md`](../AGENTS.md) | Short navigation map for AI coding agents and new contributors |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | Branching, commit style, PR checklist, code style |
| [`progress.md`](progress.md) | Where are we now: sprint/milestone status, current checklist |

## Architecture and structure

| Document | What it covers |
|---|---|
| [`architecture.md`](architecture.md) | Components, entry points, dependency rules, data flows, constraints |
| [`project-structure.md`](project-structure.md) | Directory responsibilities, where new code/tests/docs belong, conventions |

## Data (Sprint 2)

| Document | What it covers |
|---|---|
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

These are produced by `scripts/art_quickstart.py` (`make demo`) and committed
on purpose so the demo results are visible without running anything:

| Path | Produced by |
|---|---|
| [`results/art_quickstart_results.json`](results/art_quickstart_results.json) | `run_demo()` JSON report |
| [`figures/art_samples.png`](figures/art_samples.png) | original vs FGSM vs PGD grid |
| [`figures/art_accuracy_vs_eps.png`](figures/art_accuracy_vs_eps.png) | accuracy-vs-epsilon curves |

To regenerate, run the demo (see the root README). Do not hand-edit them.
`mlruns/`, `data/raw/`, and `models/` are also generated at runtime but are
gitignored, not committed.
