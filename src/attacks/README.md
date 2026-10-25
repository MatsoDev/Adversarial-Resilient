# src/attacks — adversarial attacks (Sprint 5+)

Placeholder package: no attack logic is implemented yet, only the module
boundary and this plan.

Planned:

- Sprint 5: `fgsm.py`, `pgd.py`, and `cw.py` — thin wrappers over
  `art.attacks.evasion` plus CleverHans cross-checks, with a shared attack
  configuration, perturbation-budget logging, and the feature-feasibility mask.
- Sprint 6: transfer/black-box attacks and realism constraints.

Sprint 1 reference pipeline: `scripts/art_quickstart.py` (MNIST demo).
