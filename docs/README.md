# Documentation index

**Opening the recorded results?** Start with [team_handoff.md](team_handoff.md) for
pulling main, synchronizing requirements and opening the HTML dashboard with
the recorded baseline results. For tuning/prediction use [Sprint 4](sprint4.md);
for M1 availability consult [progress](progress.md), not the historical handoff.

Start here. The root [`README.md`](../README.md) explains what the project is
and how to get it running; this page is the map to everything else.

## Which document owns the answer?

- **Setup and operations:** [development](development.md); **settings:** [configuration](configuration.md).
- **Placement and dependencies:** [project structure](project-structure.md) and [architecture](architecture.md).
- **HTTP/data/model contracts:** the component references linked below; **validation:** [testing](testing.md).
- **Current status:** [progress](progress.md); **scope:** [project plan](project_plan.md).
- **Why:** [decisions](DECISIONS.md); **dated evidence:** sprint and audit reports, not new setup instructions.

## Getting oriented

| Document | What it covers |
|---|---|
| [`../README.md`](../README.md) | Project overview, current status, quick start, command summary |
| [`../AGENTS.md`](../AGENTS.md) | Short navigation map for AI coding agents and new contributors |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | Branching, commit style, PR checklist, code style |
| [`development.md`](development.md) | Setup, verification, ART demo, API/dashboard, Docker, troubleshooting |
| [`configuration.md`](configuration.md) | Environment variables, dataset resolution, Compose ports, paths/seeds |
| [`testing.md`](testing.md) | Test layout, commands, synthetic fixtures, optional real-data checks |
| [`testing_hardening_report.md`](testing_hardening_report.md) | Verified metrics/integrity regressions, prediction-boundary tests and before/after measurements |
| [`documentation_audit.md`](documentation_audit.md) | Documentation findings, fixes, validation evidence and remaining gaps |
| [`repository_audit.md`](repository_audit.md) | Structural audit, cleanup evidence, regression guards, validation and retained exceptions |
| [`progress.md`](progress.md) | Where are we now: sprint/milestone status, current checklist |

## Architecture and structure

| Document | What it covers |
|---|---|
| [`architecture.md`](architecture.md) | Components, entry points, dependency rules, data flows, constraints |
| [`project-structure.md`](project-structure.md) | Directory responsibilities, where new code/tests/docs belong, conventions |
| [`../api/README.md`](../api/README.md) | FastAPI endpoints, responses, run commands, OpenAPI URLs |
| [`../dashboard/README.md`](../dashboard/README.md) | Primary HTML UI, feature prediction, UI checks and legacy Streamlit |
| [`../src/data/README.md`](../src/data/README.md) | Data layer APIs: preprocessing entry points and loaders |
| [`../src/models/README.md`](../src/models/README.md) | Model classes, training/tuning interfaces, verified frozen bundles and CLI discovery |
| [`../src/attacks/README.md`](../src/attacks/README.md) | Planned FGSM/PGD/CW wrappers (placeholder) |
| [`../src/defenses/README.md`](../src/defenses/README.md) | Planned hardening methods (placeholder) |
| [`../src/evaluation/README.md`](../src/evaluation/README.md) | Binary metrics/threshold semantics and bounded artifact readers |

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
| [`feature_feasibility.md`](feature_feasibility.md) | Sprint 3 feature-space attack feasibility review |
| [`reading_list.md`](reading_list.md) | Papers and why they matter to the project |
| [`literature/README.md`](literature/README.md) | Literature notes and note templates (malware + network tracks) |

## Project process and history

| Document | What it covers |
|---|---|
| [`project_plan.md`](project_plan.md) | Canonical project plan: scope, sprints, milestones, risks (baseline) |
| [`DECISIONS.md`](DECISIONS.md) | Log of non-obvious technical decisions, sprint by sprint |
| [`sprint1_report.md`](sprint1_report.md) | Sprint 1 report: what was done, run, measured, not verified |
| [`sprint2_report.md`](sprint2_report.md) | Sprint 2 report: data pipeline commands, counts, EDA, limitations |
| [`sprint3.md`](sprint3.md) | Sprint 3 branch contents, teammate data setup, dashboard run and review gate |
| [`sprint3_contract.md`](sprint3_contract.md) | Versioned read-only API and planned feature prediction contract |
| [`sprint3_report.md`](sprint3_report.md) | Real EMBER baseline metrics, verification evidence and Sprint 4 findings |
| [`sprint4.md`](sprint4.md) | Tuning, calibration, freeze gates, reproducibility and authenticated feature prediction |
| [`sprint4_report.md`](sprint4_report.md) | Sprint 4 measured evidence, verification and M1 status |
| [`sprint5.md`](sprint5.md) | Offline constrained attacks, metrics, cross-checks and HTML explorer; prerequisites |
| [`sprint5_report.md`](sprint5_report.md) | Sprint 5 implementation evidence and pending real-data acceptance |
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
`docs/results/baseline_reference.json` is also intentionally committed measured
Sprint 3 evidence; do not edit its scores by hand. Local comparison reports in
`docs/results/baselines/`, `mlruns/`, `data/raw/`, `data/processed/`, and model bundles
are generated at runtime but are gitignored, not committed. The tracked
`.gitkeep` files reserve runtime directories; they are not datasets or weights.
