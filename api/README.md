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

### Security baseline

- `Host` headers are validated by `TrustedHostMiddleware` against
  `API_ALLOWED_HOSTS` (default: `localhost,127.0.0.1,api,testserver`).
- JSON responses send `X-Content-Type-Options: nosniff`, `X-Frame-Options:
  DENY`, `Referrer-Policy: no-referrer`, `Permissions-Policy`, and a
  restrictive `Content-Security-Policy`; `/health` is `Cache-Control:
  no-store`. HSTS is added only when the request scheme is HTTPS.
- The generated docs can be turned off with `API_DOCS_ENABLED=false`.
- Uvicorn is started with `--no-server-header` in the image/Compose stack.
- There is still no authentication or rate limiting because no sensitive
  endpoint exists yet. `/predict`, `/attack`, and `/defend` must add both
  before being exposed beyond localhost. See
  [`../docs/security/SECURITY_AUDIT.md`](../docs/security/SECURITY_AUDIT.md).

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
same app with uvicorn on container port 8000, as a non-root user with dropped
capabilities. Copy [`../.env.example`](../.env.example) to `.env` before
starting the stack; `BIND_ADDR` (default `127.0.0.1`) and `API_PORT` (default
8000) control the published endpoint. See
[`../docs/development.md`](../docs/development.md#run-the-docker-stack).

## Tests and design

- [`../tests/test_api_health.py`](../tests/test_api_health.py) checks the
  health function and route registration without an HTTP client.
- [`../tests/test_api_security.py`](../tests/test_api_security.py) checks the
  security headers, Host allowlist, HSTS behavior, and docs switch.
- [`../docs/architecture.md`](../docs/architecture.md) covers the component
  boundaries and dependency rules.
- [`../docs/configuration.md`](../docs/configuration.md) documents `API_URL`
  (used by the dashboard) and the Compose ports.
- [`../docs/testing.md`](../docs/testing.md) covers test commands.
