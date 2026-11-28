# Documentation

| I want to… | Start here |
|---|---|
| Run the dashboard | [Quick start](../README.md#quick-start) · [Update an existing checkout](team_handoff.md) |
| Explore the results | [Phase 1 walkthrough](sprint8_demo.md) · [Dashboard guide](ai_journey.md) |
| Set up, configure, or test the project | [Development](development.md) · [Configuration](configuration.md) · [Testing](testing.md) |
| Find code or contribute | [Project structure](project-structure.md) · [Architecture](architecture.md) · [Contributing](../CONTRIBUTING.md) · [Agent instructions](../AGENTS.md) |
| Prepare data or train a model | [Data guide](data/README.md) · [Sprint 3 baselines](sprint3.md) · [Sprint 4 tuning and prediction](sprint4.md) |
| Check milestones or planned work | [Progress](progress.md) · [Project plan](project_plan.md) · [Versioned HTML plan](plans/README.md) |

## Component references

[API](../api/README.md) · [Dashboard](../dashboard/README.md) ·
[Data](../src/data/README.md) · [Models](../src/models/README.md) ·
[Attacks](../src/attacks/README.md) · [Evaluation](../src/evaluation/README.md) ·
[Defenses](../src/defenses/README.md)

## Research record

| Sprint | Evidence and protocols |
|---|---|
| 1 · Foundations | [Report](sprint1_report.md) · [PR snapshot](PR_sprint1.md) · [MNIST reference results](results/art_quickstart_results.json) |
| 2 · Data | [Report](sprint2_report.md) · [EDA report](data/eda_report.md) · [Manifests](data/manifests/) · [EMBER card](data_cards/ember2018.md) · [CICIDS card](data_cards/cicids2017.md) |
| 3 · Baselines | [Report](sprint3_report.md) · [API contract](sprint3_contract.md) · [Baseline reference](results/baseline_reference.json) |
| 4 · Tuning | [Report and freeze-gate results](sprint4_report.md) |
| 5 · Exploratory evaluation | [Protocol](sprint5.md) · [Report](sprint5_report.md) · [Recorded experiment](results/attack_reference.json) |
| 6 · Transfer and realism | [Protocol](sprint6.md) · [Report and baseline follow-up](sprint6_report.md) · [Proposed mappings](sprint6_mappings.md) · [Comparison table](results/sprint6_comparison.md) |
| 7 · Recorded cases | [Case catalogue provenance](data_cards/sprint7_recorded_cases.md) · [Cohort analysis](results/sprint7_cohort_analysis.md) |
| 8 · Phase 1 review | [Performance report](sprint8_phase1_report.md) · [Defense workshop draft](sprint8_defense_workshop.md) |

Use the [threat model](threat_model_v0.1.md) and [feature feasibility review](feature_feasibility.md)
for research scope. See the [reading list](reading_list.md) and [literature notes](literature/README.md)
for background.

## Maintenance records

- [Decisions](DECISIONS.md) and [application security audit](security/SECURITY_AUDIT.md)
- [Bilingual presentation review](dashboard_presentation.md) and [light-mode review](light_dashboard_review.md)
- [Documentation audit](documentation_audit.md), [repository audit](repository_audit.md),
  [test hardening report](testing_hardening_report.md), and [CI efficiency audit](efficiency_audit.md)

Use the [project structure guide](project-structure.md#generated-vs-maintained)
for the rules on generated artifacts and recorded evidence.
