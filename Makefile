.PHONY: lint format format-check backend-test build-lambda infra-synth

lint:
	npm run lint

format:
	npm run format

format-check:
	npm run format:check

backend-test:
	cd backend && make test

build-lambda:
	cd infra && make build-lambda

infra-synth:
	cd infra && make synth
