"""
Pydantic schemas for scoring engine

Type-safe data structures for scoring calculations with strict validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


class EvidenceType(str, Enum):
    """Evidence quality levels"""
    SELF_REPORTED = "self_reported"
    DOCUMENT_UPLOADED = "document_uploaded"
    LINKEDIN_VERIFIED = "linkedin_verified"
    REFERENCE_CHECK = "reference_check"
    CA_VERIFIED = "ca_verified"


class AnswerCorrectness(str, Enum):
    """Answer quality levels"""
    CORRECT = "correct"           # 1.0
    PARTIAL = "partial"           # 0.5
    INCORRECT = "incorrect"       # 0.0


class StartupStage(str, Enum):
    """Startup maturity stages"""
    IDEA = "idea"
    MVP_NO_TRACTION = "mvp_no_traction"
    MVP_EARLY_TRACTION = "mvp_early_traction"
    GROWTH = "growth"
    SCALE = "scale"


class KPIResponse(BaseModel):
    """Single KPI response with evidence"""

    model_config = ConfigDict(from_attributes=True)

    value: Any = Field(..., description="User's answer to the KPI question")
    evidence_type: EvidenceType = Field(
        default=EvidenceType.SELF_REPORTED,
        description="Quality of evidence provided"
    )
    evidence_id: Optional[UUID] = Field(
        default=None,
        description="Reference to uploaded document if applicable"
    )
    answered_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of response"
    )
    correctness: Optional[AnswerCorrectness] = Field(
        default=None,
        description="Evaluated correctness (computed during scoring)"
    )


class KPIScore(BaseModel):
    """Calculated score for a single KPI"""

    model_config = ConfigDict(from_attributes=True)

    kpi_id: str
    base_weight: float = Field(..., ge=0.0, le=1.0)
    correctness_multiplier: float = Field(..., ge=0.0, le=1.0)
    evidence_multiplier: float = Field(..., ge=0.0, le=1.0)
    decay_multiplier: float = Field(..., ge=0.0, le=1.0)
    earned_value: float = Field(..., ge=0.0)
    max_possible: float = Field(..., ge=0.0)

    @field_validator('earned_value', 'max_possible')
    @classmethod
    def validate_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Score values must be non-negative")
        return v


class SubCategoryScore(BaseModel):
    """Aggregated score for a sub-category"""

    model_config = ConfigDict(from_attributes=True)

    sub_category_id: str
    weight: float = Field(..., ge=0.0, le=1.0)
    kpi_scores: List[KPIScore]
    total_earned: float = Field(..., ge=0.0)
    total_possible: float = Field(..., ge=0.0)
    normalized_score: float = Field(..., ge=0.0,
                                    le=1.0, description="earned/possible")
    kpis_completed: int = Field(..., ge=0)
    kpis_total: int = Field(..., ge=0)


class CategoryScore(BaseModel):
    """Aggregated score for a category"""

    model_config = ConfigDict(from_attributes=True)

    category_id: str
    stage_weight: float = Field(..., ge=0.0, le=1.0)
    sub_category_scores: List[SubCategoryScore]
    raw_score: float = Field(..., ge=0.0, le=1.0)
    capped_score: float = Field(..., ge=0.0, le=1.0)
    weighted_contribution: float = Field(..., ge=0.0)
    max_possible_contribution: float = Field(..., ge=0.0)
    applied_cap: Optional[float] = Field(default=None)
    cap_reason: Optional[str] = Field(default=None)


class FatalFlag(BaseModel):
    """Triggered fatal flag with penalty details"""

    model_config = ConfigDict(from_attributes=True)

    flag_id: str
    trigger_kpi: str
    penalty_points: int = Field(..., ge=0)
    global_cap: Optional[int] = Field(default=None)
    severity: Literal["warning", "critical"]
    reason: str
    user_message: str


class DependencyViolation(BaseModel):
    """Cross-category dependency violation"""

    model_config = ConfigDict(from_attributes=True)

    dependency_rule_id: str
    source_kpi: str
    target_category: str
    action: Literal["apply_cap", "trigger_flag", "reduce_confidence"]
    cap_value: Optional[float] = Field(default=None)
    reason: str


class ScoreBreakdown(BaseModel):
    """
    Complete explainability payload

    This is the "Glass Box" - full transparency of calculation.
    """

    model_config = ConfigDict(from_attributes=True)

    final_score: int = Field(..., ge=300, le=900)
    score_band: str
    raw_score: float = Field(..., ge=0.0, le=1.0)
    framework_version: str

    # Category-level breakdown
    category_scores: List[CategoryScore]

    # Penalties and caps
    fatal_flags_triggered: List[FatalFlag]
    total_penalty_points: int = Field(default=0, ge=0)
    global_cap_applied: Optional[int] = Field(default=None)

    # Dependencies
    dependency_violations: List[DependencyViolation]

    # Actionable insights
    gaps: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Missing or low-scoring KPIs"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Specific actions to improve score"
    )

    # Metadata
    calculation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    calculation_duration_ms: Optional[int] = Field(default=None)


class AssessmentRequest(BaseModel):
    """Request to create or update assessment"""

    model_config = ConfigDict(from_attributes=True)

    startup_id: UUID
    stage: StartupStage
    framework_version: str = "1.0.0"


class KPIResponseUpdate(BaseModel):
    """Update a single KPI response"""

    model_config = ConfigDict(from_attributes=True)

    kpi_id: str = Field(..., min_length=1, max_length=100)
    value: Any
    evidence_type: EvidenceType = EvidenceType.SELF_REPORTED
    evidence_id: Optional[UUID] = None


class ScoreResponse(BaseModel):
    """API response with score and breakdown"""

    model_config = ConfigDict(from_attributes=True)

    assessment_id: UUID
    startup_id: UUID
    status: str
    score: Optional[int] = None
    score_band: Optional[str] = None
    breakdown: Optional[ScoreBreakdown] = None
    is_draft: bool = Field(
        default=True,
        description="True for preview, False for published snapshot"
    )
    published_at: Optional[datetime] = None
