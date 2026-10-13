# Assumptions and Trade-offs

- All auction datetimes are normalized to UTC at the API boundary. Naive incoming timestamps are interpreted as UTC for compatibility.
- Monetary amounts are stored as fixed-precision SQL `NUMERIC`; request schemas use `Decimal`.
- Motorcycle deletion is archival when a record has auction history; physical deletion is intentionally not allowed in that case.
- Motorcycle prices may only be changed while its auction is still in draft. Listing details are immutable once an auction is live, ended, or cancelled.
- Only draft or scheduled auctions may be cancelled. Live auctions cannot be stopped through the normal cancellation endpoint.
- The auction lifecycle worker runs in the API process. For multi-replica production deployment, run a single designated worker or move scheduling to a distributed job system.
- Bid row locking relies on PostgreSQL semantics. SQLite is used only for local automated tests and does not validate PostgreSQL concurrency locking.
- Rate limits are process-local and protect development/single-instance operation. A multi-instance deployment should move counters to Redis before scaling.
- The WebSocket connection registry is process-local. Multi-instance broadcast requires Redis pub/sub or another shared event transport.
- Seeded credentials are development-only; provision a unique administrator securely and replace the development secret before deployment.
- The project has not been deployed to a public host; no public live URL is claimed.
