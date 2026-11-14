# src/attacks — Sprint 5 feature-space research

- `runner.py`: configuration, calibrated two-logit wrapper, CPU ART
  FGSM/PGD/CW-L2 and optional independent CleverHans torch adapters.
- `constraints.py`: reviewed raw-feature bounds, immutable masks and integral
  counts, with standardized perturbation budgets.
- `experiment.py`: offline frozen-model/data/policy gates, exact paired cohorts,
  provenance and compact result serialization.

Entry point: `scripts/run_attacks.py`. Protocol, limitations, pending M1
dependency and team commands: [Sprint 5 guide](../../docs/sprint5.md).
Real EMBER results require a qualifying frozen baseline and reviewed policy;
synthetic tests never become dashboard results. CW is post-projected only.
Sprint 6 transfer/black-box and problem-space validation remain future work.
