# src/models — model architectures

Current contents:

- `baseline_mlp.py` — `BaselineMLP` (tabular skeleton, not trained yet) and
  `SmallCNN` (the MNIST demo model used by `scripts/art_quickstart.py`).

Planned:

- Sprint 3–4: classical scikit-learn baselines plus EMBER MLP/1D-CNN models,
  tuning, evaluation, and the frozen `baseline_v1`.
- Sprint 6+: CIC-IDS-2017 detector.
- Checkpoints are written to the gitignored `models/` directory.

New reusable model code belongs here; training loops that wire models to data
and attacks should live in `src/` modules or runnable `scripts/`.
