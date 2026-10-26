# dashboard/ — Streamlit UI

Current page: a placeholder plus a button that calls the API `/health` and
shows the JSON response (or an error message). Robustness charts, sample grids,
and MLflow links are planned for Semester 2.

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
