from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ValuationMethod(str, enum.Enum):
    asset_based = "asset_based"
    income_based = "income_based"
    market_multiples = "market_multiples"
    combined = "combined"


class ValuationReport(Base):
    __tablename__ = "valuation_reports"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    method = Column(Enum(ValuationMethod), nullable=False)
    estimated_value = Column(Float, nullable=False)
    asset_based_value = Column(Float, nullable=True)
    income_based_value = Column(Float, nullable=True)
    market_multiples_value = Column(Float, nullable=True)
    assumptions = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    business = relationship("Business", backref="valuations")
