from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.user import User, UserRole
from app.models.business import Business
from app.models.valuation import ValuationReport
from app.models.marketplace import Listing, Offer
from app.routers.business import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin Panel"])


# Helper to check if user is admin
def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


# Platform overview stats
@router.get("/stats")
def get_platform_stats(
    db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    total_users = db.query(User).count()
    total_businesses = db.query(Business).count()
    total_valuations = db.query(ValuationReport).count()
    total_listings = db.query(Listing).count()
    total_offers = db.query(Offer).count()

    # Users by role
    sme_owners = db.query(User).filter(User.role == UserRole.sme_owner).count()
    investors = db.query(User).filter(User.role == UserRole.investor).count()
    advisors = db.query(User).filter(User.role == UserRole.advisor).count()

    # Active listings
    active_listings = db.query(Listing).filter(Listing.status == "active").count()

    # Accepted offers
    accepted_offers = db.query(Offer).filter(Offer.status == "accepted").count()

    return {
        "total_users": total_users,
        "users_by_role": {
            "sme_owners": sme_owners,
            "investors": investors,
            "advisors": advisors,
        },
        "total_businesses": total_businesses,
        "total_valuations": total_valuations,
        "total_listings": total_listings,
        "active_listings": active_listings,
        "total_offers": total_offers,
        "accepted_offers": accepted_offers,
        "success_rate": (
            f"{(accepted_offers/total_offers*100):.1f}%" if total_offers > 0 else "0%"
        ),
    }


# Get all users
@router.get("/users")
def get_all_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "is_verified": u.is_verified,
            "is_active": u.is_active,
            "created_at": u.created_at,
        }
        for u in users
    ]


# Suspend or activate a user
@router.put("/users/{user_id}/toggle-status")
def toggle_user_status(
    user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot suspend yourself"
        )
    user.is_active = not user.is_active
    db.commit()
    return {
        "message": f"User {'activated' if user.is_active else 'suspended'} successfully",
        "user_id": user.id,
        "is_active": user.is_active,
    }


# Verify a user
@router.put("/users/{user_id}/verify")
def verify_user(
    user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    user.is_verified = True
    db.commit()
    return {"message": "User verified successfully", "user_id": user.id}


# Get all listings for moderation
@router.get("/listings")
def get_all_listings(
    db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    listings = db.query(Listing).all()
    return [
        {
            "id": l.id,
            "business_id": l.business_id,
            "owner_id": l.owner_id,
            "asking_price": l.asking_price,
            "deal_type": l.deal_type,
            "status": l.status,
            "visibility": l.visibility,
            "created_at": l.created_at,
        }
        for l in listings
    ]


# Remove a listing
@router.delete("/listings/{listing_id}")
def remove_listing(
    listing_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found"
        )
    db.delete(listing)
    db.commit()
    return {"message": "Listing removed successfully"}
