.PHONY: setup lint format format-check test security check demo data data-smoke eda docker-build docker-scan docker-up clean

PY ?= python
VENV ?= .venv
SMOKE_DIR ?= /tmp/adversarial-resilient-smoke

ifeq ($(OS),Windows_NT)
VENV_PY := $(VENV)/Scripts/python.exe
else
VENV_PY := $(VENV)/bin/python
endif

# Prefer the repo virtualenv when it exists; otherwise use $(PY).
PYTHON := $(if $(wildcard $(VENV_PY)),$(VENV_PY),$(PY))
TARGETS := src scripts tests api dashboard

setup:
	$(PY) -m venv $(VENV)
	$(VENV_PY) -m pip install --upgrade pip
	$(VENV_PY) -m pip install -r requirements-dev.txt
	$(VENV_PY) -m pip install -r requirements-torch.txt
	$(VENV_PY) -m pre_commit install || echo "pre-commit hook install skipped"

# `lint` is the CI check: it validates formatting without rewriting files.
lint: format-check
	$(PYTHON) -m ruff check $(TARGETS)

format:
	$(PYTHON) -m ruff format $(TARGETS)

format-check:
	$(PYTHON) -m ruff format --check $(TARGETS)

test:
	$(PYTHON) -m pytest

# Dependency and static security checks (also run in CI).
security:
	$(PYTHON) -m pip_audit -r requirements-dev.txt --progress-spinner off
	$(PYTHON) -m bandit -q -r src scripts api dashboard -ll

check: lint test

demo:
	$(PYTHON) scripts/art_quickstart.py --fast

data:
	$(PYTHON) scripts/preprocess.py --dataset all

data-smoke:
	$(PYTHON) scripts/preprocess.py --dataset ember --max-samples 2000 \
		--output-dir $(SMOKE_DIR)/ember --force --jobs 1
	$(PYTHON) scripts/preprocess.py --dataset cicids2017 --max-samples 2000 \
		--output-dir $(SMOKE_DIR)/cicids2017 --force

eda:
	$(PYTHON) scripts/eda_datasets.py --dataset all

docker-build:
	docker build -t adversarial-resilient:dev .

# Fixed HIGH/CRITICAL vulnerabilities only; unfixed base-image advisories are
# reported separately and addressed by bumping the pinned base-image digest.
docker-scan:
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy@sha256:790fd66d1697395d8693d1acaa1ea702406a20f109b6fc7bac8db623eca6c06c \
		image --scanners vuln --severity HIGH,CRITICAL --ignore-unfixed \
		--exit-code 1 --no-progress adversarial-resilient:dev > /tmp/trivy-scan.log 2>&1 \
		|| (cat /tmp/trivy-scan.log; exit 1)

docker-up:
	docker compose up --build

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache mlruns
	find . -path ./$(VENV) -prune -o -type d -name __pycache__ -prune -exec rm -rf {} +
