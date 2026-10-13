from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models import (
    AuditLog,
    Auction,
    AuctionStatus,
    Bid,
    Motorcycle,
    Notification,
    User,
    UserRole,
)


async def seed_demo_data() -> None:
    async with AsyncSessionLocal() as db:
        users_count = await db.scalar(select(func.count()).select_from(User))
        if users_count:
            return

        admin = User(
            email="admin@bikebid.com",
            username="admin",
            full_name="BikeBid Admin",
            password_hash=hash_password("Admin123!"),
            role=UserRole.admin.value,
        )
        buyer = User(
            email="buyer@bikebid.com",
            username="buyer",
            full_name="Demo Buyer",
            password_hash=hash_password("Password123!"),
            role=UserRole.buyer.value,
        )
        db.add_all([admin, buyer])
        await db.flush()

        motorcycles = [
            Motorcycle(
                title="2021 Kawasaki Ninja 650",
                description="Well-kept sport bike with service record and clean title.",
                manufacturer="Kawasaki",
                model="Ninja 650",
                year=2021,
                mileage=8400,
                engine_cc=649,
                fuel_type="Petrol",
                condition="Excellent",
                location="Bengaluru",
                start_price=Decimal("4200.00"),
                reserve_price=Decimal("4700.00"),
                image_urls=["https://images.unsplash.com/photo-1558980664-10e7170b5df9?auto=format&fit=crop&w=1200&q=80"],
                seller_id=admin.id,
            ),
            Motorcycle(
                title="2020 Royal Enfield Himalayan",
                description="Adventure tourer with crash protection, ready for touring.",
                manufacturer="Royal Enfield",
                model="Himalayan",
                year=2020,
                mileage=16000,
                engine_cc=411,
                fuel_type="Petrol",
                condition="Good",
                location="Pune",
                start_price=Decimal("3100.00"),
                reserve_price=Decimal("3500.00"),
                image_urls=["https://images.unsplash.com/photo-1571068316344-75bc9d0d90d1?auto=format&fit=crop&w=1200&q=80"],
                seller_id=admin.id,
            ),
            Motorcycle(
                title="2019 Honda CBR 250R",
                description="Value-focused premium commuter with clean maintenance history.",
                manufacturer="Honda",
                model="CBR 250R",
                year=2019,
                mileage=13500,
                engine_cc=249,
                fuel_type="Petrol",
                condition="Very Good",
                location="Delhi",
                start_price=Decimal("2600.00"),
                reserve_price=Decimal("2900.00"),
                image_urls=["https://images.unsplash.com/photo-1528629297340-d1d466945dc5?auto=format&fit=crop&w=1200&q=80"],
                seller_id=admin.id,
            ),
        ]
        db.add_all(motorcycles)
        await db.flush()

        now = datetime.now(timezone.utc)
        live_auction = Auction(
            motorcycle_id=motorcycles[0].id,
            status=AuctionStatus.live.value,
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=6),
            current_price=Decimal("4500.00"),
            minimum_increment=Decimal("50.00"),
            reserve_met=False,
            winner_id=buyer.id,
        )
        scheduled_auction = Auction(
            motorcycle_id=motorcycles[1].id,
            status=AuctionStatus.scheduled.value,
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(days=1),
            current_price=Decimal("0.00"),
            minimum_increment=Decimal("50.00"),
        )
        db.add_all([live_auction, scheduled_auction])
        await db.flush()
        db.add_all(
            [
                Bid(auction_id=live_auction.id, user_id=buyer.id, amount=Decimal("4500.00")),
                Notification(
                    user_id=buyer.id,
                    title="Auction update",
                    message="A bike you follow is active right now.",
                    is_read=False,
                ),
                AuditLog(user_id=admin.id, action="seed", details="Initial sample data loaded"),
            ]
        )
        await db.commit()
