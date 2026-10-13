# BikeBid Auction Platform

BikeBid is a used-motorcycle auction application with a modular FastAPI backend and React frontend.

## Backend layout

```text
backend/
  alembic/
  app/
    api/       # FastAPI route modules
    core/      # Settings, async database, auth dependencies
    models/    # SQLAlchemy models
    schemas/   # Pydantic validation schemas
    services/  # Auction rules, lifecycle, serialization, seeding
    main.py
```

## Local setup

The workspace `.env` is configured for PostgreSQL with the requested asyncpg URL. For a fresh checkout, copy `.env.example` to `.env` and update its database connection values to match your local Postgres setup.

The local `.env` is ignored by Git. Do not place database passwords or production secrets in tracked files.

Start PostgreSQL with `docker compose up -d`. On a new database, run the migrations from `backend/` before starting the API:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

From `frontend/`, install dependencies and start Vite:

```powershell
npm install
npm run dev
```

Pytest defaults to an isolated async SQLite test database (`backend/bikebid_test.db`) so test runs do not mutate the configured PostgreSQL database. To select another test database explicitly:

```powershell
$env:DATABASE_URL = "sqlite+aiosqlite:///./bikebid_test.db"
.\.venv\Scripts\python.exe -m pytest
```

SQLite test mode automatically creates its schema. PostgreSQL mode expects Alembic migrations to have been applied.

## Versioned API overview

- Authentication: `/api/v1/auth/register`, `/login`, `/refresh`, `/logout`, `/me`
- Public discovery: `/api/v1/motorcycles`, `/api/v1/auctions`, `/live`, `/upcoming`
- Buyer activity: `/api/v1/users/me/bids`, `/api/v1/users/me/auctions`
- Buyer bidding: `POST /api/v1/auctions/{id}/bids`, `GET /api/v1/auctions/{id}/bids`
- Administration: `/api/v1/admin/motorcycles`, `/auctions`, `/users`, `/analytics`
- Health: `/api/v1/health` checks database readiness; `/health/live` checks process liveness

The prior unversioned `/api` routes remain available for frontend compatibility.

## Frontend roles and workflows

- Buyers can register, browse motorcycles and auctions, place bids, and review their bid/auction activity.
- Administrators can create and edit motorcycle listings, archive listings without auction history, create and schedule auctions, update or cancel draft/scheduled auctions, and suspend or reactivate user accounts.
- Admin pages are available under `/admin`; buyer history is available under `/my-bids` and `/my-auctions`.

## Development admin

- Email: `admin@bikebid.com`
- Password: `Admin123!`

The development account is created when the database is empty. Change or disable seeded credentials before deployment.
