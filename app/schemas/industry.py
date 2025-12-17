"""Industry schemas for API requests and responses"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class IndustryBase(BaseModel):
    """Base industry schema"""
    name: str = Field(..., min_length=1, max_length=100)


class IndustryCreate(IndustryBase):
    """Schema for creating an industry"""
    pass


class IndustryUpdate(BaseModel):
    """Schema for updating an industry"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class IndustrySchema(IndustryBase):
    """Schema for industry response"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
