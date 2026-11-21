# Sprint 8 | Phase 1 performance report

Review draft for the team and supervisor. M2 remains open.

## EMBER results

The [recorded experiment](results/attack_reference.json) uses 128 EMBER2018 v2
operating-validation rows, seed 42, and an unfrozen development model. The
recorded policy covers a single numeric feature; technical Security review is
pending. The table counts decisions on the same 128 rows in each configuration.

| Evaluation | Configurations | Correct / 128 | Accuracy | Induced errors / 122 initially correct |
|---|---:|---:|---:|---:|
| Original features | Shared control | 122 | 95.31% | — |
| FGSM, zero budget | 1 | 122 | 95.31% | 0 |
| FGSM, positive budgets | 3 | 121 each | 94.53% | 1 each |
| PGD, zero budget | 4 | 122 each | 95.31% | 0 |
| PGD, positive budgets | 12 | 121 each | 94.53% | 1 each |
| CW-L2, after projection | 1 | 122 | 95.31% | 0 |

FGSM and PGD positive-budget configurations show a **0.78 percentage-point**
drop. The recorded CleverHans cross-check is complete for all 21
configurations. Counts are per configuration, and reusing the same cohort means
the rows are not independent across configurations. These results cover the
recorded scalar constraint. They cannot establish executable validity or
general detector robustness.

For the recorded FGSM example at ε = 0.05, the before/after confusion
matrices use benign and malicious order on both axes. Rows are known labels
and columns are predictions.

| Stage | True benign, predicted benign | True benign, predicted malicious | True malicious, predicted benign | True malicious, predicted malicious |
|---|---:|---:|---:|---:|
| Before | 46 | 0 | 6 | 76 |
| After | 46 | 0 | 7 | 75 |

The [cohort analysis](results/sprint7_cohort_analysis.md) documents how these
counts were recovered. It includes the [confusion matrix and L0 figure](results/sprint7-cohort/cohort_example.png)
and [all 21 aggregate results](results/sprint7-cohort/cohort_summary.json).
The Attack comparison page plots accuracy versus ε for recorded FGSM and PGD.
Positive L2 and L∞ distributions are unavailable in the saved evidence.

The model used above reached **92.1778%** on all 22,500 operating-validation
rows. The later GPU candidate reached **92.5778%** on that validation
partition and remains a separate training result. Neither passed the 93% gate.
The official test was left unopened. See the [training follow-up](sprint6_report.md#baseline-training-follow-up--2026-11-21).

## Demo and review

Follow the [Phase 1 walkthrough](sprint8_demo.md). Have a second team member
repeat it on their checkout, compare the CSV to the report, and record the
commit, environment, and any mismatches. Ask SS-C to review the
[threat model](threat_model_v0.1.md), [proposed mappings](sprint6_mappings.md)
and the limits of the cohort. Schedule the supervisor presentation after
internal review.

| Acceptance item | State |
|---|---|
| Verified frozen baseline and live authenticated prediction | Pending M1 |
| Recorded ART/CleverHans feature-space comparison | Available |
| Case index, CSV and cohort analysis | Available, aggregate evidence |
| Versioned full adversarial feature dataset | Pending |
| Threat model v1.0 and mapping sign-off | Pending technical review |
| Independent demo reproduction and supervisor review | Pending |

Use the [defense workshop draft](sprint8_defense_workshop.md) to agree on the
Phase 2 comparison contract and owners before Sprint 9.
