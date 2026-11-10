# Security audit — Adversarial-Resilient

## Current follow-up assessment — 2026-11-11

This section supersedes the historical Sprint 2 assessment below for the current
`main` application. Historical tool results are retained as dated evidence, not
claimed as checks performed again today.

### Executive summary

Assessed the Sprint 3 read-only FastAPI artifact service, HTML/JS dashboard,
legacy Streamlit client, training/data CLIs, manifests/loaders, dependencies,
Docker/Compose, CI and existing security tests. Starting point: clean worktree at
`main` commit `2ad0d2e`; work is on `fix/security-audit-followup` because repository
instructions prohibit direct pushes to `main`. The initially checked-out Sprint 4
branch was clean and was not modified or merged; its prediction code is **not**
covered by this assessment.

No confirmed critical or high remotely exploitable application vulnerability was
established on this branch. Fixed a training-integrity verification gap, bounded
aggregate run responses, and improved handling of malformed/non-regular artifacts.
Added 15 regression cases. Full suite: **290 passed, 3 skipped**, **89% combined
line/branch coverage**. Lint, dependency audit, medium/high Bandit scan, image
build and fixed HIGH/CRITICAL container vulnerability scan passed.

Principal remaining risks: unauthenticated research/MLflow services if exposed,
trusted local artifact writers, unsigned manifests, unresolved dependency
reproducibility, and the legacy optional CleverHans environment. These fixes do
not establish production readiness or compliance.

### Scope and methodology

**Architecture:** Python 3.11–3.12, CPU torch, scikit-learn, NumPy/pandas, ART,
FastAPI/Starlette/Uvicorn, plain HTML/CSS/JS, legacy Streamlit, local MLflow file
tracking. No application database, accounts, roles, tenants, cookies, login,
password recovery, JWT/OAuth, webhooks, uploads, or state-changing HTTP routes.
Training is operator-invoked; the API reads reports, not models or dataset arrays.
MLflow is a separate, unauthenticated tracking service with write capabilities.

**Reviewed surfaces:** `api/main.py`, `api/artifacts.py`,
`src/evaluation/{artifacts,binary}.py`, `src/models/{training,tabular}.py`,
`src/data/` loaders/preprocessing and parsing paths, `src/config.py`,
`scripts/` CLI/network/subprocess/output paths, `dashboard/client.py`,
`dashboard/app.py`, `dashboard/web/`, all requirements files, Docker/Compose,
environment examples, Makefile, pre-commit/CI configuration, tests and security
documentation. Review combined source inspection, dangerous-operation searches,
synthetic test execution and local container checks; it is not exhaustive formal
verification or a live penetration test.

**Trust model:** see [implementation boundaries](../threat_model_v0.1.md).
Unauthenticated network callers select allowlisted artifacts; locally supplied
files cross parser and training boundaries. Availability and experiment integrity
are the important assets. Filesystem writers and operator-selected URLs/tracking
URIs remain trusted. STRIDE tampering/DoS cases drove the new regressions.

**Official guidance consulted during this review:**
[OWASP Top 10:2025](https://owasp.org/www-project-top-ten/),
[ASVS 5.0.0](https://asvs.owasp.org/),
[OWASP DoS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html),
and [NIST SSDF 1.1](https://csrc.nist.gov/Projects/ssdf).
Mappings below are category-level; no ASVS certification or invented requirement
IDs/CVSS scores are asserted.

**Commands actually executed:**

```bash
git status --short --branch
git branch -vv
make lint
make test
make coverage
make security
.venv/bin/python -m pip check
.venv/bin/python -m pytest tests/test_artifact_security.py tests/test_sprint3.py \
  -k 'nonfinite or aggregate_budget or symlink_loop or named_pipe or actual_training_filename' --tb=short
.venv/bin/python -m pre_commit run --all-files
node --check dashboard/web/app.js
git diff --check
docker build -t adversarial-resilient:security-followup .
docker run --rm --cap-drop ALL --security-opt no-new-privileges \
  adversarial-resilient:security-followup python -c \
  'import os; from api.main import app; print("uid", os.getuid()); print("routes", len(app.routes))'
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy@sha256:790fd66d1697395d8693d1acaa1ea702406a20f109b6fc7bac8db623eca6c06c \
  image --scanners vuln --severity HIGH,CRITICAL --ignore-unfixed \
  --exit-code 1 --no-progress adversarial-resilient:security-followup
```

An inline Python regex scan inspected current tracked files for private-key,
AWS access-key, GitHub-token and Slack-token prefixes, printing filenames/counts
only: **0 matching files**. This is a limited signature scan, not an entropy,
generic-password, or renewed Git-history scan. Pre-commit private-key checks
also passed. No credential was discovered or rotated.

### Findings

| ID | Classification | Severity | Status |
|---|---|---|---|
| SEC-16 | Confirmed training-integrity verification weakness | Medium | Fixed and verified |
| SEC-17 | Confirmed aggregate resource-consumption weakness | Medium | Fixed and verified |
| SEC-18 | Confirmed malformed/special-file availability weakness | Low | Fixed and verified for tested cases |
| SEC-02/09 | Unauthenticated shared deployment | High if externally exposed | Mitigated by loopback defaults; operator action required |
| SEC-10 | Transitive dependency reproducibility | Medium | Identified, not fixed |

#### SEC-16 — Verification was not bound to actual training inputs

- **Affected/root cause:** `src/models/training.py::train_baselines` hashed
  manifest-selected paths, then loaders opened canonical filenames instead.
  Required records could also omit `sha256` because the general manifest
  verifier intentionally treats absent hashes as optional.
- **Evidence/conditions:** synthetic manifests redirected `train_X`, `val_y`
  and `feature_names` records to byte-identical decoys. All three training
  attempts succeeded before the fix instead of rejecting the mismatch. This
  requires supplying/editing local processed artifacts, not an HTTP request.
- **Impact:** canonical inputs can differ from what was verified, undermining
  tamper detection and experiment provenance; no remote code execution claim.
- **Fix:** require canonical filenames and lowercase 64-character hexadecimal
  SHA-256 digests for every required input before hashing/loading/training.
- **Verification:** three decoy cases and five missing/malformed digest cases
  now reject before creating model outputs; existing training/tampering tests
  pass, including legitimate four-model training and MLflow logging.
- **Residual:** hashes are not signatures; replacing the manifest and all data
  remains possible for a trusted-directory writer. Concurrent file mutation
  between verification and loading is not solved; restrict directory access.
- **Mapping:** OWASP A08:2025 Software or Data Integrity Failures.

#### SEC-17 — Per-file limits did not bound aggregate run responses

- **Affected/root cause:** `src/evaluation/artifacts.py::ArtifactStore.runs`
  collected up to 100 files of up to 2 MiB each and forwarded extra run fields.
  The count limit did not bound accumulated JSON/serialization memory. Sorting
  the complete directory also retained every filename in memory.
- **Evidence/conditions:** five valid synthetic reports with 900,000-byte extra
  fields produced a **4,543,861-byte** HTTP response, exceeding the existing
  Streamlit client's 4 MiB limit. Larger local result histories amplify each
  unauthenticated request's memory/CPU cost. No exhaustion attack was run.
- **Impact:** avoidable response/memory amplification and legitimate dashboard
  failures. Exploitability depends on result sizes/history or local artifact
  write access; this is not arbitrary remote file injection.
- **Fix:** conservative 4 MiB serialized-response budget, whole-batch
  truncation with the existing `truncated` field, and bounded-memory selection
  of the newest filenames. Existing per-file and batch-count caps remain.
- **Verification:** the same fixture returns valid nonempty results within
  4 MiB and `truncated: true`; existing reference/dedup/dashboard tests pass.
- **Residual:** enumeration and repeated invalid-batch parsing still consume
  resources. Public deployment needs proxy request/concurrency budgets and
  possibly caching/pagination, not only this per-response control.
- **Mapping:** OWASP A06:2025 Insecure Design; CWE-400.

#### SEC-18 — Numeric overflow and special filesystem artifacts

- **Affected/root cause:** `ArtifactStore.json/read` rejected `NaN` but not
  finite-looking exponent literals such as `1e999` that Python parses as
  infinity. Opening a FIFO could block before the byte cap applied; path
  resolution of symlink loops escaped the expected artifact error handling.
- **Evidence/conditions:** before fixes, positive/negative exponent overflow
  reached JSON response serialization and raised a server error; a guarded
  FIFO test detected an attempted blocking open (no actual hang induced),
  and a self-link raised `RuntimeError`. Requires malformed local artifacts.
- **Impact:** individual artifact unavailability, repeated error logging, and
  potential worker starvation when non-regular files are present.
- **Fix:** finite float parsing at all JSON nesting levels, regular-file
  checks before opening, and normalization of resolution errors.
- **Verification:** seven cases cover overflow, existing NaN/Infinity rejection,
  FIFO and symlink-loop handling; overflow now returns generic HTTP 503.
- **Residual:** trusted-directory assumption remains, including stat/open races;
  no claim that arbitrary hostile concurrent filesystem mutation is safe.
- **Mapping:** OWASP A10:2025 Mishandling of Exceptional Conditions; CWE-400.

### Changes implemented

- `src/models/training.py`, `tests/test_sprint3.py`: input identity/digest
  requirements and eight training regression cases.
- `src/evaluation/artifacts.py`, `tests/test_artifact_security.py`: aggregate
  response budget, bounded filename selection, finite-number and special-file
  rejection, seven artifact regression cases.
- `api/README.md`, `docs/threat_model_v0.1.md`, `docs/progress.md`, this report: limits, trust
  assumptions, current scope and verification evidence. Pre-commit removed
  pre-existing trailing whitespace from `docs/sprint3.md`.
- No dependencies, environment variables, endpoints, schemas, migrations or
  deployment privileges changed. Existing valid canonical manifests work;
  hand-authored training manifests lacking hashes or using alternate filenames
  now deliberately fail closed. Large run lists use the existing truncation
  signal rather than failing the entire dashboard response.
- New tests run automatically in the existing CI pytest/coverage job. Existing
  pip-audit, Bandit and container-scan gates were retained without suppressions.

### Verification results

| Check | Actual result |
|---|---|
| Baseline lint/tests | Passed; 275 passed, 3 skipped; existing third-party deprecation warnings |
| Pre-fix targeted regressions | 8 failed, 2 passed (existing NaN/Infinity controls); safe synthetic reproduction |
| Final full coverage suite | Passed; 290 passed, 3 skipped; 89% combined line/branch coverage |
| Lint and formatting | Passed |
| `make security` | Passed before/after; pip-audit requirements resolution: no known vulnerabilities; Bandit: no medium/high findings |
| Installed dependency consistency | `pip check` passed |
| JS syntax | `node --check` passed; not a browser execution test |
| Pre-commit | Initial run corrected pre-existing trailing whitespace in `docs/sprint3.md`; final all-files run passed all hooks |
| Focused final tests | Documentation links and artifact/training suites: 65 passed after documentation edits |
| Secrets | Limited current-tree signature scan: 0 matches; private-key hook passed |
| Container build/startup | Passed; install layers cached, current source copied; import runs as UID 1000 with capabilities dropped |
| Trivy fixed HIGH/CRITICAL | Passed; Debian 13.7 and Python packages including CPU torch/torchvision: 0 in this filtered scan |
| Optional real-data tests | 3 skipped, not exercised |
| Raw/unfixed image scan | Not repeated; historical unfixed counts below are not current counts |
| Public infrastructure, TLS/auth proxy, full Compose workflows, browser DAST, sustained load, remote CI | Not assessed in this follow-up |

The default pip-audit requirements do not include optional CleverHans or CPU
torch requirements; installed CPU wheels were covered by the image scan, not a
renewed OSV query. No new dependency advisory requiring a pin change was found
in the checks actually run. A filtered clean scan is not proof of safety.

### Remaining risks and action items

1. **Mitigated, not resolved — shared exposure (operator):** retain loopback
   bindings. Before remote access, protect **both** API/dashboard ports and
   MLflow with authenticated TLS, resource budgets and access logs. Verify from
   another host that unauthenticated artifact and MLflow requests are denied.
   Host validation is not authorization; reports may contain local provenance.
2. **Identified, not fixed — artifact trust (operator/data owner):** restrict
   write permissions on source, processed, model, docs/results and MLflow
   directories. Validate provenance out of band. Do not load untrusted joblib
   checkpoints; this branch writes them but does not load them over HTTP.
3. **Identified, not fixed — supply chain (maintainers):** transitive packages
   lack a hash-pinned lock; CPU index installation still resolves dependencies
   across configured indexes. Evaluate platform-specific locks/approved wheel
   mirrors. Re-run audits on updates; no silent wholesale upgrades were made.
4. **Previously identified, not re-audited — CleverHans:** isolated optional
   TensorFlow/Keras environment has historical advisories. Keep it off network
   services and untrusted inputs; replace/update only with compatibility tests.
5. **Partially verified — operations:** official MLflow image remains privileged
   relative to the API (root, no capability drop); monitoring, retention,
   backups, TLS termination and production configuration were not inspected.
6. **Not assessed — other branches:** separately audit Sprint 4 authentication,
   prediction/model-loading and compute controls before merging/exposing them.

### Security verification checklist

| Area | Status and evidence |
|---|---|
| Identity, roles, tenants, sessions | Not applicable to current read-only application; MLflow exposure remains operational risk |
| Authorization | Partially verified: identifier allowlists/path containment tested; no identity boundary for private deployments |
| Injection/browser | Partially verified: template escaping/CSP reviewed and header tests pass; no shell/SQL sink from requests; no browser DAST |
| API/HTTP | Verified for tested Host/header/404/405/500, fixed identifiers and aggregate-budget cases; public abuse limits not verified |
| Database | Not applicable: no application DB or migrations |
| Secrets/crypto | Partially verified: limited signature/private-key scans; no custom authentication crypto; history not rescanned |
| File handling | Partially verified: containment/special files/finite JSON tested; concurrent hostile writers excluded |
| Training integrity | Verified for canonical input/digest regressions; unsigned publisher trust unresolved |
| Dependencies | Partially verified: requirements audit and filtered image scan passed; optional environment/unfixed CVEs not rechecked |
| Infrastructure/CI | Partially verified: non-root image import and existing configuration tests; remote deployment/CI not observed |
| Logging/error handling | Partially verified: generic API errors tested; centralized monitoring absent |
| Business logic | Partially verified: training provenance tested; no payments/accounts/transactions |
| Threat modeling | Verified at documented boundary/STRIDE level; not a full adversarial-ML reassessment |

---

## Historical assessment — 2026-10-26 (Sprint 2)

**Date:** 2026-10-26
**Status:** Initial application-security baseline complete; residual risks
remain (see the end of this report).
**Scope:** Entire repository at the Sprint 2 state: `src/` data pipeline,
`scripts/`, FastAPI service, Streamlit dashboard, Docker/Compose stack,
dependency manifests, pre-commit/CI, and documentation.
**Out of scope:** adversarial-ML evasion research itself (covered by
[`../threat_model_v0.1.md`](../threat_model_v0.1.md)), live malware handling,
production infrastructure, external identity providers, and a full penetration
test.

## Executive summary

The project is a CPU-only ML research repository whose runnable surface is a
FastAPI `/health` placeholder, a Streamlit placeholder, a local MLflow stack,
and dataset preprocessing/demo scripts. There is no authentication,
authorization, user data, database, file-upload endpoint, or model-serving
endpoint yet.

The audit found and fixed:

- **Vulnerable pinned dependencies** across the old stack, including a critical
  `torch` model-loading advisory, multiple MLflow file-store/trace/server issues,
  Pillow image-parser issues, Starlette form/Host issues, and a Streamlit
  Windows SSRF advisory. The project now resolves with no known Python
  vulnerabilities (`pip-audit`), and OSV reports no entries for the CPU
  torch/torchvision versions.
- **Insecure Compose exposure**: the old stack published API, dashboard, and
  unauthenticated MLflow on every host interface. Published ports now bind to
  `127.0.0.1` by default, API/dashboard drop all capabilities, and MLflow is
  documented as requiring a TLS/auth proxy before exposure.
- **Missing HTTP hardening**: the API now validates `Host`, emits standard
  security headers (including CSP and conditional HSTS), uses no-store JSON
  responses, can hide generated docs, and suppresses the Uvicorn server header.
- **Dashboard URL/response handling**: the placeholder previously passed
  `API_URL` straight to `urlopen` and read an unbounded response. It now accepts
  only absolute `http`/`https` URLs without credentials, query, fragment,
  backslashes, or control characters, requires JSON, and caps the response.
- **Manifest path traversal/symlink escape** in artifact verification, plus
  predictable atomic temp-file names. Both are now contained/randomized.
- **Container and CI hardening**: base image digest and pip version pinned,
  compiler toolchain removed, pip removed from the runtime image, least-privilege
  Compose settings, healthchecks, SHA-pinned GitHub Actions, a CI security job,
  Dependabot, and a pinned Trivy image scan.
- **Regression coverage**: security tests for API headers/Host/docs (including
  400/404/405/500 responses), dashboard URL/redirect validation (including
  malformed IPv6 targets), manifest containment, and static Docker/CI
  invariants.

Verification: `make lint` passes; `make coverage` passes with **258 passed, 2
skipped** (the skips are the opt-in real-data checks) and **91% line/branch
coverage**; `make security` reports no known vulnerabilities and no
medium/high Bandit findings; the Docker image
builds and runs as UID 1000; the container returns the expected headers and
rejects an unknown Host; Trivy reports no fixed HIGH/CRITICAL Python or OS
vulnerabilities in the final image (`--ignore-unfixed`).

The main remaining risks are operational: there is no authentication/TLS in the
Compose stack (loopback-only by default), the official MLflow container runs as
root and has no built-in auth, and 44 HIGH Debian base-image advisories had no
vendor fix at scan time. The full three-service stack was started for health
checks, but browser UX, MLflow artifact/model workflows, and sustained load
were not exercised. These are documented below with required external actions.

## Scope and methodology

### Components inspected

- `api/main.py` and `api/README.md` (HTTP entry point, docs, health).
- `dashboard/app.py` and `dashboard/client.py` (browser-facing placeholder).
- `src/config.py`, `src/utils/seed.py`, `src/models/`, `src/data/*` (paths,
  dataset resolution, JSON/CSV parsing, manifests, atomic writes, `np.load`).
- `scripts/preprocess.py`, `scripts/eda_datasets.py`,
  `scripts/art_quickstart.py` (CLI arguments, filesystem operations, MLflow,
  torchvision download, exception paths).
- `requirements*.txt`, `Dockerfile`, `docker-compose.yml`, `.dockerignore`,
  `.env.example`, `Makefile`.
- `.github/workflows/ci.yml`, `.github/dependabot.yml`,
  `.pre-commit-config.yaml`.
- Tests and documentation, including the generated manifests and threat model.

### Standards and references

- OWASP Top 10:2025 categories, at category level.
- OWASP ASVS 5.0 chapters, at area level (no claim of full compliance or
  requirement-level certification).
- OWASP Cheat Sheets: HTTP security headers, SSRF prevention, file/path
  handling, secrets management, dependency/supply-chain guidance.
- NIST SSDF practices for secure build, dependency management, and
  verification.
- Framework/vendor advisories: PyPI advisory DB via `pip-audit`, OSV.dev,
  GitHub Security Advisories, Debian/Trivy vulnerability data.

### Tools and commands actually executed

```bash
# Baseline
git status --branch --short
make lint
make test
bandit -r src scripts api dashboard -f txt -q
pip-audit --local --progress-spinner off --desc
detect-secrets scan --all-files --exclude-files '...'
git rev-list --all | git grep -I -E '<credential patterns>'

# After remediation
make lint
make test
make security                    # pip-audit -r requirements-dev.txt + bandit
pip-audit -r requirements.txt --progress-spinner off
pre-commit run --all-files
docker build -t adversarial-resilient:sec-audit-final2 .
docker run -d --rm -p 127.0.0.1:18001:8000 adversarial-resilient:sec-audit-final2
curl -D - http://127.0.0.1:18001/health
curl -H 'Host: evil.example' http://127.0.0.1:18001/health
docker exec <container> id
docker exec <container> python -m pip check
make docker-scan                 # pinned Trivy image, --ignore-unfixed
docker compose --env-file .env.example config --quiet   # with temporary .env
python3 -m pytest tests/test_api_security.py tests/test_dashboard_security.py \
  tests/test_manifest_security.py tests/test_security_config.py -q
```

### Limitations

- No production or public deployment was tested. The Compose stack is a local
  development stack.
- The full three-service Compose stack was started on loopback with a
  temporary `.env`; API, dashboard, and MLflow health endpoints all returned
  200. The temporary `.env` and generated `mlruns/` were deleted afterward.
  Browser UX, MLflow artifact/model workflows, and sustained load were not
  exercised.
- The dashboard health probe used Streamlit's `/_stcore/health`, which reports
  200 when the runtime is ready even if the app script cannot import. A
  follow-up entrypoint check found that the documented
  `streamlit run dashboard/app.py` command could not import the `dashboard`
  package because the repository root was not on `sys.path`. Commands now use
  `python -m streamlit run ...`, and Compose probes
  `/_stcore/script-health-check`, which executes the script and fails on
  import/run errors. A regression test launches the real CLI; a rebuilt
  api/dashboard stack reported both containers healthy and the script probe
  returned `ok`.
- Real-dataset tests were not run (`RUN_REAL_DATA_TESTS` unset); two optional
  checks are skipped by design.
- No DAST/fuzzing or external penetration test was performed. Container
  behavior was checked locally only.
- `pip-audit` cannot resolve the `+cpu` torch wheels from PyPI; torch and
  torchvision were queried separately against OSV.dev.
- Trivy was run manually and in CI config; the audit did not prove absence of
  all vulnerabilities. A clean scan is not a security guarantee.

## Findings

Severity is qualitative and considers the current placeholder surface, the
default loopback Compose configuration, and the features that will be added
later. No CVSS vectors are asserted because exploitability depends on
deployment and on features not implemented yet.

| ID | Title | Severity | Status |
|---|---|---|---|
| SEC-01 | Known-vulnerable dependency pins (incl. critical torch/MLflow advisories) | High | Fixed and verified |
| SEC-02 | Unauthenticated services published on all interfaces | High (if exposed) | Mitigated by loopback default; external action required for public use |
| SEC-03 | Missing HTTP Host validation and security headers | Medium | Fixed and verified |
| SEC-04 | Dashboard accepted arbitrary URL schemes and unbounded responses | Medium | Fixed and verified |
| SEC-05 | Manifest artifact paths could escape the manifest root | Medium | Fixed and verified |
| SEC-06 | Predictable atomic-write temp paths | Low | Fixed and verified |
| SEC-07 | Container build/runtime hardening gaps | Medium | Fixed; one image-verification gap remains |
| SEC-08 | CI/supply-chain checks were incomplete | Medium | Fixed and verified locally |
| SEC-09 | No authentication/authorization/rate limiting/TLS for future endpoints | High (future exposure) | Not applicable today; residual risk |
| SEC-10 | No lockfile/hashes for transitive dependencies | Medium | Residual risk |
| SEC-11 | Debian base-image advisories without vendor fixes | High (raw scan) / Low in this runtime | Residual risk |
| SEC-12 | No centralized security-event monitoring/audit trail | Low | Residual risk |
| SEC-13 | Secrets scan findings | Informational | False positives only; no secrets found |
| SEC-14 | CORS/CSRF posture | Informational | Verified/N/A |
| SEC-15 | Future model-loading safety | Informational | Guideline |

### SEC-01 — Known-vulnerable dependency pins

**Affected:** `requirements.txt`, `requirements-dev.txt`, `Dockerfile`, the
compose MLflow image.

**Description:** The pre-audit environment pinned versions with public
advisories. `pip-audit` reported **157 advisory rows** (not a unique-CVE count)
across `mlflow==2.15.1`, `Pillow==10.4.0`, `setuptools==75.8.0`,
`starlette==0.38.6`, `streamlit==1.39.0`, `python-dotenv==1.0.1`, and
`pyarrow==15.0.2` (transitive). `pip-audit` skipped the `+cpu` torch wheels, so
OSV was queried separately: `torch==2.4.1` had multiple entries including
**GHSA-53q9-r3pm-6pq6 (CRITICAL, `torch.load` with `weights_only=True`)** and a
local DoS. Representative fixes included MLflow file-store path traversal and
trace authorization issues, an MLflow pickle-guard bypass, Pillow heap
overflows/DoS, Starlette multipart/Host issues, and a Streamlit Windows SSRF.

**Evidence and conditions:** The vulnerable code is only reachable when the
corresponding feature is used. The current API does not parse forms, serve static
files, load models, or deserialize pickles. However, the Compose MLflow service
was reachable on all interfaces by default, and future model-loading code would
reintroduce the torch risk.

**Impact:** RCE, path traversal, SSRF, model/artifact tampering, memory
exhaustion, and denial of service, depending on exposure and feature use.

**Root cause:** Stale pins from the Sprint 1/2 environment, with no automated
dependency audit.

**Remediation implemented:** Upgraded the runtime and dev stacks
(`mlflow==3.17.2`, `Pillow==13.0.0`, `starlette==1.10.0`,
`streamlit==1.66.1`, `torch==2.14.1+cpu`, `torchvision==0.29.1+cpu`,
`setuptools==84.2.1`, `pytest==9.1.1`, etc.); scoped the CPU torch index to
`requirements-torch.txt`; made MLflow's file store an explicit opt-in; removed
`pip` from the final image to eliminate vendored package findings.

**Verification:** `pip-audit -r requirements-dev.txt` reports **no known
vulnerabilities**; OSV queries for torch 2.14.1 and torchvision 0.29.1 report
**0 entries**; tests and the ART synthetic demo pass.

**Residual:** No lockfile or hash-pinned transitive set; future transitive
updates can introduce new risk. Dependabot and `make security` are the ongoing
controls. The separate optional `requirements-cleverhans.txt` environment is
still pinned to TensorFlow/Keras 2.15 and `pip-audit` reports 25 advisories
(Keras 2.15, protobuf 4.25.9). It is not installed by default, has no runtime
role, and must not process untrusted input; replacing/removing the optional
cross-check is the clean long-term fix.

**Mapping:** OWASP A03 Software Supply Chain Failures; A08 Software and Data
Integrity Failures; ASVS V13/V14/V15 areas; CWE-1104 (use of unmaintained
third-party components) and the specific CWE classes in the advisories.

### SEC-02 — Unauthenticated services published on all interfaces

**Affected:** `docker-compose.yml` (pre-audit `"<port>:<port>"` mappings for
API, dashboard, and MLflow); `MLFLOW_ALLOW_FILE_STORE` behavior after upgrade.

**Description:** Compose published all three services on every host interface.
MLflow has no built-in authentication, and the dashboard placeholder has no
authentication. Anyone who could reach the host could read/tamper with MLflow
tracking data/artifacts and use the dashboard.

**Impact:** Unauthorized access to experiment metadata/artifacts; possible
model/artifact poisoning; information disclosure. The file-store backend also
had a path-traversal advisory in the old MLflow version (see SEC-01).

**Root cause:** Development defaults were not scoped to localhost; MLflow was
treated as trusted.

**Remediation:** Published ports now use
`"${BIND_ADDR:-127.0.0.1}:..."`; API/dashboard drop all capabilities and set
`no-new-privileges`; the dashboard source mount is read-only; healthchecks and
PID limits were added; MLflow's file store opt-in is explicit; documentation
warns not to set `BIND_ADDR=0.0.0.0` without TLS/auth.

**Verification:** `docker compose config` passes with a temporary `.env`; the
Compose security invariants are covered by `tests/test_security_config.py`.
The full stack was started on loopback: API/dashboard listened on the
configured host ports, MLflow's `/health` returned 200, API/dashboard ran as
UID 1000, and the temporary files were removed afterward.

**Residual:** If an operator sets `BIND_ADDR=0.0.0.0`, MLflow and the dashboard
remain unauthenticated. A TLS reverse proxy with authentication is required.

**Mapping:** OWASP A01 Broken Access Control; A02 Security Misconfiguration;
ASVS V8/V13 areas.

### SEC-03 — Missing HTTP Host validation and security headers

**Affected:** `api/main.py`.

**Description:** The pre-audit API returned responses without
`X-Content-Type-Options`, frame/referrer/permissions policies, CSP, or
`Cache-Control: no-store`; it accepted any `Host` header; docs were always on;
Uvicorn emitted its `Server` header.

**Impact:** Defense-in-depth gaps: clickjacking/MIME-sniffing exposure in
browsers, weaker protection for future path-based authorization that reads the
reconstructed URL, and unnecessary framework fingerprinting. Not directly
exploitable against `/health` alone.

**Root cause:** The Sprint 1 placeholder was intentionally minimal.

**Remediation:** `create_app()` now installs `TrustedHostMiddleware`
(`API_ALLOWED_HOSTS`, safe default) and middleware that adds the headers above;
HSTS is conditional on HTTPS; docs can be disabled with
`API_DOCS_ENABLED=false`; Docker/Compose run Uvicorn with `--no-server-header`.

**Verification:** `tests/test_api_security.py` checks headers on successful,
rejected-Host, 404, 405, and unhandled-500 responses; no CORS header; HSTS
behavior; unknown-Host rejection; custom allowlists; docs disablement; and the
docs CSP exception. The 500 handler returns a generic body without exception
details. Container curl checks confirm the behavior.

**Residual:** No authentication or rate limiting exists because there is no
sensitive endpoint; future endpoints must add them. CSP is intentionally not
applied to Swagger/ReDoc pages so their CDN assets work.

**Mapping:** OWASP A02 Security Misconfiguration; A05 Injection (header/URL
handling context); ASVS V3/V4/V13 areas.

### SEC-04 — Dashboard accepted arbitrary URL schemes and unbounded responses

**Affected:** pre-audit `dashboard/app.py`; new `dashboard/client.py`.

**Description:** The old code used
`urllib.request.urlopen(f"{API_URL}/health")` and displayed the exception.
`API_URL` is operator-controlled, but a misconfigured or compromised
environment could supply `file://`, another scheme, credentials, or a huge
response. Bandit correctly flagged B310 (urlopen scheme risk).

**Impact:** Local file or non-HTTP resource access from the dashboard process,
unexpected network requests, and memory exhaustion from an unbounded response.
The dashboard is a local placeholder, so remote exploitability is limited.

**Remediation:** `validate_api_url()` accepts only absolute
`http`/`https` URLs with a host and no credentials, query string, fragment,
backslashes, whitespace, or control characters; `fetch_health()` requires
`application/json`, a JSON object, a positive timeout, and reads at most 64 KiB;
redirects are only followed within the configured origin (no scheme/host/port
change, no credentials); the app logs details locally but shows a generic
browser error.

**Verification:** 45 tests in `tests/test_dashboard_security.py` cover accepted
and rejected URLs (including malformed IPv6), JSON/content-type validation,
size limits, same-origin redirect enforcement, credential rejection, and
malformed redirect targets. `tests/test_dashboard_app.py` checks the user-facing
invalid-URL and error paths with a fake Streamlit module.

**Residual:** The operator can still point the dashboard at any reachable
HTTP(S) host; this is configuration trust, not an unauthenticated SSRF. An
allowlist can be added if deployment requirements demand it.

**Mapping:** OWASP A01/A10 (SSRF/URL handling) at category level; CWE-918;
ASVS V2/V4 areas.

### SEC-05 — Manifest artifact paths could escape the manifest root

**Affected:** `src/data/preprocessing.py::verify_manifest_artifacts`.

**Description:** The verifier joined `record["file"]` to the artifact root
without containment checks. A manifest with `../../secret`, an absolute path,
or a symlink pointing outside the root could make the process `stat`/hash an
unrelated file.

**Impact:** Information exposure through error/size/hash behavior and
unnecessary file access; not a write primitive. Manifests are often copied or
downloaded independently of the data they describe.

**Remediation:** `_resolve_manifest_artifact()` rejects absolute paths, NUL
bytes, malformed records, and paths/symlinks that resolve outside the resolved
root. `verify_manifest_artifacts()` reports a clear error instead of touching
the file.

**Verification:** `tests/test_manifest_security.py` covers valid/nested files,
`..` and absolute paths, symlink escapes (skipped if unsupported), and malformed
records. Existing manifest/tamper tests still pass.

**Residual:** Hardlinks are not distinguishable by path resolution; manifests
from untrusted sources should still be reviewed. The verifier only reads.

**Mapping:** CWE-22 path traversal; OWASP A01/A05 at category level; ASVS V5
File Handling and V1 Encoding/Sanitization areas.

### SEC-06 — Predictable atomic-write temp paths

**Affected:** `src/data/preprocessing.py` (`atomic_write_bytes`,
`atomic_save_npy`, `open_atomic_memmap`), `src/data/ember.py`,
`src/data/cicids2017.py`.

**Description:** Atomic writers used fixed sibling `<name>.tmp` paths. In a
shared/world-writable output directory, another local process could pre-create
or replace the temp path, causing a write to an unintended file or a collision
between runs.

**Impact:** Local integrity/availability risk; no remote attack path.

**Remediation:** Writers now use `tempfile.mkstemp()` in the destination
directory (unpredictable name, mode 0600), fsync, and `os.replace()`; cleanup
removes the temp file on failure. CSV/DataFrame writes share one helper.

**Verification:** Data pipeline/loader/CLI tests pass, including atomic memmap
and manifest flows.

**Residual:** A process killed mid-write may leave a hidden temp file; the final
path is still never partially published.

**Mapping:** CWE-377; OWASP A01/A02 at category level.

### SEC-07 — Container build/runtime hardening gaps

**Affected:** `Dockerfile`, `docker-compose.yml`, `.dockerignore`.

**Description:** The old image kept `build-essential` in the final layer, used a
mutable `python:3.11-slim` tag, upgraded pip to whatever was latest, copied files
as root before `chown`, published ports on all interfaces, mounted dashboard
source read-write, had no capability drops/PID limits/healthchecks, and retained
pip and its vendored packages.

**Impact:** Larger attack surface, supply-chain drift, and weaker isolation.

**Remediation:** Base image pinned by digest; pip pinned; no compiler
toolchain; `COPY --chown`; non-root `appuser`; pip and its vendored packages
removed after verification; loopback ports; `cap_drop: ALL` and
`no-new-privileges` for API/dashboard; PID limits; read-only dashboard source;
healthchecks; `--no-server-header`; `.dockerignore` excludes `.venv-*` and key
material.

**Verification:** `docker build` succeeds; the final image runs as UID 1000;
`pip check` passed before pip removal; `/health` returns 200 with the expected
headers; an unknown Host returns 400; no `Server` header. Trivy `--ignore-unfixed`
reports 0 fixed HIGH/CRITICAL Python/OS findings.

**Residual:** The MLflow image is pinned by tag and digest; it still runs as
root in the official image and has no built-in authentication. Debian
base-image advisories are covered by SEC-11.

**Mapping:** OWASP A02 Security Misconfiguration; A03 Supply Chain; ASVS
V12/V13 areas.

### SEC-08 — CI and supply-chain checks were incomplete

**Affected:** `.github/workflows/ci.yml`, `.pre-commit-config.yaml`,
dependency update process.

**Description:** Actions were referenced by mutable tags, checkout persisted
credentials, CI had no dependency/static security job, no container scan, no
Dependabot, and pre-commit did not check private keys/JSON/TOML/AST.

**Impact:** Lower resistance to action/tag compromise, unreviewed dependency
drift, and delayed detection of vulnerable or malformed inputs.

**Remediation:** Actions pinned by commit SHA with version comments;
`persist-credentials: false`; `make security` job; `make docker-scan` with a
digest-pinned Trivy image; Dependabot for pip/actions/docker; pre-commit
private-key/JSON/TOML/AST hooks; `make security` and security checks added to
the PR template.

**Verification:** `tests/test_security_config.py` asserts SHA pins, loopback
ports, capability drops, Trivy pinning, and the CI security job. Local
`make security`, `pre-commit run --all-files`, and `make docker-scan` pass. The
GitHub-hosted CI run is not observed in this report.

**Residual:** No lockfile/hashes (SEC-10); no SBOM generation; no scheduled DAST
or image scan outside CI. Dependabot PRs still require review and tests.

**Mapping:** OWASP A03/A08; NIST SSDF secure build/dependency practices; ASVS
V13/V15 areas.

### SEC-09 — No authentication/authorization/rate limiting/TLS for future endpoints

**Affected:** API (`/predict`, `/attack`, `/defend` planned), dashboard, MLflow.
**Status:** Not applicable to today's `/health`-only API; high residual when the
planned endpoints/stack are exposed.

The current API has no user accounts, sessions, tokens, roles, or sensitive
objects, so there is nothing to authenticate or authorize yet. The planned
prediction/attack endpoints will expose model behavior and compute and must add
server-side authentication, authorization, request-size limits, and rate
limiting before leaving localhost. The Compose stack has no TLS terminator;
remote deployment requires a hardened reverse proxy. MLflow basic auth is not
enabled in the current Compose file.

**Mapping:** OWASP A01/A04/A07; ASVS V6/V7/V8/V12 areas.

### SEC-10 — No lockfile/hashes for transitive dependencies

**Affected:** `requirements*.txt`, CI/Docker installs.

Direct dependencies are pinned, but transitive packages are resolved at install
time and no `--require-hashes`/lockfile is used. This is partly forced by the
CPU wheel index and platform-specific wheels. Consequences: a compromised or
newly vulnerable transitive release can enter a fresh build. Mitigations are
the weekly Dependabot PRs, `pip-audit`, Trivy, and the pinned direct set.

**Required action:** Evaluate a generated lock/constraints file with hashes (or
an internal package mirror) when the project moves to production or CI needs
stronger reproducibility.

### SEC-11 — Debian base-image advisories without vendor fixes

**Affected:** final Docker image (`debian 13.7` base).

Trivy reported **44 HIGH, 0 CRITICAL** OS-package findings, all unfixed in the
current Debian 13.7 package set (`--ignore-unfixed` reduces this to 0). They
are primarily `util-linux`/`mount`/`ncurses`/`perl-base` issues. The runtime is
non-root with all capabilities dropped for API/dashboard and no compiler
toolchain, which reduces but does not eliminate exposure. Base-image digest
updates (Dependabot) and periodic scans are required; a future minimal/distroless
runtime should be evaluated.

### SEC-12 — No centralized security-event monitoring/audit trail

The API logs requests via Uvicorn and startup via `logging`; the dashboard logs
failed health checks. There is no authentication/authorization event logging,
centralized audit log, alerting, or retention policy. This is acceptable for a
local placeholder but must be addressed before exposing prediction endpoints or
multi-user MLflow.

### SEC-13 — Secrets scan

`detect-secrets` reported only `Hex High Entropy String` detections (63
occurrences across `docs/data/manifests/*.json` and the `SOURCE_SHA256`
constants in `src/data/ember.py` / `src/data/cicids2017.py`). These are
dataset integrity hashes, not credentials. A Git-history scan for private-key,
AWS, GitHub, Slack, and generic token prefixes produced no matches. No secret
values are reproduced here. `.env` remains gitignored and `.env.example`
contains no credentials.

### SEC-14 — CORS/CSRF posture

The API sets no CORS headers, so browsers do not receive an
`Access-Control-Allow-Origin` grant; this was asserted in the tests. There are no
cookies, sessions, or token-authenticated state-changing endpoints, so CSRF is
not applicable yet. Adding cookies/auth later requires an explicit CSRF design
and a reviewed CORS allowlist; do not assume CORS prevents CSRF.

### SEC-15 — Future model-loading safety

No code currently calls `torch.load`, `pickle.load`, or `joblib.load`;
`np.load` uses `allow_pickle=False`. The torch upgrade removes the known
`weights_only=True` advisory, but future model loading must use safe formats
(e.g., `safetensors`) or `weights_only=True` with a trusted source and verified
hashes. Do not load MLflow artifacts from untrusted stores.

## Changes implemented

| Area | Files | Change |
|---|---|---|
| Dependencies | `requirements.txt`, `requirements-dev.txt`, `requirements-torch.txt`, `requirements-cleverhans.txt`, `scripts/art_quickstart.py` | Upgraded pins; split/scoped CPU torch index; explicit MLflow file-store opt-in; removed pip from runtime image; warning on the optional CleverHans env |
| API | `api/main.py`, `tests/test_api_security.py` | App factory, Host allowlist, security headers, HSTS/CSP/no-store, docs switch, no server header, generic 500 handling; 26 security tests |
| Dashboard | `dashboard/client.py`, `dashboard/app.py`, `tests/test_dashboard_security.py`, `tests/test_dashboard_app.py` | URL/redirect validation, JSON/content-type/size checks, generic error; 49 parameterized/security/UI cases |
| Data | `src/data/preprocessing.py`, `src/data/ember.py`, `src/data/cicids2017.py`, `tests/test_manifest_security.py` | Manifest containment, secure temp files, shared DataFrame writer, git subprocess timeout; 10 security tests |
| Containers | `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.env.example` | Digest/pip pins, non-root/no compiler/no pip, least privilege, loopback, healthchecks, read-only mount, PID limits |
| CI/process | `.github/workflows/ci.yml`, `.github/dependabot.yml`, `.pre-commit-config.yaml`, `Makefile`, `.github/PULL_REQUEST_TEMPLATE.md` | SHA pins, security job, Trivy scan, Dependabot, extra hooks, PR checklist |
| Tests | `tests/test_security_config.py` | Static invariants for deps/Docker/Compose/CI/Trivy |
| Docs | `README.md`, `AGENTS.md`, `api/README.md`, `dashboard/README.md`, `docs/*.md`, this report | Security baseline, env vars, loopback/TLS warnings, verification, residual risks |

No breaking API contract changes were made to existing endpoints. The deliberate
compatibility change is dropping Python 3.10 support (upstream support ends in
October 2026; required by the secure Pillow release). The dashboard error message no longer exposes the
underlying exception text.

## Verification results

### Passed

- `make lint` — ruff check and format check pass.
- `make coverage` — **258 passed, 2 skipped** (the two opt-in real-data
  checks), **91% line/branch coverage**; `make test` also passes.
- `make security` — `pip-audit -r requirements-dev.txt`: no known
  vulnerabilities; Bandit (`-ll`): no medium/high findings.
- `pip-audit -r requirements.txt` — no known vulnerabilities.
- `pip-audit --local` (refreshed dev environment) — no known vulnerabilities;
  torch/torchvision are skipped by pip-audit and covered by OSV below.
- OSV queries for `torch==2.14.1` / `torchvision==0.29.1` — 0 entries.
- `pre-commit run --all-files` — all hooks pass (ruff, formatting, trailing
  whitespace, EOF, YAML/JSON/TOML/AST, private key, large files, merge
  conflicts).
- `docker build` — final image builds successfully.
- Container runtime — runs as `uid=1000(appuser)`; `/health` returns 200; the
  API sends the expected security headers and no `Server` header; an unknown
  `Host` returns 400; `pip check` passed before pip removal.
- `make docker-scan` — pinned Trivy image, `--ignore-unfixed`: exit 0 (no fixed
  HIGH/CRITICAL findings).
- `docker compose config` — valid with a temporary `.env` (removed afterward).
- Full Compose stack — started on loopback with a temporary `.env`; API,
  dashboard, and MLflow health endpoints returned 200; API/dashboard ran as
  UID 1000; MLflow ran as root in the official image; the temporary `.env`
  and generated `mlruns/` were removed.
- `detect-secrets` — no credential findings; only dataset SHA-256 hashes.
- Git-history credential-pattern scan — no matches.

### Failed / inconclusive / not run

- Full Compose stack functional/browser test — **not run**: only health
  endpoints were exercised. MLflow artifact upload/download, model loading,
  dashboard button interaction, and load/soak behavior remain unverified.
- MLflow container isolation — **partially verified**: the official image runs
  as root; Compose only sets `no-new-privileges` and a PID limit. It is on
  loopback by default.
- Two optional real-data tests — **skipped** by default (datasets not exercised
  in this audit).
- GitHub-hosted CI — **not observed** at the time of writing; local equivalents
  passed. The workflow is configured to run lint, tests, security scans, Docker
  build, and Trivy.
- Trivy raw scan — 44 HIGH Debian OS findings with no fixed version; 0
  CRITICAL; Python package findings 0. This is a residual base-image risk, not a
  passing result.
- DAST/fuzzing/external penetration testing — not performed.

### Baseline record

Before changes: `make lint` clean, `make test` 60 passed / 2 skipped, Bandit 1
medium (dashboard `urlopen`) + 3 low (subprocess), `pip-audit` 157 advisory rows
plus skipped torch/torchvision, and OSV confirmed a critical torch issue. These
were pre-existing conditions, not regressions from the audit.

## Remaining risks and action items

Priority order:

1. **Exposed-stack authentication/TLS (external action).** Do not set
   `BIND_ADDR=0.0.0.0` until a TLS reverse proxy with authentication protects
   MLflow and the dashboard. Verify with an external request from another host
   that unauthenticated access is denied.
2. **Future prediction endpoints (code + design).** Before `/predict`,
   `/attack`, or `/defend`: define authn/authz, request-size limits, query
   budgets/rate limits, audit logging, and safe model loading. Add tests for
   unauthenticated, insufficient-permission, cross-user/tenant, oversized, and
   expired-credential cases.
3. **MLflow isolation (external/operator).** The image is now pinned by digest
   and the stack was health-checked, but the official container runs as root and
   has no built-in authentication. Keep it on loopback; for any shared
   deployment, add a TLS/auth reverse proxy and consider a non-root image or
   capability drop after verifying write access to the artifact store.
4. **Base-image vulnerabilities (maintenance).** Track the 44 HIGH Debian
   advisories; bump the pinned base digest when fixes land and re-run
   `make docker-scan`. Evaluate a smaller/distroless runtime for production.
5. **Dependency reproducibility (maintenance).** Decide whether to add a
   hash-pinned lock/constraints file or internal mirror; keep Dependabot PRs
   reviewed and run `make security` on every change.
6. **Monitoring/audit trail (future).** Add structured security-event logging,
   retention, and alerting before multi-user/remote deployment. Never log
   secrets, tokens, raw credentials, or unnecessary personal data.
7. **CORS/CSRF (when auth/cookies arrive).** Add a reviewed origin allowlist
   and CSRF protection appropriate to the session model; CORS alone is not
   CSRF protection.
8. **Hardlink edge case.** Manifest containment cannot detect a hardlink to an
   outside file; only accept manifests from trusted sources.

### Status legend

- **Fixed and verified:** code/config change plus executed tests/checks.
- **Mitigated but not fully resolved:** default/loopback control plus required
  external action.
- **Identified but not fixed:** documented residual requiring a decision,
  external access, or future endpoint.
- **Not assessed:** no evidence was collected.

## Security verification checklist

| Area | Status | Evidence / note |
|---|---|---|
| Authentication and identity | Not applicable today | No accounts/tokens/sessions; future `/predict` must add authn (SEC-09) |
| Authorization and access control | Not applicable today | No objects/roles; loopback protects current MLflow/dashboard (SEC-02, SEC-09) |
| Injection and path handling | Partially verified | Manifest traversal and dashboard URL handling fixed/tested; SQL/command injection N/A (no DB/shell input) |
| API and HTTP security | Verified | Host allowlist, headers, docs switch, no CORS grant, tests (SEC-03) |
| Browser security | Partially verified | API headers/CSP/HSTS verified; dashboard placeholder has no auth and no secrets; full browser DAST not run |
| Database and data protection | Not applicable | No database; dataset hashes/manifests verified; processed data gitignored |
| Secrets and cryptography | Partially verified | No secrets found; no custom crypto; TLS/authentication external (SEC-13, SEC-09) |
| File uploads/processing | Not applicable | No upload endpoint; image/model parsers not exposed; future safe-loading guidance (SEC-15) |
| Dependencies and supply chain | Verified with residual | pip-audit/OSV/Trivy clean for fixed Python issues; no lockfile/hashes; OS base CVEs (SEC-01, SEC-10, SEC-11) |
| Infrastructure and deployment | Partially verified | Image build/run, full-stack health checks, loopback/cap drop/config tests; MLflow runs as root/unauthenticated (SEC-02, SEC-07) |
| Business logic and abuse cases | Not applicable today | No payments/quotas/transactions; future API needs rate/abuse controls |
| Logging, monitoring, error handling | Partially verified | Generic dashboard errors; no traceback exposure; no centralized audit/monitoring (SEC-12) |
| CI/CD and build integrity | Partially verified | SHA pins, security job, Trivy, Dependabot, local `make security`; remote CI run not observed (SEC-08) |
| Threat modeling | Partially verified | Existing ML threat model retained; implementation-security section added |
| Dynamic testing | Partially verified | Local container/header/Host checks only; no DAST/fuzzing/pen test |

## Closing note

This audit found and fixed concrete, evidence-backed issues and added regression
coverage for each significant code-level fix. It does not prove the absence of
all vulnerabilities. The repository remains a research/development stack until
the operational items above — especially authentication/TLS, endpoint hardening,
image verification, and base-image maintenance — are completed.
