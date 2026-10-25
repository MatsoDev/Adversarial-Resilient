# Data guide — EMBER2018 and CIC-IDS-2017

How to locate, preprocess, inspect, and load the project datasets. Development
setup and service commands live in [`../development.md`](../development.md);
environment variables are summarized in [`../configuration.md`](../configuration.md).

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

## Obtaining the raw data

The pipeline expects the official releases, not a re-cleaned Kaggle copy:

- **EMBER2018 v2** — obtain the feature release from
  <https://ember.elastic.co/> and keep `train_features_0.jsonl` …
  `train_features_5.jsonl` and `test_features.jsonl` together. The optional
  pretrained model file is not used in Sprint 2. See the
  [EMBER data card](../data_cards/ember2018.md) for license and composition.
- **CIC-IDS-2017** — obtain the original eight CSVs from UNB/CIC
  (<https://www.unb.ca/cic/datasets/ids-2017.html>, `MachineLearningCSV.zip`).
  The validator checks the exact filenames, row counts, and SHA-256 values
  recorded in [`manifests/cicids2017.json`](manifests/cicids2017.json); see the
  [CICIDS data card](../data_cards/cicids2017.md).

Neither dataset is redistributed here. Point `--source` or the environment
variables at the extracted directory; the pipeline reads files in place.

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

### `scripts/preprocess.py` options

| Option | Default | Behavior |
|---|---|---|
| `--dataset {ember,cicids2017,all}` | Required | Dataset to process |
| `--source PATH` | Resolution order | Raw source for a single dataset; rejected with `--dataset all` |
| `--ember-source PATH` / `--cicids-source PATH` | Resolution order | Per-dataset sources for `--dataset all` |
| `--output-dir PATH` | `data/processed/<dataset>` | Processed artifact directory; rejected with `--dataset all` |
| `--seed N` | `42` | Sampling and split seed; recorded in the manifest |
| `--max-samples N` / `--limit N` | All rows | Deterministic subset; marks the manifest `subset: true` |
| `--force` | Off | Override source hash/count mismatches and the 1% invalid-row threshold |
| `--verify-only` | Off | Re-hash artifacts against `manifest.json`; does not read the raw source |
| `--jobs N` | Up to 4 | Worker processes for EMBER scan/vectorisation; CICIDS dedup is single-process and logs that `--jobs` is ignored |
| `--no-scale` | Off | Do not write `scaler_mean.npy` / `scaler_scale.npy` |
| `--skip-source-check` | Off | Accept non-official/synthetic sources; intended for tests only |

`--max-samples` has dataset-specific behavior: EMBER samples the labeled train
partition and the official test partition separately before vectorisation,
while CICIDS samples cleaned, deduplicated rows before the 70/15/15 split.

Exit codes: `0` success, `1` verification or pipeline failure, `2` an
ambiguous argument combination (for example `--dataset all --source ...`).
A full-run manifest is published to `docs/data/manifests/` only when the output
directory is the default `data/processed/<dataset>` and the run is not a
subset; custom or subset runs keep `manifest.json` inside their output
directory.

### `scripts/eda_datasets.py` options

| Option | Default | Behavior |
|---|---|---|
| `--dataset {ember,cicids2017,all}` | Required | Dataset(s) to scan |
| `--source PATH` | Resolution order | Raw source for a single dataset; rejected with `--dataset all` |
| `--ember-source PATH` / `--cicids-source PATH` | Resolution order | Per-dataset sources for `--dataset all` |
| `--output-dir PATH` | `docs/` | Writes `<dir>/results/data_eda.json`, `<dir>/figures/`, and `<dir>/data/eda_report.md` |
| `--seed N` | `42` | Sampling seed |
| `--max-samples N` | `5000` | Cap for feature-distribution summaries; EMBER additionally caps its sample at 20,000 rows, CICIDS uses a systematic stride sample |
| `--jobs N` | Up to 4 | Worker processes for the EMBER metadata scan |
| `--no-processed` | Off | Do not read processed manifests under `data/processed/` |
| `--ember-processed-dir PATH` / `--cicids-processed-dir PATH` | Default processed dirs | Custom processed directories for manifest enrichment |

EDA always scans the raw source for counts and cleaning statistics; processed
manifests are used only to add split summaries when available. Exit codes are
`0` success and `2` for invalid arguments; processing errors are raised.

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

Full-run manifests from the default processed directories are also published
to `docs/data/manifests/`; large arrays stay under gitignored
`data/processed/`.

## Loading processed data

```python
from src.data import load_cicids2017, load_ember

ember_train = load_ember("train")
X_train, y_train = ember_train.X, ember_train.y
cicids_val = load_cicids2017("val", target="binary", standardize=True)
```

`load_ember` always returns the binary target (`0` benign, `1` malicious).
CICIDS supports
`target="binary"` or `target="multiclass"`; the returned `label_mapping`
documents the class order. `load_ember` / `load_cicids2017` raise
`FileNotFoundError` with the preprocessing command when artifacts are missing,
and never download data. See
[`../../src/data/README.md`](../../src/data/README.md) for the full loader API
(`ProcessedDataset` fields, standardisation, and target options).

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
