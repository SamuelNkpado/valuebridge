from pydantic import BaseModel
from enum import Enum
from typing import Optional, List
from datetime import datetime

class DealStage(str, Enum):
    interested    = "interested"
    nda_sent      = "nda_sent"
    nda_signed    = "nda_signed"
    due_diligence = "due_diligence"
    term_sheet    = "term_sheet"
    closed        = "closed"
    terminated    = "terminated"

class DealRoomResponse(BaseModel):
    id:          int
    offer_id:    int
    listing_id:  int
    seller_id:   int
    investor_id: int
    advisor_id:  Optional[int]
    stage:       DealStage
    nda_acknowledged_seller:   bool
    nda_acknowledged_investor: bool
    close_confirmed_seller:    bool
    close_confirmed_investor:  bool
    term_sheet_amount:          Optional[float]
    term_sheet_stake:           Optional[float]
    term_sheet_payment_terms:   Optional[str]
    term_sheet_conditions:      Optional[str]
    term_sheet_proposed_by:     Optional[int]
    term_sheet_seller_approved:   Optional[bool]
    term_sheet_investor_approved: Optional[bool]
    closed_amount: Optional[float]
    notes:        Optional[str]
    created_at:   datetime
    # Enriched
    business_name:     Optional[str] = None
    business_industry: Optional[str] = None
    business_location: Optional[str] = None
    business_revenue:  Optional[float] = None
    business_employees: Optional[int] = None
    business_founded:  Optional[int] = None
    business_assets:   Optional[float] = None
    business_liabilities: Optional[float] = None
    business_description: Optional[str] = None
    seller_name:   Optional[str] = None
    investor_name: Optional[str] = None
    advisor_name:  Optional[str] = None

    class Config:
        from_attributes = True

class DealStageUpdate(BaseModel):
    stage:         DealStage
    closed_amount: Optional[float] = None

class DealDocumentCreate(BaseModel):
    description: Optional[str] = None

class DealDocumentResponse(BaseModel):
    id:           int
    deal_room_id: int
    uploaded_by:  int
    filename:     str
    file_type:    Optional[str]
    description:  Optional[str]
    seller_confirmed:   bool
    investor_confirmed: bool
    created_at:   datetime

    class Config:
        from_attributes = True

class ChecklistItemCreate(BaseModel):
    item: str

class ChecklistItemResponse(BaseModel):
    id:               int
    deal_room_id:     int
    item:             str
    completed:        bool
    completed_by:     Optional[int]
    completed_by_role: Optional[str]
    created_at:       datetime

    class Config:
        from_attributes = True

class DealRoomFull(BaseModel):
    deal_room: DealRoomResponse
    documents: List[DealDocumentResponse]
    checklist: List[ChecklistItemResponse]

    class Config:
        from_attributes = True

class TermSheetData(BaseModel):
    amount:        float
    stake:         float
    payment_terms: str
    conditions:    Optional[str] = None

class TermSheetApproval(BaseModel):
    approved: bool