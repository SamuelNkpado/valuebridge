from pydantic import BaseModel
from enum import Enum
from typing import Optional, List
from datetime import datetime


class ListingVisibility(str, Enum):
    public = "public"
    private = "private"
    invite_only = "invite_only"


class ListingStatus(str, Enum):
    active = "active"
    closed = "closed"
    pending = "pending"


class OfferStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    withdrawn = "withdrawn"


class DealType(str, Enum):
    full_acquisition = "full_acquisition"
    partial_investment = "partial_investment"
    partnership = "partnership"


class ListingCreate(BaseModel):
    business_id: int
    asking_price: float
    deal_type: DealType
    visibility: Optional[ListingVisibility] = ListingVisibility.public
    description: Optional[str] = None


class ListingUpdate(BaseModel):
    asking_price: Optional[float] = None
    deal_type: Optional[DealType] = None
    visibility: Optional[ListingVisibility] = None
    status: Optional[ListingStatus] = None
    description: Optional[str] = None


class ListingResponse(BaseModel):
    id: int
    business_id: int
    owner_id: int
    asking_price: float
    deal_type: DealType
    visibility: ListingVisibility
    status: ListingStatus
    description: Optional[str]
    created_at: datetime

    business_name: Optional[str] = None
    business_industry: Optional[str] = None
    business_location: Optional[str] = None
    business_revenue: Optional[float] = None
    business_employees: Optional[int] = None
    business_founded: Optional[int] = None
    seller_initials: Optional[str] = None
    seller_verified: Optional[bool] = None

    class Config:
        from_attributes = True


class OfferCreate(BaseModel):
    listing_id: int
    amount: float
    message: Optional[str] = None


class OfferUpdate(BaseModel):
    status: OfferStatus


class OfferResponse(BaseModel):
    id: int
    listing_id: int
    investor_id: int
    amount: float
    message: Optional[str]
    status: OfferStatus
    created_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    receiver_id: int
    listing_id: Optional[int] = None
    content: str


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    listing_id: Optional[int]
    content: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
