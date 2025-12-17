"""Startup schemas for API requests and responses"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.startup import StartupStage


class StartupBase(BaseModel):
    """Base startup schema"""
    name: str = Field(..., min_length=1, max_length=255)
    stage: StartupStage


class StartupCreate(StartupBase):
    """Schema for creating a startup"""
    user_id: str = Field(..., description="User ID from authentication system")


class StartupUpdate(BaseModel):
    """Schema for updating a startup"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    stage: Optional[StartupStage] = None


class StartupSchema(StartupBase):
    """Schema for startup response"""
    id: UUID
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
