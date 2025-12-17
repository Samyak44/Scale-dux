"""Question CRUD API endpoints"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.question import (
    QuestionSchema,
    QuestionCreateRequest,
    QuestionUpdateRequest,
)
from app.models.question import Question, AnswerType, QuestionCategory
from app.services.conditional_logic import ConditionalLogicService

router = APIRouter()


@router.post("", response_model=QuestionSchema, status_code=201)
async def create_question(
    request: QuestionCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new question

    The enum validation happens automatically via Pydantic:
    - Invalid category or answer_type values will be rejected with 422 error
    - OpenAPI docs show dropdown with valid enum values
    """
    question = Question(
        text=request.text,
        category=request.category,
        answer_type=request.answer_type,
        base_weight=request.base_weight,
        help_text=request.help_text,
    )

    db.add(question)
    db.commit()
    db.refresh(question)

    return question


@router.get("", response_model=List[QuestionSchema])
async def list_questions(
    category: Optional[QuestionCategory] = Query(None, description="Filter by category"),
    answer_type: Optional[AnswerType] = Query(None, description="Filter by answer type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    List questions with optional filtering

    Supports filtering by:
    - category: Question category (traction, team, finance, market)
    - answer_type: Answer type (number, boolean, enum, text)
    - is_active: Whether question is active
    - Pagination via skip and limit
    """
    query = db.query(Question)

    if category:
        query = query.filter(Question.category == category)
    if answer_type:
        query = query.filter(Question.answer_type == answer_type)
    if is_active is not None:
        query = query.filter(Question.is_active == is_active)

    # Apply pagination
    questions = query.offset(skip).limit(limit).all()

    return questions


@router.get("/{question_id}", response_model=QuestionSchema)
async def get_question(
    question_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific question by ID

    Returns:
        QuestionSchema: The question with all its details

    Raises:
        HTTPException: 404 if question not found
    """
    question = db.query(Question).filter(Question.id == question_id).first()

    if not question:
        raise HTTPException(status_code=404, detail=f"Question with id {question_id} not found")

    return question


@router.put("/{question_id}", response_model=QuestionSchema)
async def update_question(
    question_id: UUID,
    request: QuestionUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update an existing question

    Only provided fields will be updated (partial update supported).
    All enum fields are validated by Pydantic.

    Raises:
        HTTPException: 404 if question not found
    """
    question = db.query(Question).filter(Question.id == question_id).first()

    if not question:
        raise HTTPException(status_code=404, detail=f"Question with id {question_id} not found")

    # Update only provided fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)

    db.commit()
    db.refresh(question)

    return question


@router.delete("/{question_id}", status_code=204)
async def delete_question(
    question_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a question

    This will cascade delete all related:
    - Question options
    - Startup answers
    - Scoring rules

    Raises:
        HTTPException: 404 if question not found
    """
    question = db.query(Question).filter(Question.id == question_id).first()

    if not question:
        raise HTTPException(status_code=404, detail=f"Question with id {question_id} not found")

    db.delete(question)
    db.commit()

    return None


@router.patch("/{question_id}/activate", response_model=QuestionSchema)
async def activate_question(
    question_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Activate a question

    Sets is_active to True for the specified question.
    """
    question = db.query(Question).filter(Question.id == question_id).first()

    if not question:
        raise HTTPException(status_code=404, detail=f"Question with id {question_id} not found")

    question.is_active = True
    db.commit()
    db.refresh(question)

    return question


@router.patch("/{question_id}/deactivate", response_model=QuestionSchema)
async def deactivate_question(
    question_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Deactivate a question

    Sets is_active to False for the specified question.
    This doesn't delete the question, just marks it as inactive.
    """
    question = db.query(Question).filter(Question.id == question_id).first()

    if not question:
        raise HTTPException(status_code=404, detail=f"Question with id {question_id} not found")

    question.is_active = False
    db.commit()
    db.refresh(question)

    return question


@router.get("/applicable/{startup_id}", response_model=List[QuestionSchema])
async def get_applicable_questions(
    startup_id: UUID,
    category: Optional[QuestionCategory] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """
    Get questions applicable to a specific startup based on conditional logic

    This endpoint returns only the questions that should be shown to this startup based on:
    - Their current stage
    - Their previous answers
    - Conditional logic rules (e.g., skip team questions for solo founders)

    This is the RECOMMENDED endpoint for taking assessments as it provides
    a personalized question set.
    """
    service = ConditionalLogicService(db)
    questions = service.get_applicable_questions(
        startup_id=startup_id,
        category=category
    )
    return questions


@router.get("/next/{startup_id}", response_model=List[QuestionSchema])
async def get_next_questions(
    startup_id: UUID,
    count: int = Query(10, ge=1, le=50, description="Number of questions to return"),
    db: Session = Depends(get_db)
):
    """
    Get the next unanswered questions for a startup

    Returns the next batch of questions that:
    1. Haven't been answered yet
    2. Are applicable based on conditional logic
    3. Are ordered by priority/category

    Perfect for progressive assessment flows.
    """
    service = ConditionalLogicService(db)
    questions = service.get_next_unanswered_questions(
        startup_id=startup_id,
        count=count
    )
    return questions


@router.get("/progress/{startup_id}")
async def get_assessment_progress(
    startup_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get assessment progress for a startup

    Returns:
    - Total applicable questions
    - Number answered
    - Progress percentage
    - Progress by category

    Use this to show progress bars and completion status.
    """
    service = ConditionalLogicService(db)
    progress = service.get_progress(startup_id)
    return progress
