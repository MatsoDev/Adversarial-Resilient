.PHONY: setup lint test demo docker-build docker-up clean

PY ?= python
VENV ?= .venv

setup:
	$(PY) -m venv $(VENV)
	$(VENV)/Scripts/python -m pip install --upgrade pip || $(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/Scripts/pip install -r requirements.txt -r requirements-dev.txt || $(VENV)/bin/pip install -r requirements.txt -r requirements-dev.txt
	$(VENV)/Scripts/pre-commit install || $(VENV)/bin/pre-commit install || echo "pre-commit hook install skipped"

lint:
	$(VENV)/Scripts/python -m ruff check src scripts tests api dashboard || $(VENV)/bin/python -m ruff check src scripts tests api dashboard || python -m ruff check src scripts tests api dashboard

test:
	$(VENV)/Scripts/python -m pytest -q || $(VENV)/bin/python -m pytest -q || python -m pytest -q

demo:
	$(VENV)/Scripts/python scripts/art_quickstart.py --fast || $(VENV)/bin/python scripts/art_quickstart.py --fast || python scripts/art_quickstart.py --fast

docker-build:
	docker build -t adversarial-resilient:dev .

docker-up:
	docker compose up --build

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache mlruns docs/results/art_quickstart_results.json docs/figures/art_*
