# Contributing

## Development Principles

- Follow `docs/ai-context-rules.md`, `docs/mvp-business-rules.md`, and `docs/mvp-technical-specs.md`.
- Keep business logic out of the frontend.
- Keep user-facing product content in Brazilian Portuguese (`pt-BR`).
- Keep code and technical docs in English.
- Never log raw medical content, CPF, or unnecessary PII.

## Local Setup

1. Read `docs/local-development.md`.
2. Copy `.env.example` into package-level `.env` files as needed.
3. Install package dependencies (`backend/`, `infra/`, `app/`, root tools).
4. Run lint and test commands before opening a PR.

## Pull Request Checklist

- Task scope is respected.
- Lint and tests pass for touched packages.
- Contracts are updated when API shape changes.
- Documentation and task manager updates are included.
