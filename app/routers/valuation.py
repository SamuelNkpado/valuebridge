from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.valuation import ValuationReport
from app.models.business import Business
from app.models.user import User
from app.schemas.valuation import ValuationRequest, ValuationResponse
from app.routers.business import get_current_user
from app.utils.valuation_engine import (
    calculate_asset_based,
    calculate_income_based,
    calculate_market_multiples,
    calculate_combined,
)

router = APIRouter(prefix="/valuations", tags=["Valuation Engine"])


@router.post("/", response_model=ValuationResponse)
def create_valuation(
    data: ValuationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get the business
    business = (
        db.query(Business)
        .filter(Business.id == data.business_id, Business.owner_id == current_user.id)
        .first()
    )

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Business not found"
        )

    # Run all three calculations
    asset_value = calculate_asset_based(
        business.total_assets or 0, business.total_liabilities or 0
    )
    income_value = calculate_income_based(
        business.profit or 0, data.growth_rate or 0.10
    )
    market_value = calculate_market_multiples(
        business.annual_revenue or 0, business.industry
    )
    combined_value = calculate_combined(asset_value, income_value, market_value)

    # Pick the right value based on method
    method_values = {
        "asset_based": asset_value,
        "income_based": income_value,
        "market_multiples": market_value,
        "combined": combined_value,
    }
    estimated_value = method_values[data.method]

    # Save report
    report = ValuationReport(
        business_id=business.id,
        method=data.method,
        estimated_value=estimated_value,
        asset_based_value=asset_value,
        income_based_value=income_value,
        market_multiples_value=market_value,
        assumptions={
            "growth_rate": data.growth_rate,
            "discount_rate": 0.20,
            "industry_multiple": 2.0,
        },
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/business/{business_id}", response_model=List[ValuationResponse])
def get_valuations_for_business(
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
    return (
        db.query(ValuationReport)
        .filter(ValuationReport.business_id == business_id)
        .all()
    )


@router.get("/{valuation_id}", response_model=ValuationResponse)
def get_valuation(
    valuation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = (
        db.query(ValuationReport).filter(ValuationReport.id == valuation_id).first()
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Valuation report not found"
        )
    return report
