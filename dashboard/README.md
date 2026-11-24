# dashboard/ — HTML research dashboard

Sprint 5 adds `/dashboard/attacks.html`: a read-only completed-experiment
explorer with exact cohort selection, norm/attack filters, accuracy curves,
ASR counts and ART/CleverHans provenance. Missing measured reports stay pending.
See [Sprint 5](../docs/sprint5.md) for prerequisites and commands.

## Current UI: HTML / CSS / JavaScript

FastAPI serves the primary dashboard at **/dashboard/**. Research overview
(`index.html`, `journey.js`) shows a guided replay and a searchable catalogue.
`attacks.html` shows attack comparisons, `transfer.html` shows threat context and
transfer evidence, and `research.html` shows models, data and gated prediction.
All four pages use the shared English/Arabic controls, light theme and release
label from `release.js`. The UI reads `/v1/*` on the same origin.
From the repository root with the environment active:

```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Open <http://localhost:8000/dashboard/>. Success means the release label is
**v0.7.0-preview · Sprint 07**. Expand **Recorded case catalogue** to find
and replay a case from the selected experiment. See the
[journey guide](../docs/ai_journey.md) for filter and link behavior.
`make dashboard` or the Compose dashboard service uses
<http://localhost:8501/dashboard/>.

No frontend build or third-party CDN is needed. CSS/JavaScript are local files;
the UI has a separate restrictive self-only CSP, with JSON API headers retained.
All model numbers come from recorded artifacts, with explicit validation/subset
labels. Readable cards, grouped charts, dataset pages and model error matrices
replace raw JSON as the primary presentation.

Recorded comparison runs come from local ignored `docs/results/baselines/` and
the committed `docs/results/baseline_reference.json`; a fresh checkout therefore
shows the reference without datasets or weights. Invalid batches are excluded
and reported by the API. Refresh results re-fetches reports without restarting.
The UI does not load NumPy arrays, joblib models or torch checkpoints.

## Feature prediction

The research page includes a **Feature prediction**
panel. Load the frozen identity with a local research token, then submit ordered
raw or explicitly bundle-preprocessed EMBER feature rows. The UI does not save
tokens, rows or history; it sends the token/rows to the same-origin API.
Prediction is unavailable until a qualifying local frozen bundle and token are
provisioned; recorded Sprint 3 results do not provision a model. See
[Sprint 4 setup](../docs/sprint4.md#feature-inference) and the
[API contract](../api/README.md#feature-prediction) for limits and interpretation.

## Development and checks

Edit the HTML/CSS/JS files under `web/` directly; there is no build step.
Do not open the HTML as a `file:` URL or serve it without the API: requests use
absolute same-origin `/v1/*` and `/predict` paths. `API_URL` does not change them.
Serve at `/dashboard/` (including the trailing slash for relative assets).

```bash
python -m pytest tests/test_html_dashboard.py tests/test_sprint4_ui.py tests/test_attacks_ui.py tests/test_journey.py tests/test_transfer_ui.py tests/test_dashboard_presentation.py -q
node --check dashboard/web/app.js
node --check dashboard/web/prediction.js
node --check dashboard/web/attacks.js
node --check dashboard/web/journey.js
node --check dashboard/web/locale.js
node --check dashboard/web/release.js
node --check dashboard/web/transfer.js
```

Success means pytest has no failures and syntax checks exit 0 without output.
The Node.js component tests use JavaScript helpers and minimal DOMs. Node.js
is optional for tests and the FastAPI UI can run without it. See the
[testing guide](../docs/testing.md) for skip reasons and verification scope.

Sprint 6 adds `/dashboard/transfer.html` and `transfer.js`: one-snapshot
white-box/transfer table, attacker/source/target provenance, four distinct
realism layers and proposed versioned mappings. Unmeasured transfer is pending,
never relabelled white-box evidence. The same language switch applies; recorded
transfer cases join the journey only when they contain actual individual evidence.
Run `tests/test_transfer_ui.py` and `node --check dashboard/web/transfer.js`.
See [Sprint 6 research evidence](../docs/sprint6_report.md) and the earlier
[academic presentation review](../docs/dashboard_presentation.md) for historical
context, and the [light-mode review](../docs/light_dashboard_review.md)
for the current design, glossary and browser checks. `tests/test_dashboard_presentation.py`
covers local assets, consistent navigation, Arabic copy and prediction states.

The Streamlit implementation below is legacy reference only; it is no longer
the default dashboard entry point.

## Legacy Streamlit interface

Sprint 3 provides a sidebar with Overview, Datasets, Models, MNIST demo and
Methodology pages. Dataset cards include class charts, split counts, feature
statistics and source provenance. Models compares one compatible experiment
batch at a time with validation metrics, confusion matrices and MLP learning
curves. Refresh results re-fetches the API without restarting the services.

All displayed values come from HTTP artifact routes. If neither a valid local
comparison nor a committed reference is available, the UI shows a training
instruction. Missing/invalid artifacts and an offline
API produce retryable errors. MNIST figures are explicitly separated from
malware results. See the [contract](../docs/sprint3_contract.md) for details.

Start the API in one terminal first:

```bash
python -m uvicorn api.main:app --reload --port 8000 --no-proxy-headers
```

Then run the dashboard in a second terminal:

```bash
python -m streamlit run dashboard/app.py
```

Both commands block, so keep both terminals open. Run the dashboard from the
repository root so the `dashboard` package is importable. The app listens on
<http://localhost:8501>. `make dashboard` does **not** start Streamlit; it starts
the primary FastAPI/HTML UI on the same port, so choose one. Streamlit initializes
`API_URL` in session state (default `http://localhost:8000`); the sidebar can
change it. After changing the environment, use a new session. If the
API is not running, the button reports the configured endpoint without echoing
the underlying exception details.
Success means Streamlit opens its navigation and can load recorded API results.
The existing real-process regression test ran in pytest; an interactive legacy
browser session was not repeated for this documentation pass.

`dashboard/client.py` validates `API_URL` before any request: it must be an
absolute `http`/`https` URL with a host and no credentials, query string,
fragment, backslashes, or control characters. Redirects may not leave the
configured origin. Health responses must be `application/json`, a JSON object,
and at most 64 KiB (other JSON artifact responses are capped at 4 MiB). Compose binds the
published dashboard port to `127.0.0.1` by default and mounts the app source
read-only, but now runs FastAPI rather than Streamlit. Research views have no login, so do not expose them without
a TLS reverse proxy and authentication. See
[`../docs/security/SECURITY_AUDIT.md`](../docs/security/SECURITY_AUDIT.md).

Configuration details are in [`../docs/configuration.md`](../docs/configuration.md);
setup, troubleshooting, and the full service walkthrough are in
[`../docs/development.md`](../docs/development.md). The implemented dashboard and
component boundaries are described in [`../docs/architecture.md`](../docs/architecture.md).
