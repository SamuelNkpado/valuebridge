from pydantic import BaseModel
from enum import Enum
from typing import Optional


class BusinessStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    for_sale = "for_sale"
    acquired = "acquired"


# What we expect when creating a business
class BusinessCreate(BaseModel):
    name: str
    industry: str
    location: str
    legal_structure: Optional[str] = None
    founding_year: Optional[int] = None
    employee_count: Optional[int] = None
    description: Optional[str] = None
    annual_revenue: Optional[float] = None
    profit: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None


# What we expect when updating a business
class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    legal_structure: Optional[str] = None
    founding_year: Optional[int] = None
    employee_count: Optional[int] = None
    description: Optional[str] = None
    annual_revenue: Optional[float] = None
    profit: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    status: Optional[BusinessStatus] = None


# What we send back
class BusinessResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    industry: str
    location: str
    legal_structure: Optional[str]
    founding_year: Optional[int]
    employee_count: Optional[int]
    description: Optional[str]
    annual_revenue: Optional[float]
    profit: Optional[float]
    total_assets: Optional[float]
    total_liabilities: Optional[float]
    status: BusinessStatus

    class Config:
        from_attributes = True
