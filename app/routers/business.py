from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.business import Business
from app.models.user import User
from app.schemas.business import BusinessCreate, BusinessUpdate, BusinessResponse
from app.utils.auth import verify_token
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(prefix="/businesses", tags=["Business Profile"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# Helper to get current logged in user
def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


# Create a new business profile
@router.post("/", response_model=BusinessResponse)
def create_business(
    business_data: BusinessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_business = Business(owner_id=current_user.id, **business_data.model_dump())
    db.add(new_business)
    db.commit()
    db.refresh(new_business)
    return new_business


# Get all businesses owned by current user
@router.get("/my-businesses", response_model=List[BusinessResponse])
def get_my_businesses(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    businesses = db.query(Business).filter(Business.owner_id == current_user.id).all()
    return businesses


# Get a single business by ID
@router.get("/{business_id}", response_model=BusinessResponse)
def get_business(
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
    return business


# Update a business
@router.put("/{business_id}", response_model=BusinessResponse)
def update_business(
    business_id: int,
    business_data: BusinessUpdate,
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
    for key, value in business_data.model_dump(exclude_unset=True).items():
        setattr(business, key, value)
    db.commit()
    db.refresh(business)
    return business


# Delete a business
@router.delete("/{business_id}")
def delete_business(
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
    db.delete(business)
    db.commit()
    return {"message": "Business deleted successfully"}
