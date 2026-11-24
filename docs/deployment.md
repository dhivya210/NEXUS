# Deployment

## Local production-like run

1. Copy `.env.example` to `.env`.
2. Set `NEXUS_ADMIN_EMAIL`, `NEXUS_ADMIN_PASSWORD`, and a random `NEXUS_SECRET_KEY` of at least 32 characters.
3. Set `NEXUS_COOKIE_SECURE=false` for local HTTP.
4. Run `docker compose up --build`; open `http://localhost:3000`.

## Hosted deployment

- Host the frontend and backend behind HTTPS, and set `NEXUS_COOKIE_SECURE=true`.
- Configure all secrets in the hosting provider; never commit `.env`.
- Use PostgreSQL for `DATABASE_URL` in local runs or `DATABASE_URL_DOCKER` when running Docker Compose.
- Set `NEXUS_BACKEND_URL` in the frontend runtime to the backend origin.
- Restrict backend CORS to the deployed frontend origin.
- Configure OpenAI, Google Sheets, and SMTP credentials only if those integrations are needed.

The sample Docker Compose uses SQLite for a convenient demonstration. It is not a high-availability production database configuration.
