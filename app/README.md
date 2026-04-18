# Authenticated App

React + TypeScript + Vite application for authenticated physician workflows.

## Principles

- Presentation layer only.
- Backend-driven UI.
- No business rules in the client.
- Product-facing text defaults to Brazilian Portuguese (`pt-BR`).

## Implemented Flows (Task 012)

- Sign-in, session restoration, and sign-out
- Consultation list and consultation creation
- Patient creation helper for consultation setup
- Live consultation screen with microphone permission handling, WebSocket connection state, transcript partial rendering, and reconnect affordance
- Review/edit/finalization/export flow with explicit physician confirmation
- Backend-driven labels, status labels, section ordering, and action availability consumption

## Routes

- `/login`
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
