# Repository Layout

## Purpose

This document defines the top-level directory structure for the DeskAI MVP repository. It establishes where each component lives, what it owns, and how components relate to each other.

Task 003 (bootstrap) uses this layout as its blueprint for creating the actual files, packages, and configurations.

---

## 1. Top-Level Structure

```
DeskAI/
├── backend/                       # Python backend (core domain + BFF + handlers)
├── app/                           # Authenticated React web app
├── website/                       # Public marketing site (static HTML)
├── contracts/                     # Shared schemas and API contracts
├── infra/                         # AWS CDK infrastructure
├── tools/                         # Development scripts and utilities
├── v2/
│   ├── docs/                      # Architecture, requirements, specs
│   └── tasks/                     # Task files and manager
├── .github/                       # CI/CD workflows
├── CLAUDE.md                      # AI agent project context
├── README.md                      # Project README
└── .gitignore
```

### Why This Layout

- **Flat top-level packages**: Each major component is a direct child of the repository root. This keeps navigation simple and avoids deep nesting for a small team.
- **Single backend package**: The BFF and core backend share the same Python package because they share the same domain models, ports, and adapters. Separating them into two packages would create duplication and synchronization overhead. The boundary between BFF and core is enforced by module structure, not separate deployments.
- **Contracts directory**: Shared schemas live outside any single package so both backend and frontend can reference them as the source of truth.
- **Documentation stays in v2/docs**: Architecture and requirements documentation remains centralized and version-controlled alongside task files.

### CLAUDE.md

The root `CLAUDE.md` file provides AI coding assistants (such as Claude Code) with project context. Its content should mirror the instructions in `v2/implementation-prompt.md`, including:

- The mandatory reading order for project documentation
- Core engineering principles and business constraints
- The requirement to read all architecture and requirements docs referenced in task files
- The backend-driven frontend rule, hexagonal architecture rule, and other key architectural decisions

This ensures that AI agents working directly in the repository (not through the task system) receive the same context as agents following the implementation prompt.

---

## 2. Backend Package

```
backend/
├── src/
│   └── deskai/                    # Python package root
│       ├── __init__.py
│       ├── domain/                # Pure domain layer
│       ├── application/           # Application services (use cases)
│       ├── ports/                 # Port interfaces (abstract base classes)
│       ├── adapters/              # Outbound infrastructure adapters
│       ├── handlers/              # Inbound adapters (Lambda entry points)
│       ├── bff/                   # BFF assembly layer
│       └── shared/                # Cross-cutting utilities
├── tests/
│   ├── unit/                      # Unit tests (domain, application)
│   ├── integration/               # Integration tests (adapters)
│   └── conftest.py
├── pyproject.toml                 # Package metadata, dependencies
├── Makefile                       # Common dev commands
└── README.md
```

See `02-backend-architecture.md` for the full hexagonal layer breakdown.

### Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python 3.12 dependencies, build config, tool settings |
| `src/deskai/__init__.py` | Package marker |
| `tests/conftest.py` | Shared test fixtures |
| `Makefile` | Lint, format, test, deploy shortcuts |

---

## 3. Authenticated App Package

```
app/
├── src/
│   ├── api/                       # API client functions
│   ├── components/                # Reusable UI components
│   ├── hooks/                     # Custom React hooks
│   ├── pages/                     # Route-level page components
│   ├── types/                     # TypeScript type definitions
│   ├── utils/                     # Utility functions
│   ├── config/                    # Environment and runtime config
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── public/                        # Static assets
├── index.html                     # Vite entry point
├── package.json
├── tsconfig.json
├── vite.config.ts
├── eslint.config.js
└── README.md
```

### Rules

- The app is a presentation layer only. It renders backend-provided data and configuration.
- No business rules, domain calculations, or workflow decisions in this package.
- API calls go through `src/api/`, which wraps BFF endpoints.
- Types are generated from or aligned with `contracts/`.

---

## 4. Public Website Package

```
website/
├── pages/
│   ├── index.html                 # Landing page
│   ├── about.html                 # About page
│   └── pricing.html               # Pricing page
├── assets/
│   ├── css/
│   ├── js/                        # Minimal JS only when needed
│   └── images/
└── README.md
```

### Rules

- Standard HTML/CSS for SEO. No SPA framework.
- Minimal JavaScript only for interactive elements (e.g., mobile menu toggle).
- Must be crawlable, performant, and deployable as static files via CloudFront.
- No authentication logic. Login links redirect to the authenticated app.

---

## 5. Contracts Package

```
contracts/
├── http/
│   ├── auth.yaml                  # Auth API schemas
│   ├── consultations.yaml         # Consultation API schemas
│   ├── review.yaml                # Review API schemas
│   ├── exports.yaml               # Export API schemas
│   ├── ui-config.yaml             # UI config API schemas
│   └── errors.yaml                # Shared error response schemas
├── websocket/
│   ├── session.yaml               # WebSocket session messages
│   └── events.yaml                # WebSocket event messages
├── ui-config/
│   ├── screen-schemas.yaml        # Screen composition schemas
│   └── labels.yaml                # Label configuration schemas
├── feature-flags/
│   └── flags.yaml                 # Feature flag definitions
└── README.md
```

### Rules

- Schemas are defined in OpenAPI 3.1 YAML format for HTTP contracts.
- WebSocket messages use JSON Schema definitions in YAML.
- The backend generates response payloads that conform to these schemas.
- The frontend types are generated from or validated against these schemas.
- Contract changes require updating both backend and frontend.

See `03-contract-inventory.md` for the full contract inventory.

---

## 6. Infrastructure Package

```
infra/
├── app.py                         # CDK app entry point
├── stacks/
│   ├── auth_stack.py              # Cognito
│   ├── api_stack.py               # HTTP API + WebSocket API
│   ├── compute_stack.py           # Lambda functions
│   ├── storage_stack.py           # DynamoDB + S3
│   ├── orchestration_stack.py     # Step Functions + EventBridge + SQS
│   ├── monitoring_stack.py        # CloudWatch alarms + dashboards
│   ├── security_stack.py          # KMS + Secrets Manager
│   ├── cdn_stack.py               # CloudFront
│   └── budget_stack.py            # AWS Budgets + SNS alerts
├── constructs/                    # Reusable CDK constructs
│   └── tagged_construct.py        # Base construct with standard tags
├── config/
│   ├── dev.py                     # Dev environment config
│   └── prod.py                    # Prod environment config
├── cdk.json
├── pyproject.toml
└── README.md
```

### Rules

- All AWS infrastructure must be defined in CDK. No manual console changes.
- CDK uses Python to stay aligned with the backend stack.
- Each stack owns one infrastructure concern. Stacks reference each other through explicit dependencies.
- Environment-specific values (account IDs, domain names, feature flags) live in `config/`.
- All resources include environment prefix in naming: `deskai-{env}-{resource}`.

---

## 7. Tools Directory

```
tools/
├── generate-types.sh              # Generate TS types from contracts
├── lint-contracts.sh              # Validate contract schemas
└── local-setup.sh                 # Local dev environment setup
```

### Rules

- Keep scripts simple and documented.
- Prefer Makefile targets in each package over centralized scripts when possible.

---

## 8. CI/CD Directory

```
.github/
├── workflows/
│   ├── backend-ci.yml             # Backend lint, test, build
│   ├── app-ci.yml                 # Frontend lint, test, build
│   ├── infra-ci.yml               # CDK synth, diff
│   └── deploy.yml                 # Deployment pipeline
└── CODEOWNERS
```

### Rules

- Each package has its own CI workflow triggered by changes in that directory.
- Deploy workflow is manual or branch-triggered, not automatic on every push.
- CDK deployments go through `cdk diff` in CI before `cdk deploy`.

---

## 9. Environment Configuration Strategy

### Two Environments Only

| Environment | Purpose | AWS Account Isolation |
|-------------|---------|----------------------|
| `dev` | Development and testing | Separate resources, same or different account |
| `prod` | Production | Separate resources, hardened permissions |

### Configuration Approach

- CDK stacks accept an `environment` parameter (`dev` or `prod`).
- Resource naming follows: `deskai-{env}-{purpose}` (e.g., `deskai-dev-consultations`, `deskai-prod-api`).
- Environment-specific values are in `infra/config/dev.py` and `infra/config/prod.py`.
- Secrets are in AWS Secrets Manager, referenced by environment-prefixed names.
- Lambda functions receive environment through environment variables set by CDK.
- The backend reads `DESKAI_ENV` to determine the active environment.

### Naming Convention

```
# DynamoDB
deskai-dev-consultation-records
deskai-prod-consultation-records

# S3
deskai-dev-artifacts
deskai-prod-artifacts

# Lambda
deskai-dev-create-consultation
deskai-prod-create-consultation

# Cognito
deskai-dev-user-pool
deskai-prod-user-pool

# API Gateway
deskai-dev-http-api
deskai-prod-http-api
deskai-dev-ws-api
deskai-prod-ws-api
```

---

## 10. Package Dependency Rules

```
┌─────────────────────────────────────────────────────────┐
│                    contracts/                            │
│            (shared schemas, no code deps)                │
└──────────────┬────────────────────┬─────────────────────┘
               │                    │
               ▼                    ▼
┌──────────────────────┐  ┌──────────────────────┐
│      backend/        │  │        app/           │
│  (Python, Lambda)    │  │  (React, TypeScript)  │
└──────────┬───────────┘  └───────────────────────┘
           │
           ▼
┌──────────────────────┐
│       infra/         │
│    (AWS CDK)         │
│  references backend  │
│  Lambda code paths   │
└──────────────────────┘
```

### Dependency Rules

| Package | May Depend On | Must Not Depend On |
|---------|---------------|-------------------|
| `contracts/` | Nothing | Everything else |
| `backend/` | `contracts/` (for schema validation) | `app/`, `website/`, `infra/` |
| `app/` | `contracts/` (for type generation) | `backend/`, `website/`, `infra/` |
| `website/` | Nothing | Everything else |
| `infra/` | `backend/` (Lambda code paths) | `app/`, `website/`, `contracts/` |

---

## 11. Bootstrap Checklist for Task 003

Task 003 should create the following in order:

1. Initialize `backend/` with `pyproject.toml`, Python 3.12, and the `deskai` package skeleton.
2. Initialize `app/` with Vite + React + TypeScript scaffold.
3. Initialize `website/` with a placeholder landing page.
4. Initialize `contracts/` with stub schemas for the first endpoints.
5. Initialize `infra/` with a CDK app and empty stack shells.
6. Create `tools/` with a local setup script.
7. Create `.github/workflows/` with CI workflow stubs.
8. Update root `.gitignore` for Python, Node, CDK, and IDE artifacts.
9. Update root `README.md` with project overview and dev setup instructions.
