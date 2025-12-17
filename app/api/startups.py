"""Startup CRUD API endpoints"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.startup import StartupSchema, StartupCreate, StartupUpdate
from app.models.startup import Startup, StartupStage

router = APIRouter()


@router.post("", response_model=StartupSchema, status_code=201)
async def create_startup(
    request: StartupCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new startup

    Requires user_id from the authentication system to link the startup to a user.
    """
    startup = Startup(
        user_id=request.user_id,
        name=request.name,
        stage=request.stage,
    )

    db.add(startup)
    db.commit()
    db.refresh(startup)

    return startup


@router.get("", response_model=List[StartupSchema])
async def list_startups(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    stage: Optional[StartupStage] = Query(None, description="Filter by stage"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    List startups with optional filtering

    Supports filtering by:
    - user_id: Get startups for a specific user
    - stage: Filter by startup stage
    """
    query = db.query(Startup)

    if user_id:
        query = query.filter(Startup.user_id == user_id)
    if stage:
        query = query.filter(Startup.stage == stage)

    startups = query.order_by(Startup.created_at.desc()).offset(skip).limit(limit).all()

    return startups


@router.get("/{startup_id}", response_model=StartupSchema)
async def get_startup(
    startup_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific startup by ID
    """
    startup = db.query(Startup).filter(Startup.id == startup_id).first()

    if not startup:
        raise HTTPException(status_code=404, detail=f"Startup with id {startup_id} not found")

    return startup


@router.put("/{startup_id}", response_model=StartupSchema)
async def update_startup(
    startup_id: UUID,
    request: StartupUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing startup

    Only provided fields will be updated (partial update supported).
    """
    startup = db.query(Startup).filter(Startup.id == startup_id).first()

    if not startup:
        raise HTTPException(status_code=404, detail=f"Startup with id {startup_id} not found")

    # Update only provided fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(startup, field, value)

    db.commit()
    db.refresh(startup)

    return startup


@router.delete("/{startup_id}", status_code=204)
async def delete_startup(
    startup_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a startup

    This will cascade delete all related:
    - Assessments
    - Answers
    - Scores
    - Matches
    """
    startup = db.query(Startup).filter(Startup.id == startup_id).first()

    if not startup:
        raise HTTPException(status_code=404, detail=f"Startup with id {startup_id} not found")

    db.delete(startup)
    db.commit()

    return None
