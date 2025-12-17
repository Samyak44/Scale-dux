"""Investor and preference schemas for API requests and responses"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl

from app.models.startup import StartupStage


# Investor Schemas
class InvestorBase(BaseModel):
    """Base investor schema"""
    name: str = Field(..., min_length=1, max_length=255)
    firm_name: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    website: Optional[str] = Field(None, max_length=500)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    min_check_size: Optional[float] = Field(None, ge=0)
    max_check_size: Optional[float] = Field(None, ge=0)


class InvestorCreate(InvestorBase):
    """Schema for creating an investor"""
    user_id: str = Field(..., description="User ID from authentication system")


class InvestorUpdate(BaseModel):
    """Schema for updating an investor"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    firm_name: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    website: Optional[str] = Field(None, max_length=500)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    min_check_size: Optional[float] = Field(None, ge=0)
    max_check_size: Optional[float] = Field(None, ge=0)


class InvestorSchema(InvestorBase):
    """Schema for investor response"""
    id: UUID
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Investor Preference Schemas
class InvestorPreferenceBase(BaseModel):
    """Base investor preference schema"""
    industry_id: Optional[UUID] = None
    stage: Optional[StartupStage] = None
    ticket_min: Optional[float] = Field(None, ge=0)
    ticket_max: Optional[float] = Field(None, ge=0)
    weight: float = Field(default=1.0, ge=0, le=10)


class InvestorPreferenceCreate(InvestorPreferenceBase):
    """Schema for creating an investor preference"""
    investor_id: UUID


class InvestorPreferenceUpdate(BaseModel):
    """Schema for updating an investor preference"""
    industry_id: Optional[UUID] = None
    stage: Optional[StartupStage] = None
    ticket_min: Optional[float] = Field(None, ge=0)
    ticket_max: Optional[float] = Field(None, ge=0)
    weight: Optional[float] = Field(None, ge=0, le=10)


class InvestorPreferenceSchema(InvestorPreferenceBase):
    """Schema for investor preference response"""
    id: UUID
    investor_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvestorWithPreferences(InvestorSchema):
    """Schema for investor with preferences"""
    preferences: List[InvestorPreferenceSchema] = []
