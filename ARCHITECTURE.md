# BikeBid Architecture

## Backend modules

The backend keeps the requested layered organization:

```text
backend/app/
  api/       FastAPI routers grouped by auth, buyer discovery/activity, and administration
  core/      Settings, async SQLAlchemy sessions, token security, authorization, rate limiting
  models/    SQLAlchemy 2.x ORM entities
  schemas/   Pydantic request and response validation
  services/  Auction serialization, lifecycle, seeding, and WebSocket connections
  main.py    Application lifespan, middleware, router mounting, and health checks
```

## Roles

- Public visitors can browse motorcycle/auction listings.
- Buyers can bid on live auctions and read only their own dashboard, bids, and auctions.
- Administrators use `/api/v1/admin/*` to manage listings and auctions, view users, suspend accounts, and inspect analytics.
- Registration always creates a buyer; role values supplied by a client are not accepted.
- Authorization is enforced by FastAPI dependencies and checked again in operation-specific business rules.

## Auction data flow and concurrency

PostgreSQL is the authoritative record for bids and auction state. Bid submission locks the auction row with `SELECT ... FOR UPDATE`, checks server time/status and the current minimum amount, then writes the bid, updates the current price/highest bidder, and writes any outbid notification in the same transaction. Only after commit does the API broadcast the accepted auction snapshot over WebSockets. This serializes simultaneous bids for the same auction on PostgreSQL while allowing independent auctions to proceed concurrently.

Auction lifecycle processing is an asyncio background task started and stopped with FastAPI lifespan. It transitions scheduled auctions to live and live/scheduled auctions to ended using UTC timestamps, calculates reserve qualification, records the final winner only when the reserve is met, and writes lifecycle audit events. Browser timers are display-only.

WebSocket clients authenticate with an access token in the connection query and receive an initial database snapshot, then updates after accepted bids. The frontend reconnects and refreshes its auction query on events.

## Database and migrations

SQLAlchemy uses `postgresql+asyncpg` for the configured PostgreSQL DSN. Alembic manages schema evolution. Local SQLite tests can opt into automatic schema creation; PostgreSQL requires `alembic upgrade head`.

## Observability and security

HTTP requests include a generated/preserved request ID, emit structured JSON log records, and return the request ID in `X-Request-ID`. `/api/v1/health` performs a database readiness probe and `/health/live` reports process liveness. JWT access/refresh tokens carry a session version; logout and account suspension increment the user's version to invalidate existing tokens. Login and bidding endpoints use process-local rate limits.

## API families

| API | Purpose |
|---|---|
| `/api/v1/auth/*` | Registration, login, refresh, logout, and current identity |
| `/api/v1/motorcycles*` | Public motorcycle browsing |
| `/api/v1/auctions*` | Public auctions and bid actions |
| `/api/v1/users/me/*` | Current buyer's bid and auction history |
| `/api/v1/admin/*` | Protected listings, auction operations, user status, analytics |

Unversioned `/api` endpoints are retained for compatibility with the existing frontend.
