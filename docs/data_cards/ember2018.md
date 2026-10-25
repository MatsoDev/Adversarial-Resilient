# Data card — EMBER 2018 v2

## Motivation

EMBER is the project's primary malware-detection dataset. It provides
pre-extracted static PE features at a scale that is practical on CPU laptops,
so the team can train a detector and study feature-space adversarial evasion
without handling or redistributing live malware.

## Composition

- **Version:** EMBER2018 feature version **2** (`2381` dimensions). This is
  **not** EMBER2024 (feature v3, ~3.2M files), which is out of scope.
- **Files:** six `train_features_*.jsonl` files, one `test_features.jsonl`,
  and a pretrained `ember_model_2018.txt` (ignored in Sprint 2).
- **Size:** ~9.4 GB of JSONL on the local machine; raw data is not copied into
  the repository.
- **Train rows:** 800,000 = 300,000 benign (label 0) + 300,000 malicious
  (label 1) + 200,000 unlabelled (label -1).
- **Test rows:** 200,000 = 100,000 benign + 100,000 malicious. The official
  test boundary is preserved; test samples are never moved into train/val.
- **Duplicate `sha256`:** zero across all 1,000,000 records in the local copy.
- **Feature groups:** histogram 256, byte-entropy 256, strings 104, general 10,
  header 62, section 255, imports 1280, exports 128, data directories 30.
  See [`../data/ember_feature_layout.md`](../data/ember_feature_layout.md).
- **Raw record keys:** `sha256`, `md5`, `appeared`, `label`, `avclass`,
  `histogram`, `byteentropy`, `strings`, `general`, `header`, `section`,
  `imports`, `exports`, `datadirectories`.

## Collection

EMBER2018 was published by Endgame/Elastic. The 2018 release selected Windows
PE files from a larger corpus with different criteria from EMBER2017; labels
come from VirusTotal antivirus consensus, and `appeared` records the first
month a file was observed. The dataset ships only static features, not raw
binaries. Paper: Anderson and Roth, *EMBER: An Open Dataset of Malware and
Benign Executables for Benchmarking Static PE Malware Machine Learning*,
arXiv:1804.04637 (2018).

## Labeling

- Labels are supplied by the dataset authors: `1` malicious, `0` benign,
  `-1` unlabelled.
- `avclass` records family-like AV labels for malicious samples, but it is not
  used as a target in Sprint 2.
- Label noise is inherent in AV-consensus labels: some benign files may be
  flagged and some malware may be missed. Report per-family results with care.

## Preprocessing and cleaning

Actual full-run results from `scripts/preprocess.py --dataset ember`
(manifest: [`../data/manifests/ember2018.json`](../data/manifests/ember2018.json)):

- JSONL is streamed line by line; the 9.4 GB source is never loaded as a whole.
- Each record is validated (required keys, sha256 format, `appeared` format,
  label in `{-1,0,1}`, group shapes) and vectorised to 2381 finite `float32`
  values in the official v2 order. Empty imports/exports/sections produce zero
  hashed blocks.
- Histogram and byte-entropy counts are normalised to sum 1 (zero vector for an
  all-zero raw counter).
- **No duplicate sha256** were found across train/test; the removal step and
  cross-split duplicate check both report zero.
- The 200,000 unlabelled train rows are counted but excluded from supervised
  train/val arrays.
- **Time-based validation split:** labelled train records are sorted by
  `appeared` (month) with a deterministic `sha256` tie-break. The latest 15%
  (90,000 rows) is validation. The global split kept both classes large enough,
  so no per-class fallback was needed (`strategy = global_time`).
- Train: 510,000 rows (267,626 benign / 242,374 malicious), appeared
  2006-12 … 2018-09.
- Validation: 90,000 rows (32,374 benign / 57,626 malicious), appeared
  2018-09 … 2018-10.
- Test: 200,000 rows (100,000 / 100,000), appeared 2018-11 … 2018-12.
- A train-only mean/population-std scaler is saved (`scaler_mean.npy`,
  `scaler_scale.npy`); zero-variance columns use scale 1. It is not applied to
  the raw arrays unless the loader is called with `standardize=True`.

The training files were assembled by the dataset authors; the local run scans
six files and writes one test array without reshuffling the official test order.

## Splits

| Split | Rows | Benign | Malicious | Appeared |
|---|---:|---:|---:|---|
| train | 510,000 | 267,626 | 242,374 | 2006-12 … 2018-09 |
| val | 90,000 | 32,374 | 57,626 | 2018-09 … 2018-10 |
| test | 200,000 | 100,000 | 100,000 | 2018-11 … 2018-12 |

The validation period overlaps September with train at the month boundary
(`appeared` has monthly resolution); there is no exact sample overlap. The test
set is strictly later and untouched.

## Intended uses

- Malware/benign classification from static PE features.
- Adversarial evasion experiments in feature space (FGSM/PGD/CW in later
  sprints), with a documented feature-space → problem-space gap.
- Temporal generalization analysis using the official later test set.
- Teaching/benchmarking on CPU hardware.

## Distribution and license

- **Data files:** MIT-licensed EMBER2018 release. Raw data is not redistributed
  in this repository; obtain it from the EMBER/Elastic release.
- **Official extraction code:** the archived `elastic/ember` repository is
  AGPL-3.0. It was **not copied or vendored**. `src/data/ember.py` is an
  independent clean-room implementation of the published feature layout.
- Do not redistribute raw executables or derived per-sample features in a way
  that violates the dataset terms; this repo commits only aggregate manifests,
  reports, and code.

## Maintenance

- Read-only JSONL source with verified SHA-256, sizes, and row counts.
- Manifest-based versioning (`docs/data/manifests/ember2018.json`); arrays live
  under gitignored `data/processed/ember2018/`.
- Regenerate with `python scripts/preprocess.py --dataset ember` and
  `python scripts/eda_datasets.py --dataset ember`.
- Full vectorisation is CPU-heavy (roughly 6 minutes with 6 workers on this
  machine, plus source hashing/scanning/scaling); subset runs are available for
  smoke tests.

## Biases and limitations

- **EMBER2018 v2, not modern malware.** The corpus ends in 2018; performance
  and robustness claims do not automatically transfer to 2026 threats.
- **Temporal drift.** Validation is the latest labeled train months and test is
  later still. This makes evaluation more realistic than a random split but
  also means train/val/test distributions differ (malware share rises in
  validation).
- **AV label noise and selection bias.** Labels come from AV consensus and the
  corpus was filtered by the dataset authors; false positives/negatives and
  family imbalance remain.
- **Monthly `appeared` resolution.** Month-level timestamps create ties at split
  boundaries; the sha256 tie-break is deterministic but not true file-time
  ordering.
- **Unlabelled data excluded.** 200,000 train records (label -1) are not used
  in Sprint 2; semi-supervised use is future work.
- **Feature-space only.** Features are hashed/summarised PE properties; a
  feature perturbation may not correspond to a valid, still-malicious PE. This
  gap must be discussed for every attack result.
- **Hash collisions.** Section/import/header summaries use 10–1024-dimensional
  feature hashing with signed collisions; information is intentionally lossy.
- **No raw bytes.** The repository cannot reconstruct binaries or verify
  problem-space realizability from these features alone.

## Ethical and safety notes

Defensive research only. No malware binaries, PE execution, live PCAPs, or
weaponized tooling are included. Work with the public feature dataset; do not
upload derived per-sample data to third-party services or attempt to obtain the
original binaries. Keep attack experiments in feature space unless a separate,
isolated problem-space protocol is approved.

## References

- Anderson, Roth (2018), *EMBER: An Open Dataset of Malware and Benign
  Executables for Benchmarking Static PE Malware Machine Learning*:
  <https://arxiv.org/abs/1804.04637>.
- EMBER 2018 talk (selection criteria differ from EMBER2017):
  <https://www.camlis.org/2019/talks/roth>.
- Gebru et al. (2018), *Datasheets for Datasets*:
  <https://arxiv.org/abs/1803.09010> (structure used for this card).
