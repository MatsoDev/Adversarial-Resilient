"""Minimal FastAPI service. Sprint 1: /health only.

Semester 2 adds the real /predict, /attack, and /defend endpoints. This module
also establishes the HTTP security baseline those endpoints must inherit:
validated Host headers, no-store/cache-free JSON responses, and standard
browser security headers.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_ALLOWED_HOSTS = ("localhost", "127.0.0.1", "api", "testserver")
DOC_PATHS = ("/docs", "/redoc", "/openapi.json")
_TRUTHY = {"1", "true", "yes", "on"}
_FALSEY = {"0", "false", "no", "off"}


def _env_flag(name: str, *, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in _TRUTHY:
        return True
    if value in _FALSEY:
        return False
    logger.warning("ignoring invalid boolean value for %s", name)
    return default


def _allowed_hosts() -> list[str]:
    raw = os.getenv("API_ALLOWED_HOSTS", "")
    hosts = [host.strip() for host in raw.split(",") if host.strip()]
    if not hosts:
        return list(DEFAULT_ALLOWED_HOSTS)
    if "*" in hosts:
        logger.warning("API_ALLOWED_HOSTS contains '*'; Host header validation is disabled")
    return hosts


def health() -> dict[str, str]:
    """Liveness probe used by docker-compose and CI."""
    return {"status": "ok"}


def root() -> dict[str, str]:
    """Return a short service message; use /health for the liveness probe."""
    return {"message": "Adversarial-Resilient API placeholder (Sprint 1). See /health."}


def _is_docs_request(path: str) -> bool:
    return path in DOC_PATHS or path.startswith("/docs/")


def _add_security_headers(response: Response, *, docs_request: bool, https: bool) -> None:
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
    if not docs_request:
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
        )
    if https:
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
        )


async def _unhandled_exception(request: Request, exc: Exception) -> Response:
    """Return a generic 500 response that still carries the security headers.

    Exception handlers run outside the normal HTTP middleware stack, so the
    headers have to be applied here as well. Exception details are logged, not
    returned to the client.
    """
    logger.exception("unhandled error while serving %s", request.url.path)
    response = JSONResponse({"detail": "Internal server error"}, status_code=500)
    _add_security_headers(response, docs_request=False, https=request.url.scheme == "https")
    return response


def create_app() -> FastAPI:
    """Build the API app from environment settings (factory is test-friendly)."""
    docs_enabled = _env_flag("API_DOCS_ENABLED", default=True)
    app = FastAPI(
        title="Adversarial-Resilient API",
        version="0.1.0",
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts())
    app.add_api_route("/health", health, methods=["GET"], summary="Liveness probe")
    app.add_api_route("/", root, methods=["GET"], summary="Service message")

    @app.middleware("http")
    async def security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        _add_security_headers(
            response,
            docs_request=_is_docs_request(request.scope.get("path", "")),
            https=request.url.scheme == "https",
        )
        return response

    app.add_exception_handler(Exception, _unhandled_exception)
    return app


app = create_app()
