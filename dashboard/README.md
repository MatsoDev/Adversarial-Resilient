# dashboard/ — Streamlit UI

Current page: placeholder plus a button that calls the API `/health`.

```bash
streamlit run dashboard/app.py
```

`API_URL` defaults to `http://localhost:8000` for local runs; compose sets it to
`http://api:8000`. Setup and troubleshooting are in
[`docs/development.md`](../docs/development.md); the planned dashboard is
described in [`docs/architecture.md`](../docs/architecture.md).
