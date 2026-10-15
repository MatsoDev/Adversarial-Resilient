# Decisions log (Sprint 1)

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
