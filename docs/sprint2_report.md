# Sprint 2 report — Data pipeline

**Date:** 2026-10-25 · **Branch:** working tree (not committed) · **Python:**
3.11.16 · **Machine:** Linux, 12 CPU cores, 14 GB RAM (CPU-only)

This report records what was actually run and verified. Generated numbers are
also reproducible from the committed manifests and EDA JSON; do not edit the
generated report by hand.

## What was delivered

- `src/config.py`: dataset source resolution (CLI > env var > repo-local >
  `~/Documents`), processed directories, manifest/data-card paths.
- `src/data/ember.py`: local EMBER2018 v2 discovery, JSONL metadata scan,
  clean-room 2381-dim vectoriser, time-based validation split, duplicate sha256
  handling, atomic array writes, scaler, manifest, subset guard.
- `src/data/cicids2017.py`: eight original CSV files, whitespace/duplicate
  columns, label canonicalisation, inf/NaN handling, global dedup, binary and
  multiclass targets, 70/15/15 stratified split, train-only scaler, manifest,
  subset guard.
- `src/data/preprocessing.py`: atomic writes, SHA-256/manifest verification,
  scaler statistics, deterministic stratified/time splits.
- `src/data/loader.py`: `load_ember()` / `load_cicids2017()` returning
  `ProcessedDataset`.
- `scripts/preprocess.py`: full/subset/verify pipeline for one or both datasets.
- `scripts/eda_datasets.py`: deterministic EDA JSON, compact figures, generated
  Markdown report.
- Tests: synthetic EMBER/CICIDS/CLI/loader tests, plus optional real-data
  checks behind `RUN_REAL_DATA_TESTS=1`.
- Documentation: feature layout, two data cards, generated EDA report,
  decisions log, README/architecture/structure/AGENTS updates, progress tracker.
- Committed full-run manifests: `docs/data/manifests/ember2018.json` and
  `docs/data/manifests/cicids2017.json`.

## Commands and actual results

### Lint and test suite

```bash
.venv/bin/python -m ruff check src scripts tests api dashboard
.venv/bin/python -m ruff format --check src scripts tests api dashboard
.venv/bin/python -m pytest -o addopts='' --disable-warnings -q
```

Results:

```text
All checks passed!
31 files already formatted
26 passed, 2 skipped, 31 warnings in 45.63s
```

The two skips are the optional real-data availability checks
(`tests/test_data_real_optional.py`), disabled unless
`RUN_REAL_DATA_TESTS=1`. The warnings are existing third-party
Pydantic/pyparsing/pkg_resources deprecations, not test failures.

### EMBER smoke (subset, twice for reproducibility)

```bash
.venv/bin/python scripts/preprocess.py --dataset ember \
  --source ~/Documents/EMBER-Dataset --max-samples 2000 \
  --output-dir /tmp/ember_smoke --force --jobs 1
# repeated to /tmp/ember_smoke_repro
```

Actual results: train 1,700 / val 300 / test 2,000 rows; validation appeared
2018-09 … 2018-10; source hashing + scan + vectorisation about 2.3 minutes per
run with `--jobs 1`. Arrays and all manifest fields except `generated_at` were
byte-for-byte identical between the two runs. The loader returned
`(1700, 2381)` `float32`.

### CICIDS smoke (subset)

```bash
.venv/bin/python scripts/preprocess.py --dataset cicids2017 \
  --source ~/Documents/CIC-IDS-Dataset --max-samples 2000 \
  --output-dir /tmp/cicids_smoke --force
```

Actual results: train 1,400 / val 300 / test 300 rows, 77 features, about
1.1 minutes. Manifest `subset: true`; full source cleaning/dedup statistics are
still computed during the scan.

### Full EMBER run

```bash
.venv/bin/python scripts/preprocess.py --dataset ember \
  --source ~/Documents/EMBER-Dataset \
  --output-dir data/processed/ember2018 --jobs 6
```

Actual results (manifest `docs/data/manifests/ember2018.json`):

| Item | Value |
|---|---|
| Source train rows | 800,000 (300,000 benign, 300,000 malicious, 200,000 unlabelled) |
| Source test rows | 200,000 (100,000 benign, 100,000 malicious) |
| Duplicate sha256 | 0 (train/test/cross-split) |
| Feature dimensions | 2381 `float32` |
| Train | 510,000 rows (267,626 benign / 242,374 malicious) |
| Validation | 90,000 rows (32,374 benign / 57,626 malicious) |
| Test | 200,000 rows (100,000 / 100,000) |
| Split strategy | global time split, latest 15%; val appeared 2018-09 … 2018-10 |
| Test order | official order preserved (`source_index` 0..199,999) |
| Scaler | train-only; 40 zero-variance columns use scale 1 |
| Runtime | about 10 minutes with 6 workers (hash + scan + vectorise + scaler + hashes) |
| Arrays | ~7.6 GB (~7.2 GiB) under gitignored `data/processed/ember2018/` |

Checks run: all arrays finite; label counts and row counts match the manifest;
no sha256 appears in more than one split; histogram/byte-entropy rows sum to 1;
`--verify-only` re-hashed all 14 artifacts successfully.

### Full CICIDS run

```bash
.venv/bin/python scripts/preprocess.py --dataset cicids2017 \
  --source ~/Documents/CIC-IDS-Dataset \
  --output-dir data/processed/cicids2017
```

Actual results (manifest `docs/data/manifests/cicids2017.json`):

| Item | Value |
|---|---|
| Source rows | 2,830,743 |
| Source binary balance | 2,273,097 BENIGN / 557,646 attack (80.30% / 19.70%) |
| Feature dimensions | 77 (after dropping exact duplicate `Fwd Header Length.1`) |
| Inf values | 4,376 (Flow Bytes/s 1,509; Flow Packets/s 2,867) |
| NaN values before inf replacement | 1,358 |
| Invalid rows dropped | 2,867 (0.1013% < 1% threshold) |
| Duplicate rows dropped (float32) | 330,614 (within file 203,796; cross file 126,818) |
| Duplicate rows (raw float64 scan) | 307,775 |
| Identical rows with conflicting labels | 5,228 (float32) / 5,052 (float64) |
| Cleaned rows | 2,497,262 |
| Train | 1,748,083 (1,450,516 benign / 297,567 attack) |
| Validation | 374,589 (310,825 / 63,764) |
| Test | 374,590 (310,825 / 63,765) |
| Scaler | train-only; 8 zero-variance columns use scale 1 |
| Runtime | 1:16 |
| Arrays | ~0.8 GB under gitignored `data/processed/cicids2017/` |

Checks run: all features finite; per-split hashes have no intersection; scaler
mean matches the train split exactly; manifest artifacts verified.

**Duplicate-count discrepancy:** the briefing estimated ~254,479 exact
duplicates. Independent scans of the local original CSVs found 307,775 at raw
float64 precision and 330,614 after casting to the stored float32 precision
(rows indistinguishable to the model are collapsed). The measured values are
reported in the manifest/data card instead of forcing the estimate.

### Full EDA

```bash
.venv/bin/python scripts/eda_datasets.py --dataset all
.venv/bin/python scripts/eda_datasets.py --dataset all --max-samples 5000 \
  --output-dir /tmp/eda_smoke
```

Both completed (about 2.2 minutes each). Outputs: `docs/results/data_eda.json`,
seven `docs/figures/data_*.png`, `docs/data/eda_report.md`; the `--output-dir`
run stayed under `/tmp`.

EDA highlights:

- EMBER source: 1,000,000 rows, labels `-1: 200,000`, `0: 400,000`,
  `1: 400,000` (train+test); zero duplicate sha256; zero missing required keys;
  histogram and byte-entropy sample rows all sum to 1 within float32 tolerance.
- EMBER feature-group sample (n=5,000): imports non-zero fraction 0.0696,
  section 0.0807, exports 0.0266; general/header/datadirectory magnitudes are
  large, so train-only standardisation is saved for modelling.
- CICIDS: 15 classes; rare classes Heartbleed 11, SQL Injection 21,
  Infiltration 36; duplicate-column check 0 mismatches over all 2,830,743 rows;
  Heartbleed is absent from validation (10 train / 1 test / 0 val).
- CICIDS feature distributions use a systematic sample of 4,997 rows
  (stride 566); all source/cleaning counts cover every row.

### Manifest verification

```bash
.venv/bin/python scripts/preprocess.py --dataset all --verify-only
```

Result: `verified ember2018: 14 artifacts`, `verified cicids2017: 17 artifacts`,
exit code 0, about 22 seconds (warm page cache).

## Bugs found and fixed during verification

1. **Time split direction (critical).** The first full EMBER run selected the
   *earliest* 15% as validation because groups were traversed in ascending
   `appeared` order. It was caught by inspecting the manifest (`val` contained
   2006-12 while train reached 2018-10). Fixed by sorting groups latest-first
   with a deterministic `sha256` tie-break; regression tests now assert that
   validation is the latest period. The invalid artifacts were deleted and the
   full EMBER run was repeated. The committed manifest is from the fixed run.
2. **Subset overwrite guard.** A subset run could have overwritten full
   artifacts if pointed at the same output directory. Both pipelines now refuse
   to replace a manifest with `subset: false`; tests cover this.
3. **CICIDS float32 dedup precision.** Dedup is performed after casting to the
   stored representation, which collapses ~22.8k additional rows relative to
   raw float64. This is documented with both counts rather than hidden.

## What was not done or not verified

- **CIC-MalMem:** not present locally; skipped (optional supplement).
- **NSL-KDD:** not downloaded; skipped (optional stretch).
- **Baselines, attacks, defenses, API/dashboard changes:** out of Sprint 2 scope.
- **Problem-space validation of EMBER perturbations:** deferred to later
  sprints; only static feature vectors are available here.
- **Time-based CICIDS split:** not implemented; current split is stratified
  random. Documented as a limitation for deployment-style claims.
- **Official EMBER tarball hash:** not checked because only the extracted files
  exist locally. Per-file SHA-256 values are recorded in the manifest instead.
- **Full CI run on GitHub:** not triggered here; local `ruff` and `pytest` pass.
- **DVC/Git LFS:** deliberately not added (not installed, no remote); manifests
  provide per-file and per-artifact versioning instead.

## Honest status

Required Sprint 2 data work is complete and verified on the local datasets.
The optional CIC-MalMem and NSL-KDD items are explicitly skipped rather than
faked. All processed arrays and scalers are gitignored; only code, manifests,
data cards, reports, and EDA figures are intended for commit.
