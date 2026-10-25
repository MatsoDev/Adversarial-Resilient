"""Static regression checks for security-sensitive repository configuration."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

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
    assert services["dashboard"]["volumes"] == ["./dashboard:/app/dashboard:ro"]


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
