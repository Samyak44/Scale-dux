"""Matching schemas for API requests and responses"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class MatchBase(BaseModel):
    """Base match schema"""
    match_score: float = Field(..., ge=0, le=100, description="Match score (0-100)")
    match_reason: str = Field(..., min_length=1, description="Explanation for the match")
    algorithm_version: Optional[str] = None
    is_manual_override: bool = False


class MatchCreate(MatchBase):
    """Schema for creating a match"""
    startup_id: UUID
    investor_id: UUID


class MatchUpdate(BaseModel):
    """Schema for updating a match"""
    match_score: Optional[float] = Field(None, ge=0, le=100)
    match_reason: Optional[str] = Field(None, min_length=1)
    algorithm_version: Optional[str] = None
    is_manual_override: Optional[bool] = None


class MatchSchema(MatchBase):
    """Schema for match response"""
    id: UUID
    startup_id: UUID
    investor_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MatchWithDetails(MatchSchema):
    """Schema for match with startup and investor details"""
    startup_name: Optional[str] = None
    investor_name: Optional[str] = None
