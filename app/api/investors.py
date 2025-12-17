"""Investor CRUD API endpoints"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.schemas.investor import (
    InvestorSchema,
    InvestorCreate,
    InvestorUpdate,
    InvestorWithPreferences,
)
from app.models.investor import Investor

router = APIRouter()


@router.post("", response_model=InvestorSchema, status_code=201)
async def create_investor(
    request: InvestorCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new investor

    Requires user_id from the authentication system to link the investor to a user.
    """
    investor = Investor(
        user_id=request.user_id,
        name=request.name,
        firm_name=request.firm_name,
        bio=request.bio,
        website=request.website,
        linkedin_url=request.linkedin_url,
        min_check_size=request.min_check_size,
        max_check_size=request.max_check_size,
    )

    try:
        db.add(investor)
        db.commit()
        db.refresh(investor)
        return investor
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"User ID {request.user_id} already has an investor profile")


@router.get("", response_model=List[InvestorSchema])
async def list_investors(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    List investors with optional filtering

    Supports filtering by user_id to get investor profile for a specific user.
    """
    query = db.query(Investor)

    if user_id:
        query = query.filter(Investor.user_id == user_id)

    investors = query.order_by(Investor.created_at.desc()).offset(skip).limit(limit).all()

    return investors


@router.get("/{investor_id}", response_model=InvestorWithPreferences)
async def get_investor(
    investor_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific investor by ID

    Includes all investor preferences.
    """
    investor = db.query(Investor).filter(Investor.id == investor_id).first()

    if not investor:
        raise HTTPException(status_code=404, detail=f"Investor with id {investor_id} not found")

    return investor


@router.put("/{investor_id}", response_model=InvestorSchema)
async def update_investor(
    investor_id: UUID,
    request: InvestorUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing investor

    Only provided fields will be updated (partial update supported).
    """
    investor = db.query(Investor).filter(Investor.id == investor_id).first()

    if not investor:
        raise HTTPException(status_code=404, detail=f"Investor with id {investor_id} not found")

    # Update only provided fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(investor, field, value)

    db.commit()
    db.refresh(investor)

    return investor


@router.delete("/{investor_id}", status_code=204)
async def delete_investor(
    investor_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete an investor

    This will cascade delete all related:
    - Investor preferences
    - Matches
    """
    investor = db.query(Investor).filter(Investor.id == investor_id).first()

    if not investor:
        raise HTTPException(status_code=404, detail=f"Investor with id {investor_id} not found")

    db.delete(investor)
    db.commit()

    return None
