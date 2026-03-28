# Task 003: Bootstrap Repository And Engineering Foundation

## 1. Overview

### Objective
Create the initial working repository structure, developer tooling, baseline CI conventions, and local engineering setup needed for implementation to begin safely and consistently.

### Why This Matters
The repo is effectively empty. Before feature work starts, the team needs the agreed project layout, package management, linting, formatting, schema locations, environment handling, and contributor instructions in place.

### Task Type
- DevOps

### Priority
- High

## 2. Context

### Product Context
This task supports every later workstream by turning planning documents into a workable codebase for the website, authenticated app, backend, BFF, and CDK layers.

### Technical Context
Bootstrap must align with the architecture blueprint and make it easy to add Lambda handlers, React pages, static pages, shared schemas, and deployment code without reorganization later.

### Related Systems
- Backend API
- Frontend app
- CI/CD

### Dependencies
- `002-design-system-architecture-and-project-structure.md`

## 3. Scope

### In Scope
- Create the top-level folder structure defined in Task 002.
- Initialize Python project tooling for backend, BFF, and CDK packages.
- Initialize React + TypeScript + Vite app structure for the authenticated app.
- Initialize the static public website structure with simple asset conventions.
- Add linting, formatting, and validation conventions for Python, TypeScript, CSS, and Markdown.
- Add shared config patterns for environment variables, secrets references, and contract versioning.
- Add contributor and local setup documentation.

### Out of Scope
- Full feature implementation.
- Provisioning real AWS environments.
- Production-grade CI/CD pipelines beyond a baseline structure.

## 4. Requirements

### Functional Requirements
- Developers must be able to install dependencies, run the frontend app, run local backend tests, and synthesize CDK locally.
- Shared contract directories must exist for schemas used by BFF and frontend.
- The repository must contain placeholders for prompts, adapters, and UI configuration assets.

### Non-Functional Requirements
- Tooling must favor a low-friction setup for a small team.
- Formatting and validation should be automatic where practical.
- The bootstrap should reduce future repo churn by establishing stable folder conventions early.

### Business Rules
- User-facing product copy defaults to `pt-BR`.
- Code and documentation are written in English.

### Technical Rules
- Backend stack aligns with Python 3.12.
- The authenticated app uses React, TypeScript, and Vite.
- The public website uses standard HTML, CSS, and minimal JavaScript.
- CDK uses Python to stay aligned with the backend stack.

## 5. Implementation Notes

### Proposed Approach
Create a monorepo-style layout with clearly separated packages and shared tooling. Add minimal starter apps and package commands, but keep business logic out until later tasks.

### AWS / Infrastructure Notes
- Add local configuration patterns for stack names, environment names, and secrets references without hardcoding live values.

### Backend Notes
- Create package scaffolding for domain, application, adapters, and entrypoints.
- Add schema validation and shared utility placeholders.

### Frontend Notes
- Create app shell, route skeletons, and API client placeholders.
- Keep only technical fallback copy in the frontend scaffold.

## 6. Deliverables

The task should produce:
- Initial repository structure
- Tooling and package manifests
- Lint and format configuration
- Local setup and contributor documentation
- CI/CD starter conventions or workflow placeholders

## 7. Acceptance Criteria

- [ ] The repo contains the agreed top-level project structure.
- [ ] Backend, frontend, and CDK packages can install and run their basic local commands.
- [ ] Shared schema or contract locations exist and are documented.
- [ ] Local setup documentation is sufficient for a new developer to start the project.
- [ ] Relevant tests are added or updated
- [ ] Documentation is updated if behavior or setup changed

## 8. Testing

### Required Tests
- Validate install, lint, format, and starter build commands for each package.

### Manual Verification
Follow the local setup guide from a clean checkout and confirm the developer can run the frontend starter, backend test command, and CDK synth command.

## 9. Risks and Edge Cases

### Risks
- Poor bootstrap choices could lock the team into avoidable tooling churn.
- Missing shared contract locations could cause contract duplication later.

### Edge Cases
- Frontend and BFF may need separate build pipelines even if they share TypeScript contracts later.
- Some local development flows may need mocked AWS or provider dependencies before real integrations exist.

## 10. Definition of Done

- [ ] Implementation is complete
- [ ] Acceptance criteria are met
- [ ] Tests pass
- [ ] No obvious regressions were introduced
- [ ] Logs, metrics, and error handling were considered
- [ ] Security and permissions were reviewed if relevant
- [ ] Task is ready for review or merge
