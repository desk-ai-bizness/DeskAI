PYTHON ?= python3

.PHONY: install lint format typecheck test check hooks smoke-test seed-dev

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .[dev]

lint:
	$(PYTHON) -m ruff check src tests

format:
	$(PYTHON) -m ruff format src tests

typecheck:
	$(PYTHON) -m mypy src

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -p 'test_*.py'

check: lint typecheck test

smoke-test:
	$(PYTHON) scripts/smoke_test.py

seed-dev:
	PYTHONPATH=src $(PYTHON) scripts/seed_dev_data.py --apply

hooks:
	$(PYTHON) -m pip install pre-commit
	cd .. && pre-commit install
