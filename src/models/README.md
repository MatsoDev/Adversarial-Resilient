# src/models — model architectures

Current contents:

- `baseline_mlp.py` — `BaselineMLP` (tabular skeleton, not trained yet) and
  `SmallCNN` (the MNIST demo model used by `scripts/art_quickstart.py`).
- `tabular.py` — binary PyTorch MLP: 2381 → 1024 → 512 → 128 → 1,
  BatchNorm, ReLU and dropout, with a raw output logit.
- `training.py` — reproducible Logistic Regression, Random Forest, LinearSVC
  and MLP training. Memory-mapped inputs are sampled before scaling; the scaler
  fits selected training rows only. Validation selects the MLP checkpoint by
  BCE loss. No test predictions are generated in Sprint 3.

Run `python scripts/train_baselines.py --dataset ember2018` after preprocessing.
Defaults: 10,000 train / 5,000 validation rows, seed 42, 10 epochs, two CPU
threads. `--full` removes row limits. `--no-mlflow` disables tracking. Checkpoints
and scalers live under ignored `models/baselines/<batch>/`; JSON summaries go
to `docs/results/baselines/`. The API never loads pickle/joblib model files.

Planned:

- Sprint 3–4: classical scikit-learn baselines plus EMBER MLP/1D-CNN models,
  tuning, evaluation, and the frozen `baseline_v1`.
- Sprint 6+: CIC-IDS-2017 detector.
- Checkpoints are written to the gitignored `models/` directory.

New reusable model code belongs here; training loops that wire models to data
and attacks should live in `src/` modules or runnable `scripts/`.
