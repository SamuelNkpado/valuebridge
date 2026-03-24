from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    Enum,
    Boolean,
    Text,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ListingVisibility(str, enum.Enum):
    public = "public"
    private = "private"
    invite_only = "invite_only"


class ListingStatus(str, enum.Enum):
    active = "active"
    closed = "closed"
    pending = "pending"


class OfferStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    withdrawn = "withdrawn"


class DealType(str, enum.Enum):
    full_acquisition = "full_acquisition"
    partial_investment = "partial_investment"
    partnership = "partnership"


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    asking_price = Column(Float, nullable=False)
    deal_type = Column(Enum(DealType), nullable=False)
    visibility = Column(Enum(ListingVisibility), default=ListingVisibility.public)
    status = Column(Enum(ListingStatus), default=ListingStatus.active)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    business = relationship("Business", backref="listings")
    owner = relationship("User", backref="listings")
    offers = relationship("Offer", backref="listing")


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    investor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    message = Column(Text, nullable=True)
    status = Column(Enum(OfferStatus), default=OfferStatus.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    investor = relationship("User", backref="offers")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=True)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sender = relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    receiver = relationship(
        "User", foreign_keys=[receiver_id], backref="received_messages"
    )
