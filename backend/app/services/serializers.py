from decimal import Decimal
from typing import Any

from app.models import Auction, Motorcycle


def decimal_to_float(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def motorcycle_response(motorcycle: Motorcycle) -> dict[str, Any]:
    return {
        "id": motorcycle.id,
        "title": motorcycle.title,
        "description": motorcycle.description,
        "manufacturer": motorcycle.manufacturer,
        "model": motorcycle.model,
        "year": motorcycle.year,
        "mileage": motorcycle.mileage,
        "engine_cc": motorcycle.engine_cc,
        "fuel_type": motorcycle.fuel_type,
        "condition": motorcycle.condition,
        "location": motorcycle.location,
        "start_price": decimal_to_float(motorcycle.start_price),
        "reserve_price": decimal_to_float(motorcycle.reserve_price),
        "image_urls": [str(url) for url in (motorcycle.image_urls or [])],
        "status": motorcycle.status,
        "seller_id": motorcycle.seller_id,
        "seller_name": motorcycle.seller.full_name if motorcycle.seller else None,
        "created_at": motorcycle.created_at.isoformat() if motorcycle.created_at else None,
    }


def auction_response(auction: Auction) -> dict[str, Any]:
    bids = sorted(auction.bids, key=lambda bid: bid.created_at, reverse=True)
    return {
        "id": auction.id,
        "motorcycle_id": auction.motorcycle_id,
        "status": auction.status,
        "start_time": auction.start_time.isoformat(),
        "end_time": auction.end_time.isoformat(),
        "current_price": decimal_to_float(auction.current_price),
        "minimum_increment": decimal_to_float(auction.minimum_increment),
        "reserve_met": auction.reserve_met,
        "winner_id": auction.winner_id,
        "winner_name": auction.winner.full_name if auction.winner else None,
        "motorcycle": motorcycle_response(auction.motorcycle),
        "bids": [
            {
                "id": bid.id,
                "user_id": bid.user_id,
                "user_name": bid.user.full_name if bid.user else None,
                "amount": decimal_to_float(bid.amount),
                "created_at": bid.created_at.isoformat(),
            }
            for bid in bids
        ],
    }
