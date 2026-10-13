from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models import Auction, AuctionStatus, AuditLog, Bid, Motorcycle, Notification, User
from app.services.auction_queries import auction_detail_statement
from app.services.serializers import auction_response, decimal_to_float

router = APIRouter(tags=["dashboards"])


@router.get("/dashboard")
async def buyer_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bids_result = await db.execute(
        select(Bid, Motorcycle.title)
        .join(Auction, Bid.auction_id == Auction.id)
        .join(Motorcycle, Auction.motorcycle_id == Motorcycle.id)
        .where(Bid.user_id == current_user.id)
        .order_by(Bid.created_at.desc())
        .limit(10)
    )
    won_result = await db.execute(
        auction_detail_statement().where(
            Auction.winner_id == current_user.id,
            Auction.status == AuctionStatus.ended.value,
            Auction.reserve_met.is_(True),
        )
    )
    active_result = await db.execute(
        auction_detail_statement().where(
            Auction.status.in_([AuctionStatus.live.value, AuctionStatus.scheduled.value])
        )
    )
    return {
        "active_auctions": [auction_response(item) for item in active_result.scalars().unique().all()],
        "recent_bids": [
            {
                "auction_id": bid.auction_id,
                "auction_title": motorcycle_title,
                "amount": decimal_to_float(bid.amount),
                "created_at": bid.created_at.isoformat(),
            }
            for bid, motorcycle_title in bids_result.all()
        ],
        "won_auctions": [auction_response(item) for item in won_result.scalars().unique().all()],
    }


@router.get("/admin/summary")
async def admin_summary(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return {
        "auctions": await db.scalar(select(func.count()).select_from(Auction)),
        "motorcycles": await db.scalar(select(func.count()).select_from(Motorcycle)),
        "users": await db.scalar(select(func.count()).select_from(User)),
        "bids": await db.scalar(select(func.count()).select_from(Bid)),
        "user_role": current_user.role,
    }


@router.get("/notifications")
async def notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    return [
        {
            "id": item.id,
            "title": item.title,
            "message": item.message,
            "is_read": item.is_read,
            "created_at": item.created_at.isoformat(),
        }
        for item in result.scalars().all()
    ]
