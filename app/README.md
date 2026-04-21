# Authenticated App

React + TypeScript + Vite application for authenticated physician workflows.

## Principles

- Presentation layer only.
- Backend-driven UI.
- No business rules in the client.
- Product-facing text defaults to Brazilian Portuguese (`pt-BR`).

## Implemented Flows

- Sign-in, session restoration, and sign-out
- Staged `Nova consulta` flow with patient-first entry, existing-patient search, patient detail/history, and new-patient quick start
- Consultation history screen separated from new-consultation setup
- Live consultation screen with microphone permission handling, WebSocket connection state, transcript partial rendering, and reconnect affordance
- Review/edit/finalization/export flow with explicit physician confirmation
- Backend-driven labels, status labels, section ordering, and action availability consumption

## Design System

The authenticated app has a small local design system under `src/components/ui`.

Available primitives:

- `Button` for primary, secondary, ghost, danger, disabled, and loading actions.
- `Text`, `Heading`, and `Link` for consistent typography and links.
- `Chip` for compact statuses and selectable filters.
- `Loader` for inline and section loading states.
- `Card` for single-level panels and page sections.
- `TextField`, `TextAreaField`, and `SelectField` for accessible form fields with labels, help text, and errors.
- `Alert` for information, success, warning, and danger banners.
- `EmptyState` for empty list or missing-content states.
- `Icon` for a curated `lucide-react` icon set. Icons are decorative by default; pass `label` only when the icon itself communicates meaning.

Styling lives in:

- `src/styles/tokens.css` for shared color, spacing, type, elevation, focus, radius, motion, and layout tokens.
- `src/styles/design-system.css` for the component classes used by the primitives.

Design-system components must not own business rules. Page components should keep rendering based on backend-provided labels, statuses, entitlements, and action availability.

The core authenticated pages use these primitives for cards, actions, loading states, alerts, form fields, status chips, and empty states.

## Request State

HTTP server state uses TanStack Query through app-local hooks in `src/api/query-hooks.ts`.

- `createAppQueryClient` defines conservative in-memory defaults with disabled global retries and no cache persistence.
- Query keys are centralized in `queryKeys`.
- Page reads use query hooks for user profile, UI config, patients, consultation list/detail, and review data.
- Writes use mutation hooks for patient creation, consultation creation, session start/end, review updates, finalization, and export.
- Mutations invalidate or update the affected query keys so screens refresh after successful writes.
- `AuthProvider` clears the query client when the user signs out or session restoration fails.
- Live WebSocket connection, microphone, and transcript streaming state stays local to the live consultation page and is not hidden behind HTTP cache state.

## Routes

- `/login`
- `/nova-consulta`
- `/patients/:patientId`
- `/consultations`
- `/consultations/:consultationId/live`
- `/consultations/:consultationId/review`

## Environment Variables

- `VITE_API_BASE_URL`
- `VITE_API_PROXY_TARGET` (used only by local Vite dev server proxy)
- `VITE_WS_BASE_URL`
- `VITE_CONTRACT_VERSION`

For local development against AWS `dev`, use:

```bash
VITE_API_BASE_URL=/api
VITE_API_PROXY_TARGET=https://i0dueykjuc.execute-api.us-east-1.amazonaws.com/dev
VITE_WS_BASE_URL=wss://dzy4cvrae2.execute-api.us-east-1.amazonaws.com/dev
VITE_CONTRACT_VERSION=v1
```

## Local Commands

```bash
npm install
npm run dev
npm run lint
npm run typecheck
npm run test
npm run build
```
