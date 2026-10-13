from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models import (
    AuditLog,
    Auction,
    AuctionStatus,
    Bid,
    Motorcycle,
    User,
)
from app.schemas.admin import UserStatusUpdate
from app.schemas.auction import AuctionCreate, AuctionUpdate
from app.schemas.motorcycle import MotorcycleCreate, MotorcycleUpdate
from app.services.auction_queries import auction_detail_statement
from app.services.lifecycle import as_utc
from app.services.serializers import auction_response, motorcycle_response

router = APIRouter(prefix="/admin", tags=["administrator"])


def _audit(user_id: int, action: str, details: str) -> AuditLog:
    return AuditLog(user_id=user_id, action=action, details=details)


@router.post("/motorcycles", status_code=status.HTTP_201_CREATED)
async def create_motorcycle(
    payload: MotorcycleCreate,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if payload.reserve_price is not None and payload.reserve_price < payload.start_price:
        raise HTTPException(status_code=400, detail="Reserve price cannot be below starting price")
    motorcycle = Motorcycle(
        **payload.model_dump(exclude={"image_urls", "start_price", "reserve_price"}),
        start_price=Decimal(payload.start_price),
        reserve_price=Decimal(payload.reserve_price) if payload.reserve_price is not None else None,
        image_urls=[str(url) for url in payload.image_urls],
        seller_id=current_admin.id,
    )
    db.add(motorcycle)
    await db.flush()
    db.add(_audit(current_admin.id, "motorcycle.created", f"motorcycle_id={motorcycle.id}"))
    await db.commit()
    result = await db.execute(
        select(Motorcycle)
        .options(selectinload(Motorcycle.seller))
        .where(Motorcycle.id == motorcycle.id)
    )
    return motorcycle_response(result.scalar_one())


@router.get("/motorcycles")
async def list_motorcycles(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(
        select(Motorcycle)
        .options(selectinload(Motorcycle.seller))
        .order_by(Motorcycle.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return [motorcycle_response(item) for item in result.scalars().all()]


@router.get("/motorcycles/{motorcycle_id}")
async def get_motorcycle(
    motorcycle_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(
        select(Motorcycle)
        .options(selectinload(Motorcycle.seller))
        .where(Motorcycle.id == motorcycle_id)
    )
    motorcycle = result.scalar_one_or_none()
    if motorcycle is None:
        raise HTTPException(status_code=404, detail="Motorcycle not found")
    return motorcycle_response(motorcycle)


@router.patch("/motorcycles/{motorcycle_id}")
async def update_motorcycle(
    motorcycle_id: int,
    payload: MotorcycleUpdate,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    motorcycle = await db.get(Motorcycle, motorcycle_id, with_for_update=True)
    if motorcycle is None:
        raise HTTPException(status_code=404, detail="Motorcycle not found")

    auction = await db.scalar(select(Auction).where(Auction.motorcycle_id == motorcycle_id))
    changes = payload.model_dump(exclude_unset=True)
    if auction is not None:
        price_changed = (
            changes.get("start_price", motorcycle.start_price) != motorcycle.start_price
            or changes.get("reserve_price", motorcycle.reserve_price) != motorcycle.reserve_price
        )
        if auction.status not in {AuctionStatus.draft.value} and {
            "start_price",
            "reserve_price",
        }.intersection(changes) and price_changed:
            raise HTTPException(status_code=400, detail="Prices can only be changed before an auction is scheduled")
        if auction.status in {
            AuctionStatus.live.value,
            AuctionStatus.ended.value,
            AuctionStatus.cancelled.value,
        }:
            raise HTTPException(status_code=400, detail="Motorcycle details cannot be edited after the auction starts")

    new_start_price = changes.get("start_price", motorcycle.start_price)
    new_reserve_price = changes.get("reserve_price", motorcycle.reserve_price)
    if new_reserve_price is not None and new_reserve_price < new_start_price:
        raise HTTPException(status_code=400, detail="Reserve price cannot be below starting price")
    image_urls = changes.pop("image_urls", None)
    for field, value in changes.items():
        setattr(motorcycle, field, value)
    if image_urls is not None:
        motorcycle.image_urls = [str(url) for url in image_urls]
    db.add(_audit(current_admin.id, "motorcycle.updated", f"motorcycle_id={motorcycle.id}"))
    await db.commit()
    result = await db.execute(
        select(Motorcycle)
        .options(selectinload(Motorcycle.seller))
        .where(Motorcycle.id == motorcycle_id)
    )
    return motorcycle_response(result.scalar_one())


@router.delete("/motorcycles/{motorcycle_id}")
async def delete_motorcycle(
    motorcycle_id: int,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    motorcycle = await db.get(Motorcycle, motorcycle_id, with_for_update=True)
    if motorcycle is None:
        raise HTTPException(status_code=404, detail="Motorcycle not found")
    has_auction = await db.scalar(select(Auction.id).where(Auction.motorcycle_id == motorcycle_id))
    if has_auction is not None:
        raise HTTPException(status_code=409, detail="Motorcycle has auction history; archive it instead")
    motorcycle.status = "ARCHIVED"
    db.add(_audit(current_admin.id, "motorcycle.archived", f"motorcycle_id={motorcycle.id}"))
    await db.commit()
    return {"message": "Motorcycle archived"}


@router.post("/auctions", status_code=status.HTTP_201_CREATED)
async def create_auction(
    payload: AuctionCreate,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    motorcycle = await db.get(Motorcycle, payload.motorcycle_id)
    if motorcycle is None or motorcycle.status != "ACTIVE":
        raise HTTPException(status_code=404, detail="Active motorcycle not found")
    exists = await db.scalar(select(Auction.id).where(Auction.motorcycle_id == motorcycle.id))
    if exists is not None:
        raise HTTPException(status_code=409, detail="This motorcycle already has an auction")
    auction = Auction(
        motorcycle_id=motorcycle.id,
        status=AuctionStatus.draft.value,
        start_time=payload.start_time,
        end_time=payload.end_time,
        current_price=Decimal("0.00"),
        minimum_increment=payload.minimum_increment,
        reserve_met=False,
    )
    db.add(auction)
    await db.flush()
    db.add(_audit(current_admin.id, "auction.created", f"auction_id={auction.id}"))
    await db.commit()
    return await _auction_payload(db, auction.id)


@router.get("/auctions")
async def list_admin_auctions(
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    statement = auction_detail_statement()
    if status_filter:
        statement = statement.where(Auction.status == status_filter)
    result = await db.execute(statement.order_by(Auction.created_at.desc()))
    return [auction_response(item) for item in result.scalars().unique().all()]


@router.get("/auctions/{auction_id}")
async def get_admin_auction(
    auction_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await _auction_payload(db, auction_id)


@router.patch("/auctions/{auction_id}")
async def update_admin_auction(
    auction_id: int,
    payload: AuctionUpdate,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    auction = await db.get(Auction, auction_id, with_for_update=True)
    if auction is None:
        raise HTTPException(status_code=404, detail="Auction not found")
    if auction.status not in {AuctionStatus.draft.value, AuctionStatus.scheduled.value}:
        raise HTTPException(status_code=400, detail="Only draft or scheduled auctions can be edited")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(auction, field, value)
    if as_utc(auction.end_time) <= as_utc(auction.start_time):
        raise HTTPException(status_code=400, detail="End time must be after start time")
    db.add(_audit(current_admin.id, "auction.updated", f"auction_id={auction.id}"))
    await db.commit()
    return await _auction_payload(db, auction_id)


@router.get("/auctions/{auction_id}/bids")
async def get_admin_auction_bids(
    auction_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    if await db.get(Auction, auction_id) is None:
        raise HTTPException(status_code=404, detail="Auction not found")
    result = await db.execute(
        select(Bid, User)
        .join(User, User.id == Bid.user_id)
        .where(Bid.auction_id == auction_id)
        .order_by(Bid.created_at.desc())
    )
    return [
        {
            "id": bid.id,
            "user_id": user.id,
            "user_name": user.full_name,
            "user_email": user.email,
            "amount": float(bid.amount),
            "created_at": bid.created_at.isoformat(),
        }
        for bid, user in result.all()
    ]


@router.post("/auctions/{auction_id}/schedule")
async def schedule_auction(
    auction_id: int,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    auction = await db.get(Auction, auction_id, with_for_update=True)
    if auction is None:
        raise HTTPException(status_code=404, detail="Auction not found")
    if auction.status != AuctionStatus.draft.value:
        raise HTTPException(status_code=400, detail="Only draft auctions can be scheduled")
    now = datetime.now(timezone.utc)
    if as_utc(auction.end_time) <= now:
        raise HTTPException(status_code=400, detail="Auction end time must be in the future")
    auction.status = AuctionStatus.scheduled.value
    db.add(_audit(current_admin.id, "auction.scheduled", f"auction_id={auction.id}"))
    await db.commit()
    return await _auction_payload(db, auction_id)


@router.post("/auctions/{auction_id}/cancel")
async def cancel_admin_auction(
    auction_id: int,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    auction = await db.get(Auction, auction_id, with_for_update=True)
    if auction is None:
        raise HTTPException(status_code=404, detail="Auction not found")
    if auction.status not in {AuctionStatus.draft.value, AuctionStatus.scheduled.value}:
        raise HTTPException(status_code=400, detail="Only draft or scheduled auctions can be cancelled")
    auction.status = AuctionStatus.cancelled.value
    db.add(_audit(current_admin.id, "auction.cancelled", f"auction_id={auction.id}"))
    await db.commit()
    return await _auction_payload(db, auction_id)


@router.get("/users")
async def list_users(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    users = await db.scalars(select(User).order_by(User.created_at.desc()).offset(offset).limit(limit))
    output = []
    for user in users.all():
        bid_count = await db.scalar(select(func.count()).select_from(Bid).where(Bid.user_id == user.id))
        output.append(
            {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "bid_count": bid_count,
            }
        )
    return output


@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    bid_count = await db.scalar(select(func.count()).select_from(Bid).where(Bid.user_id == user.id))
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
        "bid_count": bid_count,
    }


@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id, with_for_update=True)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_admin.id and not payload.is_active:
        raise HTTPException(status_code=400, detail="Administrators cannot suspend their own account")
    user.is_active = payload.is_active
    if not payload.is_active:
        user.token_version += 1
    db.add(
        _audit(
            current_admin.id,
            "user.activated" if payload.is_active else "user.suspended",
            f"user_id={user.id}",
        )
    )
    await db.commit()
    return {"id": user.id, "is_active": user.is_active}


@router.get("/analytics")
async def admin_analytics(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return {
        "total_motorcycles": await db.scalar(select(func.count()).select_from(Motorcycle)),
        "total_users": await db.scalar(select(func.count()).select_from(User)),
        "total_bids": await db.scalar(select(func.count()).select_from(Bid)),
        "draft_auctions": await _count_auctions(db, AuctionStatus.draft.value),
        "upcoming_auctions": await _count_auctions(db, AuctionStatus.scheduled.value),
        "live_auctions": await _count_auctions(db, AuctionStatus.live.value),
        "completed_auctions": await _count_auctions(db, AuctionStatus.ended.value),
        "cancelled_auctions": await _count_auctions(db, AuctionStatus.cancelled.value),
        "recent_activity": await _recent_activity(db),
    }


async def _count_auctions(db: AsyncSession, auction_status: str) -> int:
    return await db.scalar(
        select(func.count()).select_from(Auction).where(Auction.status == auction_status)
    ) or 0


async def _recent_activity(db: AsyncSession) -> list[dict]:
    logs = await db.scalars(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(20)
    )
    return [
        {
            "action": log.action,
            "details": log.details,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs.all()
    ]


async def _auction_payload(db: AsyncSession, auction_id: int) -> dict:
    auction = await db.scalar(auction_detail_statement().where(Auction.id == auction_id))
    if auction is None:
        raise HTTPException(status_code=404, detail="Auction not found")
    return auction_response(auction)
