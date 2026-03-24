from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Boolean, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class DealStage(str, enum.Enum):
    interested    = "interested"
    nda_sent      = "nda_sent"
    nda_signed    = "nda_signed"
    due_diligence = "due_diligence"
    term_sheet    = "term_sheet"
    closed        = "closed"

class DealRoom(Base):
    __tablename__ = "deal_rooms"

    id            = Column(Integer, primary_key=True, index=True)
    offer_id      = Column(Integer, ForeignKey("offers.id"), nullable=False, unique=True)
    listing_id    = Column(Integer, ForeignKey("listings.id"), nullable=False)
    seller_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    investor_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    stage         = Column(Enum(DealStage), default=DealStage.interested)
    nda_acknowledged_seller   = Column(Boolean, default=False)
    nda_acknowledged_investor = Column(Boolean, default=False)
    notes         = Column(Text, nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    offer    = relationship("Offer",   backref="deal_room")
    listing  = relationship("Listing", backref="deal_rooms")

class DealDocument(Base):
    __tablename__ = "deal_documents"

    id          = Column(Integer, primary_key=True, index=True)
    deal_room_id = Column(Integer, ForeignKey("deal_rooms.id"), nullable=False)
    uploaded_by  = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename     = Column(String, nullable=False)
    file_type    = Column(String, nullable=True)
    description  = Column(String, nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    deal_room = relationship("DealRoom", backref="documents")

class DealChecklistItem(Base):
    __tablename__ = "deal_checklist"

    id           = Column(Integer, primary_key=True, index=True)
    deal_room_id = Column(Integer, ForeignKey("deal_rooms.id"), nullable=False)
    item         = Column(String, nullable=False)
    completed    = Column(Boolean, default=False)
    completed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    deal_room = relationship("DealRoom", backref="checklist")