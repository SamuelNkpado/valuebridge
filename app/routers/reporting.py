from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.user import User, UserRole
from app.models.business import Business
from app.models.valuation import ValuationReport
from app.models.marketplace import Listing, Offer, Message
from app.routers.business import get_current_user

router = APIRouter(prefix="/reports", tags=["Reporting & Analytics"])


# SME Owner Dashboard Summary
@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # Get all businesses owned by user
    businesses = db.query(Business).filter(Business.owner_id == current_user.id).all()
    business_ids = [b.id for b in businesses]

    # Get valuations for those businesses
    valuations = (
        db.query(ValuationReport)
        .filter(ValuationReport.business_id.in_(business_ids))
        .all()
    )

    # Get listings
    listings = db.query(Listing).filter(Listing.owner_id == current_user.id).all()
    listing_ids = [l.id for l in listings]

    # Get offers received
    offers_received = db.query(Offer).filter(Offer.listing_id.in_(listing_ids)).all()

    # Get unread messages
    unread_messages = (
        db.query(Message)
        .filter(Message.receiver_id == current_user.id, Message.is_read == False)
        .count()
    )

    # Calculate highest valuation
    highest_valuation = max([v.estimated_value for v in valuations], default=0)

    return {
        "user": current_user.full_name,
        "total_businesses": len(businesses),
        "total_valuations": len(valuations),
        "highest_valuation": highest_valuation,
        "active_listings": len([l for l in listings if l.status == "active"]),
        "total_offers_received": len(offers_received),
        "pending_offers": len([o for o in offers_received if o.status == "pending"]),
        "unread_messages": unread_messages,
        "businesses": [
            {
                "id": b.id,
                "name": b.name,
                "industry": b.industry,
                "annual_revenue": b.annual_revenue,
                "status": b.status,
            }
            for b in businesses
        ],
    }


# Valuation history for a business
@router.get("/valuation-history/{business_id}")
def get_valuation_history(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    business = (
        db.query(Business)
        .filter(Business.id == business_id, Business.owner_id == current_user.id)
        .first()
    )
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Business not found"
        )
    valuations = (
        db.query(ValuationReport)
        .filter(ValuationReport.business_id == business_id)
        .order_by(ValuationReport.created_at.desc())
        .all()
    )

    return {
        "business_name": business.name,
        "total_valuations": len(valuations),
        "latest_value": valuations[0].estimated_value if valuations else 0,
        "history": [
            {
                "id": v.id,
                "method": v.method,
                "estimated_value": v.estimated_value,
                "asset_based_value": v.asset_based_value,
                "income_based_value": v.income_based_value,
                "market_multiples_value": v.market_multiples_value,
                "created_at": v.created_at,
            }
            for v in valuations
        ],
    }


# Marketplace performance report
@router.get("/marketplace-performance")
def get_marketplace_performance(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    listings = db.query(Listing).filter(Listing.owner_id == current_user.id).all()
    listing_ids = [l.id for l in listings]

    all_offers = db.query(Offer).filter(Offer.listing_id.in_(listing_ids)).all()

    return {
        "total_listings": len(listings),
        "active_listings": len([l for l in listings if l.status == "active"]),
        "closed_listings": len([l for l in listings if l.status == "closed"]),
        "total_offers": len(all_offers),
        "pending_offers": len([o for o in all_offers if o.status == "pending"]),
        "accepted_offers": len([o for o in all_offers if o.status == "accepted"]),
        "rejected_offers": len([o for o in all_offers if o.status == "rejected"]),
        "highest_offer": max([o.amount for o in all_offers], default=0),
        "average_offer": (
            sum([o.amount for o in all_offers]) / len(all_offers) if all_offers else 0
        ),
    }
