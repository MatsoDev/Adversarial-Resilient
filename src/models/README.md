# src/models — model architectures

Current contents:

- `sampling.py` — shared sorted stratified row selection and little-endian
  index hashes for Sprint 3/4 provenance. Tuning selects indices without reading
  feature matrices; comparison training materializes only selected rows.
- `baseline_mlp.py` — `BaselineMLP` (demo-era tabular skeleton, not the trained `TabularMLP`) and
  `SmallCNN` (the MNIST demo model used by `scripts/art_quickstart.py`).
- `tabular.py` — configurable binary `TabularMLP` (default 2381 → 1024 → 512 →
  128 → 1, BatchNorm/ReLU/dropout) and `TabularCNN`. Both return one raw logit
  per row; preprocessing/calibration is external. CNN adjacency is feature
  ordering, not executable-byte adjacency.
- `training.py` — reproducible Logistic Regression, Random Forest, LinearSVC
  and MLP training. Memory-mapped inputs are sampled before scaling; the scaler
  fits selected training rows only. Validation selects the MLP checkpoint by
  BCE loss. No test predictions are generated in Sprint 3.

Run `python scripts/train_baselines.py --dataset ember2018` after preprocessing.
Defaults: 10,000 train / 5,000 validation rows, seed 42, 10 epochs, two CPU
threads. `--full` removes row limits. `--no-mlflow` disables tracking. Checkpoints
and scalers live under ignored `models/baselines/<batch>/`; JSON summaries go
to `docs/results/baselines/`. The API never loads pickle/joblib model files.

New reusable model code belongs here; training loops that wire models to data
and attacks should live in `src/` modules or runnable `scripts/`.

## Sprint 4

`tuning.py` implements the primary EMBER MLP/CNN search, independent temperature
calibration and full-data accuracy gates. `frozen.py` verifies immutable local
bundles and performs explicitly raw/scaled feature inference. Run
`python scripts/tune_baseline.py --help`; see the
[reproduction/protocol guide](../../docs/sprint4.md). Existing Sprint 3 training
remains validation-only; both paths use the shared mandatory-hash verifier in
`src/data/preprocessing.py` rather than duplicating digest validation.

### Reusable interfaces and outputs

| Interface | Contract |
|---|---|
| `TrainingConfig(...)`, `train_baselines(data_root, *, config=None, models=MODEL_NAMES, results_dir=..., model_dir=..., tracking_uri=None, log_mlflow=True)` | Verify canonical train/val inputs and required hashes, fit comparison models, write checkpoints/scaler/feature names plus `training.json` under a unique batch directory, and return/publish a report with `runs`. Invalid config/artifacts raise `ValueError`; missing files raise `FileNotFoundError`. |
| `Trial(...)`, `default_trials(epochs=10)`, `tune_baseline(data_root, output_dir, *, trials=None, max_train=None, max_val=None, seed=42, threads=2, log_mlflow=True, tracking_uri=None)` | EMBER only; return measured report and write a new directory (`selection.json`, `weights.pt`, `scaler.npz`, `features.json`, `bundle.json`). Existing output directories are refused, including partial prior runs. |
| `FrozenBaseline(root, *, require_frozen=True)` | Verify compatible schema, required hashes and (by default) full-data validation/test freeze gates; load trusted CPU weights. Loading may raise `ValueError`, filesystem, parsing or torch errors. `require_frozen=False` is for local candidate research/tests, not serving. |
| `FrozenBaseline.predict(rows, *, representation, preprocessing_id, schema_id)` | Validate 1–32 ordered 2381-dim EMBER rows and exact identities, transform raw inputs or accept bundle-scaled inputs, return calibrated probabilities/labels. Invalid inputs raise `ValueError` (numeric conversion can also raise `OverflowError`). Full contract: [API](../../api/README.md#feature-prediction). |

`FrozenBaseline.model` exposes the scaled-input neural logit module for local
research. Its signed-log1p scaler and temperature remain part of the bundle
identity; the model alone is not an equivalent raw-feature detector. In
particular, loader `standardize=True` applies Sprint 2 raw-feature scaling,
**not** the Sprint 4 transform. Hashes are integrity checks, not signatures:
trust the publisher and restrict filesystem access to model directories.

### CLI discovery and extension

Run `python scripts/train_baselines.py --help` or
`python scripts/tune_baseline.py --help` for flags/defaults from argparse.
Sprint 3 supports binary `ember2018` and `cicids2017` training; that support is
not evidence of measured CICIDS results. Sprint 4 tunes/freezes EMBER only.
Training returns CLI code 0 on completion, 1 on handled validation/missing-data
errors (argparse errors use 2). Tuning returns 0 frozen, 2 measured but gated,
1 on handled run errors. Do not confuse tuning's blocked code with a freeze.

Keep new architectures in `tabular.py` (or a focused model module), reusable
training in `src/models/`, and CLI orchestration in `scripts/`. Any bundle-format
change must update the writer, verified loader and synthetic integrity tests
together. Tests: `tests/test_models.py`, `test_sprint3.py`, `test_sprint4.py`;
see [the protocol](../../docs/sprint4.md) before changing selection/gates.
