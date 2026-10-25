# Decisions log

Entries record choices that are not obvious from the code, grouped by sprint
and date. Sprint reports and manifests remain the evidence for what was run;
this log explains why.

- **Python 3.11 canonical (CI), 3.10–3.12 tolerated.** Spec asked 3.10/3.11; this
  machine has 3.12.1, so pins were chosen to work on 3.11 (CI) and verified on
  3.12. See sprint1_report for actual `python --version`.
- **CPU torch via PyPI (+ `--extra-index-url .../cpu`).** Keeps `pip install`
  simple on Windows/Linux/macOS laptops; avoids CUDA wheels.
- **numpy==1.26.4 (not 2.x).** ART 1.18.x + torchvision + mlflow break on numpy 2
  on Windows in our tests; pin <2 until upstream supports it.
- **ART==1.18.1, torch==2.4.1, torchvision==0.19.1.** Mutually compatible,
  support py3.11/3.12, include FastGradientMethod/ProjectedGradientDescent/CarliniL2Method.
- **CleverHans isolated (`requirements-cleverhans.txt`).** cleverhans 4.0.0
  (2020) needs TF 2.15 + old scipy and conflicts with the ART stack; the demo
  imports it lazily behind `--cleverhans` and skips gracefully if missing.
- **MNIST `ToTensor()` only (0..1), no mean/std norm.** So ART `clip_values=(0,1)`
  and eps 0.05–0.3 are interpretable; normalization would shift clip bounds.
- **SmallCNN for demo, BaselineMLP as skeleton.** CNN hits >95% in 3 epochs on CPU;
  MLP kept for EMBER tabular intuition (Sprint 2).
- **`make` shim for Windows.** No `make` on this machine; Makefile targets also
  work via `python -m ...` (documented in README + report).
- **Docker not run here.** No Docker daemon; files written + `docker compose config`
  equivalent YAML check via Python; marked Not Verified in report.
- **setuptools==75.8.0.** mlflow 2.15.1 needs `pkg_resources`, removed in
  setuptools>=81. Fresh install pulled 84.0.0 and mlflow import failed;
  downgrade fixed it; pinned to keep `make setup` reproducible.
- **set_seed() thread handling.** `torch.set_num_interop_threads(1)` raises
  RuntimeError on second call per process; wrapped in try/except so tests and
  repeated demo runs don't crash.
- **`--fast` = 5000 train / 1000 FGSM-PGD / 20 CW / 2 epochs.** Full CW-200 +
  6-eps PGD grid exceeds 10 min on CPU (observed timeout); fast keeps
  `make demo` feasible while full 60k×3 epochs (clean 0.988) is logged separately.
- **Smoke test overwrites demo artifacts.** `--synthetic` writes to the same
  `docs/results` + `docs/figures`; Sprint 2 should redirect synthetic to temp.
  Restored real outputs by re-running `--fast` after tests.

## Post-merge maintenance (2026-10-15, Linux, Python 3.11.16)

Branch `chore/repository-structure-cleanup` (main is protected; nothing pushed
to it directly). Scope: repository navigation/documentation, hygiene fixes,
and one Makefile fix (`clean`); no changes to application code or CI behavior.

- **Documentation system added.** `docs/README.md` is now the documentation
  index; `docs/architecture.md` documents components/dependency rules/data
  flows; `docs/project-structure.md` is the "where does this belong" reference;
  `AGENTS.md` is the short navigation map for AI coding agents. The root README
  links to them. Rationale: future contributors and agents previously had to
  reverse-engineer the structure; there was no index and no agent instructions.
- **Dead `[tool.black]` config removed from `pyproject.toml`.** Black is not in
  any requirements file nor in pre-commit; `ruff format` (pre-commit hook) is
  the configured formatter. The section was misleading configuration only.
- **`scripts/art_quickstart.py` formatted with `ruff format`.** It was the only
  file that failed `ruff format --check` — the pre-commit `ruff-format` hook
  would have reformatted it on the next local commit. Purely line-wrapping
  changes; logic untouched.
- **Project plan converted to Markdown (`docs/project_plan.md`); HTML removed.**
  The HTML export rendered as raw source on GitHub and mixed the content with
  embedded CSS; every other doc is Markdown. Conversion used pandoc and was
  verified token-by-token against the original (the only added tokens are the
  header note pointing at the tracker and the ordinals pandoc emits for `<ol>`
  lists). The original export remains in git history (commit `c8a9d0a` added
  `docs/project_plan.html`) if the exact file is ever needed.
- **`docs/PR_sprint1.md` labeled as a historical snapshot.** Kept for the
  sprint record (the merged PR body also exists on GitHub); a header note
  now points readers to `sprint1_report.md` as the living report.
- **Living tracker added (`docs/progress.md`).** Division of labor: the plan
  holds scope and schedule (rare, deliberate edits), `progress.md` holds
  sprint/milestone status and the current checklist (updated constantly), and
  `sprintN_report.md` files remain the evidence of record. This keeps one
  authoritative place per question (what / now / what happened) instead of
  re-editing the plan or the README on every status change.
- **`make clean` keeps committed demo artifacts.** It used to delete
  `docs/results/art_quickstart_results.json` and `docs/figures/art_*` along
  with the caches, leaving a dirty working tree for no benefit — those files
  are committed reference outputs that `make demo` regenerates anyway. Clean
  removes only caches and `mlruns/` now.
- **Generated JSON ends with a newline.** `scripts/art_quickstart.py` now
  writes a trailing newline after `json.dump`, so `make demo` output matches
  the pre-commit `end-of-file-fixer` instead of leaving a one-byte diff in
  the committed artifact (found by running `pre-commit run --all-files`).

## Pre-merge audit (2026-10-15, Linux, Python 3.11.16)

- **Demo/test outputs are caller-supplied.** `run_demo(args, output_dir=...)`
  now writes results/figures/mlruns under `output_dir`; the smoke test uses
  pytest `tmp_path`. Fixes the Sprint 1 known issue where `pytest` overwrote
  the committed `docs/results` + `docs/figures` artifacts (reproduced before
  the fix, clean `git status` after).
- **Dashboard copied into the Docker image + `.dockerignore` added.** Compose
  mounts `./dashboard` at runtime, but the image is now self-contained; the
  ignore file keeps local builds small (`.venv`, data, docs, mlruns excluded
  from the context). No behavior change for CI.
- **API smoke test added.** `tests/test_api_health.py` covers `/health`
  (function + route registration) without adding `httpx`/TestClient deps.
- **Sprint 1 literature notes drafted.** `docs/literature/anderson_2018_ember.md`
  and `docs/literature/sharafaldin_2018_cicids2017.md` (templates were the only
  literature artifacts committed before). Numbers verified against the papers;
  marked draft for SS-A/SS-B review. Also corrected the Grosse et al. title in
  `reading_list.md` and added the CICIDS2017 data-quality critique (Engelen et
  al., 2021).

## Sprint 2 — Data pipeline (2026-10-25)

- **Datasets are read in place; nothing is downloaded or copied.** Resolution
  order is CLI `--source` > `EMBER_DATA_DIR` / `CICIDS_DATA_DIR` > repo-local
  `data/raw/<dataset>` > `~/Documents/<dataset>`. `src/config.py` owns the
  helpers; library code never hard-codes a personal path. The local copies are
  EMBER2018 feature v2 (not EMBER2024) and the eight original UNB/CIC CSV files
  (no Kaggle "cleaned" variant).
- **Manifest-based versioning instead of DVC/Git LFS.** Neither tool is
  installed and no remote is configured. Each run writes a JSON manifest with
  source names/sizes/SHA-256, row/label/split counts, feature dimensions, the
  preprocessing configuration and seed, output artifact hashes, UTC timestamp,
  and code revision. Compact full-run manifests are committed under
  `docs/data/manifests/`; arrays stay in gitignored `data/processed/`. DVC can
  later wrap the same directories without changing the loader API.
- **EMBER vectoriser is a clean-room implementation.** The published
  `elastic/ember` extraction code is AGPL-3.0, incompatible with this MIT
  repository. `src/data/ember.py` was written from the published 2381-dim
  specification. It uses `sklearn.feature_extraction.FeatureHasher` with the
  official `n_features`/`input_type` and default signed hashing. The raw EMBER
  data files themselves are MIT-licensed.
- **EMBER validation is time-based.** The official 200k test set is preserved
  untouched and never used for fitting/tuning. Labeled train records are sorted
  by `appeared` (then `sha256`) and the latest ~15% becomes validation. If that
  global split leaves a class missing/too small, the code falls back to the
  latest ~15% within each class and records `strategy = per_class_time`. Rows
  sharing a `sha256` are kept in the same split; train/val copies that duplicate
  official test hashes are removed and counted. On the local EMBER2018 copy
  there are zero duplicate sha256 values across all 1,000,000 records.
- **CICIDS cleaning choices.** UTF-8 with `errors="replace"` was selected after
  a probe (all eight files decode as UTF-8; latin-1 is the fallback). Column
  names are stripped (`65/79` headers had leading spaces), the
  `Fwd Header Length.1` column is verified identical to `Fwd Header Length`
  (2,830,743 rows checked, 0 mismatches) and dropped, web-attack U+FFFD labels
  are canonicalised, and `+/-inf` becomes NaN before rows with any NaN are
  dropped. Invalid rows are 2,867 (0.1013%), below the 1% safety threshold.
- **CICIDS duplicate detection is at stored float32 precision.** Exact
  duplicate rows are removed globally before splitting so no identical row can
  appear in two splits. Casting to the saved `float32` representation collapses
  rows that differ only beyond float32 precision; those rows are
  indistinguishable to a model, so they are treated as duplicates. The full run
  removed 330,614 such rows (203,796 within a file, 126,818 across files).
  An independent raw `float64` scan found 307,775 duplicate rows; the briefing's
  approximate ~254,479 was not reproducible with the local original CSVs, so the
  measured counts are reported instead. 5,228 identical feature rows had
  conflicting labels at float32 (5,052 at float64); the first occurrence is kept
  and the conflict count is recorded.
- **CICIDS split and scaling.** 70/15/15 stratified on the binary target with
  seed 42. Multiclass labels and a sorted mapping are preserved, but splits are
  not forced to include rare classes (Heartbleed is absent from validation in
  the full run). No resampling or class weighting is applied; Sprint 3 owns
  modelling decisions. The scaler is fitted on train only; zero-variance
  columns use `scale = 1`.
- **Subset manifests never masquerade as full runs.** `--max-samples` marks the
  manifest `subset: true`; for EMBER the sample is drawn before vectorisation
  (per source partition, stratified by label), while CICIDS samples cleaned,
  deduplicated rows. Full manifests are published to `docs/data/manifests/` only
  when the output directory is the default processed directory.
- **One-process CICIDS cleaning, multi-process EMBER vectorisation.** CICIDS
  dedup is global, so `--jobs` applies only to EMBER. EMBER metadata is scanned
  in parallel, final arrays are preallocated as `.npy` memmaps and atomically
  renamed after all workers finish, keeping peak memory bounded.
- **Ruff `UP017` suppressed for `datetime.timezone.utc`.** The project supports
  Python 3.10, where the `datetime.UTC` alias does not exist; `# noqa: UP017`
  keeps the 3.10–3.12 compatibility promised in the README/AGENTS.

## Repository maintenance (2026-10-26)

- **The README is an entry point, not the manual.** Setup/verification/demo/
  services moved to `docs/development.md`, and the data pipeline moved to
  `docs/data/README.md`. This keeps the root README short while preserving one
  authoritative place for operational detail.
- **Make targets are the command source of truth.** CI now calls `make lint`
  and `make test`; `make lint` includes `ruff format --check` so formatting is
  enforced remotely as well as by pre-commit. `make` resolves the repo venv
  automatically and falls back to the system Python.
- **Local dashboard defaults to `http://localhost:8000`.** Compose still sets
  `API_URL=http://api:8000` for the container network, so local development no
  longer requires an environment variable that only worked inside Docker.
- **`data/external/` is tracked with a `.gitkeep`.** `src/config.py` creates and
  documents the directory, so the ignore rule now excludes its contents instead
  of the directory itself. Unused `.env` template entries (`PYTHONPATH`,
  `SEED`, `MLFLOW_TRACKING_URI`) were removed because compose does not read
  them.
