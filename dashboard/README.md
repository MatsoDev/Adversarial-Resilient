# dashboard/ — Streamlit UI

Sprint 3 provides a sidebar with Overview, Datasets, Models, MNIST demo and
Methodology pages. Dataset cards include class charts, split counts, feature
statistics and source provenance. Models compares one compatible experiment
batch at a time with validation metrics, confusion matrices and MLP learning
curves. Refresh results re-fetches the API without restarting the services.

All displayed values come from HTTP artifact routes. Baseline results are read
from `docs/results/baselines/` (local runtime outputs, ignored by Git); no
raw arrays or weights are loaded by the dashboard. An empty results directory
shows a clear training instruction. Missing/invalid artifacts and an offline
API produce retryable errors. MNIST figures are explicitly separated from
malware results. See the [contract](../docs/sprint3_contract.md) for details.

Start the API in one terminal first:

```bash
python -m uvicorn api.main:app --reload --port 8000
```

Then run the dashboard in a second terminal:

```bash
python -m streamlit run dashboard/app.py
# or, from the repo root: make dashboard
```

Both commands block, so keep both terminals open. Run the dashboard from the
repository root so the `dashboard` package is importable. The app listens on
<http://localhost:8501>. It reads `API_URL` at import time;
the default is `http://localhost:8000` for local runs. Compose sets it to
`http://api:8000`, so the same page works inside the container network. If the
API is not running, the button reports the configured endpoint without echoing
the underlying exception details.

`dashboard/client.py` validates `API_URL` before any request: it must be an
absolute `http`/`https` URL with a host and no credentials, query string,
fragment, backslashes, or control characters. Redirects may not leave the
configured origin. Health responses must be `application/json`, a JSON object,
and at most 64 KiB. Compose binds the
published dashboard port to `127.0.0.1` by default and mounts the app source
read-only; the placeholder has no authentication, so do not expose it without
a TLS reverse proxy and authentication. See
[`../docs/security/SECURITY_AUDIT.md`](../docs/security/SECURITY_AUDIT.md).

Configuration details are in [`../docs/configuration.md`](../docs/configuration.md);
setup, troubleshooting, and the full service walkthrough are in
[`../docs/development.md`](../docs/development.md). The planned dashboard and
component boundaries are described in [`../docs/architecture.md`](../docs/architecture.md).
