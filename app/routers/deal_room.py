from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from app.database import get_db
from app.models.deal_room import DealRoom, DealDocument, DealChecklistItem, DealStage
from app.models.marketplace import Offer, Listing
from app.models.business import Business, BusinessStatus
from app.models.user import User
from app.schemas.deal_room import (
    DealRoomResponse, DealRoomFull, DealStageUpdate,
    DealDocumentCreate, DealDocumentResponse,
    ChecklistItemCreate, ChecklistItemResponse,
    TermSheetData, TermSheetApproval
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

def enrich_deal_room(deal: DealRoom, db: Session) -> dict:
    data = deal.__dict__.copy()
    data.pop("_sa_instance_state", None)

    # Safe stage string for comparisons
    stage_str = str(deal.stage.value) if hasattr(deal.stage, 'value') else str(deal.stage)
    nda_complete = deal.nda_acknowledged_seller and deal.nda_acknowledged_investor

    listing  = db.query(Listing).filter(Listing.id == deal.listing_id).first()
    business = db.query(Business).filter(
        Business.id == listing.business_id
    ).first() if listing else None

    if business:
        data["business_name"]     = business.name
        data["business_industry"] = business.industry
        if nda_complete:
            data["business_location"]    = business.location
            data["business_revenue"]     = business.annual_revenue
            data["business_employees"]   = business.employee_count
            data["business_founded"]     = business.founding_year
            data["business_assets"]      = business.total_assets
            data["business_liabilities"] = business.total_liabilities
            data["business_description"] = business.description

    seller   = db.query(User).filter(User.id == deal.seller_id).first()
    investor = db.query(User).filter(User.id == deal.investor_id).first()
    advisor  = db.query(User).filter(User.id == deal.advisor_id).first() if deal.advisor_id else None

    data["seller_name"]   = seller.full_name   if seller   else None
    data["investor_name"] = investor.full_name if investor else None
    data["advisor_name"]  = advisor.full_name  if advisor  else None

    return data


# ── Create deal room ──────────────────────────────────
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

    existing = db.query(DealRoom).filter(DealRoom.offer_id == offer_id).first()
    if existing:
        return enrich_deal_room(existing, db)

    # Auto-reject all other pending offers for this listing
    other_offers = db.query(Offer).filter(
        Offer.listing_id == offer.listing_id,
        Offer.id != offer_id,
        Offer.status == "pending"
    ).all()
    for o in other_offers:
        o.status = "rejected"

    deal_room = DealRoom(
        offer_id=offer_id,
        listing_id=offer.listing_id,
        seller_id=current_user.id,
        investor_id=offer.investor_id,
        stage=DealStage.interested
    )
    db.add(deal_room)
    db.flush()

    for item_text in DEFAULT_CHECKLIST:
        db.add(DealChecklistItem(deal_room_id=deal_room.id, item=item_text))

    db.commit()
    db.refresh(deal_room)
    return enrich_deal_room(deal_room, db)


# ── Get deal room by offer ID ─────────────────────────
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
    return enrich_deal_room(deal, db)


# ── Get my deal rooms ─────────────────────────────────
@router.get("/my-deals", response_model=List[DealRoomResponse])
def get_my_deal_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deals = db.query(DealRoom).filter(
        (DealRoom.seller_id   == current_user.id) |
        (DealRoom.investor_id == current_user.id) |
        (DealRoom.advisor_id  == current_user.id)
    ).all()
    return [enrich_deal_room(d, db) for d in deals]


# ── Get single deal room ──────────────────────────────
@router.get("/{deal_room_id}", response_model=DealRoomFull)
def get_deal_room(
    deal_room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deal = db.query(DealRoom).filter(DealRoom.id == deal_room_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if current_user.id not in [deal.seller_id, deal.investor_id, deal.advisor_id]:
        raise HTTPException(status_code=403, detail="Access denied")
    docs      = db.query(DealDocument).filter(DealDocument.deal_room_id == deal_room_id).all()
    checklist = db.query(DealChecklistItem).filter(DealChecklistItem.deal_room_id == deal_room_id).all()
    return {"deal_room": enrich_deal_room(deal, db), "documents": docs, "checklist": checklist}


# ── Update stage ──────────────────────────────────────
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

    stage_val = data.stage.value if hasattr(data.stage, 'value') else str(data.stage)

    if stage_val == "closed":
        raise HTTPException(status_code=400,
            detail="Use the confirm-close flow to close a deal")

    stages_requiring_nda = ["due_diligence", "term_sheet"]
    if stage_val in stages_requiring_nda:
        if not (deal.nda_acknowledged_seller and deal.nda_acknowledged_investor):
            raise HTTPException(status_code=400,
                detail="Both parties must acknowledge the NDA before proceeding")

    db.execute(
        text(f"UPDATE deal_rooms SET stage = '{stage_val}'::dealstage WHERE id = :id"),
        {"id": deal_room_id}
    )
    db.commit()
    db.refresh(deal)
    return enrich_deal_room(deal, db)


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

    if deal.nda_acknowledged_seller and deal.nda_acknowledged_investor:
        db.execute(
            text("UPDATE deal_rooms SET stage = 'nda_signed'::dealstage WHERE id = :id"),
            {"id": deal_room_id}
        )

    db.commit()
    db.refresh(deal)
    return enrich_deal_room(deal, db)


@router.put("/{deal_room_id}/confirm-close", response_model=DealRoomResponse)
def confirm_close(
    deal_room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import text
    deal = db.query(DealRoom).filter(DealRoom.id == deal_room_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal room not found")

    stage_str = db.execute(
        text("SELECT stage::text FROM deal_rooms WHERE id = :id"),
        {"id": deal_room_id}
    ).scalar()

    if stage_str != "term_sheet":
        raise HTTPException(status_code=400,
            detail="Deal must be at Term Sheet stage before closing")
    if not (deal.term_sheet_seller_approved and deal.term_sheet_investor_approved):
        raise HTTPException(status_code=400,
            detail="Both parties must approve the term sheet before closing")

    # Check all checklist items complete
    checklist = db.query(DealChecklistItem).filter(
        DealChecklistItem.deal_room_id == deal_room_id
    ).all()
    incomplete = [c.item for c in checklist if not c.completed]
    if incomplete:
        raise HTTPException(status_code=400,
            detail=f"Complete all due diligence items first. Incomplete: {', '.join(incomplete[:3])}{'...' if len(incomplete) > 3 else ''}")

    if current_user.id == deal.seller_id:
        deal.close_confirmed_seller = True
    elif current_user.id == deal.investor_id:
        deal.close_confirmed_investor = True
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    if deal.close_confirmed_seller and deal.close_confirmed_investor:
        # Use raw SQL to update stage avoiding enum issues
        db.execute(
            text("UPDATE deal_rooms SET stage = 'closed'::dealstage WHERE id = :id"),
            {"id": deal_room_id}
        )
        deal.closed_amount = deal.term_sheet_amount

        listing = db.query(Listing).filter(Listing.id == deal.listing_id).first()
        if listing:
            listing.status = "closed"
            business = db.query(Business).filter(
                Business.id == listing.business_id
            ).first()
            if business:
                business.status = BusinessStatus.acquired

        # Terminate other active deal rooms for same listing
        db.execute(
            text("""
                UPDATE deal_rooms
                SET stage = 'terminated'::dealstage
                WHERE listing_id = :listing_id
                AND id != :deal_id
                AND stage::text NOT IN ('closed', 'terminated')
            """),
            {"listing_id": deal.listing_id, "deal_id": deal_room_id}
        )

        # Reject remaining pending offers
        db.execute(
            text("""
                UPDATE offers SET status = 'rejected'
                WHERE listing_id = :listing_id
                AND status = 'pending'
            """),
            {"listing_id": deal.listing_id}
        )

    db.commit()
    db.refresh(deal)
    return enrich_deal_room(deal, db)


# ── Propose term sheet ────────────────────────────────
@router.post("/{deal_room_id}/term-sheet", response_model=DealRoomResponse)
def propose_term_sheet(
    deal_room_id: int,
    data: TermSheetData,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deal = db.query(DealRoom).filter(DealRoom.id == deal_room_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if current_user.id not in [deal.seller_id, deal.investor_id]:
        raise HTTPException(status_code=403, detail="Access denied")

    deal.term_sheet_amount        = data.amount
    deal.term_sheet_stake         = data.stake
    deal.term_sheet_payment_terms = data.payment_terms
    deal.term_sheet_conditions    = data.conditions
    deal.term_sheet_proposed_by   = current_user.id
    deal.term_sheet_seller_approved   = None
    deal.term_sheet_investor_approved = None
    deal.close_confirmed_seller   = False
    deal.close_confirmed_investor = False

    db.commit()
    db.refresh(deal)
    return enrich_deal_room(deal, db)


# ── Approve/reject term sheet ─────────────────────────
@router.put("/{deal_room_id}/term-sheet/approve", response_model=DealRoomResponse)
def approve_term_sheet(
    deal_room_id: int,
    data: TermSheetApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deal = db.query(DealRoom).filter(DealRoom.id == deal_room_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if current_user.id not in [deal.seller_id, deal.investor_id]:
        raise HTTPException(status_code=403, detail="Access denied")

    stage_str = db.execute(
        text("SELECT stage::text FROM deal_rooms WHERE id = :id"),
        {"id": deal_room_id}
    ).scalar()

    if stage_str in ("terminated", "closed"):
        raise HTTPException(status_code=400, detail="Deal is already finalised")

    if current_user.id == deal.seller_id:
        deal.term_sheet_seller_approved = data.approved
    elif current_user.id == deal.investor_id:
        deal.term_sheet_investor_approved = data.approved

    if data.approved is False:
        db.execute(
            text("UPDATE deal_rooms SET stage = 'terminated'::dealstage WHERE id = :id"),
            {"id": deal_room_id}
        )
        listing = db.query(Listing).filter(Listing.id == deal.listing_id).first()
        if listing:
            listing.status = "active"

    db.commit()
    db.refresh(deal)
    return enrich_deal_room(deal, db)


# ── Add document record ───────────────────────────────
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


# ── Confirm document (dual acknowledgement) ───────────
@router.put("/{deal_room_id}/documents/{doc_id}/confirm", response_model=DealDocumentResponse)
def confirm_document(
    deal_room_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deal = db.query(DealRoom).filter(DealRoom.id == deal_room_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal room not found")
    doc = db.query(DealDocument).filter(
        DealDocument.id == doc_id,
        DealDocument.deal_room_id == deal_room_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if current_user.id == deal.seller_id:
        doc.seller_confirmed = True
    elif current_user.id == deal.investor_id:
        doc.investor_confirmed = True
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    db.commit()
    db.refresh(doc)
    return doc


# ── Toggle checklist — investor only ─────────────────
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

    # Only investor or advisor can complete checklist items
    if current_user.id == deal.seller_id:
        raise HTTPException(status_code=403,
            detail="Only the investor or advisor can complete checklist items")
    if current_user.id not in [deal.investor_id, deal.advisor_id]:
        raise HTTPException(status_code=403, detail="Access denied")

    item = db.query(DealChecklistItem).filter(
        DealChecklistItem.id == item_id,
        DealChecklistItem.deal_room_id == deal_room_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    item.completed = not item.completed
    if item.completed:
        item.completed_by      = current_user.id
        item.completed_by_role = (
            "investor" if current_user.id == deal.investor_id else "advisor"
        )
    else:
        item.completed_by      = None
        item.completed_by_role = None

    db.commit()
    db.refresh(item)
    return item


# ── Add checklist item ────────────────────────────────
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
    item = DealChecklistItem(deal_room_id=deal_room_id, item=data.item)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ── Assign advisor ────────────────────────────────────
@router.put("/{deal_room_id}/assign-advisor", response_model=DealRoomResponse)
def assign_advisor(
    deal_room_id: int,
    advisor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deal = db.query(DealRoom).filter(DealRoom.id == deal_room_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal room not found")
    if current_user.id not in [deal.seller_id, deal.investor_id]:
        raise HTTPException(status_code=403, detail="Only deal parties can assign an advisor")
    from app.models.user import UserRole
    advisor = db.query(User).filter(
        User.id == advisor_id,
        User.role == UserRole.advisor,
        User.is_verified == True
    ).first()
    if not advisor:
        raise HTTPException(status_code=404, detail="Verified advisor not found")
    deal.advisor_id = advisor_id
    db.commit()
    db.refresh(deal)
    return enrich_deal_room(deal, db)


# ── Get available advisors ────────────────────────────
@router.get("/advisors/available")
def get_available_advisors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.user import UserRole
    advisors = db.query(User).filter(
        User.role == UserRole.advisor,
        User.is_verified == True,
        User.is_active == True
    ).all()
    return [{"id": a.id, "full_name": a.full_name, "email": a.email} for a in advisors]