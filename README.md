# BikeBid

BikeBid is a motorcycle marketplace and auction application. Buyers can browse motorcycle listings, follow auctions, and place bids. Administrators can manage listings, auctions, users, and view platform analytics.

> **Project status:** This repository does not declare a semantic release version. The backend exposes a versioned API at `/api/v1`; legacy `/api` routes remain available for frontend compatibility.

## Features

- Buyer registration, login, logout, access-token refresh, and authenticated profile.
- Motorcycle discovery and detail pages; auction list, detail, live, and upcoming views.
- Auction bidding with minimum-increment validation, bid history, and outbid notifications.
- WebSocket updates for live auction activity; clients refresh auction data when updates arrive.
- Buyer dashboard, bid history, auction history, and notifications.
- Admin workflows for motorcycle listings, auction scheduling and cancellation, user suspension/reactivation, and analytics.
- UTC-based auction lifecycle management, reserve-price checks, winner selection, and audit events.
- Liveness and database-readiness health endpoints, request IDs, and structured request logs.

## Architecture

```text
Browser
  └── React 19 + TypeScript + Vite static frontend (Render Static Site)
        ├── HTTP / JSON ────────────────┐
        └── WebSocket live updates ─────┤
                                        v
                              FastAPI API (Render Web Service)
                                ├── API routers and validation
                                ├── SQLAlchemy async sessions
                                ├── auction lifecycle task
                                └── WebSocket connection manager
                                        |
                         asyncpg over TLS (ssl=require)
                                        v
                              PostgreSQL (Aiven)
```

### Source layout

```text
backend/
  app/
    api/        Authentication, motorcycles, auctions, buyer activity, admin
    core/       Settings, database sessions, security, authorization, rate limiting
    models/     SQLAlchemy entities and enums
    schemas/    Pydantic request and response models
    services/   Auction lifecycle, query helpers, serialization, seeding, realtime
    main.py     FastAPI lifespan, middleware, routers, and health endpoints
  alembic/      Database migration environment and version history
  test_*.py    API and workflow tests
frontend/
  src/App.tsx   React routes, pages, API calls, and WebSocket client
  src/          UI styles and static assets
```

The backend is a FastAPI application using async SQLAlchemy 2.x and PostgreSQL via `asyncpg`. Alembic manages PostgreSQL schema changes. The frontend is a single-page React application using React Router and TanStack Query. It calls the backend over HTTP and opens authenticated WebSocket connections for auction updates.

### Data model

The database contains users, motorcycle listings, auctions, bids, refresh tokens, notifications, and audit logs. PostgreSQL is the source of truth for auction and bid state. A bid request locks the auction row, checks its state and minimum bid, and stores the bid and price update in a transaction before broadcasting the committed result.

### Roles and security behavior

- Public visitors can browse motorcycles and auctions.
- Registration creates buyer accounts; a client cannot self-assign the administrator role.
- Buyers can access their own dashboard and activity.
- Admin API routes require administrator authorization.
- Access tokens carry a session version. Logout and account suspension invalidate sessions by changing that version.
- Login and bid endpoints have process-local rate limits.

### API overview

All versioned routes are under `/api/v1`. The same primary routers are also mounted under `/api` for compatibility.

| Route | Purpose |
| --- | --- |
| `/api/v1/auth/*` | Register, log in, refresh/logout sessions, and retrieve the current user |
| `/api/v1/motorcycles` | Browse motorcycle listings and retrieve listing details |
| `/api/v1/auctions` | Browse auctions, inspect bids, publish/cancel auctions, and place bids |
| `/api/v1/users/me/*` | Retrieve the signed-in buyer's bids and auction activity |
| `/api/v1/dashboard` | Buyer dashboard |
| `/api/v1/admin/*` | Admin listing, auction, user, and analytics operations |
| `/ws/auction/{auction_id}` | Authenticated live auction updates |
| `/health/live` | Process liveness probe |
| `/api/v1/health` | Database readiness probe |
| `/docs` | Interactive OpenAPI documentation |

## Local development

### Requirements

- Python 3.11 or newer (the project has been exercised with Python 3.14).
- Node.js compatible with the installed Vite version and npm.
- PostgreSQL/Aiven credentials for the application, or use the included Docker Compose PostgreSQL service for local development.

### Backend setup

From the repository root, create `backend/.venv`, install dependencies, configure the root `.env`, and apply migrations:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd ..
Copy-Item .env.example .env
```

Edit `.env` with a PostgreSQL connection URL. For Aiven use the `asyncpg` SQLAlchemy URL form, enable TLS with `?ssl=require`, and URL-encode any reserved characters in the password:

```text
DATABASE_URL=postgresql+asyncpg://avnadmin:<URL_ENCODED_PASSWORD>@<AIVEN_HOST>:<PORT>/defaultdb?ssl=require
AUTO_CREATE_SCHEMA=false
FRONTEND_URL=http://localhost:5173
SECRET_KEY=<long-random-secret>
```

Keep `.env` private and untracked. Never commit database credentials or production secrets. `POSTGRES_*` and `REDIS_URL` are only relevant if you use the optional local Compose service; the application database connection is `DATABASE_URL`.

Apply schema migrations and run the API:

```powershell
cd backend
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Alternatively, run local PostgreSQL from the repository root with `docker compose up -d` and set `DATABASE_URL` to match the Compose credentials.

### Frontend setup

In a separate terminal:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

Open <http://127.0.0.1:5173>. During Vite development the frontend defaults to `http://localhost:8000`. Set `VITE_API_BASE_URL` in the frontend build environment when the API is hosted elsewhere.

### Tests and build

The backend test configuration uses an isolated SQLite database by default, so tests do not modify the configured Aiven or local PostgreSQL database:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Build and lint the frontend:

```powershell
cd frontend
npm run build
npm run lint
```

SQLite tests cover API/workflow behavior but do not verify PostgreSQL row-lock concurrency. Check `/api/v1/health` against the deployed service to verify its database connection.

## Deployment: Render + Aiven

Deploy the frontend and backend as separate Render services and use Aiven PostgreSQL as the persistent database. Do not expose the database password in the frontend, source code, or repository.

### 1. Configure Aiven PostgreSQL

1. Create or select an Aiven PostgreSQL service and database.
2. Copy the host, port, database name, username, and password from Aiven's connection information.
3. In Render, set the backend's `DATABASE_URL` using a password placeholder:

   ```text
   postgresql+asyncpg://avnadmin:${AIVEN_PASSWORD}@<AIVEN_HOST>:<PORT>/<DATABASE_NAME>?ssl=require
   ```

4. Add a separate backend environment variable named `AIVEN_PASSWORD` with the exact password from Aiven. The backend resolves `${AIVEN_PASSWORD}` itself and URL-encodes it, so this does not depend on Render interpolating environment variables inside `DATABASE_URL`.
5. Ensure the Aiven service is running and accepts connections from the Render service's network. If Aiven IP allowlists are enabled, configure access for the deployed backend using the current Render egress IP information or the appropriate Aiven networking option.

### 2. Deploy the backend on Render

Create a Render **Web Service** connected to this repository:

| Setting | Value |
| --- | --- |
| Root directory | `backend` |
| Runtime | Python |
| Build command | `pip install -r requirements.txt` |
| Pre-deploy command | `alembic upgrade head` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health check path | `/health/live` |

If the selected Render plan does not provide a pre-deploy command, run `alembic upgrade head` once from the Render shell before the first deployment, and repeat it when deploying schema changes. Do not run migrations concurrently from multiple app replicas.

Set these backend environment variables in Render:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Aiven URL in the `postgresql+asyncpg` format above, using `${AIVEN_PASSWORD}` |
| `AIVEN_PASSWORD` | The current Aiven password (secret) |
| `AUTO_CREATE_SCHEMA` | `false` |
| `SECRET_KEY` | A long, unique random secret |
| `FRONTEND_URL` | The deployed frontend's exact `https://` origin, without a trailing slash |
| `ALGORITHM` | `HS256` (optional; this is the application default) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` (optional default) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` (optional default) |

The app reads Render's `PORT` at startup through Uvicorn's command. Do not define `DATABASE_URL` in the frontend service.

### 3. Deploy the frontend on Render

Create a Render **Static Site** from the same repository:

| Setting | Value |
| --- | --- |
| Root directory | `frontend` |
| Build command | `npm ci && npm run build` |
| Publish directory | `dist` |

Set this frontend environment variable before the build:

| Variable | Value |
| --- | --- |
| `VITE_API_BASE_URL` | The backend's public Render URL, e.g. `https://<backend-service>.onrender.com` |

Vite embeds `VITE_*` values into the built client bundle. This URL is public; do not put secrets in `VITE_*` variables. Add a Render rewrite rule for the SPA: source `/*`, destination `/index.html`, action **Rewrite**, so direct navigation to app routes works.

After creating the frontend service, set the backend's `FRONTEND_URL` to the exact Render Static Site origin, then redeploy/restart the backend. If using a custom domain, use that origin instead.

### 4. Verify deployment

1. Visit `https://<backend-service>.onrender.com/health/live`; expect `{"status":"ok"}`.
2. Visit `https://<backend-service>.onrender.com/api/v1/health`; expect `{"status":"ok","database":"ready"}`.
3. Open the frontend Render URL, register a buyer, browse listings, and check browser network requests for API/CORS errors.
4. Verify WebSocket behavior from an auction page; the connection URL should use `wss://` for an HTTPS deployment.
5. Confirm Alembic migrations ran and review Render logs for startup or database errors.

## Production limitations and launch checklist

- **Demo seed data:** On startup, an empty database is automatically seeded with demo accounts (`admin@bikebid.com` / `Admin123!` and `buyer@bikebid.com` / `Password123!`) and sample auctions. Do not expose a deployment with these credentials; change/remove the seed behavior or secure the admin account before public launch.
- **Run one backend instance:** The auction lifecycle worker, rate-limit counters, and WebSocket connection registry are process-local. Use one backend instance for the current design. Scaling to multiple instances requires a shared job/leader mechanism, shared rate limiting, and cross-instance WebSocket pub/sub (for example Redis).
- **Secrets:** Rotate any credentials that have been shared outside a private secret manager. Store production secrets only in Render's environment settings and Aiven's secret controls.
- **Backups and migrations:** Enable Aiven backups, apply Alembic migrations before running code that depends on them, and verify migrations against a non-production database first.
- **TLS and CORS:** Use HTTPS/WSS in production and set `FRONTEND_URL` to the precise frontend origin. Only allow origins that you control.
- **Persistence:** The application stores user-upload-free listing image URLs; keep externally hosted image resources available. Render's local filesystem is not a persistent database.
- **Email/operations:** No production email delivery, distributed task runner, or centralized metrics/alerting integration is currently configured.

## License

No license file is currently included. Contact the repository owner before redistributing the project.
