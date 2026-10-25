# Testing guide

How the test suite is organized and how to run it. Setup and environment
prerequisites live in [`development.md`](development.md); commands are the same
locally and in CI.

## Quick commands

From the repository root, with the virtual environment active (or use
`.venv/bin/python` / `.venv\Scripts\python.exe` directly):

```bash
make test                 # full suite; synthetic fixtures, no datasets needed
make lint                 # ruff check + ruff format --check
make check                # lint + test (run before pushing)

python -m pytest -q
python -m pytest tests/test_data_loader.py -q          # one file
python -m pytest tests/test_api_health.py::test_health_returns_ok -q
python -m pytest -k "loader or preprocess" -q          # name/keyword filter
```

The default suite does not download MNIST or read the raw EMBER/CICIDS
datasets. Two optional real-data checks are skipped unless
`RUN_REAL_DATA_TESTS=1` is set (see below).

## Test layout

| File | Covers |
|---|---|
| `tests/data_fixtures.py` | Synthetic EMBER JSONL and CICIDS CSV builders (not a test module) |
| `tests/test_config.py` | `ensure_dirs()` creates the runtime directories |
| `tests/test_seed.py` | `set_seed()` determinism and seed changes |
| `tests/test_api_health.py` | `health()` return value and `/health` route registration (no HTTP client needed) |
| `tests/test_art_quickstart_smoke.py` | Synthetic end-to-end ART demo, including JSON/figure outputs under `tmp_path` |
| `tests/test_data_ember.py` | EMBER vectorizer layout/normalisation, time split, dedup, manifest, subset guard, tamper detection |
| `tests/test_data_cicids.py` | Label canonicalisation, duplicate column handling, cleaning/dedup, stratified split, scaler, manifest, subset guard |
| `tests/test_preprocess_cli.py` | `scripts/preprocess.py` subset/verify/force flows for both datasets |
| `tests/test_data_loader.py` | Loader API, standardisation, target/split validation, missing-artifact errors |
| `tests/test_data_real_optional.py` | Local dataset availability only; skipped by default |
| `tests/test_docs_links.py` | Relative Markdown links in the root docs and component READMEs resolve |

The suite is flat: add new tests as `tests/test_<area>.py` rather than creating
nested test packages.

## Test conventions

- **Dataset-free by default.** Build synthetic inputs with
  `tests/data_fixtures.py`; never make the default suite depend on
  `~/Documents`, `data/processed/`, or a network download.
- **Never write into `docs/`.** Pass pytest's `tmp_path` to `run_demo()` and
  `--output-dir` to the preprocessing/EDA CLIs. The smoke test and CLI tests
  use this pattern so committed demo artifacts are not overwritten.
- **Deterministic and isolated.** Pass explicit seeds, avoid order-dependent
  assertions, and keep test output inside `tmp_path`.
- **Optional real data.** Mark checks with
  `pytest.mark.skipif(os.environ.get("RUN_REAL_DATA_TESTS") != "1", ...)`;
  tests run only when the user opts in and has the datasets locally.
- **Docs are part of the contract.** When you add or move a Markdown file,
  update its links; `tests/test_docs_links.py` fails on broken relative links.

## Optional real-data checks

These require the resolved EMBER and CIC-IDS-2017 directories (see
[`configuration.md`](configuration.md)) and only check that the expected files
exist:

```bash
RUN_REAL_DATA_TESTS=1 python -m pytest tests/test_data_real_optional.py -q
```

The EMBER check expects `train_features_0.jsonl` and `test_features.jsonl`;
the CICIDS check expects exactly eight CSVs. They do not run preprocessing or
train a model. Full pipeline verification is separate:

```bash
python scripts/preprocess.py --dataset all --verify-only
```

## Adding tests

1. Put synthetic input construction in `tests/data_fixtures.py` when it can be
   reused.
2. For a pipeline change, assert both the returned manifest and the written
   artifacts (shapes, dtypes, row counts, and `verify_manifest_artifacts()`).
3. For a CLI change, call `main([...])` and assert the exit code plus the
   expected files, using `tmp_path`.
4. For docs changes, link new pages from [`README.md`](README.md) and run
   `python -m pytest tests/test_docs_links.py -q`.
5. Run `make check` before committing; `make lint` includes the formatting
   check that CI enforces.

## CI and expected results

[`../.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs `make lint`
and `make test` on Python 3.11, plus `docker build`. The local equivalents are
`make check` and `docker build -t adversarial-resilient:dev .`.

A healthy default run passes with the two real-data checks skipped. Warnings
from third-party packages (for example matplotlib/pyparsing, mlflow's
`pkg_resources`, and Pydantic deprecations) are not test failures.
