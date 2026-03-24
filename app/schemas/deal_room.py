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

class DealRoomResponse(BaseModel):
    id:          int
    offer_id:    int
    listing_id:  int
    seller_id:   int
    investor_id: int
    stage:       DealStage
    nda_acknowledged_seller:   bool
    nda_acknowledged_investor: bool
    notes:       Optional[str]
    created_at:  datetime

    class Config:
        from_attributes = True

class DealStageUpdate(BaseModel):
    stage: DealStage

class DealDocumentCreate(BaseModel):
    description: Optional[str] = None

class DealDocumentResponse(BaseModel):
    id:          int
    deal_room_id: int
    uploaded_by: int
    filename:    str
    file_type:   Optional[str]
    description: Optional[str]
    created_at:  datetime

    class Config:
        from_attributes = True

class ChecklistItemCreate(BaseModel):
    item: str

class ChecklistItemResponse(BaseModel):
    id:           int
    deal_room_id: int
    item:         str
    completed:    bool
    completed_by: Optional[int]
    created_at:   datetime

    class Config:
        from_attributes = True

class DealRoomFull(BaseModel):
    deal_room: DealRoomResponse
    documents: List[DealDocumentResponse]
    checklist: List[ChecklistItemResponse]

    class Config:
        from_attributes = True