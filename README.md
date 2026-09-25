# Signalwatch

Signalwatch is a production-oriented competitor blog monitoring platform. It discovers RSS/Atom feeds, sitemaps, and direct article listings, queues checks through Redis/Celery, extracts article content, and reports exact publication-to-detection delay.

## Quick start

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open the dashboard at http://localhost:5173 and API docs at http://localhost:8000/docs.

## Database migration

With PostgreSQL available and the backend environment active:

```powershell
alembic upgrade head
```

The API reads `DATABASE_URL`; Docker Compose supplies the same value through `.env`.

## Controlled demo

Set `ALLOW_LOCAL_DEMO_TARGETS=true` in `.env`, start the stack, and publish a real demo article:

```powershell
Invoke-RestMethod http://localhost:9100/publish -Method Post -ContentType 'application/json' -Body '{"site":"a","title":"A controlled RSS article"}'
```

Add `http://localhost:9100/a/blog` (or its feed/sitemap URL) in the dashboard. The worker then discovers and extracts the article through the normal pipeline.

## Authentication

Register or log in through `POST /api/auth/register` or `POST /api/auth/login`; both return a bearer JWT. Passwords are Argon2-hashed and secrets are supplied through environment configuration.

## Load test

Run `python scripts/load_test.py` against a started set of controlled endpoints. The command writes `load-test-report.json` with measured concurrency, failures, timeouts, and latency; it never inserts fake monitoring rows.

## Local development

Backend: `cd backend; python -m venv .venv; .venv\\Scripts\\Activate.ps1; pip install -r requirements.txt; uvicorn app.main:app --reload`

Frontend: `cd frontend; npm install; npm run dev`

Tests: `cd backend; pytest`

The implementation is intentionally built in vertical slices. See `docs/` for architecture, operations, demo workflow, and load testing.
