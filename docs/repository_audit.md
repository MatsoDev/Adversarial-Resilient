# Repository audit — 2026-11-11

## Scope and baseline

Audited the tracked tree, relevant ignored artifacts, repository instructions,
Python/JavaScript entry points and dependencies, tests, docs, build/container
configuration and Git workflow. No dependencies were installed or upgraded.
The repository has no package build, database/migrations, frontend bundler or
separate type checker. Existing Ruff, pytest/coverage, security tools, Node
component checks, Docker and pre-commit remain the validation system.

Initial checkout: clean `main` at `134d0a0`, with no staged/unstaged/untracked
work. Fetching `origin` established that all three apparently local-only commits
were already merged in `5097ad0`; its tree was identical. Work started from that
remote commit on `chore/repository-maintenance-2026-11-11`. Local `main` was not
modified, and no existing commits were rewritten or unrelated work staged.
Repository instructions require PRs rather than direct pushes to `main`.

Baseline on Linux/Python 3.11.16: `make lint` passed (65 Python files), `make test`
reported **377 passed, 3 optional skips**, and `make security` reported no known
audited dependency vulnerabilities or medium/high Bandit findings.
`setup_environment.py --check-only` matched every direct pin and passed `pip check`.
Existing matplotlib/pyparsing deprecation warnings were present before changes.

## Findings and implementation

| Area | Evidence and decision |
|---|---|
| Directory design | The existing `src` / HTTP / UI / CLI boundaries are coherent. No static forbidden imports or nonempty byte-identical tracked files were found. Retain stable entry points and artifact paths rather than cosmetically relocating the tree. |
| Shared ownership | Sprint 4 imported private `_sample`/`_index_hash` from Sprint 3 training and constructed a dummy feature matrix just to select indices. Extract `src/models/sampling.py`; both pipelines now use it directly. |
| Duplicate validation | Sprint 3 duplicated lowercase SHA-256 validation already implemented by `verify_manifest_artifacts(require_hashes=True)`. Reuse that verifier, retaining canonical filename checks, required input subsets and all test/freeze gates. |
| Provenance | Tuning records hashes of implementation files. Replace the no-longer-used training file with the new sampling implementation in that list. Preserve row-selection/hash formats and existing generated research evidence. |
| Navigation checks | Reproduced tilde-fenced example links being treated as real links and an empty destination raising `IndexError`. Add tested fence/empty-target handling and correct percent-encoded `#` filenames. Include GitHub templates, and require every `docs/**/*.md` page to be reachable through links from the index. |
| Dependency rules | Add a small AST-based pytest guard for documented static library/API/dashboard import directions. No new checker dependency or speculative abstraction. |
| Ignore policy | `.env.staging`, arbitrary local model JSON metadata and `coverage.xml` were not ignored. Cover local variants/runtime model directories and add isolated tests proving templates, source and committed reference artifacts remain visible. Exclude coverage/build outputs from the container context. |
| Stale guidance | Current tree claimed a Dependabot configuration that was intentionally deleted in `557b34b`. Correct the map/comment and annotate historical security claims; do not restore automation against that decision. |
| Documentation ownership | Keep existing guides/references and stable names. Clarify ownership in the index, shorten the structural tree, link literature notes/templates, update contributor/agent guidance and distinguish current instructions from dated evidence. |

### Verified removals

| Removed | Why safe / reference investigation |
|---|---|
| `data/.gitkeep` | Four tracked child-directory placeholders already preserve the parent. No application, test, build, documentation or automation reference to this parent placeholder was found. Child placeholders remain. |
| `MNIST_MEAN` / `MNIST_STD` in `src/config.py` | Repository-wide search found definitions only; the actual demo uses `ToTensor()` and ART's `[0,1]` bounds, deliberately without mean/std normalization. No preprocessing behavior changed. |
| Compose dashboard `API_URL` entry | The service runs FastAPI/HTML and browser requests are same-origin; Python reads this setting only in the separately documented legacy Streamlit app. Removing the unused entry does not remove the supported legacy configuration. |
| Duplicate digest check and redundant ignore entries | Shared mandatory-hash validation replaces the former check; broader equivalent data/model rules subsume narrow duplicate patterns. Invalid digests and canonical filenames remain regression-tested. |

No source packages, datasets, weights, binary assets, reference JSON/figures,
generated manifests or historical research documents were deleted or regenerated.
Ignored local processed data, environment and existing model/MLflow artifacts
were not cleaned or used for a new research measurement.

## Deliberately retained / outside scope

- **Legacy Streamlit:** documented and covered by both UI and real-process tests;
  not unused just because HTML is primary. Its dependency and client stay.
- **Planned boundaries and placeholders:** attacks/defenses, notebook and runtime
  directory placeholders express the approved plan; no speculative code added.
- **Historical evidence:** sprint/PR/security reports, literature templates and
  committed generated outputs have distinct supported purposes. Clarify dated
  claims rather than deleting them or treating them as current setup guidance.
- **Optional CleverHans:** an explicit isolated cross-check with recorded advisory
  risks, not a default dependency. Removal needs a research-scope decision.
- **`make clean`:** intentionally removes `mlruns/` as well as caches. This is
  documented, not invoked during the audit or silently redefined.
- **Security/reproducibility:** no hash-pinned transitive lock, complete Sprint 4
  security assessment, browser end-to-end suite or production TLS/authz operations.
  Existing security notes remain authoritative; this is not a security certification.
- **Research status:** no full-data retraining, official-test evaluation or M1
  freeze claim. Baseline behavior is checked with synthetic fixtures only.

## Validation

| Check actually executed | Result |
|---|---|
| `make lint` | Passed: Ruff check/format, 69 Python files |
| `make coverage` | **418 passed, 3 opt-in skips**, **89% combined line/branch coverage**; existing third-party warnings only. Includes synthetic training/inference, legacy Streamlit process, HTML and Node component tests. |
| Focused sampling/training/tuning/manifest suite | Passed: 94 cases before final documentation edits |
| `make security` | Passed before/after: no known vulnerabilities in the audited requirements; no medium/high Bandit findings |
| Environment verification | `scripts/setup_environment.py --check-only` passed direct-pin checks and `pip check`; no installation |
| Compilation / CLI discovery | All 69 Python files compiled into a temporary directory; all six script `--help` commands passed |
| JavaScript syntax | Both dashboard JS files passed `node --check`; Node-backed component test also passed in the suite |
| Compose configuration | `docker compose config --quiet` passed using unchanged source YAML and the environment template in an isolated temporary directory; no stack started |
| Docker build | `adversarial-resilient:repository-maintenance` built successfully with existing dependency layers cached |
| Pinned Trivy image scan | Passed: **0 fixed HIGH/CRITICAL** findings in Debian 13.7 and Python packages, including CPU torch/torchvision (`--ignore-unfixed --exit-code 1`); not an unfiltered clean bill of health |
| Container smoke | Network-disabled, capabilities-dropped container imported API/new sampling code, generated OpenAPI, found HTML/reference assets and excluded `.coverage`; UID 1000 |
| Native loopback HTTP smoke | Health, HTML/JS, runs, dataset, report, figure and OpenAPI returned 200 with security headers; token-unset metadata/prediction returned expected 503; process stopped afterward |
| Pre-commit | All-files hooks and an explicit pass over new files passed, using existing cached environments |
| Limited secrets / artifact review | No credential-signature matches in changed/new files; no changed generated results/figures/manifests, datasets or weights |
| `git diff --check` | Passed |

No separate type-check target exists. Fresh dependency installation, full Compose
workflows, browser end-to-end/load tests, Windows/macOS, real-data opt-ins,
training/freezing and the network MNIST/CleverHans demos were not run. Existing
Linux synthetic checks do not establish those workflows or a full security audit.

## Maintaining the map

Start with [the index](README.md), [structure](project-structure.md) and
[architecture](architecture.md); agents use [AGENTS.md](../AGENTS.md).
Operational commands belong in [development](development.md), settings in
[configuration](configuration.md), test conventions in [testing](testing.md).
Keep non-obvious choices in [decisions](DECISIONS.md), status in [progress](progress.md)
and measured evidence in dated reports. The new checks run in the normal pytest
suite; anchors, external/reference-style links, dynamic imports and hostile
filesystem mutation still require review beyond these lightweight guards.
