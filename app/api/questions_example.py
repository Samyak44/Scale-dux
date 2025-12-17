"""Example API endpoints for questions - shows enum validation in action"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.schemas.question import (
    QuestionSchema,
    QuestionCreateRequest,
    QuestionUpdateRequest
)
from app.models.question import Question, AnswerType, QuestionCategory

router = APIRouter(prefix="/questions", tags=["questions"])


# Example endpoint - Pydantic validates enum automatically!
@router.post("", response_model=QuestionSchema)
async def create_question(request: QuestionCreateRequest, db: Session):
    """
    Create a new question

    The enum validation happens automatically:
    - If request has category="invalid", Pydantic rejects it
    - OpenAPI docs show dropdown with valid values
    - Just like Django serializers!
    """
    question = Question(
        text=request.text,
        category=request.category,  # Already validated by Pydantic
        answer_type=request.answer_type,  # Already validated by Pydantic
        base_weight=request.base_weight,
        help_text=request.help_text
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    return question


@router.get("", response_model=List[QuestionSchema])
async def list_questions(
    category: QuestionCategory = None,  # ← Query param with enum validation!
    answer_type: AnswerType = None,
    db: Session = None
):
    """
    List questions with optional filtering

    Try in Swagger UI - you'll see dropdowns for category and answer_type!
    Just like Django's browsable API.
    """
    query = db.query(Question)

    if category:
        query = query.filter(Question.category == category)
    if answer_type:
        query = query.filter(Question.answer_type == answer_type)

    return query.all()


# What happens at runtime:

# ✅ Valid request:
# POST /questions
# {
#   "text": "How many employees?",
#   "category": "team",          ← Valid enum value
#   "answer_type": "number"      ← Valid enum value
# }
# Result: 201 Created

# ❌ Invalid request:
# POST /questions
# {
#   "text": "How many employees?",
#   "category": "invalid_cat",   ← NOT in enum!
#   "answer_type": "number"
# }
# Result: 422 Unprocessable Entity
# {
#   "detail": [
#     {
#       "loc": ["body", "category"],
#       "msg": "value is not a valid enumeration member; permitted: 'traction', 'team', 'finance', 'market'",
#       "type": "type_error.enum"
#     }
#   ]
# }
