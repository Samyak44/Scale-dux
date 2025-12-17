"""Investor Preference CRUD API endpoints"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.investor import (
    InvestorPreferenceSchema,
    InvestorPreferenceCreate,
    InvestorPreferenceUpdate,
)
from app.models.investor import InvestorPreference, Investor
from app.models.startup import StartupStage

router = APIRouter()


@router.post("", response_model=InvestorPreferenceSchema, status_code=201)
async def create_investor_preference(
    request: InvestorPreferenceCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new investor preference

    Allows investors to specify their investment criteria across multiple dimensions:
    - Industry preferences
    - Stage preferences
    - Ticket size ranges
    """
    # Verify investor exists
    investor = db.query(Investor).filter(Investor.id == request.investor_id).first()
    if not investor:
        raise HTTPException(status_code=404, detail=f"Investor with id {request.investor_id} not found")

    preference = InvestorPreference(
        investor_id=request.investor_id,
        industry_id=request.industry_id,
        stage=request.stage,
        ticket_min=request.ticket_min,
        ticket_max=request.ticket_max,
        weight=request.weight,
    )

    db.add(preference)
    db.commit()
    db.refresh(preference)

    return preference


@router.get("", response_model=List[InvestorPreferenceSchema])
async def list_investor_preferences(
    investor_id: Optional[UUID] = Query(None, description="Filter by investor ID"),
    stage: Optional[StartupStage] = Query(None, description="Filter by stage"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    List investor preferences with optional filtering

    Supports filtering by:
    - investor_id: Get all preferences for a specific investor
    - stage: Filter by preferred startup stage
    """
    query = db.query(InvestorPreference)

    if investor_id:
        query = query.filter(InvestorPreference.investor_id == investor_id)
    if stage:
        query = query.filter(InvestorPreference.stage == stage)

    preferences = query.order_by(InvestorPreference.weight.desc()).offset(skip).limit(limit).all()

    return preferences


@router.get("/{preference_id}", response_model=InvestorPreferenceSchema)
async def get_investor_preference(
    preference_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific investor preference by ID
    """
    preference = db.query(InvestorPreference).filter(InvestorPreference.id == preference_id).first()

    if not preference:
        raise HTTPException(status_code=404, detail=f"Investor preference with id {preference_id} not found")

    return preference


@router.put("/{preference_id}", response_model=InvestorPreferenceSchema)
async def update_investor_preference(
    preference_id: UUID,
    request: InvestorPreferenceUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing investor preference

    Only provided fields will be updated (partial update supported).
    """
    preference = db.query(InvestorPreference).filter(InvestorPreference.id == preference_id).first()

    if not preference:
        raise HTTPException(status_code=404, detail=f"Investor preference with id {preference_id} not found")

    # Update only provided fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preference, field, value)

    db.commit()
    db.refresh(preference)

    return preference


@router.delete("/{preference_id}", status_code=204)
async def delete_investor_preference(
    preference_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete an investor preference
    """
    preference = db.query(InvestorPreference).filter(InvestorPreference.id == preference_id).first()

    if not preference:
        raise HTTPException(status_code=404, detail=f"Investor preference with id {preference_id} not found")

    db.delete(preference)
    db.commit()

    return None
