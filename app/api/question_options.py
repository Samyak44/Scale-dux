"""Question Option CRUD API endpoints"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.question_option import (
    QuestionOptionSchema,
    QuestionOptionCreate,
    QuestionOptionUpdate,
)
from app.models.question import QuestionOption, Question

router = APIRouter()


@router.post("", response_model=QuestionOptionSchema, status_code=201)
async def create_question_option(
    request: QuestionOptionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new question option

    Question options are used for enum-type questions to provide predefined answer choices.
    """
    # Verify question exists
    question = db.query(Question).filter(Question.id == request.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail=f"Question with id {request.question_id} not found")

    option = QuestionOption(
        question_id=request.question_id,
        value=request.value,
        score_weight=request.score_weight,
        display_order=request.display_order,
    )

    db.add(option)
    db.commit()
    db.refresh(option)

    return option


@router.get("", response_model=List[QuestionOptionSchema])
async def list_question_options(
    question_id: UUID = Query(None, description="Filter by question ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    List question options with optional filtering

    Supports filtering by question_id to get all options for a specific question.
    """
    query = db.query(QuestionOption)

    if question_id:
        query = query.filter(QuestionOption.question_id == question_id)

    # Order by display_order if available, otherwise by created_at
    options = query.order_by(
        QuestionOption.display_order.asc().nullslast(),
        QuestionOption.created_at
    ).offset(skip).limit(limit).all()

    return options


@router.get("/{option_id}", response_model=QuestionOptionSchema)
async def get_question_option(
    option_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific question option by ID
    """
    option = db.query(QuestionOption).filter(QuestionOption.id == option_id).first()

    if not option:
        raise HTTPException(status_code=404, detail=f"Question option with id {option_id} not found")

    return option


@router.put("/{option_id}", response_model=QuestionOptionSchema)
async def update_question_option(
    option_id: UUID,
    request: QuestionOptionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing question option
    """
    option = db.query(QuestionOption).filter(QuestionOption.id == option_id).first()

    if not option:
        raise HTTPException(status_code=404, detail=f"Question option with id {option_id} not found")

    # Update only provided fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(option, field, value)

    db.commit()
    db.refresh(option)

    return option


@router.delete("/{option_id}", status_code=204)
async def delete_question_option(
    option_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a question option

    This will set selected_option_id to NULL for any answers using this option.
    """
    option = db.query(QuestionOption).filter(QuestionOption.id == option_id).first()

    if not option:
        raise HTTPException(status_code=404, detail=f"Question option with id {option_id} not found")

    db.delete(option)
    db.commit()

    return None
