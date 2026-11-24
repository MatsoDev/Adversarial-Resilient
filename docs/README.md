# Documentation index

Use the [team handoff](team_handoff.md) to update an existing checkout and open
the recorded results. The [project README](../README.md) covers first-time setup,
[Sprint 4](sprint4.md) covers tuning and prediction, and
[progress](progress.md) tracks M1 availability.

## Where to look

- [Development](development.md) covers setup and operations.
  [Configuration](configuration.md) lists settings.
- [Project structure](project-structure.md) covers file placement.
  [Architecture](architecture.md) explains component boundaries and dependencies.
- The component references below describe HTTP, data and model contracts.
  [Testing](testing.md) covers validation.
- [Progress](progress.md) tracks current status.
  The [project plan](project_plan.md) defines scope and schedule.
- [Decisions](DECISIONS.md) records technical rationale. Sprint and audit reports
  preserve dated evidence.

## Dashboard and research evidence

- [AI journey](ai_journey.md) covers the dashboard, catalogue filters and case links.
- [Sprint 7 recorded EMBER case card](data_cards/sprint7_recorded_cases.md): case provenance, CSV fields and limits.
- [Sprint 7 cohort analysis](results/sprint7_cohort_analysis.md): recovered confusion matrices and L0 distributions.
- Sprint 8: [Phase 1 performance report](sprint8_phase1_report.md),
  [demo walkthrough](sprint8_demo.md) and [Phase 2 workshop draft](sprint8_defense_workshop.md).
- [Academic bilingual presentation review](dashboard_presentation.md): design,
  localization, demonstration route and actual browser/verification limits.
- [Light-mode dashboard review](light_dashboard_review.md): current presentation
  palette, academic copy, Arabic glossary and verification limits.
- [Sprint 6 protocol](sprint6.md), [implementation report](sprint6_report.md),
  [proposed mappings](sprint6_mappings.md) and
  [generated white-box / black-box table](results/sprint6_comparison.md).

## Getting oriented

The complete versioned HTML plan is in [plans/](plans/README.md), including the
[v0.5.2 export](plans/project_plan_v0.5.2.html) for the team to open after pulling.

| Document | What it covers |
|---|---|
| [`../README.md`](../README.md) | Project overview, current status, quick start, command summary |
| [`../AGENTS.md`](../AGENTS.md) | Short navigation map for AI coding agents and new contributors |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | Branching, commit style, PR checklist, code style |
| [`development.md`](development.md) | Setup, verification, ART demo, API/dashboard, Docker, troubleshooting |
| [`configuration.md`](configuration.md) | Environment variables, dataset resolution, Compose ports, paths/seeds |
| [`testing.md`](testing.md) | Test layout, commands, synthetic fixtures, optional real-data checks |
| [`testing_hardening_report.md`](testing_hardening_report.md) | Verified metrics/integrity regressions, prediction-boundary tests and before/after measurements |
| [`documentation_audit.md`](documentation_audit.md) | Dated documentation audits, complete inventory, file-by-file fixes, verified examples and remaining gaps |
| [`repository_audit.md`](repository_audit.md) | Structural audit, cleanup evidence, regression guards, validation and retained exceptions |
| [`efficiency_audit.md`](efficiency_audit.md) | CI deduplication, Docker caching and CLI characterization; local before/after measurements and hosted-verification limits |
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
| [`../src/attacks/README.md`](../src/attacks/README.md) | ART/CleverHans FGSM/PGD/CW, policies and gated/exploratory experiments |
| [`../src/defenses/README.md`](../src/defenses/README.md) | Planned hardening methods (placeholder) |
| [`../src/evaluation/README.md`](../src/evaluation/README.md) | Binary/paired attack metrics, report validation and bounded artifact readers |

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
| [`sprint5_report.md`](sprint5_report.md) | Measured exploratory EMBER results; frozen-benchmark and technical-review acceptance still pending |
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

The measured [Sprint 5 reference](results/attack_reference.json) and
[Sprint 4 reports](sprint4_report.md) are also committed evidence, not editable
examples. Preserve their original scores, identities and source hashes.
Local attack outputs under `results/attacks/` are ignored; use the
[offline runner](sprint5.md) for new measurements.
