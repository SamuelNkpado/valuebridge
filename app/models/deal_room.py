from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Boolean, Text, JSON, Float
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
    terminated    = "terminated"

class DealRoom(Base):
    __tablename__ = "deal_rooms"

    id            = Column(Integer, primary_key=True, index=True)
    offer_id      = Column(Integer, ForeignKey("offers.id"), nullable=False, unique=True)
    listing_id    = Column(Integer, ForeignKey("listings.id"), nullable=False)
    seller_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    investor_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    advisor_id    = Column(Integer, ForeignKey("users.id"), nullable=True)
    stage         = Column(Enum(DealStage), default=DealStage.interested)

    # NDA
    nda_acknowledged_seller   = Column(Boolean, default=False)
    nda_acknowledged_investor = Column(Boolean, default=False)

    # Close confirmation — both must confirm
    close_confirmed_seller   = Column(Boolean, default=False)
    close_confirmed_investor = Column(Boolean, default=False)

    # Term sheet
    term_sheet_amount       = Column(Float,   nullable=True)
    term_sheet_stake        = Column(Float,   nullable=True)
    term_sheet_payment_terms = Column(String, nullable=True)
    term_sheet_conditions   = Column(Text,    nullable=True)
    term_sheet_proposed_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    term_sheet_seller_approved   = Column(Boolean, nullable=True)
    term_sheet_investor_approved = Column(Boolean, nullable=True)

    # Close
    closed_amount = Column(Float,  nullable=True)
    notes         = Column(Text,   nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    offer    = relationship("Offer",   backref="deal_room")
    listing  = relationship("Listing", backref="deal_rooms")
    advisor  = relationship("User", foreign_keys=[advisor_id], backref="advised_deals")

class DealDocument(Base):
    __tablename__ = "deal_documents"

    id           = Column(Integer, primary_key=True, index=True)
    deal_room_id = Column(Integer, ForeignKey("deal_rooms.id"), nullable=False)
    uploaded_by  = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename     = Column(String,  nullable=False)
    file_type    = Column(String,  nullable=True)
    description  = Column(String,  nullable=True)
    # Dual acknowledgement
    seller_confirmed   = Column(Boolean, default=False)
    investor_confirmed = Column(Boolean, default=False)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    deal_room = relationship("DealRoom", backref="documents")

class DealChecklistItem(Base):
    __tablename__ = "deal_checklist"

    id           = Column(Integer, primary_key=True, index=True)
    deal_room_id = Column(Integer, ForeignKey("deal_rooms.id"), nullable=False)
    item         = Column(String,  nullable=False)
    completed    = Column(Boolean, default=False)
    completed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    completed_by_role = Column(String, nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    deal_room = relationship("DealRoom", backref="checklist")