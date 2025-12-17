"""Assessment CRUD API endpoints"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.assessment import (
    AssessmentSchema,
    AssessmentCreate,
    AssessmentUpdate,
)
from app.models.assessment import Assessment, AssessmentStatus
from app.models.startup import Startup, StartupStage

router = APIRouter()


@router.post("", response_model=AssessmentSchema, status_code=201)
async def create_assessment(
    request: AssessmentCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new assessment

    Initializes a draft assessment for a startup that can be progressively filled out.
    """
    # Verify startup exists
    startup = db.query(Startup).filter(Startup.id == request.startup_id).first()
    if not startup:
        raise HTTPException(status_code=404, detail=f"Startup with id {request.startup_id} not found")

    assessment = Assessment(
        startup_id=request.startup_id,
        stage=request.stage,
        framework_version=request.framework_version,
        status=AssessmentStatus.DRAFT,
        responses={},
    )

    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return assessment


@router.get("", response_model=List[AssessmentSchema])
async def list_assessments(
    startup_id: Optional[UUID] = Query(None, description="Filter by startup ID"),
    status: Optional[AssessmentStatus] = Query(None, description="Filter by status"),
    stage: Optional[StartupStage] = Query(None, description="Filter by stage"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    List assessments with optional filtering

    Supports filtering by:
    - startup_id: Get all assessments for a specific startup
    - status: Filter by assessment status (draft, in_progress, completed, published, archived)
    - stage: Filter by startup stage
    """
    query = db.query(Assessment)

    if startup_id:
        query = query.filter(Assessment.startup_id == startup_id)
    if status:
        query = query.filter(Assessment.status == status)
    if stage:
        query = query.filter(Assessment.stage == stage)

    assessments = query.order_by(Assessment.created_at.desc()).offset(skip).limit(limit).all()

    return assessments


@router.get("/{assessment_id}", response_model=AssessmentSchema)
async def get_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific assessment by ID

    Returns full assessment details including responses and score metadata.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()

    if not assessment:
        raise HTTPException(status_code=404, detail=f"Assessment with id {assessment_id} not found")

    return assessment


@router.put("/{assessment_id}", response_model=AssessmentSchema)
async def update_assessment(
    assessment_id: UUID,
    request: AssessmentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing assessment

    Only provided fields will be updated (partial update supported).
    Used to update responses, status, or stage.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()

    if not assessment:
        raise HTTPException(status_code=404, detail=f"Assessment with id {assessment_id} not found")

    # Update only provided fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assessment, field, value)

    db.commit()
    db.refresh(assessment)

    return assessment


@router.delete("/{assessment_id}", status_code=204)
async def delete_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete an assessment

    This will cascade delete all related evidence uploads and audit logs.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()

    if not assessment:
        raise HTTPException(status_code=404, detail=f"Assessment with id {assessment_id} not found")

    db.delete(assessment)
    db.commit()

    return None


@router.patch("/{assessment_id}/status", response_model=AssessmentSchema)
async def update_assessment_status(
    assessment_id: UUID,
    status: AssessmentStatus,
    db: Session = Depends(get_db)
):
    """
    Update assessment status

    Convenience endpoint to change assessment status:
    - draft -> in_progress
    - in_progress -> completed
    - completed -> published
    - any -> archived
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()

    if not assessment:
        raise HTTPException(status_code=404, detail=f"Assessment with id {assessment_id} not found")

    assessment.status = status
    db.commit()
    db.refresh(assessment)

    return assessment
