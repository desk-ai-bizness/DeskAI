#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# Validate OpenAPI contracts (HTTP)
npx redocly lint \
  --skip-rule no-empty-servers \
  --skip-rule security-defined \
  --skip-rule path-parameters-defined \
  --skip-rule info-license \
  --skip-rule operation-operationId \
  --skip-rule operation-4xx-response \
  contracts/http/*.yaml

# Validate YAML parseability and formatting for all contract files
npx prettier --check contracts/**/*.yaml
