.PHONY: lint format format-check backend-test infra-synth

lint:
	npm run lint

format:
	npm run format

format-check:
	npm run format:check

backend-test:
	cd backend && make test

infra-synth:
	cd infra && make synth
