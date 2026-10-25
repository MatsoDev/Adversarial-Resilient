# api/ — FastAPI service

Minimal HTTP service for the project. **Current scope is a placeholder:** it
exposes liveness/message endpoints only. Model prediction, attack, and defense
endpoints are planned for Semester 2 and are not implemented.

## Endpoints

| Method | Path | Status | Response |
|---|---|---|---|
| `GET` | `/health` | 200 | `{"status": "ok"}` |
| `GET` | `/` | 200 | `{"message": "Adversarial-Resilient API placeholder (Sprint 1). See /health."}` |

FastAPI also serves its generated documentation:

- `GET /docs` — Swagger UI
- `GET /redoc` — ReDoc
- `GET /openapi.json` — OpenAPI schema

There are no request bodies, query parameters, authentication requirements, or
persistent state. Unknown paths return FastAPI's default `404`; unsupported
methods on a known path return `405`.

## Run locally

From the repository root, with the virtual environment active:

```bash
python -m uvicorn api.main:app --reload --port 8000
```

Then open <http://127.0.0.1:8000/health>, <http://127.0.0.1:8000/>, or
<http://127.0.0.1:8000/docs>.

Example:

```bash
curl -s http://127.0.0.1:8000/health
# {"status":"ok"}

curl -s http://127.0.0.1:8000/
# {"message":"Adversarial-Resilient API placeholder (Sprint 1). See /health."}
```

## Docker

The `api` service in [`../docker-compose.yml`](../docker-compose.yml) runs the
same app with uvicorn on container port 8000. Copy
[`../.env.example`](../.env.example) to `.env` before starting the stack; the
host port is controlled by `API_PORT` (default 8000). See
[`../docs/development.md`](../docs/development.md#run-the-docker-stack).

## Tests and design

- [`../tests/test_api_health.py`](../tests/test_api_health.py) checks the
  health function and route registration without an HTTP client.
- [`../docs/architecture.md`](../docs/architecture.md) covers the component
  boundaries and dependency rules.
- [`../docs/configuration.md`](../docs/configuration.md) documents `API_URL`
  (used by the dashboard) and the Compose ports.
- [`../docs/testing.md`](../docs/testing.md) covers test commands.
