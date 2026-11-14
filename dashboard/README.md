# dashboard/ — HTML research dashboard

Sprint 5 adds `/dashboard/attacks.html`: a read-only completed-experiment
explorer with exact cohort selection, norm/attack filters, accuracy curves,
ASR counts and ART/CleverHans provenance. Missing measured reports stay pending.
See [Sprint 5](../docs/sprint5.md) for prerequisites and commands.

## Current UI: HTML / CSS / JavaScript

The primary dashboard is now `dashboard/web/index.html`, `styles.css` and
`app.js`. It is served by FastAPI at **/dashboard/** and reads `/v1/*` on the
same origin. Start `python -m uvicorn api.main:app --host 127.0.0.1 --port 8000`
and open <http://localhost:8000/dashboard/>. `make dashboard` or the Compose
dashboard service uses <http://localhost:8501/dashboard/>.

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

The primary HTML dashboard includes a **Frozen baseline · feature prediction**
panel. Load the frozen identity with a local research token, then submit ordered
raw or explicitly bundle-preprocessed EMBER feature rows. The UI does not save
tokens, rows or history; it sends the token/rows to the same-origin API.
Prediction is unavailable until a qualifying local frozen bundle and token are
provisioned; recorded Sprint 3 results do not provision a model. See
[Sprint 4 setup](../docs/sprint4.md#feature-inference) and the
[API contract](../api/README.md#feature-prediction) for limits and interpretation.

## Development and checks

Edit `web/index.html`, `styles.css`, `app.js` and `prediction.js` directly.
Do not open the HTML as a `file:` URL or serve it without the API: requests use
absolute same-origin `/v1/*` and `/predict` paths. `API_URL` does not change them.
Serve at `/dashboard/` (including the trailing slash for relative assets).

```bash
python -m pytest tests/test_html_dashboard.py tests/test_sprint4_ui.py -q
node --check dashboard/web/app.js
node --check dashboard/web/prediction.js
```

Node.js is optional test tooling, not required to serve the UI. The component
test skips without Node and uses a minimal DOM, not a full browser. There is no
frontend package manager, build pipeline or browser end-to-end runner.

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
python -m uvicorn api.main:app --reload --port 8000
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
