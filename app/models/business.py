from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class BusinessStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    for_sale = "for_sale"
    acquired = "acquired"


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Basic Info from FR2.1
    name = Column(String, nullable=False)
    industry = Column(String, nullable=False)
    location = Column(String, nullable=False)
    legal_structure = Column(String, nullable=True)
    founding_year = Column(Integer, nullable=True)
    employee_count = Column(Integer, nullable=True)
    description = Column(String, nullable=True)

    # Financial Info for Valuation
    annual_revenue = Column(Float, nullable=True)
    profit = Column(Float, nullable=True)
    total_assets = Column(Float, nullable=True)
    total_liabilities = Column(Float, nullable=True)

    status = Column(Enum(BusinessStatus), default=BusinessStatus.active)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", backref="businesses")
