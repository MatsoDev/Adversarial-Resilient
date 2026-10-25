# dashboard/ — Streamlit UI

Current page: a placeholder plus a button that calls the API `/health` and
shows the JSON response (or an error message). Robustness charts, sample grids,
and MLflow links are planned for Semester 2.

```bash
streamlit run dashboard/app.py
```

The app listens on <http://localhost:8501>. It reads `API_URL` at import time;
the default is `http://localhost:8000` for local runs. Compose sets it to
`http://api:8000`, so the same page works inside the container network. If the
API is not running, the button reports the URL it tried.

Configuration details are in [`../docs/configuration.md`](../docs/configuration.md);
setup, troubleshooting, and the full service walkthrough are in
[`../docs/development.md`](../docs/development.md). The planned dashboard and
component boundaries are described in [`../docs/architecture.md`](../docs/architecture.md).
