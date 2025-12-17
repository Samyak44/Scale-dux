"""Answer schemas for API requests and responses"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class AnswerCreate(BaseModel):
    """Schema for creating/updating an answer"""
    startup_id: UUID
    question_id: UUID
    answer_text: Optional[str] = None
    answer_number: Optional[float] = None
    selected_option_id: Optional[UUID] = None

    @field_validator('answer_text', 'answer_number', 'selected_option_id')
    @classmethod
    def check_at_least_one_answer(cls, v, info):
        """At least one answer field must be provided"""
        values = info.data
        if not any([
            values.get('answer_text'),
            values.get('answer_number') is not None,
            values.get('selected_option_id')
        ]):
            if v is None and info.field_name == 'selected_option_id':
                raise ValueError('At least one answer field must be provided')
        return v


class AnswerUpdate(BaseModel):
    """Schema for updating an answer"""
    answer_text: Optional[str] = None
    answer_number: Optional[float] = None
    selected_option_id: Optional[UUID] = None


class AnswerSchema(BaseModel):
    """Schema for answer response"""
    id: UUID
    startup_id: UUID
    question_id: UUID
    answer_text: Optional[str] = None
    answer_number: Optional[float] = None
    selected_option_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnswerWithDetails(AnswerSchema):
    """Schema for answer with question details"""
    question_text: Optional[str] = None
    question_category: Optional[str] = None
    selected_option_value: Optional[str] = None
