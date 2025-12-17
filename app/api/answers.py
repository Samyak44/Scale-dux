"""Answer CRUD API endpoints"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.schemas.answer import AnswerSchema, AnswerCreate, AnswerUpdate
from app.models.answer import StartupAnswer
from app.models.startup import Startup
from app.models.question import Question

router = APIRouter()


@router.post("", response_model=AnswerSchema, status_code=201)
async def create_answer(
    request: AnswerCreate,
    db: Session = Depends(get_db)
):
    """
    Create or update an answer

    If an answer already exists for this startup-question pair, it will be updated.
    This endpoint uses upsert logic to ensure one answer per startup per question.
    """
    # Verify startup exists
    startup = db.query(Startup).filter(Startup.id == request.startup_id).first()
    if not startup:
        raise HTTPException(status_code=404, detail=f"Startup with id {request.startup_id} not found")

    # Verify question exists
    question = db.query(Question).filter(Question.id == request.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail=f"Question with id {request.question_id} not found")

    # Check if answer already exists
    existing_answer = db.query(StartupAnswer).filter(
        StartupAnswer.startup_id == request.startup_id,
        StartupAnswer.question_id == request.question_id
    ).first()

    if existing_answer:
        # Update existing answer
        existing_answer.answer_text = request.answer_text
        existing_answer.answer_number = request.answer_number
        existing_answer.selected_option_id = request.selected_option_id
        db.commit()
        db.refresh(existing_answer)
        return existing_answer
    else:
        # Create new answer
        answer = StartupAnswer(
            startup_id=request.startup_id,
            question_id=request.question_id,
            answer_text=request.answer_text,
            answer_number=request.answer_number,
            selected_option_id=request.selected_option_id,
        )

        db.add(answer)
        db.commit()
        db.refresh(answer)
        return answer


@router.get("", response_model=List[AnswerSchema])
async def list_answers(
    startup_id: Optional[UUID] = Query(None, description="Filter by startup ID"),
    question_id: Optional[UUID] = Query(None, description="Filter by question ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    List answers with optional filtering

    Supports filtering by:
    - startup_id: Get all answers for a specific startup
    - question_id: Get all answers for a specific question
    """
    query = db.query(StartupAnswer)

    if startup_id:
        query = query.filter(StartupAnswer.startup_id == startup_id)
    if question_id:
        query = query.filter(StartupAnswer.question_id == question_id)

    answers = query.order_by(StartupAnswer.created_at.desc()).offset(skip).limit(limit).all()

    return answers


@router.get("/{answer_id}", response_model=AnswerSchema)
async def get_answer(
    answer_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific answer by ID
    """
    answer = db.query(StartupAnswer).filter(StartupAnswer.id == answer_id).first()

    if not answer:
        raise HTTPException(status_code=404, detail=f"Answer with id {answer_id} not found")

    return answer


@router.put("/{answer_id}", response_model=AnswerSchema)
async def update_answer(
    answer_id: UUID,
    request: AnswerUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing answer

    Only provided fields will be updated (partial update supported).
    """
    answer = db.query(StartupAnswer).filter(StartupAnswer.id == answer_id).first()

    if not answer:
        raise HTTPException(status_code=404, detail=f"Answer with id {answer_id} not found")

    # Update only provided fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(answer, field, value)

    db.commit()
    db.refresh(answer)

    return answer


@router.delete("/{answer_id}", status_code=204)
async def delete_answer(
    answer_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete an answer
    """
    answer = db.query(StartupAnswer).filter(StartupAnswer.id == answer_id).first()

    if not answer:
        raise HTTPException(status_code=404, detail=f"Answer with id {answer_id} not found")

    db.delete(answer)
    db.commit()

    return None


@router.get("/startup/{startup_id}/question/{question_id}", response_model=AnswerSchema)
async def get_answer_by_startup_and_question(
    startup_id: UUID,
    question_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get answer for a specific startup and question combination

    This is a convenience endpoint to quickly retrieve an answer without knowing its ID.
    """
    answer = db.query(StartupAnswer).filter(
        StartupAnswer.startup_id == startup_id,
        StartupAnswer.question_id == question_id
    ).first()

    if not answer:
        raise HTTPException(
            status_code=404,
            detail=f"Answer not found for startup {startup_id} and question {question_id}"
        )

    return answer
