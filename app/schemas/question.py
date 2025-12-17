"""Question schemas for API requests and responses"""

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

# Import enums from models - just like Django!
from app.models.question import AnswerType, QuestionCategory


class QuestionOptionSchema(BaseModel):
    """Schema for question options"""
    id: UUID
    value: str
    score_weight: float
    display_order: Optional[int] = None

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models


class QuestionSchema(BaseModel):
    """Schema for questions"""
    id: UUID
    text: str
    category: QuestionCategory  # ← Enum imported from models!
    answer_type: AnswerType  # ← Enum imported from models!
    base_weight: float
    is_active: bool
    help_text: Optional[str] = None
    options: List[QuestionOptionSchema] = []

    class Config:
        from_attributes = True


class QuestionCreateRequest(BaseModel):
    """Schema for creating a new question"""
    text: str
    category: QuestionCategory  # ← Same enum, validates input!
    answer_type: AnswerType  # ← Same enum, validates input!
    base_weight: float = Field(default=1.0, ge=0, le=10)
    help_text: Optional[str] = None

    # Pydantic will automatically:
    # - Reject invalid category values
    # - Show valid options in OpenAPI docs
    # - Provide autocomplete in IDEs


class QuestionUpdateRequest(BaseModel):
    """Schema for updating a question"""
    text: Optional[str] = None
    category: Optional[QuestionCategory] = None  # ← Still validated by enum!
    answer_type: Optional[AnswerType] = None
    base_weight: Optional[float] = Field(default=None, ge=0, le=10)
    is_active: Optional[bool] = None
    help_text: Optional[str] = None
