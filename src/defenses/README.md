# src/defenses — hardening methods (Sprint 9+)

Placeholder package: no defense logic is implemented yet, only the module
boundary and this plan.

Planned:

- `adversarial_training.py` (Sprint 9)
- `ensemble.py`, `distillation.py` (Sprint 10)
- `sanitization.py`, `detector.py` (Sprint 11)

Each defense should expose a `fit()`/`defend()`-style API and report
robustness versus clean accuracy so defenses can be compared and ablated.
