from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.marketplace import Listing, Offer, Message
from app.models.business import Business
from app.models.user import User
from app.models.deal_room import DealRoom, DealStage, DealChecklistItem
from app.schemas.marketplace import (
    ListingCreate,
    ListingUpdate,
    ListingResponse,
    OfferCreate,
    OfferUpdate,
    OfferResponse,
    MessageCreate,
    MessageResponse,
)
from app.routers.business import get_current_user

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])

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


def enrich_listing(listing: Listing, db: Session) -> dict:
    data = {
        "id": listing.id,
        "business_id": listing.business_id,
        "owner_id": listing.owner_id,
        "asking_price": listing.asking_price,
        "deal_type": listing.deal_type,
        "visibility": listing.visibility,
        "status": listing.status,
        "share_token": listing.share_token,
        "description": listing.description,
        "created_at": listing.created_at,
        "business_name": None,
        "business_industry": None,
        "business_location": None,
        "business_revenue": None,
        "business_employees": None,
        "business_founded": None,
        "latest_valuation": None,
        "seller_initials": None,
        "seller_name": None,
        "seller_verified": None,
    }

    business = db.query(Business).filter(
        Business.id == listing.business_id
    ).first()
    if business:
        data["business_name"]      = business.name
        data["business_industry"]  = business.industry
        data["business_location"]  = business.location
        data["business_revenue"]   = business.annual_revenue
        data["business_employees"] = business.employee_count
        data["business_founded"]   = business.founding_year

        # Get latest valuation for this business
        from app.models.valuation import ValuationReport
        latest = db.query(ValuationReport).filter(
            ValuationReport.business_id == business.id
        ).order_by(ValuationReport.created_at.desc()).first()
        if latest:
            data["latest_valuation"] = latest.estimated_value

    seller = db.query(User).filter(User.id == listing.owner_id).first()
    if seller:
        name_parts = seller.full_name.split()
        data["seller_initials"] = "".join([p[0].upper() for p in name_parts[:2]])
        data["seller_name"]     = seller.full_name
        data["seller_verified"] = seller.is_verified

    return data


@router.post("/listings", response_model=ListingResponse)
def create_listing(
    data: ListingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    business = (
        db.query(Business)
        .filter(Business.id == data.business_id, Business.owner_id == current_user.id)
        .first()
    )
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    import secrets
    share_token = secrets.token_urlsafe(16) if data.visibility != "public" else None

    listing = Listing(owner_id=current_user.id, share_token=share_token, **data.model_dump())
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return enrich_listing(listing, db)


@router.get("/listings/shared/{token}", response_model=ListingResponse)
def get_listing_by_token(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    listing = db.query(Listing).filter(
        Listing.share_token == token,
        Listing.status == "active"
    ).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found or expired")
    return enrich_listing(listing, db)


@router.get("/listings/my-listings", response_model=List[ListingResponse])
def get_my_listings(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    listings = db.query(Listing).filter(Listing.owner_id == current_user.id).all()
    return [enrich_listing(l, db) for l in listings]


@router.get("/listings", response_model=List[ListingResponse])
def get_listings(
    industry: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    deal_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Listing).join(Business).filter(
        Listing.visibility == "public", Listing.status == "active"
    )
    if industry:
        query = query.filter(Business.industry == industry)
    if min_price:
        query = query.filter(Listing.asking_price >= min_price)
    if max_price:
        query = query.filter(Listing.asking_price <= max_price)
    if deal_type:
        query = query.filter(Listing.deal_type == deal_type)
    return [enrich_listing(l, db) for l in query.all()]


@router.put("/listings/{listing_id}", response_model=ListingResponse)
def update_listing(
    listing_id: int,
    data: ListingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    listing = (
        db.query(Listing)
        .filter(Listing.id == listing_id, Listing.owner_id == current_user.id)
        .first()
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(listing, key, value)
    db.commit()
    db.refresh(listing)
    return enrich_listing(listing, db)


@router.delete("/listings/{listing_id}")
def delete_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    listing = (
        db.query(Listing)
        .filter(Listing.id == listing_id, Listing.owner_id == current_user.id)
        .first()
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    db.delete(listing)
    db.commit()
    return {"message": "Listing deleted successfully"}


@router.post("/offers", response_model=OfferResponse)
def make_offer(
    data: OfferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    listing = (
        db.query(Listing)
        .filter(Listing.id == data.listing_id, Listing.status == "active")
        .first()
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found or inactive")
    if listing.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot offer on your own listing")
    offer = Offer(investor_id=current_user.id, **data.model_dump())
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


@router.get("/offers/my-offers", response_model=List[OfferResponse])
def get_my_offers(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return db.query(Offer).filter(Offer.investor_id == current_user.id).all()


@router.get("/offers/received", response_model=List[OfferResponse])
def get_received_offers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    listings = db.query(Listing).filter(
        Listing.owner_id == current_user.id
    ).all()
    listing_ids = [l.id for l in listings]
    offers = db.query(Offer).filter(
        Offer.listing_id.in_(listing_ids)
    ).all()

    result = []
    for o in offers:
        investor = db.query(User).filter(User.id == o.investor_id).first()
        offer_dict = {
            "id": o.id,
            "listing_id": o.listing_id,
            "investor_id": o.investor_id,
            "amount": o.amount,
            "message": o.message,
            "status": o.status,
            "created_at": o.created_at,
            "investor_name": investor.full_name if investor else None,
        }
        result.append(offer_dict)
    return result


@router.put("/offers/{offer_id}", response_model=OfferResponse)
def update_offer_status(
    offer_id: int,
    data: OfferUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    listing = (
        db.query(Listing)
        .filter(Listing.id == offer.listing_id, Listing.owner_id == current_user.id)
        .first()
    )
    if not listing:
        raise HTTPException(status_code=403, detail="Not authorized")
    offer.status = data.status

    # If offer is accepted, create deal room
    if data.status == "accepted":
        # Check if deal room already exists
        existing = db.query(DealRoom).filter(DealRoom.offer_id == offer_id).first()
        if not existing:
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
    db.refresh(offer)
    return offer


@router.post("/messages", response_model=MessageResponse)
def send_message(
    data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    receiver = db.query(User).filter(User.id == data.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    message = Message(sender_id=current_user.id, **data.model_dump())
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.get("/messages", response_model=List[MessageResponse])
def get_messages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    messages = db.query(Message).filter(
        (Message.receiver_id == current_user.id) |
        (Message.sender_id == current_user.id)
    ).all()

    result = []
    for m in messages:
        sender   = db.query(User).filter(User.id == m.sender_id).first()
        receiver = db.query(User).filter(User.id == m.receiver_id).first()
        result.append({
            "id":          m.id,
            "sender_id":   m.sender_id,
            "receiver_id": m.receiver_id,
            "listing_id":  m.listing_id,
            "content":     m.content,
            "is_read":     m.is_read,
            "created_at":  m.created_at,
            "sender_name":   sender.full_name   if sender   else f"User #{m.sender_id}",
            "receiver_name": receiver.full_name if receiver else f"User #{m.receiver_id}",
        })
    return result
