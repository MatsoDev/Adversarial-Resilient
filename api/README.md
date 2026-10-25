# api/ — FastAPI service

Current endpoints:

- `GET /health` → `{"status": "ok"}` (used by compose and CI)
- `GET /` → service message

Run locally:

```bash
python -m uvicorn api.main:app --reload --port 8000
```

Docker: the `api` service in `docker-compose.yml` runs the same app. Setup and
troubleshooting are in [`docs/development.md`](../docs/development.md); planned
endpoints and layering are in [`docs/architecture.md`](../docs/architecture.md).
