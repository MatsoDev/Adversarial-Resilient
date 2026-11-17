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

### Parameter types and effects

For both `run_*_preprocessing` functions, `source_dir` and `output_dir` are
`str | Path`. Sources are read in place; outputs are created under `output_dir`.
The library returns the manifest dictionary and writes `manifest.json` plus the
arrays/metadata/schema files. Only the CLI additionally publishes a full default-
directory manifest under `docs/data/manifests/`.

| Keyword | Type / default | Effect |
|---|---|---|
| `seed` | Integer; `42` | Reproducible sampling/split seed |
| `max_samples` | Positive integer or `None`; `None` | Optional row cap; any non-`None` value marks the manifest as a subset |
| `jobs` | Integer; `1` | EMBER workers; CICIDS stays single-process for global deduplication |
| `force` | Boolean; `False` | Override official source hash/count mismatches; also bypass CICIDS's invalid-row fraction guard, not schema checks |
| `verify_source` | Boolean; `True` | Check official source names/hashes/counts; disabling is intended for synthetic fixtures |
| `scaler` | Boolean; `True` | Save train-fitted raw-feature mean/scale; never changes the raw saved feature matrices |
| `val_fraction` (EMBER) | Float in `(0,1)`; `0.15` | Latest labeled training fraction held out by time |
| `chunk_size` (CICIDS) | Positive integer; `200000` | CSV rows per cleaning chunk |
| `max_drop_fraction` (CICIDS) | Float fraction; `0.01` | Reject excessive invalid-row removal unless forced |

EMBER caps labeled training and official test separately before vectorization;
CICIDS caps cleaned/deduplicated rows before splitting. A cap does not imply that
source hashing/scanning is skipped. Missing files raise `FileNotFoundError`;
malformed records, integrity mismatches and output guards raise validation/runtime
errors. A full-data output directory must never be reused for a subset.

Minimal library examples, **not run on real sources in the documentation pass**.
They require locally obtained official datasets. Temporary outputs are removed
when the block ends; use a chosen local output directory if you need to keep them:

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from src.config import resolve_ember_source, resolve_cicids_source
from src.data.ember import run_ember_preprocessing
from src.data.cicids2017 import run_cicids_preprocessing

with TemporaryDirectory() as temporary:
    root = Path(temporary)
    ember = run_ember_preprocessing(resolve_ember_source(), root / "ember", max_samples=2000)
    cicids = run_cicids_preprocessing(resolve_cicids_source(), root / "cicids", max_samples=2000)
    assert ember["subset"] is True and cicids["subset"] is True
    assert (root / "ember" / "manifest.json").is_file()
    assert (root / "cicids" / "manifest.json").is_file()
```

Success means manifests and artifacts exist and the subset assertions pass,
not that the outputs qualify for a full-data model benchmark.

### Discovery, vectorization and labels

- `discover_ember_files(source_dir: str | Path, *, strict: bool = True)` returns
  `EmberSourceFiles`, with `.train: tuple[Path, ...]`, `.test: Path`, and `.all`
  combining them. `discover_cicids_files` takes the same arguments and returns
  `tuple[Path, ...]` in canonical day order. Strict mode requires official filenames;
  missing directories/files raise `FileNotFoundError`.
- `scan_ember_metadata(files: EmberSourceFiles, *, jobs: int = 1,
  show_progress: bool = True)` returns `(train_frame, test_frame, file_stats)`:
  two pandas DataFrames and a list of per-file dictionaries. It scans JSONL
  metadata, not a full in-memory feature matrix.
- `EmberVectorizer().transform(record: Mapping[str, Any], *, context: str = "record")`
  validates a raw JSON record and returns a finite float32 array `(2381,)`.
  `context` identifies the record in validation errors. `feature_names()`
  takes no arguments and returns the corresponding `list[str]`.
- `normalize_label(value: object) -> str` canonicalizes one CICIDS label or raises
  `ValueError` for unknown labels. `binary_label(label: str) -> int` maps exact
  `"BENIGN"` to 0 and **any other string** to 1; normalize first, since the latter
  helper does not validate raw label spelling.

Read-only EMBER example, not run here because it requires the raw files:

```python
import json
import numpy as np
from src.config import resolve_ember_source
from src.data.ember import EmberVectorizer, discover_ember_files, feature_names, scan_ember_metadata

files = discover_ember_files(resolve_ember_source())
with files.train[0].open(encoding="utf-8") as source:
    vector = EmberVectorizer().transform(json.loads(next(source)), context="first train row")
assert vector.shape == (len(feature_names()),) == (2381,)
assert vector.dtype == np.float32
train_metadata, test_metadata, file_stats = scan_ember_metadata(files, show_progress=False)
assert len(file_stats) == len(files.all)
```

Success means a correctly shaped vector and per-file scan records are returned.
Label normalization needs no data and was executed successfully:

```python
from src.data.cicids2017 import binary_label, normalize_label

assert binary_label(normalize_label(" benign ")) == 0
assert normalize_label("Web Attack \ufffd Sql Injection") == "Web Attack - SQL Injection"
```

## Load processed data

Both loaders return `ProcessedDataset`:

| Parameter | Type / default | Effect |
|---|---|---|
| `split` | String; `"train"` | `"train"`, `"val"` or `"test"` |
| `root` | `str \| Path`; dataset-specific processed directory | Location of the previously generated arrays/schema |
| `standardize` | Boolean; `False` | Allocate a transformed float32 feature matrix using saved Sprint 2 statistics |
| `mmap_mode` | NumPy mode string or `None`; `None` | Passed to `np.load` for the feature array only; `"r"` enables read-only mapping |
| `target` (CICIDS only) | String; `"binary"` | Select `"binary"` or `"multiclass"` labels |

Example not executed on real arrays in this pass. It requires previous
preprocessing; the standardized validation call allocates the transformed matrix:

```python
from src.data import load_ember, load_cicids2017

ember_train = load_ember("train", mmap_mode="r")     # X float32 (N, 2381), y int8
ember_val = load_ember("val", standardize=True)     # train-only mean/scale

cicids_train = load_cicids2017("train", target="binary")
cicids_multi = load_cicids2017("test", target="multiclass")
assert ember_train.X.shape[1] == 2381
assert len(cicids_train) == len(cicids_train.y)
```

`ProcessedDataset` contains `X` (`float32`, shape `(N, D)`), `y` (integer
targets), `metadata` (a pandas DataFrame when the split metadata CSV exists),
`feature_names`, `split`, `dataset`, `target`, and `label_mapping`. `len()`
returns the number of rows. EMBER always uses the binary target; CICIDS accepts
`target="binary"` or `target="multiclass"`. Missing artifacts raise
`FileNotFoundError` with the preprocessing command to run, invalid
split/target names raise `ValueError`, and loaders never download data.

Both loaders also accept `root=Path(...)` for custom processed directories and
`mmap_mode="r"` for memory-mapping the feature file. `standardize=True` allocates
a transformed matrix using the saved Sprint 2 raw-feature scaler; it is **not**
the Sprint 4 signed-log1p/bundle scaler. Neither loader implicitly verifies
manifest SHA-256 digests: use `scripts/preprocess.py --verify-only` for complete
artifact verification, or explicit required-input checks at training/inference
boundaries. Missing metadata CSVs are allowed and yield `metadata=None`.
For project-generated files, `feature_names` is `list[str]`, `split`/`dataset`/
`target` identify the returned split, and `label_mapping` is a dictionary. The
success criteria above check shape/alignment, not accuracy or artifact integrity.
Malformed NumPy/JSON files can also propagate parsing or filesystem errors.

### Explicit integrity verification

`verify_manifest_artifacts(manifest: dict, root: str | Path, *,
require_hashes: bool = False) -> list[str]` checks contained regular files
against supplied size/hash records. It does not repair files. An empty list
means the recorded checks passed; otherwise it returns error strings. Hashes
are optional by default; training/inference boundaries use `require_hashes=True`.
Neither mode authenticates a publisher or protects against concurrent hostile writers.

Executed synthetic example, isolated from committed evidence:

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from src.data.preprocessing import artifact_record, verify_manifest_artifacts

with TemporaryDirectory() as temporary:
    root = Path(temporary)
    sample = root / "sample.txt"
    sample.write_text("example\n", encoding="utf-8")
    manifest = {"artifacts": {"sample": artifact_record(sample, root=root)}}
    assert verify_manifest_artifacts(manifest, root, require_hashes=True) == []
```

`artifact_record(path: str | Path, *, root: str | Path, shape: tuple | None = None,
dtype: str | None = None) -> dict` records the relative filename, byte size and
SHA-256, plus optional shape/dtype metadata. Success in this example means no
verification errors; it does not inspect any local dataset.

## Adding data code

- Keep raw-data discovery in `src/config.py` (`resolve_ember_source`,
  `resolve_cicids_source`) rather than hard-coding paths.
- Write artifacts atomically and record them in the manifest so
  `scripts/preprocess.py --verify-only` keeps working.
- Add synthetic tests in `tests/test_data_<area>.py` using
  `tests/data_fixtures.py`; never require the real datasets in the default
  test run.
