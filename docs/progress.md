# Progress tracker

**Last updated:** 2026-11-24 · **Current sprint:** Sprint 8 Phase 1 review preparation.

| Milestone | Status |
|---|---|
| M0 · Foundations | Complete. [Sprint 1 report](sprint1_report.md) |
| M1 · Frozen baseline | Blocked. The latest candidate reached **92.5778%** operating-validation accuracy, below the **93%** freeze gate. The official test remains unopened. [Training follow-up](sprint6_report.md#baseline-training-follow-up--2026-11-21) |
| M2 · Phase 1 report and adversarial dataset | In progress. The report, demo, case catalogue, CSV, and recorded cohort analysis are available. Independent reproduction, technical Security review, real transfer measurements, and the full versioned adversarial dataset remain pending. [Phase 1 acceptance items](sprint8_phase1_report.md#demo-and-review) |
| M3–M7 · Phase 2 | Planned. [Milestone schedule](project_plan.md#milestone-summary) |

## Sprint evidence

| Sprint | Outcome |
|---|---|
| 1 · Foundations | Pinned environment, threat model draft, and MNIST tooling demo. [Report](sprint1_report.md) |
| 2 · Data | EMBER2018 v2 and CIC-IDS-2017 preprocessing, manifests, and EDA. Optional CIC-MalMem and NSL-KDD were skipped. [Report](sprint2_report.md) |
| 3 · Baselines | Recorded development-subset validation and dashboard MVP. [Report](sprint3_report.md) |
| 4 · Tuning | CPU/GPU measurements, calibration, and authenticated prediction gate. [Report](sprint4_report.md) |
| 5 · Exploratory evaluation | 21 recorded EMBER configurations with CleverHans cross-checks and 57 recorded case summaries. Frozen-benchmark acceptance remains pending. [Report](sprint5_report.md) |
| 6 · Transfer and realism | Offline transfer infrastructure and bilingual evidence views. [Report](sprint6_report.md) · [Presentation reviews](README.md#maintenance-records) |
| 7 · Recorded cases | Searchable catalogue, shareable replay links, authenticated upload and history, and recovered cohort confusion matrices and L0 distributions. L2/L∞ distributions remain unavailable. [Case card](data_cards/sprint7_recorded_cases.md) · [Cohort analysis](results/sprint7_cohort_analysis.md) |
| 8 · Phase 1 review | Report draft, fixed-case walkthrough, and Phase 2 workshop draft. [Report](sprint8_phase1_report.md) · [Walkthrough](sprint8_demo.md) · [Workshop](sprint8_defense_workshop.md) |

## How to update this file

Update the date and milestone row when project status changes. Link to the
report, PR, or run that supports the change. Record schedule changes in the
[project plan](project_plan.md) and rationale in the [decisions log](DECISIONS.md).
Dated maintenance evidence is linked from the [docs index](README.md#maintenance-records).
