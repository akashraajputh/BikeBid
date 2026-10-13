from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl


class MotorcycleCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str
    manufacturer: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=80)
    year: int = Field(ge=1885)
    mileage: int = Field(ge=0)
    engine_cc: int = Field(gt=0)
    fuel_type: str
    condition: str
    location: str
    start_price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    reserve_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    image_urls: list[HttpUrl] = Field(default_factory=list)
    status: str = "ACTIVE"


class MotorcyclePublic(BaseModel):
    id: int
    title: str
    description: str
    manufacturer: str
    model: str
    year: int
    mileage: int
    engine_cc: int
    fuel_type: str
    condition: str
    location: str
    start_price: Decimal
    reserve_price: Decimal | None
    image_urls: list[str]
    status: str
    seller_id: int
    seller_name: str | None
    created_at: str


class MotorcycleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    manufacturer: str | None = Field(default=None, min_length=1, max_length=80)
    model: str | None = Field(default=None, min_length=1, max_length=80)
    year: int | None = Field(default=None, ge=1885)
    mileage: int | None = Field(default=None, ge=0)
    engine_cc: int | None = Field(default=None, gt=0)
    fuel_type: str | None = None
    condition: str | None = None
    location: str | None = None
    start_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    reserve_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    image_urls: list[HttpUrl] | None = None
