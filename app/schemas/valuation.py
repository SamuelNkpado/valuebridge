from pydantic import BaseModel
from enum import Enum
from typing import Optional
from datetime import datetime


class ValuationMethod(str, Enum):
    asset_based = "asset_based"
    income_based = "income_based"
    market_multiples = "market_multiples"
    combined = "combined"


class ValuationRequest(BaseModel):
    business_id: int
    method: ValuationMethod
    growth_rate: Optional[float] = 0.10


class ValuationResponse(BaseModel):
    id: int
    business_id: int
    method: ValuationMethod
    estimated_value: float
    asset_based_value: Optional[float]
    income_based_value: Optional[float]
    market_multiples_value: Optional[float]
    assumptions: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True
