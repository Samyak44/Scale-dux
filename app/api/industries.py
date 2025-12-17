"""Industry CRUD API endpoints"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.schemas.industry import IndustrySchema, IndustryCreate, IndustryUpdate
from app.models.lookup import Industry

router = APIRouter()


@router.post("", response_model=IndustrySchema, status_code=201)
async def create_industry(
    request: IndustryCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new industry

    Industries are lookup values used for investor preferences and categorization.
    """
    industry = Industry(name=request.name)

    try:
        db.add(industry)
        db.commit()
        db.refresh(industry)
        return industry
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Industry '{request.name}' already exists")


@router.get("", response_model=List[IndustrySchema])
async def list_industries(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    List all industries

    Returns industries ordered by name.
    """
    industries = db.query(Industry).order_by(Industry.name).offset(skip).limit(limit).all()
    return industries


@router.get("/{industry_id}", response_model=IndustrySchema)
async def get_industry(
    industry_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific industry by ID
    """
    industry = db.query(Industry).filter(Industry.id == industry_id).first()

    if not industry:
        raise HTTPException(status_code=404, detail=f"Industry with id {industry_id} not found")

    return industry


@router.put("/{industry_id}", response_model=IndustrySchema)
async def update_industry(
    industry_id: UUID,
    request: IndustryUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing industry
    """
    industry = db.query(Industry).filter(Industry.id == industry_id).first()

    if not industry:
        raise HTTPException(status_code=404, detail=f"Industry with id {industry_id} not found")

    # Update only provided fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(industry, field, value)

    try:
        db.commit()
        db.refresh(industry)
        return industry
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Industry name already exists")


@router.delete("/{industry_id}", status_code=204)
async def delete_industry(
    industry_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete an industry

    This will cascade delete all investor preferences using this industry.
    """
    industry = db.query(Industry).filter(Industry.id == industry_id).first()

    if not industry:
        raise HTTPException(status_code=404, detail=f"Industry with id {industry_id} not found")

    db.delete(industry)
    db.commit()

    return None
