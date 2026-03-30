# Local Development Setup

## Prerequisites

- Python 3.12 (project target)
- Node.js 20+
- npm 10+

## 1. Clone and Environment

```bash
git clone <repo-url>
cd DeskAI
cp .env.example .env.local
```

## 2. Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
make lint
make test
```

## 3. Infrastructure Setup

```bash
cd infra
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
npm install
make synth
```

## 4. Authenticated App Setup

```bash
cd app
npm install
npm run lint
npm run typecheck
npm run dev
```

## 5. Public Website Setup

```bash
cd website
npm install
npm run lint
npm run dev
```

## 6. Root Formatting and Contract Validation

```bash
npm install
npm run lint
npm run format:check
```

## Notes

- The frontend app is intentionally backend-driven.
- Do not add business logic to `app/`.
- Keep `contracts/` as the shared source of truth for API shapes.
