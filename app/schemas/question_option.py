"""Question option schemas for API requests and responses"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class QuestionOptionBase(BaseModel):
    """Base question option schema"""
    value: str = Field(..., min_length=1, description="Option text/value")
    score_weight: float = Field(default=1.0, ge=0, le=10, description="Scoring multiplier")
    display_order: Optional[int] = Field(None, ge=0)


class QuestionOptionCreate(QuestionOptionBase):
    """Schema for creating a question option"""
    question_id: UUID


class QuestionOptionUpdate(BaseModel):
    """Schema for updating a question option"""
    value: Optional[str] = Field(None, min_length=1)
    score_weight: Optional[float] = Field(None, ge=0, le=10)
    display_order: Optional[int] = Field(None, ge=0)


class QuestionOptionSchema(QuestionOptionBase):
    """Schema for question option response"""
    id: UUID
    question_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
