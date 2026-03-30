# Contracts

Shared contract source of truth for backend and frontend.

## Layout

- `http/`: OpenAPI 3.1 HTTP contracts
- `websocket/`: JSON-schema-like message contracts in YAML
- `ui-config/`: UI configuration schemas
- `feature-flags/`: feature flag definitions

## Versioning

- HTTP contracts use `/v1` API path prefix.
- Breaking changes require a new version prefix.
- Keep `version.json` aligned with the active contract baseline.

## Validation

From repository root:

```bash
npm run lint:contracts
```
