PYTHON ?= python3

.PHONY: install lint format typecheck synth

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .[dev]
	npm install

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

typecheck:
	$(PYTHON) -m mypy .

synth:
	JSII_RUNTIME_PACKAGE_CACHE=.jsii-cache npm run synth
