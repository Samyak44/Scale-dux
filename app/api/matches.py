"""Startup-Investor Matching API endpoints"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.schemas.matching import MatchSchema, MatchCreate, MatchUpdate
from app.models.matching import StartupInvestorMatch
from app.models.startup import Startup
from app.models.investor import Investor

router = APIRouter()


@router.post("", response_model=MatchSchema, status_code=201)
async def create_match(
    request: MatchCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new startup-investor match

    Stores computed match scores and reasoning for explainability.
    Used to cache ML-based or rule-based matching results.
    """
    # Verify startup exists
    startup = db.query(Startup).filter(Startup.id == request.startup_id).first()
    if not startup:
        raise HTTPException(status_code=404, detail=f"Startup with id {request.startup_id} not found")

    # Verify investor exists
    investor = db.query(Investor).filter(Investor.id == request.investor_id).first()
    if not investor:
        raise HTTPException(status_code=404, detail=f"Investor with id {request.investor_id} not found")

    match = StartupInvestorMatch(
        startup_id=request.startup_id,
        investor_id=request.investor_id,
        match_score=request.match_score,
        match_reason=request.match_reason,
        algorithm_version=request.algorithm_version,
        is_manual_override=request.is_manual_override,
    )

    try:
        db.add(match)
        db.commit()
        db.refresh(match)
        return match
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Match already exists for startup {request.startup_id} and investor {request.investor_id}"
        )


@router.get("", response_model=List[MatchSchema])
async def list_matches(
    startup_id: Optional[UUID] = Query(None, description="Filter by startup ID"),
    investor_id: Optional[UUID] = Query(None, description="Filter by investor ID"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum match score"),
    is_manual_override: Optional[bool] = Query(None, description="Filter by manual override status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    List matches with optional filtering

    Supports filtering by:
    - startup_id: Get all matches for a specific startup
    - investor_id: Get all matches for a specific investor
    - min_score: Filter matches above a certain score threshold
    - is_manual_override: Filter manually curated vs algorithmically generated matches
    """
    query = db.query(StartupInvestorMatch)

    if startup_id:
        query = query.filter(StartupInvestorMatch.startup_id == startup_id)
    if investor_id:
        query = query.filter(StartupInvestorMatch.investor_id == investor_id)
    if min_score is not None:
        query = query.filter(StartupInvestorMatch.match_score >= min_score)
    if is_manual_override is not None:
        query = query.filter(StartupInvestorMatch.is_manual_override == is_manual_override)

    matches = query.order_by(StartupInvestorMatch.match_score.desc()).offset(skip).limit(limit).all()

    return matches


@router.get("/{match_id}", response_model=MatchSchema)
async def get_match(
    match_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific match by ID
    """
    match = db.query(StartupInvestorMatch).filter(StartupInvestorMatch.id == match_id).first()

    if not match:
        raise HTTPException(status_code=404, detail=f"Match with id {match_id} not found")

    return match


@router.put("/{match_id}", response_model=MatchSchema)
async def update_match(
    match_id: UUID,
    request: MatchUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing match

    Only provided fields will be updated (partial update supported).
    Useful for manual score adjustments or updating match reasoning.
    """
    match = db.query(StartupInvestorMatch).filter(StartupInvestorMatch.id == match_id).first()

    if not match:
        raise HTTPException(status_code=404, detail=f"Match with id {match_id} not found")

    # Update only provided fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(match, field, value)

    db.commit()
    db.refresh(match)

    return match


@router.delete("/{match_id}", status_code=204)
async def delete_match(
    match_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a match

    Removes the cached match record. This doesn't prevent re-matching.
    """
    match = db.query(StartupInvestorMatch).filter(StartupInvestorMatch.id == match_id).first()

    if not match:
        raise HTTPException(status_code=404, detail=f"Match with id {match_id} not found")

    db.delete(match)
    db.commit()

    return None


@router.get("/startup/{startup_id}/investor/{investor_id}", response_model=MatchSchema)
async def get_match_by_startup_and_investor(
    startup_id: UUID,
    investor_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get match for a specific startup-investor pair

    Convenience endpoint to retrieve a match without knowing its ID.
    """
    match = db.query(StartupInvestorMatch).filter(
        StartupInvestorMatch.startup_id == startup_id,
        StartupInvestorMatch.investor_id == investor_id
    ).first()

    if not match:
        raise HTTPException(
            status_code=404,
            detail=f"Match not found for startup {startup_id} and investor {investor_id}"
        )

    return match
