# Sprint 8 | Phase 2 workshop draft

Proposed order for review: adversarial training, ensemble and distillation,
sanitization and detector, then integration and ablation. These are the
Sprint 9–12 work packages in the [project plan](project_plan.md).

| Decision | Proposed owner | Approval needed |
|---|---|---|
| Training data partitions, candidate configurations and stopping rule | AI + DS | Approve before training |
| Threat assumptions, robustness scope and admissibility review | SS-A/B/C | Technical sign-off |
| Comparison fields and reproducibility checks | DS + CS | Approve before publishing |
| Model, dashboard and report integration | CS | Verify gates and missing-result labels |

Comparison records should include the dataset and split, ordered cohort hash,
model and preprocessing identity, policy identity, seed, configuration and
evidence status. Store clean and evaluated accuracy, class confusion counts,
false positive rate, recall, sample counts and denominators. Include the
operating threshold used and distinguish frozen results from development
results. Report clean performance alongside robustness, and use identical
cohorts and a documented threshold policy for direct comparisons.

Agree on parameter grids, holdout rules, compatible comparators and resource
limits in the workshop. Lock the final evaluation protocol before Sprint 9
measurements and record any change with its rationale. Approval, owners and
final configurations remain pending.
