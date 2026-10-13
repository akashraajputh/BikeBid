from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class AuctionCreate(BaseModel):
    motorcycle_id: int
    start_time: datetime
    end_time: datetime
    minimum_increment: Decimal = Field(default=Decimal("50.00"), gt=0, max_digits=12, decimal_places=2)

    @field_validator("start_time", "end_time")
    @classmethod
    def normalize_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class AuctionUpdate(BaseModel):
    start_time: datetime | None = None
    end_time: datetime | None = None
    minimum_increment: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)

    @field_validator("start_time", "end_time")
    @classmethod
    def normalize_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class BidCreate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
