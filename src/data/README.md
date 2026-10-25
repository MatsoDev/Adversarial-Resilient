# src/data — EMBER2018 and CIC-IDS-2017 data layer

Reusable code for reading the local raw datasets, cleaning/vectorising them,
splitting reproducibly, and loading the processed arrays. Raw data is never
copied into the repository.

Dataset locations, preprocessing/EDA commands, expected runtime, and generated
outputs are documented in [`docs/data/README.md`](../../docs/data/README.md).
This page covers the module APIs and boundaries.

## Modules

| Module | Contents |
|---|---|
| `ember.py` | EMBER2018 v2 discovery, JSONL metadata scan, clean-room 2381-dim vectoriser, time-based split, manifest |
| `cicids2017.py` | CIC-IDS-2017 discovery, label canonicalisation, inf/NaN handling, dedup, stratified split, manifest |
| `preprocessing.py` | atomic writes, SHA-256/manifest helpers, scaler statistics, stratified/time splits |
| `loader.py` | `load_ember()` / `load_cicids2017()` returning `ProcessedDataset` |

The 2381-dim layout is documented in
[`docs/data/ember_feature_layout.md`](../../docs/data/ember_feature_layout.md).
CLI entry points live in `scripts/preprocess.py` and `scripts/eda_datasets.py`;
business logic belongs in this package, not in those scripts.

## Preprocessing API

The CLI wraps these functions; notebooks and tests can import them directly.

| Entry point | Behavior |
|---|---|
| `run_ember_preprocessing(source_dir, output_dir, *, seed=42, max_samples=None, jobs=1, force=False, verify_source=True, scaler=True, val_fraction=0.15)` | Scans/vectorises EMBER, splits train/val by time, writes arrays/metadata/scalers, and returns the manifest dict |
| `run_cicids_preprocessing(source_dir, output_dir, *, seed=42, max_samples=None, jobs=1, force=False, verify_source=True, scaler=True, chunk_size=200_000, max_drop_fraction=0.01)` | Cleans/deduplicates the eight CSVs, makes binary + multiclass targets, writes a stratified split, and returns the manifest dict |
| `EmberVectorizer().transform(record, *, context="record")` | Converts one validated EMBER JSON record to a 2381-dim `float32` vector |
| `discover_ember_files(source_dir, *, strict=True)` / `discover_cicids_files(source_dir, *, strict=True)` | Locate the expected source files or raise `FileNotFoundError` |
| `scan_ember_metadata(files, *, jobs=1, show_progress=True)` | Stream JSONL metadata into train/test frames plus per-file statistics |
| `normalize_label(value)` / `binary_label(label)` | Canonicalise CICIDS labels and map BENIGN→0, any attack→1 |
| `feature_names()` | Human-readable names for the 2381 EMBER positions |

Both pipeline functions are deterministic for a fixed seed, write artifacts
atomically, record source/artifact hashes in the manifest, and refuse to
overwrite a full run with a subset. They do not download data. The shared
helpers in `preprocessing.py` (atomic writes, SHA-256, scaler statistics,
splits, manifest verification) are reusable without running the full
pipelines.

## Load processed data

```python
from src.data import load_ember, load_cicids2017

ember_train = load_ember("train")                   # X float32 (N, 2381), y int8
ember_val = load_ember("val", standardize=True)     # train-only mean/scale

cicids_train = load_cicids2017("train", target="binary")
cicids_multi = load_cicids2017("test", target="multiclass")
```

`ProcessedDataset` contains `X` (`float32`, shape `(N, D)`), `y` (integer
targets), `metadata` (a pandas DataFrame when the split metadata CSV exists),
`feature_names`, `split`, `dataset`, `target`, and `label_mapping`. `len()`
returns the number of rows. EMBER always uses the binary target; CICIDS accepts
`target="binary"` or `target="multiclass"`. Missing artifacts raise
`FileNotFoundError` with the preprocessing command to run, invalid
split/target names raise `ValueError`, and loaders never download data.

## Adding data code

- Keep raw-data discovery in `src/config.py` (`resolve_ember_source`,
  `resolve_cicids_source`) rather than hard-coding paths.
- Write artifacts atomically and record them in the manifest so
  `scripts/preprocess.py --verify-only` keeps working.
- Add synthetic tests in `tests/test_data_<area>.py` using
  `tests/data_fixtures.py`; never require the real datasets in the default
  test run.
