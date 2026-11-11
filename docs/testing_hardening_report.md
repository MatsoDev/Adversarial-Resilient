# Test hardening — 2026-11-11

## Scope and baseline

Assessed clean `main` at `c6c729c`, using the existing Python 3.11.16 virtualenv.
No packages were installed and no datasets or committed generated reports were
changed. Verification preceded the subsequent user-requested Git commits.
The application uses FastAPI, CPU
PyTorch/scikit-learn, local artifact files and MLflow; there is no application
database, account/tenant system or queue. The primary UI is HTML/JavaScript;
Streamlit is legacy. Tests use pytest/pytest-cov, synthetic files, TestClient,
real CPU training/checkpoints and optional Node component checks. CI already
runs lint/format, coverage, dependency/static security checks and Docker build/scan.

Baseline `make coverage`: **304 passed, 3 skipped, 252 warnings, 68.32 seconds**.
Statement coverage: **3034/3307 (91.74%)**; branch coverage: **762/948 (80.38%)**;
combined: **89.21%**. Coverage.py reports executable statements and branches,
not separate function coverage. The three skips are opt-in raw/processed dataset
checks; Node was available and its component test ran. Existing warnings are
third-party matplotlib/pyparsing deprecations. No pre-existing test failure was
observed. Baseline lint, `pip check`, `make security`, JS syntax and Docker build
also passed (Docker dependency-install layers were cached).

## Defects reproduced and fixed

1. **Operating-point correctness.** Default ROC plot simplification discarded
   thresholds inside vertical segments. For labels `[0,1,1,1,1,0]` and scores
   `[.9,.8,.7,.6,.5,.1]`, target TPR 0.5 returned 0.5 instead of the highest
   qualifying threshold, 0.7. A 20-positive example returned the 100%-recall
   threshold instead of the requested 95%-recall threshold. Retaining all ROC
   thresholds fixes selection without changing the metric schema or default
   classification threshold. Existing recorded results are historical; they
   were not regenerated or used for test-driven retuning.
2. **Sprint 4 integrity boundaries.** The generic manifest verifier intentionally
   permits absent hashes, but tuning and frozen loading treated it as mandatory
   integrity verification. Missing train/validation or test digests were accepted;
   missing bundle weights/features digests were accepted, while missing scaler
   digest raised a raw KeyError. Added an opt-in `require_hashes` argument and
   enabled it at these three boundaries. Valid generated manifests still work;
   the generic verifier's existing default behavior is preserved. Invalid local
   manifests now fail closed, before training output creation or before freezing
   after a locked selection, as appropriate. Hashes detect corruption, not an
   untrusted publisher or concurrent hostile filesystem writer.

Before production fixes, the focused regression command returned exit status 1:
**17 failed, 10 passed, 20 deselected in 6.60 seconds**. These are failing cases
for the defect families above, not 17 independent vulnerabilities. Three
malformed nonempty digests already rejected correctly and remain control cases.

```bash
.venv/bin/python -m pytest tests/test_binary_metrics.py tests/test_sprint4.py \
  -k 'threshold or tpr or digest or integrity_failure' --tb=short
```

## Changes

### New tests

- `tests/test_binary_metrics.py`: independent hand-calculated metric values,
  margin scores, threshold equality, tied/permuted rows, undefined single-class
  metrics, invalid shapes/values/targets, highest-threshold and default-95%-TPR
  regression cases.
- `tests/test_prediction_streaming.py`: real asynchronous ASGI body chunks,
  absent/spoofed Content-Length, stopping reads on overflow, exact 2 MiB boundary.

### Improved existing tests

- `tests/test_sprint4.py`: separate named invalid payload/body cases; required
  digests for all six training inputs, both test inputs and all three bundle
  artifacts; preserved selection after test-integrity failure; deterministic
  shared-route rate windows, exact reset, forwarded-header spoof resistance,
  independent socket peers and non-consuming unauthorized requests; inclusive
  raw/scaled numeric limits; real hash-verified constant-logit checkpoints with
  known calibrated scores/labels for 32-row HTTP batches.
- `tests/test_manifest_security.py`: strict digest syntax, opt-in compatibility,
  valid hashes and same-size content corruption.

### Infrastructure and CI

Reused pytest, temporary paths, existing fixtures and existing CI collection.
No dependencies, global coverage thresholds, retries, CI privileges or external
settings changed. The prediction clock fixture changes only the module-local
clock reference, so async I/O clocks remain intact. Testing commands and scope
are documented in [testing.md](testing.md).

### Narrow production fixes

- `src/evaluation/binary.py`: keep all candidate ROC thresholds.
- `src/data/preprocessing.py`: optional mandatory-digest validation.
- `src/models/tuning.py`: require digests for train/validation and gated test.
- `src/models/frozen.py`: require digests for every frozen bundle artifact.

## Final verification

| Check | Result | Executed command / evidence |
|---|---|---|
| New/changed test groups | Pass | `.venv/bin/python -m pytest tests/test_binary_metrics.py tests/test_manifest_security.py tests/test_sprint4.py tests/test_prediction_streaming.py --tb=short`: **92 passed in 11.07s** |
| Previously failing regression selection | Pass | The pre-fix `-k 'threshold or tpr or digest or integrity_failure'` command now reports **27 passed, 45 deselected in 5.44s** |
| Full suite | Pass | `make test`: **376 passed, 3 skipped, 252 warnings in 60.65s** |
| Full coverage suite | Measured, pass | `make coverage`: **376 passed, 3 skipped in 69.18s**; statements **3044/3312 (91.91%)**, branches **769/950 (80.95%)**, combined **89.47%** |
| Unit group | Pass | `.venv/bin/python -m pytest tests/test_binary_metrics.py tests/test_manifest_security.py -q`: **37 passed** |
| Integration/protocol group | Pass | `.venv/bin/python -m pytest tests/test_sprint4.py tests/test_prediction_streaming.py -q`: **55 passed** |
| UI component checks | Pass | `.venv/bin/python -m pytest tests/test_sprint4_ui.py tests/test_html_dashboard.py -q`: **2 passed**, Node available |
| Lint/format | Pass | `make lint`: **65 files already formatted**, Ruff clean |
| Python compilation | Pass | `.venv/bin/python -m compileall -q src api dashboard scripts` |
| Dependency consistency | Pass | `.venv/bin/python -m pip check`: no broken requirements |
| Security tooling | Pass | `make security`: requirements audit found no known vulnerabilities; Bandit reported no medium/high findings |
| JavaScript syntax | Pass | `node --check dashboard/web/app.js` and `node --check dashboard/web/prediction.js` |
| Docker build | Pass | `docker build -t adversarial-resilient:test-hardening .`: current source rebuilt; dependency layers cached |
| Container import/route registration | Pass | Network-disabled, capabilities-dropped container imported app as UID 1000 and exposed `/predict` in OpenAPI |
| Documentation links/diff hygiene | Pass | `.venv/bin/python -m pytest tests/test_docs_links.py -q`: **43 passed**; `git diff --check` clean |
| Type checker / browser E2E / optional real data | Not run | No configured type checker or browser runner; three dataset checks deliberately remain opt-in |

The container smoke command was:

```bash
docker run --rm --network none --cap-drop ALL --security-opt no-new-privileges \
  adversarial-resilient:test-hardening python -c \
  "import os; from api.main import app; assert '/predict' in app.openapi()['paths']; print('uid:', os.getuid()); print('prediction route registered')"
```

An initial ad-hoc container probe failed because it assumed every FastAPI route
object had a `.path` attribute. That was a probe error, not an application failure;
the corrected check above uses public OpenAPI and passed. No production change
was made for that probe. Container vulnerability scanning, full Compose workflows
and remote CI were not rerun/observed in this task.

### Measurable changes

| Metric | Before | After |
|---|---:|---:|
| Passing tests | 304 | 376 |
| Collected cases (including skips) | 307 | 379 |
| Optional skips | 3 | 3 |
| Statement coverage | 91.74% | 91.91% |
| Branch coverage | 80.38% | 80.95% |
| Combined coverage | 89.21% | 89.47% |
| Binary metrics module, combined coverage | 80.00% | 100.00% |
| Full coverage execution time | 68.32s | 69.18s |

The net 72 cases include independently collected replacements for assertions
formerly inside one large API test, plus the new documentation-link case; they
are not 72 newly discovered behaviors. Ten targeted behavior groups now have
explicit checks: highest-TPR threshold, training digests, gated test digests,
bundle digests, exact query window/reset, peer isolation/spoof resistance,
unauthorized-budget isolation, streamed body limits, numeric limits and calibrated
maximum-batch inference. Global coverage gains are modest because baseline
coverage was already high; the value is demonstrated defect detection and
stronger boundary assertions. Execution times are local snapshots, not controlled
performance benchmarks. No flaky test was claimed repaired and no new CI gate
or coverage threshold was introduced.

Raw local logs and machine-readable coverage snapshots are under
`/tmp/opencode/testing-*.log` and `/tmp/opencode/coverage-{baseline,final}.json`.
They are session-local evidence, not repository artifacts. The coverage JSON
was generated with `.venv/bin/python -m coverage json -o <path>` after each run.

## Remaining gaps and next steps

1. **High impact:** keep prediction/MLflow on loopback. Public TLS/auth proxy,
   concurrency/abuse behavior and the full Sprint 4 security assessment remain
   outside these synthetic regression checks. A single research bearer token
   is not multi-user authorization.
2. **Medium:** real datasets and full-data model evaluation were deliberately
   not exercised. Review operating-point effects before creating future
   research evidence; do not silently overwrite reports or retune on test.
3. **Medium:** add a small real-browser workflow for feature entry, token
   failures and recovery. Node/minimal-DOM and HTTP tests are not browser E2E.
4. **Medium:** trusted local file assumptions remain: unsigned manifests,
   stat/open races and special-file model artifacts warrant a separate review.
5. **Lower:** bootstrap/error branches and several neural numerical-rejection
   branches remain untested; there is no configured type checker, function
   coverage, mutation runner or demonstrated flaky-test repair in this change.
   Dependency reproducibility and browser accessibility deserve follow-up.

Full/unit/integration/component commands are in [testing.md](testing.md).
