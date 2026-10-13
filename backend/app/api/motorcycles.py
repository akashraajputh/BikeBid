from decimal import Decimal

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models import Motorcycle, User
from app.schemas.motorcycle import MotorcycleCreate
from app.services.serializers import motorcycle_response

router = APIRouter(prefix="/motorcycles", tags=["motorcycles"])


@router.get("")
async def list_motorcycles(
    query: str | None = Query(default=None, max_length=100),
    status_filter: str | None = Query(default=None, alias="status"),
    year_min: int | None = Query(default=None, ge=1885),
    year_max: int | None = Query(default=None, ge=1885),
    price_min: Decimal | None = Query(default=None, ge=0),
    price_max: Decimal | None = Query(default=None, ge=0),
    condition: str | None = Query(default=None, max_length=30),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=24, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    statement = select(Motorcycle).options(selectinload(Motorcycle.seller))
    if query:
        search = f"%{query.strip()}%"
        statement = statement.where(
            or_(
                Motorcycle.title.ilike(search),
                Motorcycle.manufacturer.ilike(search),
                Motorcycle.model.ilike(search),
                Motorcycle.location.ilike(search),
            )
        )
    if status_filter:
        statement = statement.where(Motorcycle.status == status_filter)
    if year_min is not None:
        statement = statement.where(Motorcycle.year >= year_min)
    if year_max is not None:
        statement = statement.where(Motorcycle.year <= year_max)
    if price_min is not None:
        statement = statement.where(Motorcycle.start_price >= price_min)
    if price_max is not None:
        statement = statement.where(Motorcycle.start_price <= price_max)
    if condition:
        statement = statement.where(Motorcycle.condition.ilike(condition))
    result = await db.execute(
        statement.order_by(Motorcycle.created_at.desc()).offset(offset).limit(limit)
    )
    return [motorcycle_response(motorcycle) for motorcycle in result.scalars().all()]


@router.get("/{motorcycle_id}")
async def get_motorcycle(motorcycle_id: int, db: AsyncSession = Depends(get_db)):
    statement = (
        select(Motorcycle)
        .options(selectinload(Motorcycle.seller))
        .where(Motorcycle.id == motorcycle_id)
    )
    motorcycle = await db.scalar(statement)
    if motorcycle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Motorcycle not found")
    return motorcycle_response(motorcycle)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_motorcycle(
    payload: MotorcycleCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if payload.reserve_price is not None and payload.reserve_price < payload.start_price:
        raise HTTPException(status_code=400, detail="Reserve price cannot be below starting price")

    motorcycle = Motorcycle(
        **payload.model_dump(exclude={"image_urls", "start_price", "reserve_price"}),
        start_price=Decimal(payload.start_price),
        reserve_price=Decimal(payload.reserve_price) if payload.reserve_price is not None else None,
        image_urls=[str(url) for url in payload.image_urls],
        seller_id=current_user.id,
    )
    db.add(motorcycle)
    await db.commit()
    result = await db.execute(
        select(Motorcycle)
        .options(selectinload(Motorcycle.seller))
        .where(Motorcycle.id == motorcycle.id)
    )
    return motorcycle_response(result.scalar_one())
