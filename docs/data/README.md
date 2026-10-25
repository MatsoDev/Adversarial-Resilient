# Data guide — EMBER2018 and CIC-IDS-2017

How to locate, preprocess, inspect, and load the project datasets. Development
setup and service commands live in [`../development.md`](../development.md).

Raw datasets are **read in place** from outside the repository and are never
committed. Processed arrays and scalers also stay out of Git
(`data/processed/` is gitignored). Only compact manifests, data cards, and EDA
results/report/figures are committed.

## Dataset locations

| Dataset | Local files |
|---|---|
| EMBER2018 v2 | `~/Documents/EMBER-Dataset/` (6 train JSONL files + `test_features.jsonl`) |
| CIC-IDS-2017 | `~/Documents/CIC-IDS-Dataset/` (8 original UNB/CIC CSVs) |

Resolution order:

```text
CLI --source
  > EMBER_DATA_DIR / CICIDS_DATA_DIR
  > data/raw/EMBER-Dataset or data/raw/CIC-IDS-Dataset
  > ~/Documents/EMBER-Dataset or ~/Documents/CIC-IDS-Dataset
```

No download is performed by the pipeline. Do not copy the datasets into the
repository; if you symlink them under `data/raw/`, they remain ignored.

## Commands

```bash
# Full pipeline (default source locations; publishes manifests)
python scripts/preprocess.py --dataset all
# or: make data

# Explicit sources/outputs (same commands as the Sprint 2 verification)
python scripts/preprocess.py --dataset ember \
  --source ~/Documents/EMBER-Dataset \
  --output-dir data/processed/ember2018
python scripts/preprocess.py --dataset cicids2017 \
  --source ~/Documents/CIC-IDS-Dataset \
  --output-dir data/processed/cicids2017

# Verify artifacts against the manifests without reprocessing
python scripts/preprocess.py --dataset all --verify-only

# Fast deterministic subsets (write subset=true; /tmp only)
python scripts/preprocess.py --dataset ember --max-samples 2000 \
  --output-dir /tmp/ember_smoke --force --jobs 1
python scripts/preprocess.py --dataset cicids2017 --max-samples 2000 \
  --output-dir /tmp/cicids_smoke --force
# or both: make data-smoke

# EDA (default outputs in docs/; --output-dir keeps tests out of docs/)
python scripts/eda_datasets.py --dataset all
python scripts/eda_datasets.py --dataset all --max-samples 5000 \
  --output-dir /tmp/eda_smoke
# or: make eda
```

Useful `preprocess.py` flags: `--seed` (default 42), `--max-samples`/`--limit`,
`--force`, `--verify-only`, `--jobs` (EMBER vectorisation only), `--no-scale`,
and `--skip-source-check` (synthetic/test sources only).

## Expected runtime and outputs

On the reference Linux machine (12 CPU cores, 14 GB RAM, Python 3.11):

- Full EMBER: about 10 minutes with `--jobs 6` (source hashing, metadata scan,
  vectorisation, scaler, artifact hashing), ~7.6 GB of arrays.
- Full CICIDS2017: about 1.5 minutes, ~0.8 GB of arrays.
- Subset smoke runs: about 1–2.5 minutes each (EMBER also hashes the 9.4 GB
  source even for a subset).
- `make test` stays dataset-free and runs in under a minute.

Per dataset directory under `data/processed/<dataset>/`:

- `train_X.npy`, `val_X.npy`, `test_X.npy` — float32 features.
- `train_y.npy` (EMBER) or `train_y_binary.npy` /
  `train_y_multiclass.npy` (CICIDS) — integer targets.
- `train_metadata.csv`, `val_metadata.csv`, `test_metadata.csv`.
- `feature_names.json`, `label_mapping.json`.
- `scaler_mean.npy`, `scaler_scale.npy`, `scaler.json` — fitted on train only.
- `manifest.json` — source hashes/sizes, counts, splits, choices, artifact
  hashes, seed, timestamp, and code revision.

Full-run manifests are also published to `docs/data/manifests/`; large arrays
stay under gitignored `data/processed/`.

## Loading processed data

```python
from src.data import load_ember, load_cicids2017

X_train, y_train = load_ember("train").X, load_ember("train").y
cicids_val = load_cicids2017("val", target="binary", standardize=True)
```

`load_ember` / `load_cicids2017` raise a clear error if artifacts are missing
and never download data. See [`../../src/data/README.md`](../../src/data/README.md)
for the full loader API (`ProcessedDataset`, target options, outputs).

## Committed data documentation

- [`ember_feature_layout.md`](ember_feature_layout.md) — 2381-dim feature
  layout and processing semantics.
- [`eda_report.md`](eda_report.md) — generated EDA report (do not hand-edit).
- [`manifests/`](manifests/) — generated full-run manifests (do not hand-edit).
- [`../data_cards/`](../data_cards/) — datasheets, licenses, limitations.
- [`../sprint2_report.md`](../sprint2_report.md) — commands and actual
  Sprint 2 results.
- [`../results/data_eda.json`](../results/data_eda.json) and
  `../figures/data_*.png` — generated EDA artifacts (committed on purpose).

Regenerate EDA outputs with `make eda`; never edit them by hand.
