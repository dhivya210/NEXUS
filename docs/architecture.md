# Architecture

NEXUS is a single-tenant command center with a Next.js web app, FastAPI service, SQLAlchemy persistence, and provider adapters.

## Request flow

1. The browser sends same-origin `/api/*` requests.
2. Next.js rewrites those requests to `NEXUS_BACKEND_URL`.
3. FastAPI verifies an HMAC-signed, HTTP-only boss session on every non-public API route.
4. Alembic migrations manage the SQLAlchemy schema; records use SQLite locally or PostgreSQL when `DATABASE_URL` is configured.
5. Agent execution and chat use the OpenAI Chat Completions API only when `OPENAI_API_KEY` is configured. Structured agent JSON is validated before deliverables are saved.
6. Google Sheets and SMTP adapters report provider-confirmed results; unavailable credentials are recorded as unconfigured/failed rather than successful.

## Main entities

Clients own projects; projects own tasks; tasks have specialist assignments, dependency edges, executions, and deliverables. Activity, chat, integrations, tests, security findings, deployments, and email delivery are stored as separate records.

## Workflow

New client requests create a project plan and seven role-specific tasks. Tasks can only execute when the project is active, the specialist is assigned, required dependencies are complete, and an AI key is configured. Completion requires a validated agent response and persisted deliverable. Task completion updates project progress and activity history.

## Security boundaries

- The admin password, session signing key, LLM key, Google credentials, and SMTP credentials are environment-only.
- Session cookies are HTTP-only and same-site; set `NEXUS_COOKIE_SECURE=true` behind HTTPS.
- Agent prompts receive only the assigned task and project context.
- Agent-generated state is not trusted; task state transitions and persisted deliverables are controlled by the backend.
