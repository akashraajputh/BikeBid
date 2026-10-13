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

The root `.env` file configures PostgreSQL for the backend. For a fresh checkout, copy `.env.example` to `.env` and update its database connection values to match your local Postgres setup. The backend loads this file from the workspace root; run backend commands from `backend/`.

The local `.env` is ignored by Git. Do not place database passwords or production secrets in tracked files.

For the configured Aiven database, replace `AIVEN_PASSWORD` in `.env` with the database password. The connection uses the asyncpg driver and requires SSL; URL-encode reserved characters in the password before using it.

Install the backend dependencies once:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start PostgreSQL from the workspace root:

```powershell
cd ..
docker compose up -d
```

For a new PostgreSQL database, apply migrations before starting the API. In a backend terminal:

```powershell
cd backend
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a separate terminal, install frontend dependencies once and start Vite:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

Open the frontend at <http://127.0.0.1:5173>. Backend liveness is available at <http://127.0.0.1:8000/health/live>; database readiness is available at <http://127.0.0.1:8000/api/v1/health>.

Pytest defaults to an isolated async SQLite test database (`backend/bikebid_test.db`) so test runs do not mutate the configured PostgreSQL database. Run tests from `backend/`:

```powershell
cd backend
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
