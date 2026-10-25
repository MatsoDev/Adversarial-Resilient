.PHONY: setup lint format format-check test check demo data data-smoke eda docker-build docker-up clean

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
	$(VENV_PY) -m pip install -r requirements.txt -r requirements-dev.txt
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

docker-up:
	docker compose up --build

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache mlruns
	find . -path ./$(VENV) -prune -o -type d -name __pycache__ -prune -exec rm -rf {} +
