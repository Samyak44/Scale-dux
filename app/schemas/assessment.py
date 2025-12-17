"""Assessment schemas for API requests and responses"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.assessment import AssessmentStatus, ScoreBand
from app.models.startup import StartupStage


class AssessmentBase(BaseModel):
    """Base assessment schema"""
    stage: StartupStage
    framework_version: str = "1.0.0"


class AssessmentCreate(AssessmentBase):
    """Schema for creating an assessment"""
    startup_id: UUID


class AssessmentUpdate(BaseModel):
    """Schema for updating an assessment"""
    stage: Optional[StartupStage] = None
    status: Optional[AssessmentStatus] = None
    responses: Optional[Dict[str, Any]] = None


class AssessmentSchema(AssessmentBase):
    """Schema for assessment response"""
    id: UUID
    startup_id: UUID
    status: AssessmentStatus
    computed_score: Optional[int] = None
    score_band: Optional[ScoreBand] = None
    responses: Dict[str, Any] = {}
    score_metadata: Optional[Dict[str, Any]] = None
    last_calculated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssessmentWithStartup(AssessmentSchema):
    """Schema for assessment with startup details"""
    startup_name: Optional[str] = None
