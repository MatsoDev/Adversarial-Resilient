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
This real-data command was not rerun for the documentation pass. Success is a
`Completed validation batch ...; test split remains untouched` log, new local
checkpoints and a report containing the selected models' validation runs.

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
| `Trial(...)`, `default_trials(epochs=10)`, `tune_baseline(data_root, output_dir, *, trials=None, max_train=None, max_val=None, seed=42, threads=2, log_mlflow=True, tracking_uri=None, device="cpu")` | EMBER only; return measured report and write a new directory (`selection.json`, `weights.pt`, `scaler.npz`, `features.json`, `bundle.json`). Existing output directories are refused, including partial prior runs. |
| `FrozenBaseline(root, *, require_frozen=True)` | Verify compatible schema, required hashes and (by default) full-data validation/test freeze gates; load trusted CPU weights. Loading may raise `ValueError`, filesystem, parsing or torch errors. `require_frozen=False` is for local candidate research/tests, not serving. |
| `FrozenBaseline.predict(rows, *, representation, preprocessing_id, schema_id)` | Validate 1–32 ordered 2381-dim EMBER rows and exact identities, transform raw inputs or accept bundle-scaled inputs, return calibrated probabilities/labels. Invalid inputs raise `ValueError` (numeric conversion can also raise `OverflowError`). Full contract: [API](../../api/README.md#feature-prediction). |

`FrozenBaseline.model` exposes the scaled-input neural logit module for local
research. Its signed-log1p scaler and temperature remain part of the bundle
identity; the model alone is not an equivalent raw-feature detector. In
particular, loader `standardize=True` applies Sprint 2 raw-feature scaling,
**not** the Sprint 4 transform. Hashes are integrity checks, not signatures:
trust the publisher and restrict filesystem access to model directories.

### Configuration types and defaults

`TrainingConfig` controls Sprint 3 comparisons; `Trial` describes one Sprint 4
search candidate. Their `.validate() -> None` methods raise `ValueError` for
invalid supported values/counts. Constructing either dataclass alone does not
run training or call validation.

| Field | Type | `TrainingConfig` default | `Trial` default |
|---|---|---|---|
| `dataset` | String: `ember2018` or `cicids2017` | `ember2018` | Not a field; tuning is EMBER-only |
| `seed` | Integer | `42` | Not a field; supplied to `tune_baseline` |
| `max_train`, `max_val` | Integer or `None` | `10000`, `5000` | Not fields; supplied to `tune_baseline` |
| `architecture` | String: `mlp` or `cnn` | Not a field | `mlp` |
| `hidden` | Tuple of positive integer widths | `(1024, 512, 128)` | `(256, 128)`; widths <=2048 |
| `dropout` | Float in `[0, 1)` | `0.2` | `0.2` |
| `learning_rate` | Positive finite float | `0.001` | `0.001`, at most 1 |
| `epochs` | Positive integer | `10` | `10` |
| `batch_size` | Integer >=2 | `256` | `256` |
| `trees`, `max_iter`, `threads` | Positive integers | `100`, `1000`, `2` | Not fields |
| `optimizer` | String: `adam` or `adamw` | Not a field; MLP uses Adam | `adam` |
| `weight_decay` | Finite float in `[0, 1]` | Not a field | `0.0` |

Sprint 3 non-`None` row caps must be >=4; Sprint 4 caps must be >=16. Actual
stratification also requires enough rows per class. CNN uses its fixed
convolutional architecture rather than `hidden`, but the trial still validates
that field. `default_trials(epochs: int = 10) -> tuple[Trial, ...]` returns six
predeclared configurations with that epoch budget; it does not evaluate them.

Executed configuration-only example (no data or outputs):

```python
from src.models.training import TrainingConfig
from src.models.tuning import Trial, default_trials

config = TrainingConfig(max_train=1000, max_val=1000)
config.validate()
trial = Trial(epochs=1, optimizer="adamw", weight_decay=0.01)
trial.validate()
assert len(default_trials(epochs=1)) == 6
```

### Training and verified prediction inputs

- `train_baselines`: `data_root`, `results_dir` and `model_dir` are `Path`
  objects; defaults for the latter two are `BASELINE_RESULTS_DIR` and
  `BASELINE_MODELS_DIR`. `config` is `TrainingConfig | None`; `models` is a
  nonempty tuple of unique names from `MODEL_NAMES`. `tracking_uri` is
  `str | None`; `log_mlflow` is boolean. Return a dict with `schema_version`,
  `batch_id` and a list of `runs`, also written under the local batch/results paths.
- `tune_baseline`: path-like `data_root` and **new** `output_dir`; `trials` is
  `tuple[Trial, ...] | None` (default six-trial search). Row caps are
  `int | None`; `seed` and positive `threads` are integers. Tracking options
  match training. `device` is `"cpu"` or explicitly requested `"cuda"`; missing
  CUDA raises `ValueError`, with no fallback. Return the measured bundle/report
  dict; its `status`, not the directory name, determines qualification.
- `FrozenBaseline`: path-like `root` and boolean `require_frozen`. It loads
  verified weights on CPU. `.predict` accepts numeric `(N,2381)` rows,
  `representation: str` (`raw`/`scaled`), `preprocessing_id: str` and
  `schema_id: str` matching the record. It returns a dict with ordered
  `predictions` (label/score), identities, score type, threshold and latency.
  The [API reference](../../api/README.md#feature-prediction) gives numeric limits
  and the complete return fields.

Minimal library examples, **not executed on real data in this pass**. They
require full locally preprocessed EMBER data; the final example also requires a
genuinely frozen bundle. Choose an unused tuning output directory:

```python
from src.config import EMBER_PROCESSED_DIR, FROZEN_BASELINE_DIR, SPRINT4_MODELS_DIR
from src.data import load_ember
from src.models.frozen import FrozenBaseline
from src.models.training import TrainingConfig, train_baselines
from src.models.tuning import Trial, tune_baseline

comparison = train_baselines(
    EMBER_PROCESSED_DIR, config=TrainingConfig(max_train=1000, max_val=1000),
    models=("logistic_regression",), log_mlflow=False,
)
assert comparison["runs"][0]["test_evaluated"] is False

candidate = tune_baseline(
    EMBER_PROCESSED_DIR, SPRINT4_MODELS_DIR / "python-development",
    trials=(Trial(epochs=1),), max_train=1000, max_val=1000, log_mlflow=False, device="cpu",
)
assert candidate["status"] == "blocked_subset"

# Only after a separately qualified freeze; the candidate above cannot supply it.
baseline = FrozenBaseline(FROZEN_BASELINE_DIR)
data = load_ember("val", root=EMBER_PROCESSED_DIR, mmap_mode="r")
prediction = baseline.predict(
    data.X[:1], representation="raw",
    preprocessing_id=baseline.record["preprocessing_sha256"],
    schema_id=baseline.record["feature_schema_sha256"],
)
assert len(prediction["predictions"]) == 1
```

Success criteria are the assertions and corresponding local reports/bundles.
No synthetic or subset result may be relabelled frozen to make the last call work.

### Architectures and shared sampling

`TabularMLP(input_dim: int = 2381, hidden: tuple[int, ...] = (1024,512,128),
dropout: float = 0.2)` and `TabularCNN(input_dim: int = 2381, dropout: float = 0.2)`
accept float tensors `(N,D)` and return raw logits `(N,)`. Use evaluation mode
for inference; MLP training uses BatchNorm and needs at least two rows per batch.
Executed shape example, not trained-model evidence:

```python
import torch
from src.models.tabular import TabularMLP, TabularCNN

rows = torch.zeros(2, 2381)
assert TabularMLP(hidden=(32, 16)).eval()(rows).shape == (2,)
assert TabularCNN().eval()(rows).shape == (2,)
```

`sampling.py` owns selection shared by training, tuning and candidate attacks:

| Function | Parameters / return |
|---|---|
| `sample_indices(y, limit, seed)` | Label ndarray `(N,)`, integer cap or `None`, integer seed; return sorted indices, or every row when no reduction is needed |
| `sample_rows(X, y, limit, seed)` | Feature ndarray `(N,D)` and matching labels/cap/seed; return selected float32 features, labels and original indices |
| `validation_partitions(y, seed)` | Label ndarray and integer seed; return sorted disjoint selection/calibration/operating index arrays, approximately 50/25/25 |
| `index_hash(indices)` | Integer index ndarray; return SHA-256 string over ordered little-endian int64 bytes |

Stratified selection can raise scikit-learn `ValueError` for insufficient class
counts. Indices are positions in the supplied label array, so callers must map
them back before hashing if that array is already a subset. Executed example:

```python
import numpy as np
from src.models.sampling import index_hash, sample_indices, sample_rows, validation_partitions

y = np.tile([0, 1], 10)
indices = sample_indices(y, 8, 42)
X, selected_y, selected = sample_rows(np.zeros((20, 3)), y, 8, 42)
parts = validation_partitions(y, 42)
assert X.shape == (8, 3) and X.dtype == np.float32
np.testing.assert_array_equal(selected, indices)
assert len(indices) == 8 and len(index_hash(indices)) == 64
assert sum(map(len, parts)) == len(y)
assert len(np.unique(np.concatenate(parts))) == len(y)
```

All dataset-free examples above passed their assertions without writing outputs.

### CLI discovery and extension

Run `python scripts/train_baselines.py --help` or
`python scripts/tune_baseline.py --help` for flags/defaults from argparse.
Sprint 3 supports binary `ember2018` and `cicids2017` training; that support is
not evidence of measured CICIDS results. Sprint 4 tunes/freezes EMBER only.
Training returns CLI code 0 on completion, 1 on handled validation/missing-data
errors (argparse errors use 2). Tuning returns 0 frozen, 2 measured but gated,
1 on handled run errors. Do not confuse tuning's blocked code with a freeze.
Both `--help` commands exited 0 in the documentation audit; CUDA training and
real-data tuning/freezing were not rerun. For a dataset-free protocol check:

```bash
python -m pytest tests/test_models.py tests/test_model_sampling.py tests/test_sprint3.py tests/test_sprint4.py -q
```

Success means no failures; this exercises synthetic fixtures, not M1 research acceptance.

Keep new architectures in `tabular.py` (or a focused model module), reusable
training in `src/models/`, and CLI orchestration in `scripts/`. Any bundle-format
change must update the writer, verified loader and synthetic integrity tests
together. Tests: `tests/test_models.py`, `test_sprint3.py`, `test_sprint4.py`;
see [the protocol](../../docs/sprint4.md) before changing selection/gates.
