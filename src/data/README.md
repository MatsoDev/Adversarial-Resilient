# src/data — EMBER2018 and CIC-IDS-2017 preprocessing

Reusable Sprint 2 code for reading the local raw datasets, cleaning/vectorising
them, splitting reproducibly, and loading the processed arrays in later
sprints. Raw data is never copied into the repository.

## Modules

| Module | Contents |
|---|---|
| `ember.py` | EMBER2018 v2 discovery, JSONL metadata scan, clean-room 2381-dim vectoriser, time-based split, manifest |
| `cicids2017.py` | CIC-IDS-2017 discovery, label canonicalisation, inf/NaN handling, dedup, stratified split, manifest |
| `preprocessing.py` | atomic writes, SHA-256/manifest helpers, scaler statistics, stratified/time splits |
| `loader.py` | `load_ember()` / `load_cicids2017()` returning `ProcessedDataset` |

The 2381-dim layout is documented in
[`docs/data/ember_feature_layout.md`](../../docs/data/ember_feature_layout.md).

## Run the pipeline

```bash
# Full runs (defaults resolve from EMBER_DATA_DIR / CICIDS_DATA_DIR, then
# data/raw/<name>, then ~/Documents/<name>)
python scripts/preprocess.py --dataset all

# Explicit sources and outputs
python scripts/preprocess.py --dataset ember \
  --source ~/Documents/EMBER-Dataset --output-dir data/processed/ember2018
python scripts/preprocess.py --dataset cicids2017 \
  --source ~/Documents/CIC-IDS-Dataset --output-dir data/processed/cicids2017

# Smoke subset; writes subset=true and never replaces full manifests
python scripts/preprocess.py --dataset ember --max-samples 2000 \
  --output-dir /tmp/ember_smoke --force --jobs 1

# Verify all processed artifacts against their manifests
python scripts/preprocess.py --dataset all --verify-only
```

Useful flags: `--seed` (default 42), `--max-samples`/`--limit`, `--force`,
`--verify-only`, `--jobs` (EMBER vectorisation only), `--no-scale`, and
`--skip-source-check` (synthetic/test sources only).

## Load processed data

```python
from src.data import load_ember, load_cicids2017

ember_train = load_ember("train")                   # X float32 (N, 2381), y int8
ember_val = load_ember("val", standardize=True)     # train-only mean/scale

cicids_train = load_cicids2017("train", target="binary")
cicids_multi = load_cicids2017("test", target="multiclass")
```

`ProcessedDataset` contains `X`, `y`, `metadata` (a pandas DataFrame when the
split metadata CSV exists), `feature_names`, `split`, `dataset`, `target`, and
`label_mapping`. Missing artifacts raise `FileNotFoundError` with the command
to run.

## Outputs (per dataset directory)

- `train_X.npy`, `val_X.npy`, `test_X.npy` — float32 features.
- `train_y.npy` (EMBER) or `train_y_binary.npy` /
  `train_y_multiclass.npy` (CICIDS) — integer targets.
- `train_metadata.csv`, `val_metadata.csv`, `test_metadata.csv`.
- `feature_names.json`, `label_mapping.json`.
- `scaler_mean.npy`, `scaler_scale.npy`, `scaler.json` — fitted on train only.
- `manifest.json` — source hashes/sizes, counts, splits, choices, artifact
  hashes, seed, timestamp, code revision.

Full-run manifests are also published to `docs/data/manifests/`; the large
arrays stay under gitignored `data/processed/`. No raw data, arrays, scalers,
or model weights are committed.
