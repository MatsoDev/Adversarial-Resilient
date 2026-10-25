.PHONY: setup lint test demo data data-smoke eda docker-build docker-up clean

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

data:
	$(VENV)/Scripts/python scripts/preprocess.py --dataset all || $(VENV)/bin/python scripts/preprocess.py --dataset all || python scripts/preprocess.py --dataset all

data-smoke:
	$(VENV)/Scripts/python scripts/preprocess.py --dataset ember --max-samples 2000 --output-dir /tmp/adversarial-resilient-smoke/ember --force --jobs 1 || $(VENV)/bin/python scripts/preprocess.py --dataset ember --max-samples 2000 --output-dir /tmp/adversarial-resilient-smoke/ember --force --jobs 1 || python scripts/preprocess.py --dataset ember --max-samples 2000 --output-dir /tmp/adversarial-resilient-smoke/ember --force --jobs 1
	$(VENV)/Scripts/python scripts/preprocess.py --dataset cicids2017 --max-samples 2000 --output-dir /tmp/adversarial-resilient-smoke/cicids2017 --force || $(VENV)/bin/python scripts/preprocess.py --dataset cicids2017 --max-samples 2000 --output-dir /tmp/adversarial-resilient-smoke/cicids2017 --force || python scripts/preprocess.py --dataset cicids2017 --max-samples 2000 --output-dir /tmp/adversarial-resilient-smoke/cicids2017 --force

eda:
	$(VENV)/Scripts/python scripts/eda_datasets.py --dataset all || $(VENV)/bin/python scripts/eda_datasets.py --dataset all || python scripts/eda_datasets.py --dataset all

docker-build:
	docker build -t adversarial-resilient:dev .

docker-up:
	docker compose up --build

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache mlruns
