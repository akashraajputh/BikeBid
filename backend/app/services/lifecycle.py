import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models import AuditLog, Auction, AuctionStatus, Bid, Motorcycle


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class AuctionLifecycle:
    def __init__(self, interval_seconds: int = 10) -> None:
        self.interval_seconds = interval_seconds

    def start(self) -> asyncio.Task:
        return asyncio.create_task(self.run())

    async def run(self) -> None:
        while True:
            async with AsyncSessionLocal() as db:
                await self.update_statuses(db)
            await asyncio.sleep(self.interval_seconds)

    async def update_statuses(self, db: AsyncSession) -> None:
        result = await db.execute(
            select(Auction)
            .options(
                selectinload(Auction.motorcycle),
                selectinload(Auction.bids),
            )
            .where(Auction.status.in_([AuctionStatus.scheduled.value, AuctionStatus.live.value]))
        )
        now = datetime.now(timezone.utc)
        changed = False

        for auction in result.scalars().all():
            starts_at = as_utc(auction.start_time)
            ends_at = as_utc(auction.end_time)
            if auction.status == AuctionStatus.scheduled.value and starts_at <= now < ends_at:
                auction.status = AuctionStatus.live.value
                changed = True
                db.add(
                    AuditLog(
                        action="auction.started",
                        details=f"auction_id={auction.id}",
                    )
                )
            if ends_at <= now:
                auction.status = AuctionStatus.ended.value
                highest_bid = max(auction.bids, key=lambda bid: bid.amount, default=None)
                reserve = auction.motorcycle.reserve_price
                auction.reserve_met = bool(highest_bid and (reserve is None or highest_bid.amount >= reserve))
                auction.winner_id = (
                    highest_bid.user_id
                    if highest_bid is not None and auction.reserve_met
                    else None
                )
                changed = True
                db.add(
                    AuditLog(
                        action="auction.ended",
                        details=f"auction_id={auction.id}; reserve_met={auction.reserve_met}",
                    )
                )

        if changed:
            await db.commit()


auction_lifecycle = AuctionLifecycle()
