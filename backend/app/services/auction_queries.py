from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from app.models import Auction, Bid, Motorcycle


def auction_detail_statement() -> Select:
    return select(Auction).options(
        selectinload(Auction.motorcycle).selectinload(Motorcycle.seller),
        selectinload(Auction.bids).selectinload(Bid.user),
        selectinload(Auction.winner),
    ).execution_options(populate_existing=True)
