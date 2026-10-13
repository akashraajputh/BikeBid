from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, get_db
from app.core.dependencies import get_current_user, require_admin
from app.core.rate_limit import rate_limit
from app.core.security import decode_access_token
from app.models import AuditLog, Auction, AuctionStatus, Bid, Motorcycle, Notification, User, UserRole
from app.schemas.auction import AuctionCreate, AuctionUpdate, BidCreate
from app.services.auction_queries import auction_detail_statement
from app.services.lifecycle import as_utc
from app.services.realtime import auction_connections
from app.services.serializers import auction_response

router = APIRouter(prefix="/auctions", tags=["auctions"])
websocket_router = APIRouter(tags=["auction realtime"])


@router.get("/live")
async def list_live_auctions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        auction_detail_statement()
        .where(Auction.status == AuctionStatus.live.value)
        .order_by(Auction.end_time.asc())
    )
    return [auction_response(item) for item in result.scalars().unique().all()]


@router.get("/upcoming")
async def list_upcoming_auctions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        auction_detail_statement()
        .where(Auction.status == AuctionStatus.scheduled.value)
        .order_by(Auction.start_time.asc())
    )
    return [auction_response(item) for item in result.scalars().unique().all()]


@router.get("")
async def list_auctions(
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    statement = auction_detail_statement()
    if status_filter:
        statement = statement.where(Auction.status == status_filter)
    result = await db.execute(statement.order_by(Auction.start_time.asc()))
    return [auction_response(auction) for auction in result.scalars().unique().all()]


@router.get("/{auction_id}")
async def get_auction(auction_id: int, db: AsyncSession = Depends(get_db)):
    auction = await db.scalar(
        auction_detail_statement().where(Auction.id == auction_id)
    )
    if auction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auction not found")
    return auction_response(auction)


@router.get("/{auction_id}/bids")
async def list_auction_bids(auction_id: int, db: AsyncSession = Depends(get_db)):
    auction = await db.scalar(auction_detail_statement().where(Auction.id == auction_id))
    if auction is None:
        raise HTTPException(status_code=404, detail="Auction not found")
    return auction_response(auction)["bids"]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_auction(
    payload: AuctionCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    motorcycle = await db.get(Motorcycle, payload.motorcycle_id)
    if motorcycle is None:
        raise HTTPException(status_code=404, detail="Motorcycle not found")
    existing = await db.scalar(
        select(Auction.id).where(Auction.motorcycle_id == payload.motorcycle_id)
    )
    if existing is not None:
        raise HTTPException(status_code=400, detail="This motorcycle already has an auction")

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
    await db.commit()
    return await _get_auction_response(db, auction.id)


@router.post("/{auction_id}/publish")
async def publish_auction(
    auction_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    auction = await db.get(Auction, auction_id, with_for_update=True)
    if auction is None:
        raise HTTPException(status_code=404, detail="Auction not found")
    if auction.status != AuctionStatus.draft.value:
        raise HTTPException(status_code=400, detail="Only draft auctions can be published")
    now = datetime.now(timezone.utc)
    if as_utc(auction.end_time) <= now:
        raise HTTPException(status_code=400, detail="Auction end time must be in the future")
    auction.status = AuctionStatus.scheduled.value if as_utc(auction.start_time) > now else AuctionStatus.live.value
    await db.commit()
    return await _get_auction_response(db, auction_id)


@router.post("/{auction_id}/cancel")
async def cancel_auction(
    auction_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    auction = await db.get(Auction, auction_id, with_for_update=True)
    if auction is None:
        raise HTTPException(status_code=404, detail="Auction not found")
    if auction.status not in {AuctionStatus.draft.value, AuctionStatus.scheduled.value}:
        raise HTTPException(status_code=400, detail="Only draft or scheduled auctions can be cancelled")
    auction.status = AuctionStatus.cancelled.value
    await db.commit()
    return await _get_auction_response(db, auction_id)


@router.patch("/{auction_id}")
async def update_auction(
    auction_id: int,
    payload: AuctionUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    auction = await db.get(Auction, auction_id, with_for_update=True)
    if auction is None:
        raise HTTPException(status_code=404, detail="Auction not found")
    if auction.status not in {AuctionStatus.draft.value, AuctionStatus.scheduled.value}:
        raise HTTPException(status_code=400, detail="Only draft or scheduled auctions can be edited")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(auction, field, value)
    if auction.end_time <= auction.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="auction.updated",
            details=f"auction_id={auction.id}",
        )
    )
    await db.commit()
    return await _get_auction_response(db, auction_id)


@router.post("/{auction_id}/bid")
@router.post("/{auction_id}/bids")
async def place_bid(
    auction_id: int,
    payload: BidCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit(limit=20, window_seconds=60)),
):
    if current_user.role != UserRole.buyer.value:
        raise HTTPException(status_code=403, detail="Only buyers may place bids")

    statement = auction_detail_statement().where(Auction.id == auction_id).with_for_update()
    auction = await db.scalar(statement)
    if auction is None:
        raise HTTPException(status_code=404, detail="Auction not found")

    now = datetime.now(timezone.utc)
    starts_at = auction.start_time
    ends_at = auction.end_time
    if starts_at.tzinfo is None:
        starts_at = starts_at.replace(tzinfo=timezone.utc)
    if ends_at.tzinfo is None:
        ends_at = ends_at.replace(tzinfo=timezone.utc)
    if auction.status != AuctionStatus.live.value or not starts_at <= now < ends_at:
        raise HTTPException(status_code=400, detail="Auction is not currently open for bidding")

    previous_bid = await db.scalar(
        select(Bid)
        .where(Bid.auction_id == auction_id)
        .order_by(Bid.amount.desc(), Bid.created_at.desc())
        .limit(1)
    )
    minimum_bid = (
        auction.current_price + auction.minimum_increment
        if auction.current_price > 0
        else auction.motorcycle.start_price
    )
    if payload.amount < minimum_bid:
        raise HTTPException(status_code=400, detail=f"Bid must be at least {minimum_bid}")

    bid = Bid(auction_id=auction.id, user_id=current_user.id, amount=payload.amount)
    auction.current_price = payload.amount
    auction.winner_id = current_user.id
    auction.reserve_met = (
        auction.motorcycle.reserve_price is None
        or payload.amount >= auction.motorcycle.reserve_price
    )
    db.add(bid)
    if previous_bid is not None and previous_bid.user_id != current_user.id:
        db.add(
            Notification(
                user_id=previous_bid.user_id,
                title="You have been outbid",
                message=f"A higher bid was placed on {auction.motorcycle.title}.",
            )
        )
    await db.commit()
    response = await _get_auction_response(db, auction_id)
    await auction_connections.broadcast(
        auction_id,
        {"event": "bid", "data": response},
    )
    return response


async def _get_auction_response(db: AsyncSession, auction_id: int) -> dict:
    auction = await db.scalar(auction_detail_statement().where(Auction.id == auction_id))
    if auction is None:
        raise HTTPException(status_code=404, detail="Auction not found")
    return auction_response(auction)


@websocket_router.websocket("/ws/auction/{auction_id}")
async def auction_websocket(websocket: WebSocket, auction_id: int, token: str):
    try:
        claims = decode_access_token(token)
    except JWTError:
        await websocket.close(code=1008, reason="Authentication required")
        return
    if not claims.get("sub"):
        await websocket.close(code=1008, reason="Invalid token")
        return

    async with AsyncSessionLocal() as db:
        email = claims.get("sub")
        user = await db.scalar(select(User).where(User.email == email))
        if (
            user is None
            or not user.is_active
            or claims.get("ver", 0) != user.token_version
        ):
            await websocket.close(code=1008, reason="Session is no longer valid")
            return
        auction = await db.scalar(auction_detail_statement().where(Auction.id == auction_id))
        if auction is None:
            await websocket.close(code=1008, reason="Auction not found")
            return
        initial_state = auction_response(auction)

    await auction_connections.connect(auction_id, websocket)
    try:
        await websocket.send_json({"event": "state", "data": initial_state})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        auction_connections.disconnect(auction_id, websocket)
