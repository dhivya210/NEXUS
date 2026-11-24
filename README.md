# NEXUS — Autonomous IT Agency

NEXUS is a full-stack command center for an AI-powered software agency. It brings project planning, task delivery, employee chats, reports, and integrations together in one dashboard.

## Project overview

- **Frontend:** Next.js dashboard for projects, tasks, AI employees, reports, chats, automation, and settings.
- **Backend:** FastAPI service with authenticated APIs, SQLite by default, and PostgreSQL support.
- **AI workflows:** Eight role-specific employee profiles can plan and execute work through the configured OpenAI provider. Task completion requires a saved deliverable.
- **Integrations:** Optional Google Sheets synchronization and scheduled SMTP reports.

AI and external integrations require your own provider credentials; they remain unavailable until configured. Do not commit `.env` or other secrets.

## Run locally

Create the environment file and configure the required Boss session values:
```powershell
Copy-Item .env.example .env
# Set NEXUS_ADMIN_EMAIL, NEXUS_ADMIN_PASSWORD, and NEXUS_SECRET_KEY in .env
```

Backend:
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:
```powershell
cd frontend
npm run dev
```

Open `http://localhost:3000`.
Sign in using the configured Boss email and password.

## Run with Docker

```powershell
docker compose up --build
```

## Configuration

SQLite is used by default. Set `DATABASE_URL` to a PostgreSQL connection string for production. External integrations remain disabled until credentials are supplied.
Docker Compose uses a persistent SQLite data volume by default; set `DATABASE_URL_DOCKER` to a PostgreSQL URL when deploying the Compose stack with PostgreSQL.

- `OPENAI_API_KEY`: enables LLM execution and employee chat; without it, requests report that AI is unconfigured and do not claim work completed.
- `GOOGLE_SERVICE_ACCOUNT_JSON`: Google service-account credential JSON.
- `GOOGLE_SPREADSHEET_ID`: target spreadsheet.
- `SMTP_*`: secure email provider settings.

Google Sheets and email delivery are not claimed as connected or delivered without provider credentials and confirmation.

See [agency proposal](docs/agency-proposal.md), [architecture](docs/architecture.md), [workflow](docs/workflow.md), [employee plan](docs/employee-plan.md), [integrations](docs/integrations.md), and [deployment](docs/deployment.md).
