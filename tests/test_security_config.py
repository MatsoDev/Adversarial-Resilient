"""Static regression checks for security-sensitive repository configuration."""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

import uvicorn
import yaml
from api.main import create_app
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


def test_torch_index_is_scoped_and_cpu_pinned():
    runtime = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    torch = (ROOT / "requirements-torch.txt").read_text(encoding="utf-8")
    assert "--index-url" not in runtime
    assert "--extra-index-url" not in runtime
    assert "--index-url https://download.pytorch.org/whl/cpu" in torch
    assert re.search(r"^torch==\S+\+cpu$", torch, re.MULTILINE)
    assert re.search(r"^torchvision==\S+\+cpu$", torch, re.MULTILINE)


def test_dockerfile_pins_base_and_drops_root():
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert re.search(r"^FROM python:3\.11-slim@sha256:[0-9a-f]{64}$", text, re.MULTILINE)
    assert re.search(r"^USER appuser$", text, re.MULTILINE)
    assert "build-essential" not in text
    assert "--no-server-header" in text


def test_compose_defaults_are_loopback_and_least_privilege():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    services = compose["services"]
    assert set(services) == {"api", "dashboard", "mlflow"}
    for service in services.values():
        port = service["ports"][0]
        assert str(port).startswith("${BIND_ADDR:-127.0.0.1}:")
        assert "no-new-privileges:true" in service["security_opt"]
    assert "ALL" in services["api"]["cap_drop"]
    assert "ALL" in services["dashboard"]["cap_drop"]
    assert "@sha256:" in services["mlflow"]["image"]
    assert "MLFLOW_ALLOW_FILE_STORE=true" in services["mlflow"]["environment"]
    assert services["dashboard"]["volumes"] == [
        "./dashboard:/app/dashboard:ro",
        "./docs:/app/docs:ro",
        "./models/sprint4:/app/models/sprint4:ro",
    ]
    assert "./models/sprint4:/app/models/sprint4:ro" in services["api"]["volumes"]


def test_compose_dashboard_serves_html_with_page_healthcheck():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    dashboard = compose["services"]["dashboard"]
    assert dashboard["command"].startswith("python -m uvicorn api.main:app")
    assert "--no-server-header" in dashboard["command"]
    assert not any("API_URL" in value for value in dashboard.get("environment", []))

    healthcheck = dashboard["healthcheck"]["test"]
    probe = healthcheck[-1]
    assert "/dashboard/" in probe
    assert "/_stcore/health" not in probe


def test_makefile_has_dashboard_entrypoint():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert re.search(
        r"^dashboard:\n\t\$\(PYTHON\) -m uvicorn api.main:app --host 127\.0\.0\.1 --port 8501 --no-proxy-headers$",
        makefile,
        re.MULTILINE,
    )


def test_server_entrypoints_preserve_socket_peer_for_prediction_limits(tmp_path, monkeypatch):
    monkeypatch.setenv("PREDICTION_API_TOKEN", "x" * 32)
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    command = json.loads(re.search(r"^CMD (.+)$", dockerfile, re.MULTILINE)[1])
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    commands = [command] + [
        shlex.split(compose["services"][name]["command"]) for name in ("api", "dashboard")
    ]
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    commands.append(shlex.split(re.search(r"^dashboard:\n\t(.+)$", makefile, re.MULTILINE)[1]))
    for args in commands:
        # Exercise Uvicorn's actual wrapper, not only FastAPI's TestClient:
        # Uvicorn otherwise trusts forwarded headers from loopback by default.
        config = uvicorn.Config(
            create_app(baseline_dir=tmp_path / "missing"),
            proxy_headers="--no-proxy-headers" not in args,
            forwarded_allow_ips="127.0.0.1",
        )
        config.load()
        with TestClient(config.loaded_app, client=("127.0.0.1", 45000)) as client:
            client.headers["Authorization"] = "Bearer " + "x" * 32
            for number in range(30):
                response = client.get(
                    "/v1/baseline",
                    headers={"X-Forwarded-For": f"192.0.2.{number}"},
                )
                assert response.status_code == 503  # Missing bundle still consumes a query.
            assert (
                client.get("/v1/baseline", headers={"X-Forwarded-For": "198.51.100.1"}).status_code
                == 429
            )


def test_trivy_image_is_sha_pinned():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert re.search(r"aquasec/trivy@sha256:[0-9a-f]{64}", makefile)


def test_ci_actions_are_sha_pinned_and_security_job_runs():
    text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    uses = re.findall(r"uses:\s*(\S+)", text)
    assert uses
    assert all(re.search(r"@[0-9a-f]{40}$", action) for action in uses)
    assert "persist-credentials: false" in text
    assert "make security" in text
    assert "make docker-scan" in text
    workflow = yaml.safe_load(text)
    assert "security" in workflow["jobs"]


def test_ci_runs_the_coverage_target_and_pytest_cov_is_pinned():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert re.search(r"^coverage:", makefile, re.MULTILINE)
    assert "--cov=src" in makefile
    assert "--cov=api" in makefile

    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "make coverage" in ci

    dev = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    assert re.search(r"^pytest-cov==\S+$", dev, re.MULTILINE)


def test_ci_checks_pull_requests_and_main_pushes_without_duplicate_branch_runs():
    # BaseLoader preserves GitHub's YAML 1.2 "on" key (SafeLoader treats it as True).
    workflow = yaml.load(
        (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    assert workflow["on"] == {"push": {"branches": ["main"]}, "pull_request": ""}
    assert workflow["concurrency"] == {
        "group": "${{ github.workflow }}-${{ github.ref }}",
        "cancel-in-progress": "true",
    }


def test_ci_caches_docker_layers_and_scans_the_loaded_image_without_publishing():
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["docker"]["steps"]
    setup = next(i for i, step in enumerate(steps) if step.get("name") == "Set up Docker Buildx")
    build = next(i for i, step in enumerate(steps) if step.get("name") == "Build image (no push)")
    scan = next(i for i, step in enumerate(steps) if step.get("run") == "make docker-scan")
    assert setup < build < scan
    assert steps[setup]["uses"].startswith("docker/setup-buildx-action@")
    assert steps[build]["uses"].startswith("docker/build-push-action@")
    assert steps[build]["with"] == {
        "context": ".",
        "load": True,
        "push": False,
        "tags": "adversarial-resilient:dev",
        "cache-from": "type=gha,scope=adversarial-resilient",
        "cache-to": "type=gha,scope=adversarial-resilient,mode=max",
    }
    assert workflow["permissions"] == {"contents": "read"}
