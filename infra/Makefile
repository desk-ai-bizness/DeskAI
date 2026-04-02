PYTHON ?= python3

.PHONY: install lint format typecheck test build-lambda clean-lambda synth

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

test:
	$(PYTHON) -m unittest discover -s tests

build-lambda:
	bash scripts/build_lambda.sh

clean-lambda:
	rm -rf .build/

synth: build-lambda
	JSII_RUNTIME_PACKAGE_CACHE=.jsii-cache npm run synth
