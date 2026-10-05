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
