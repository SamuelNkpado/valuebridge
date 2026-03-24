from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.deal_room import DealRoom, DealDocument, DealChecklistItem, DealStage
from app.models.marketplace import Offer, Listing
from app.models.user import User
from app.schemas.deal_room import (
    DealRoomResponse, DealStageUpdate, DealDocumentCreate,
    DealDocumentResponse, ChecklistItemCreate, ChecklistItemResponse,
    DealRoomFull
)
from app.routers.business import get_current_user

router = APIRouter(prefix="/deal-rooms", tags=["Deal Rooms"])

DEFAULT_CHECKLIST = [
    "Seller identity verified (KYC)",
    "Business registration documents reviewed (CAC)",
    "Financial statements reviewed (last 3 years)",
    "NDA signed by both parties",
    "Asset inventory confirmed",
    "Outstanding liabilities disclosed",
    "Key employees / contracts reviewed",
    "Legal ownership structure confirmed",
    "Term sheet agreed by both parties",
    "Final deal closed",
]

# ── Create deal room when offer accepted ──────────────
@router.post("/create/{offer_id}", response_model=DealRoomResponse)
def create_deal_room(
    offer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    listing = db.query(Listing).filter(Listing.id == offer.listing_id).first()
    if listing.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the seller can create a deal room")

    # Check if deal room already exists
    existing = db.query(DealRoom).filter(DealRoom.offer_id == offer_id).first()
    if existing:
        return existing

    # Create deal room
    deal_room = DealRoom(
        offer_id=offer_id,
        listing_id=offer.listing_id,
        seller_id=current_user.id,
        investor_id=offer.investor_id,
        stage=DealStage.interested
    )
    db.add(deal_room)
    db.flush()

    # Auto-create default checklist
    for item_text in DEFAULT_CHECKLIST:
        item = DealChecklistItem(
            deal_room_id=deal_room.id,
            item=item_text
        )
        db.add(item)

    db.commit()
    db.refresh(deal_room)
    return deal_room

# ── Get deal room by offer ID (for investor) ─────────
@router.get("/by-offer/{offer_id}", response_model=DealRoomResponse)
def get_deal_room_by_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deal = db.query(DealRoom).filter(DealRoom.offer_id == offer_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if current_user.id not in [deal.seller_id, deal.investor_id]:
        raise HTTPException(status_code=403, detail="Access denied")
    return deal

# ── Get all my deal rooms ─────────────────────────────
@router.get("/my-deals", response_model=List[DealRoomResponse])
def get_my_deal_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deals = db.query(DealRoom).filter(
        (DealRoom.seller_id == current_user.id) |
        (DealRoom.investor_id == current_user.id)
    ).all()
    return deals

# ── Get single deal room with documents + checklist ───
@router.get("/{deal_room_id}", response_model=DealRoomFull)
def get_deal_room(
    deal_room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deal = db.query(DealRoom).filter(DealRoom.id == deal_room_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if current_user.id not in [deal.seller_id, deal.investor_id]:
        raise HTTPException(status_code=403, detail="Access denied")

    docs = db.query(DealDocument).filter(DealDocument.deal_room_id == deal_room_id).all()
    checklist = db.query(DealChecklistItem).filter(
        DealChecklistItem.deal_room_id == deal_room_id
    ).all()

    return {"deal_room": deal, "documents": docs, "checklist": checklist}

# ── Update deal stage ─────────────────────────────────
@router.put("/{deal_room_id}/stage", response_model=DealRoomResponse)
def update_stage(
    deal_room_id: int,
    data: DealStageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deal = db.query(DealRoom).filter(DealRoom.id == deal_room_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if current_user.id not in [deal.seller_id, deal.investor_id]:
        raise HTTPException(status_code=403, detail="Access denied")

    # ── NDA must be signed by both before progressing past nda_sent ──
    stages_requiring_nda = ["due_diligence", "term_sheet", "closed"]
    if data.stage in stages_requiring_nda:
        if not deal.nda_acknowledged_seller or not deal.nda_acknowledged_investor:
            raise HTTPException(
                status_code=400,
                detail="Both parties must acknowledge the NDA before proceeding"
            )

    deal.stage = data.stage
    if data.closed_amount:
        deal.closed_amount = data.closed_amount

    if data.stage == "closed":
        from app.models.marketplace import Listing
        from app.models.business import Business, BusinessStatus
        listing = db.query(Listing).filter(Listing.id == deal.listing_id).first()
        if listing:
            listing.status = "closed"
            business = db.query(Business).filter(
                Business.id == listing.business_id
            ).first()
            if business:
                business.status = BusinessStatus.acquired

    db.commit()
    db.refresh(deal)
    return deal
# ── Acknowledge NDA ───────────────────────────────────
@router.put("/{deal_room_id}/acknowledge-nda", response_model=DealRoomResponse)
def acknowledge_nda(
    deal_room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deal = db.query(DealRoom).filter(DealRoom.id == deal_room_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal room not found")

    if current_user.id == deal.seller_id:
        deal.nda_acknowledged_seller = True
    elif current_user.id == deal.investor_id:
        deal.nda_acknowledged_investor = True
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    # Auto advance to nda_signed if both acknowledged
    if deal.nda_acknowledged_seller and deal.nda_acknowledged_investor:
        deal.stage = DealStage.nda_signed

    db.commit()
    db.refresh(deal)
    return deal

# ── Upload document ───────────────────────────────────
@router.post("/{deal_room_id}/documents", response_model=DealDocumentResponse)
def upload_document(
    deal_room_id: int,
    data: DealDocumentCreate,
    filename: str,
    file_type: str = "document",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deal = db.query(DealRoom).filter(DealRoom.id == deal_room_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if current_user.id not in [deal.seller_id, deal.investor_id]:
        raise HTTPException(status_code=403, detail="Access denied")

    doc = DealDocument(
        deal_room_id=deal_room_id,
        uploaded_by=current_user.id,
        filename=filename,
        file_type=file_type,
        description=data.description
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

# ── Toggle checklist item ─────────────────────────────
@router.put("/{deal_room_id}/checklist/{item_id}", response_model=ChecklistItemResponse)
def toggle_checklist(
    deal_room_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deal = db.query(DealRoom).filter(DealRoom.id == deal_room_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if current_user.id not in [deal.seller_id, deal.investor_id]:
        raise HTTPException(status_code=403, detail="Access denied")

    item = db.query(DealChecklistItem).filter(
        DealChecklistItem.id == item_id,
        DealChecklistItem.deal_room_id == deal_room_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    item.completed = not item.completed
    item.completed_by = current_user.id if item.completed else None
    db.commit()
    db.refresh(item)
    return item

# ── Add custom checklist item ─────────────────────────
@router.post("/{deal_room_id}/checklist", response_model=ChecklistItemResponse)
def add_checklist_item(
    deal_room_id: int,
    data: ChecklistItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deal = db.query(DealRoom).filter(DealRoom.id == deal_room_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal room not found")

    item = DealChecklistItem(
        deal_room_id=deal_room_id,
        item=data.item
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item