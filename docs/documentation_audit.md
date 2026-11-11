# Documentation audit — 2026-11-11

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
