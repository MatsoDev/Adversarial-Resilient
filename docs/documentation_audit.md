# Documentation audit — 2026-11-11

For the current review, see [the 2026-11-17 follow-up](#follow-up-audit--2026-11-17),
including the full inventory and approved first-pass scope. The earlier report
below remains dated evidence, not a claim that its checks ran again.

**Follow-up clarification:** code-labelled links were already checked by the
original file-link test; this report initially overstated that limitation.
[Repository maintenance](repository_audit.md) adds tested fence/empty-target
handling, index discoverability and GitHub-template coverage. The dated results
below describe this earlier documentation-only pass.

## Scope and approach

Documentation-only audit of `main` at `6de64ad`: onboarding, environment/dependency
manifests, Make/CI, FastAPI routes/middleware, primary HTML and legacy Streamlit
clients, configuration, data loaders/preprocessing interfaces, baseline training,
tuning/calibration/freeze gates, artifact readers, metrics and regression tests.
Source/configuration/tests were checked before updating their guides.

The existing flat documentation structure is sufficient: [development](development.md)
and [data](data/README.md) are task guides, [configuration](configuration.md) and
[API](../api/README.md) are references, [architecture](architecture.md) is the
system explanation, and sprint reports retain historical evidence. No new
documentation framework, dependencies or generator was introduced.

## Prioritized findings and resolutions

No critical documentation defect was established in this pass.

| Severity | Finding | Resolution |
|---|---|---|
| High | Root/component/architecture guides contradicted the merged implementation: health-only API, Streamlit-only UI, prediction/evaluation described as future/placeholders | Updated README, architecture, structure, agent map and component references to current HTML, artifact, training/tuning and authenticated prediction paths |
| High | Current API/security guidance claimed no authentication or model loading despite implemented prediction | Reconciled API contract and threat-boundary delta; explicitly retained the dated Sprint 3 audit scope and outstanding full Sprint 4 assessment |
| High | `make dashboard` incorrectly documented as Streamlit; separate-terminal and `API_URL` instructions misdirected primary UI setup | Documented single-process HTML serving, exact `/dashboard/` URL and the two same-app Compose instances; isolated legacy workflow |
| High | Native `.env` loading and environment activation were unclear, preventing token/config provisioning | Explained exports/`--env-file`, Compose loading, venv interpreter selection, bootstrap versus Make hooks, and disabled/unavailable prediction diagnosis |
| Medium | Prediction schema/response/error coverage was split across contradictory guides, with an abbreviated non-executable row | Centralized detailed fields, identities, inclusive numeric bounds, status codes, budgets/cache semantics and real-data client example in API README; protocol links to it |
| Medium | `src/evaluation` implementation and model/data interfaces were difficult to discover | Documented metrics/thresholds, artifact exceptions, model/tuning interfaces, outputs and integrity boundaries; distinguished all three scaling paths |
| Medium | Synthetic demo CLI could overwrite committed evidence; no CLI output-redirection flag exists | Agent command now runs the isolated smoke test; development guide explicitly distinguishes Python `run_demo(output_dir=...)` from CLI behavior |
| Medium | Test docs mixed two/three opt-ins and overstated link-check coverage | Corrected raw versus processed opt-ins, Node/minimal-DOM coverage and file-link/anchor/inline-label limitations |
| Low | Index and repository tree still described old modules/services; historical branch setup was presented as current | Updated navigation/tree/handoff and Sprint 3 guide while preserving dated measurements, decisions and research plan |

## Validation

Checks actually executed in this audit on Linux with the existing Python 3.11
venv (no dependencies installed):

| Check | Result |
|---|---|
| `make lint` | Passed: Ruff format/check, 65 Python files |
| `make coverage` | Final run: **377 passed, 3 opt-in skips**, **89% combined line/branch coverage**. Initial run: 376 passed (the new audit document adds one parameterized link case). Existing matplotlib/pyparsing deprecation warnings. |
| `.venv/bin/python scripts/setup_environment.py --check-only` | Passed: all direct pins match and `pip check` reports no broken requirements |
| `.venv/bin/python -m pytest tests/test_docs_links.py tests/test_html_dashboard.py tests/test_sprint4_ui.py -q` | Passed: 46 cases, including Node-backed component test |
| `node --check dashboard/web/app.js` and `node --check dashboard/web/prediction.js` | Passed |
| All six documented script CLIs with `--help` | Passed: setup, preprocessing, EDA, training, tuning and ART demo |
| Temporary loopback uvicorn subprocess (`--host 127.0.0.1 --port 0`) and urllib smoke | 200: health, HTML, runs, dataset, report, figure, OpenAPI. Prediction metadata returned expected 503 with token intentionally unset. Request-schema fields matched documentation. Process stopped after checks. |
| Python examples | API client syntax compiled; evaluation example compiled and executed with the documented confusion matrix. Real-data prediction client not executed. |
| Supplemental changed-doc structural check | 19 changed/new documents: 214 relative links including inline-code labels/heading anchors checked; fences balanced (local regex-based check, not rendered Markdown validation) |
| Compose source assertions using installed PyYAML | Verified same-app commands, read-only docs/bundle mounts, env-file declarations and absence of an MLflow Compose healthcheck; not a live Compose test |
| `git diff --check` | Passed |
| `.venv/bin/python -m pre_commit run --files <changed Markdown paths>` | Applicable whitespace/newline, private-key, size and merge-conflict hooks passed; Python/config-only hooks skipped (no matching files). Used existing cached environments. |

**Environment failures, not test failures:** bare `python` was unavailable;
system `python3` was outside the supported 3.11–3.12 range and the bootstrap
correctly rejected it. Explicit `.venv/bin/python` passed without installation.

**Not run:** fresh installation, real-data opt-ins/training/freezing, MNIST
download, CleverHans, Docker build/scan/stack, new dependency/security audit,
graphical browser/Mermaid rendering, Windows/macOS checks and remote CI. Those
would exceed this documentation validation scope or require external data/
services; historical successful results are not claimed as repeated here.

## Remaining gaps and maintenance

- **M1 evidence:** the tracker/report still records full-data measurement in
  progress. This audit did not evaluate official test labels, verify a real
  frozen research bundle, or declare M1 complete. Synthetic freeze fixtures are
  protocol tests only. The real-data client requires local data, token and a
  genuine freeze; there is no fresh-checkout successful prediction guarantee.
- **API schema coverage:** OpenAPI contains the request schema, but artifact
  responses/error models and bearer security are not fully declared. Future code
  work can add response/security schemas to reduce manual duplication; this
  documentation task intentionally does not change contracts or tests.
- **Documentation validation:** the original pytest check omitted anchors and
  external URLs, but did check inline-code labels. A supplemental local review checked changed docs;
  no persistent Markdown/anchor checker or rendered-Mermaid build is introduced.
- **Security/operations:** the full Sprint 4 security assessment, real browser
  end-to-end flow, sustained load, shared TLS/authz deployment and recovery/
  rollback automation are not established. Compose is a development stack, not
  a documented production deployment system.
- **Historical scope:** dated sprint/security reports, decision entries, paper
  claims, raw data releases and generated figures/results were not revalidated
  wholesale. Historical versions/passed checks remain historical, not current
  execution claims. This pass prioritizes developer-facing operational and
  architectural documentation, not a fresh research or security audit.
- **Platform coverage:** Linux checks do not establish Windows/macOS installation
  success. CPU wheel availability on every macOS architecture is not established
  here; dependency manifests remain unchanged.

For changes to behavior/settings, update their existing reference rather than
adding another parallel guide. Keep status in [progress](progress.md), not the
scope plan; record measured evidence only from actual runs. Link new pages from
[the index](README.md), run link tests, review anchors/code-labelled links, and
leave generated evidence to its producer scripts.

## Scope confirmation

Only maintained Markdown documentation was changed. No application code,
dependencies, schemas, infrastructure, runtime configuration, generated evidence,
data or weights were modified. Research milestone status is unchanged.

---

## Follow-up audit — 2026-11-17

### Scope, inventory and approval

Audited the tracked documentation surface at `041568d`, on the clean
`sprint5/attacks-dashboard-handoff` branch. Source code, tests and configuration
take precedence over prose. The preceding commit's cleanup and corrected
MNIST conditional ASR were preserved. The user approved a 23-file first pass
after receiving the inventory, line-referenced findings and prioritized plan.
No file deletion, move, documentation-framework change or new dependency was proposed.

Readers are contributors setting up/changing the project and researchers or
teammates viewing recorded results or reproducing offline feature-space work.
This is not a production-scanner or hosted multi-user operations manual.
The existing Markdown guides, component references, dated evidence, tables,
shell/PowerShell fences and relative links were retained. No changelog or
populated notebook is tracked. There is no docs-site generator, Python package
build, frontend build or generated Python API reference.

The inventory covers 189 tracked files: 52 Markdown documents, four HTML files,
79 Python files, six JavaScript files, four CSS files, 12 JSON inputs/evidence
files and ten PNGs (nine research figures plus the official logo). Python has
162 existing docstrings and 92 comment tokens at the audited baseline, including
test descriptions and tool pragmas. The per-file inventory below records their
locations; it is a snapshot, not a new generated API reference.

Generated/recorded JSON was parsed and important identities, counts and report
states were checked. Figures were inventoried with their producers; their pixels
and all scholarly claims were not independently revalidated. Ignored datasets,
weights, environments, local planning material, tracking stores and secrets
were not edited or cleaned. No local `.env` values were read or changed.

### Findings and prioritized fixes

References in this findings table use baseline `041568d` line numbers.
Correctness/setup came first, missing core references second, clarity and
navigation third. Lower-priority items remain explicitly listed below rather
than receiving shallow rewrites.

| Category / priority | Finding and reason | Resolution |
|---|---|---|
| Incorrect / high | `docs/development.md:42,76`: Linux/macOS installation used exact CPU torch pins with no matching macOS wheels on the configured index | Disclose native macOS incompatibility; show an explicitly supported interpreter, without changing pins or inventing a workaround |
| Incorrect / high | `src/evaluation/README.md:42`: reusable attack metrics were called future work | Document implemented paired metrics, validation and artifact APIs with executed examples |
| Incorrect / high | `docs/sprint5.md:6`: no completed measured baseline report was claimed despite three tracked reports | Distinguish completed blocked-candidate measurements from an unavailable qualifying frozen bundle |
| Incorrect / high | `src/attacks/experiment.py:46`, `scripts/run_attacks.py:1`: frozen-only descriptions omitted explicit candidate mode | Correct docstrings while retaining every gate and runtime statement |
| Incorrect / medium | `src/data/preprocessing.py:201`: scale one was described as a standardization no-op | Explain that mean centering still turns a constant training column into zero |
| Incorrect interpretation / high | `docs/sprint1_report.md:42`, `docs/PR_sprint1.md:21`: historical ASR labels are overall adversarial error rates | Annotate both records and the API guide; preserve original scores and generated outputs |
| Missing / medium | `api/README.md:30`: attack listing lacked its response/error/pending/limit contract | Add envelope types, report identity, candidate labels, deduplication, limits and a checked read-only client |
| Missing / medium | `src/attacks/README.md:3`, `src/models/README.md:43`, `src/data/README.md:29`: abbreviated reusable interfaces omitted parameter/return detail and tuning's `device` argument | Document types/defaults/effects, prerequisites and minimal examples; label unexecuted real-data paths |
| Missing / medium | `docs/configuration.md:32,105`: optional test/CUDA settings and attack output path were absent | Add existing `CLEVERHANS_TORCH_PATH`, internally defaulted `CUBLAS_WORKSPACE_CONFIG` and `ATTACK_RESULTS_DIR` |
| Missing / medium | `docs/testing.md:33`, `dashboard/README.md:50`: Sprint 5 suites and current JavaScript checks were omitted | Document all current UI suites/scripts and data/CleverHans/Node skip reasons |
| Unclear / medium | `docs/sprint4.md:65`, `docs/feature_feasibility.md:41`: absolute prerequisites obscured the narrow owner-authorized exception | Cross-link exploratory operating-validation work without implying M1, SS review or problem-space validity |
| Unclear / medium | `docs/development.md:278`: optional CleverHans advice did not distinguish the torch-only overlay from legacy TensorFlow | Separate the workflows and state that MNIST helper verification is not Sprint 5 evidence |
| Inconsistent / low | `docs/README.md:19`: UI v0.5.1 contradicted `dashboard/web/release.js:4` | Identify v0.5.2 |
| Missing / low | `docs/project-structure.md:49,59,121`: current launcher, planning snapshot and torch-only requirements were absent | Update the existing map, not the repository layout |

The feasibility table also put section count in `general`; the feature layout
places it in `section`. The corrected `general` examples use import/export
counts. This does not approve any new feature mutation.

### Changes made — approved 23-file first pass

| File | Change and reason |
|---|---|
| `README.md` | Explicit clone/interpreter path, native macOS limit, success criteria and optional-check guidance for newcomers |
| `docs/development.md` | Supported-platform setup, environment verification, historical-versus-current demo expectations, optional workflow distinction and safer separation of checks from cleanup |
| `docs/sprint5.md` | Correct measured-report status; document CLI defaults, configuration counts, limits, effects, outputs and unexecuted reproduction prerequisites |
| `src/evaluation/README.md` | Document existing paired metrics, completed-report validation and attack listing, replacing the obsolete future-work claim |
| `docs/sprint1_report.md` | Add historical ASR context without changing measurements |
| `docs/PR_sprint1.md` | Clarify old metric semantics while preserving the PR snapshot |
| `scripts/run_attacks.py` | Module docstring only: frozen default and explicit candidate exception |
| `src/attacks/experiment.py` | Public docstring only: parameter/effect, candidate gate, returned report and failure semantics |
| `src/data/preprocessing.py` | Docstrings only: constant-column centering and optional/mandatory manifest verification contract |
| `api/README.md` | Complete attack response reference, executed read-only example, historical MNIST warning and prediction-example limitations |
| `src/attacks/README.md` | Configuration/policy/generation/case/experiment interfaces, limitations and verified synthetic examples |
| `src/models/README.md` | Correct tuning signature, explain configuration types/defaults and add architecture/sampling/training/inference examples |
| `src/data/README.md` | Complete preprocessing/loader/helper contracts, memory and integrity caveats, and example prerequisites |
| `docs/configuration.md` | Add existing optional settings/output path and concrete response-based success criteria |
| `docs/testing.md` | Add Sprint 5 suites, optional skip rules, focused groups and all six JavaScript syntax commands |
| `dashboard/README.md` | Copyable startup, release/success check and current component/syntax coverage |
| `docs/sprint4.md` | Explain measured blocked outcomes, report overwrite caution and the separately authorized exploration |
| `docs/feature_feasibility.md` | Separate proposed constraints, pending technical review and the measured scalar-only probe |
| `src/attacks/runner.py` | Docstrings only: configuration, logit-wrapper and paired generation contracts |
| `src/evaluation/attacks.py` | Docstrings only: array shapes, tie behavior, denominators, norms and null ASR |
| `docs/README.md` | Reconcile release/reference labels and link evidence without changing its contents |
| `docs/project-structure.md` | Include current entry points, overlay, case module, plan snapshot and measured-artifact handling |
| `docs/documentation_audit.md` | Preserve the earlier audit and append this inventory, findings, file-by-file record and validation limits |

No useful historical content was deleted. Incorrect statements were replaced,
and `make format`/`make clean` moved out of the verification command block into
maintenance guidance; both commands remain documented. No test, exported symbol,
runtime statement, request/response contract, dependency pin, secret or measured
artifact was changed. Python comparisons remove docstrings from the AST and
confirm that all remaining syntax is identical to the baseline.

### Verification record

Linux, existing Python 3.11.16 venv, no new installations. There is no separate
Python-package/frontend build target; Docker is the configured build check.
The baseline was recorded before edits, then checks were repeated per batch.

| Check | Executed result |
|---|---|
| Baseline `make lint`, `make test`, `make coverage` | Ruff clean, 79 files; 468 passed, 6 skipped; 88% combined line/branch coverage |
| First correctness batch | `make lint`, `make test` (468 passed, 6 skipped) and `make docker-build` passed |
| Core-reference batch | Same lint/test/build checks passed; 468 passed, 6 skipped |
| Final navigation/audit batch | `make lint`, `make test` (468 passed, 6 skipped) and `make docker-build` passed |
| Final `make coverage` | 468 passed, 6 skipped; 88% combined line/branch coverage, unchanged from baseline |
| Baseline and post-edit `make security` | Requirements audit found no known vulnerabilities; Bandit had no medium/high findings |
| Environment check, before and after core edits | `scripts/setup_environment.py --check-only`: all direct pins match; no broken requirements |
| All eight tracked script `--help` commands | Exit 0; includes attack CLI and existing-torch launcher |
| All six `node --check dashboard/web/<file>.js` commands | Exit 0, no syntax errors |
| Documentation examples | All changed-document Python fences compiled; 12 dataset-free examples executed successfully; real-data examples compiled but were not run |
| Python behavior comparison | All five changed Python files have identical ASTs after docstrings are removed |
| Documentation navigation/structure | File links and index discoverability passed in pytest; 32 supplemental Markdown fragment links passed; all changed-document fences balanced and table column counts matched |
| Inventory/scope/evidence guards | Inventory and 23-file change table matched tracked files; only 18 Markdown and five docstring-only Python files changed; all tracked results, manifests and figures remained byte-identical to baseline |
| Native uvicorn HTTP smoke | Health, all three HTML pages, runs, attacks, demo, dataset summary, report, figure and OpenAPI returned 200; processes stopped afterward |
| Documented curl/read-only API client | Health, runs and Sprint 4 report requests passed; client printed `completed: 1 experiment(s)` using the ephemeral loopback port |
| Pending listing | Empty temporary artifact store returned HTTP 200, `status: "pending"`, `experiments: []` |
| Docs switch / disabled prediction | With docs disabled: health/dashboard 200, docs/ReDoc/OpenAPI 404. With token unset: metadata/prediction 503, `{"detail":"Prediction is disabled"}` |
| Recorded evidence inspection | 21 configurations, 57 cases and 21 completed recorded CleverHans checks; three baseline searches remained blocked with official test unopened |
| Critical external URL HEAD requests during audit | Project GitHub, direct EMBER archive, official CICIDS page and two arXiv references returned 200; no datasets downloaded |
| PyTorch CPU index metadata during audit | Exact torch/torchvision pins listed zero macOS wheels; this is metadata inspection, not a native installation test |

Existing matplotlib/pyparsing warnings were present before edits. The six Linux
skips are three real-data opt-ins and three absent CleverHans cases; Node was
available. Baseline Docker build initially exceeded the tool's 120-second export/
unpack timeout; retry with a longer limit passed, using cached dependency layers.
Subsequent editing-batch builds also used cached dependency layers.

**Not run:** fresh clone/install, Windows/macOS execution, real-data opt-ins,
real MNIST/preprocessing/EDA/training/freezing/attacks, optional CleverHans calls,
Compose startup, Trivy, graphical browser/end-to-end/load checks, remote CI or
exhaustive scholarly/external-link validation. A tiny synthetic ART example is
not a new real-data measurement. Synthetic tests and examples used temporary
outputs, never committed evidence. The installed-environment check is not proof
of a fresh or cross-platform installation.

### Open questions

1. `requirements-torch.txt:12–13`: Is native macOS support required? Documentation
   now discloses the missing compatible wheels; a supported alternative needs
   an approved platform/dependency decision, not an undocumented pin replacement.
2. `docs/results/art_quickstart_results.json:9,22,37`: Should a later authorized
   MNIST run regenerate evidence with corrected conditional ASR? This pass only
   annotates historical semantics and preserves the scores.
3. `scripts/art_quickstart.py:344–351`: Should the optional MNIST CleverHans
   gradient-context concern be investigated in a separate code task? It was not
   executed with that absent backend or fixed in this documentation pass.

### Recommended follow-ups — flagged, not changed

Each location below remains outside this approved first pass.

1. **Behavior investigation:** `scripts/art_quickstart.py:344–351` calls
   gradient-based attacks inside `torch.no_grad()`; this is a potential optional
   helper defect, not a confirmed new measurement. `dashboard/web/research.html:4`
   links to `#overview`, but no matching element or hash-navigation handler exists
   in `dashboard/web/app.js:22`; fixing it would change UI behavior.
2. **Platform/evidence decisions:** answer the macOS and MNIST regeneration
   questions above. Neither a supported macOS workaround nor new research scores
   were invented.
3. **Chronology and terminology:** `docs/team_handoff.md:60` ambiguously says
   no automatic downloads although setup invokes pip; `docs/sprint4_report.md:29,83`
   retains in-progress wording below completed follow-ups; `docs/sprint3_report.md:173`
   retains an old Streamlit/unmerged handoff. Add dated context in a later batch.
4. **Units and small stale descriptions:** `docs/data_cards/ember2018.md:16,54`
   and `docs/data/README.md:134` say 9.4 GB, versus 9,946,142,816 source bytes
   (9.95 GB / 9.26 GiB) in the manifest. `api/__init__.py:1` still says placeholder;
   `src/models/tabular.py:1` omits the CNN; `AGENTS.md:138` omits the torch-only
   overlay; `.github/workflows/ci.yml:4` overstates push/PR deduplication.
5. **CLI help and sparse inline references:** `scripts/art_quickstart.py:39`
   promises about two minutes, unlike the historical four–five-minute report;
   changing runtime help strings exceeds the source-docstrings/comments-only
   constraint. `api/main.py:103`, `dashboard/client.py:97`,
   `src/models/frozen.py:115`, `src/models/sampling.py:15` and
   `src/data/ember.py:325` have sparse public docstrings; improve useful contracts
   separately rather than adding boilerplate to every obvious wrapper/test.
6. **Reviewer-owned literature:** `docs/literature/anderson_2018_ember.md:74,82`
   treats LightGBM/EMBER choices as unresolved current recommendations;
   `docs/literature/sharafaldin_2018_cicids2017.md:71` recommends day splits,
   not the implemented binary-stratified split. Preserve paper claims and ask
   reviewers to distinguish recommendations from delivered behavior.
7. **Validation/API declarations:** `tests/test_docs_links.py:5` intentionally
   omits anchor/external validation; browser rendering is not established by
   Node/HTTP checks. `api/prediction.py:97–105` declares request bodies, not a
   complete bearer/response schema. Persistent validators or OpenAPI declarations
   would be separate code/tooling work; no dependency or CI gate was added here.

### Complete documentation inventory

The following is the tracked baseline inventory. Paths in fenced lists are
literal inventory entries, not new setup commands. Generated/recorded evidence
is listed for completeness, not authorization to edit it.

#### Markdown — 52 files

```text
.github/ISSUE_TEMPLATE/bug.md
.github/ISSUE_TEMPLATE/task.md
.github/PULL_REQUEST_TEMPLATE.md
AGENTS.md
CONTRIBUTING.md
README.md
api/README.md
dashboard/README.md
docs/DECISIONS.md
docs/PR_sprint1.md
docs/README.md
docs/ai_journey.md
docs/architecture.md
docs/configuration.md
docs/data/README.md
docs/data/eda_report.md                         [generated]
docs/data/ember_feature_layout.md
docs/data_cards/cicids2017.md
docs/data_cards/ember2018.md
docs/development.md
docs/documentation_audit.md
docs/feature_feasibility.md
docs/literature/README.md
docs/literature/anderson_2018_ember.md
docs/literature/malware_team_note_TEMPLATE.md
docs/literature/network_team_note_TEMPLATE.md
docs/literature/sharafaldin_2018_cicids2017.md
docs/plans/README.md
docs/progress.md
docs/project-structure.md
docs/project_plan.md
docs/reading_list.md
docs/repository_audit.md
docs/security/SECURITY_AUDIT.md
docs/sprint1_report.md
docs/sprint2_report.md
docs/sprint3.md
docs/sprint3_contract.md
docs/sprint3_report.md
docs/sprint4.md
docs/sprint4_report.md
docs/sprint5.md
docs/sprint5_report.md
docs/team_handoff.md
docs/testing.md
docs/testing_hardening_report.md
docs/threat_model_v0.1.md
src/attacks/README.md
src/data/README.md
src/defenses/README.md
src/evaluation/README.md
src/models/README.md
```

#### HTML, UI explanations and source comments

UI strings are documentation-bearing, but runtime-string/navigation edits were
not included in the docstrings/comments-only source-edit scope.

```text
docs/plans/project_plan_v0.5.2.html              [dated exported snapshot]
dashboard/web/index.html                       [introduction, FAQ, limitations]
dashboard/web/attacks.html                     [metric/projection definitions]
dashboard/web/research.html                    [prediction instructions]
dashboard/web/app.js                           [research/demo explanations]
dashboard/web/attacks.js                       [provenance; comment :68]
dashboard/web/journey.js                       [recorded-case explanations]
dashboard/web/locale.js                        [bilingual copy; comments :2,124]
dashboard/web/prediction.js                    [validation guidance; comment :2]
dashboard/web/release.js                       [release identity; comment :2]
dashboard/web/attacks.css                      [no standalone comments]
dashboard/web/journey.css                     [comment :8]
dashboard/web/styles.css                      [comment :3]
dashboard/web/theme.css                       [comment :1]
dashboard/web/arsm-logo.png                    [official UI logo]
```

#### JSON inputs and evidence — 12 files

```text
docs/data/manifests/cicids2017.json
docs/data/manifests/ember2018.json
docs/results/art_quickstart_results.json
docs/results/attack_reference.json
docs/results/baseline_reference.json
docs/results/data_eda.json
docs/results/sprint4_extended_10epochs.json
docs/results/sprint4_regularized_gpu10.json
docs/results/sprint4_regularized_search_config.json
docs/results/sprint4_search_3epochs.json
docs/sprint5_policy_template.json
docs/sprint5_size_probe_policy.json
```

#### Generated research figures — nine files

```text
docs/figures/art_accuracy_vs_eps.png
docs/figures/art_samples.png
docs/figures/data_cicids_class_counts.png
docs/figures/data_cicids_feature_histograms.png
docs/figures/data_cicids_inf_nan.png
docs/figures/data_cicids_per_file.png
docs/figures/data_ember_appeared_by_label.png
docs/figures/data_ember_feature_groups.png
docs/figures/data_ember_label_counts.png
```

#### License, configuration and process comments

```text
LICENSE
Makefile
Dockerfile
docker-compose.yml
pyproject.toml
.env.example                                  [template only]
.pre-commit-config.yaml
.github/workflows/ci.yml
.gitignore
.dockerignore
.gitattributes
requirements.txt
requirements-dev.txt
requirements-torch.txt
requirements-cleverhans.txt
requirements-cleverhans-torch.txt
```

Six empty tracked `.gitkeep` files reserve `data/{adversarial,external,processed,raw}/`,
`models/` and `notebooks/`; they contain no documentation. No vendored docs,
migration files or docs-site configuration are tracked.

#### All Python documentation-bearing locations — 79 files

`D` gives docstring spans, including module/private descriptions; `C` gives comment
token lines, including pragmas. **All numbers below refer to baseline `041568d`,
before the approved docstring edits**, not live line numbers in later revisions.
This inventories existing documentation rather than demanding docstrings on
every test or obvious wrapper.

| Runtime/library/CLI file | D | C |
|---|---|---|
| `api/__init__.py` | 1 | — |
| `api/artifacts.py` | 1 | — |
| `api/main.py` | 1–7,58,63,90–95,103 | — |
| `api/prediction.py` | 1 | 50 |
| `dashboard/__init__.py` | 1 | — |
| `dashboard/app.py` | 1 | 21,83 |
| `dashboard/client.py` | 1–7,23,27,37,61,93,103,114 | — |
| `scripts/art_quickstart.py` | 1–16,58,135,153–157,178–183,333 | 30,31,65,66,81,88,89,95,197,297,409,410 |
| `scripts/eda_datasets.py` | 1–11 | 31,40,49,55,60,788 |
| `scripts/preprocess.py` | 1–13,101 | 26,33,34,35 |
| `scripts/run_attacks.py` | 1 | 13 |
| `scripts/setup_environment.py` | 1 | 34 |
| `scripts/train_baselines.py` | 1 | — |
| `scripts/tune_baseline.py` | 1 | 14 |
| `scripts/tune_with_existing_torch.py` | 1–5 | — |
| `src/__init__.py` | 1 | — |
| `src/attacks/__init__.py` | 1 | — |
| `src/attacks/constraints.py` | 1–5,78,94–98 | 108 |
| `src/attacks/examples.py` | 1,10–14 | — |
| `src/attacks/experiment.py` | 1,46–50 | 94,95,155 |
| `src/attacks/runner.py` | 1,73,98–103 | 111,112,159 |
| `src/config.py` | 1–5,60–66,86,93,106 | 12,38,39,48,99,100 |
| `src/data/__init__.py` | 1 | — |
| `src/data/cicids2017.py` | 1–8,125,141,163,187,215,339 | — |
| `src/data/ember.py` | 1–12,149,160,192,304–310,433,500,718 | 75,76,619 |
| `src/data/loader.py` | 1–4,25–32,117–126,175–186 | — |
| `src/data/preprocessing.py` | 1–6,30,35,51,71,77,99,115,138,156–160,185,199–203,231,249,285,302–311,431,447–452,470 | 31,57,175,176 |
| `src/defenses/__init__.py` | 1 | — |
| `src/evaluation/__init__.py` | 1 | — |
| `src/evaluation/artifacts.py` | 1,81,89 | 138,139,200,201 |
| `src/evaluation/attack_results.py` | 1,11 | — |
| `src/evaluation/attacks.py` | 1 | — |
| `src/evaluation/binary.py` | 1,16,46 | 49,50 |
| `src/models/__init__.py` | 1 | — |
| `src/models/baseline_mlp.py` | 1,10,26 | — |
| `src/models/frozen.py` | 1–5,34,46 | 124 |
| `src/models/sampling.py` | 1–5,16,26,37,43 | — |
| `src/models/tabular.py` | 1,9,33 | — |
| `src/models/training.py` | 1–4,143 | 85,152,159,160,185,235 |
| `src/models/tuning.py` | 1,70,195–200 | 92,135,136,242,293,304,413 |
| `src/utils/__init__.py` | 1 | — |
| `src/utils/seed.py` | 1,10 | 25,29,33,34,35 |

| Test/helper file | D | C |
|---|---|---|
| `tests/__init__.py` | 1 | — |
| `tests/conftest.py` | 1–6 | 11 |
| `tests/data_fixtures.py` | 1,228 | — |
| `tests/test_api_security.py` | 1 | — |
| `tests/test_architecture.py` | 1–5 | — |
| `tests/test_art_metrics.py` | 1 | — |
| `tests/test_art_quickstart_smoke.py` | 1 | — |
| `tests/test_artifact_security.py` | 1 | — |
| `tests/test_attacks.py` | 1 | 55,239,240,300,301 |
| `tests/test_attacks_ui.py` | 1 | — |
| `tests/test_binary_metrics.py` | 1 | — |
| `tests/test_config.py` | 1 | — |
| `tests/test_dashboard_app.py` | 1 | — |
| `tests/test_dashboard_entrypoint.py` | 1 | — |
| `tests/test_dashboard_security.py` | 1 | — |
| `tests/test_data_cicids.py` | 1 | 31,36 |
| `tests/test_data_ember.py` | 1 | 142,144 |
| `tests/test_data_loader.py` | 1 | — |
| `tests/test_data_real_optional.py` | 1–5 | — |
| `tests/test_data_resolution.py` | 1 | — |
| `tests/test_docs_links.py` | 1–7,56,106 | — |
| `tests/test_eda_cli.py` | 1 | — |
| `tests/test_html_dashboard.py` | 1 | — |
| `tests/test_journey.py` | 1 | — |
| `tests/test_manifest_security.py` | 1 | 101 |
| `tests/test_model_sampling.py` | 1 | — |
| `tests/test_models.py` | 1 | — |
| `tests/test_prediction_streaming.py` | 1 | 58 |
| `tests/test_preprocess_cli.py` | 1 | — |
| `tests/test_preprocessing.py` | 1 | — |
| `tests/test_repository_hygiene.py` | 1 | 18 |
| `tests/test_security_config.py` | 1 | — |
| `tests/test_seed.py` | 1 | — |
| `tests/test_sprint3.py` | 1 | 74,95 |
| `tests/test_sprint3_real.py` | 1 | — |
| `tests/test_sprint4.py` | 1 | 33,204,482,553 |
| `tests/test_sprint4_ui.py` | 1 | — |
