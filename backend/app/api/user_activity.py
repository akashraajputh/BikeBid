from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import Auction, Bid, User
from app.services.auction_queries import auction_detail_statement
from app.services.serializers import auction_response, decimal_to_float

router = APIRouter(prefix="/users/me", tags=["buyer activity"])


@router.get("/bids")
async def my_bids(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Bid, Auction.motorcycle_id)
        .join(Auction, Auction.id == Bid.auction_id)
        .where(Bid.user_id == current_user.id)
        .order_by(Bid.created_at.desc())
    )
    rows = result.all()
    auctions = {}
    if rows:
        auction_result = await db.execute(
            auction_detail_statement().where(Auction.id.in_({bid.auction_id for bid, _ in rows}))
        )
        auctions = {auction.id: auction for auction in auction_result.scalars().unique().all()}
    return [
        {
            "id": bid.id,
            "auction_id": bid.auction_id,
            "auction_title": auctions[bid.auction_id].motorcycle.title,
            "amount": decimal_to_float(bid.amount),
            "created_at": bid.created_at.isoformat(),
            "is_highest_bidder": auctions[bid.auction_id].winner_id == current_user.id,
            "auction_status": auctions[bid.auction_id].status,
        }
        for bid, _ in rows
    ]


@router.get("/auctions")
async def my_auctions(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    auction_ids = select(Bid.auction_id).where(Bid.user_id == current_user.id).distinct()
    result = await db.execute(auction_detail_statement().where(Auction.id.in_(auction_ids)))
    return [auction_response(item) for item in result.scalars().unique().all()]
