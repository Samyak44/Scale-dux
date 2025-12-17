"""Assessment and related models"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
import enum

from sqlalchemy import (
    DateTime, Enum as SQLEnum, ForeignKey, Integer,
    String, Boolean, Float, JSON, Index, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, GUID, TimestampMixin, UUIDMixin
from .startup import StartupStage


class AssessmentStatus(str, enum.Enum):
    """Assessment lifecycle states"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ScoreBand(str, enum.Enum):
    """Score ranges for categorical rating"""
    CRITICAL = "critical"      # 300-400
    POOR = "poor"              # 401-550
    FAIR = "fair"              # 551-680
    GOOD = "good"              # 681-800
    EXCELLENT = "excellent"    # 801-900


class Assessment(Base, UUIDMixin, TimestampMixin):
    """
    Core assessment entity storing startup responses and calculated scores

    Uses JSON for flexible schema to support evolving KPI structures
    without database migrations.
    """

    __tablename__ = "assessments"

    # Foreign Keys
    startup_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("startups.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Assessment Metadata
    stage: Mapped[StartupStage] = mapped_column(
        SQLEnum(StartupStage),
        nullable=False
    )

    framework_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="1.0.0"
    )

    status: Mapped[AssessmentStatus] = mapped_column(
        SQLEnum(AssessmentStatus),
        nullable=False,
        default=AssessmentStatus.DRAFT
    )

    # Scoring Data
    computed_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True  # For sorting/filtering
    )

    score_band: Mapped[Optional[ScoreBand]] = mapped_column(
        SQLEnum(ScoreBand),
        nullable=True
    )

    # JSON Columns (Core Innovation)
    responses: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="KPI responses in format: {kpi_id: {value, evidence_type, evidence_id, answered_at}}"
    )

    score_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=True,
        comment="Explainability payload: category breakdown, penalties, recommendations"
    )

    # Calculation Tracking
    last_calculated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    calculation_duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Performance tracking"
    )

    # Relationships
    startup: Mapped["Startup"] = relationship(
        "Startup",
        back_populates="assessments"
    )

    evidence_uploads: Mapped[List["EvidenceUpload"]] = relationship(
        "EvidenceUpload",
        back_populates="assessment",
        cascade="all, delete-orphan"
    )

    snapshots: Mapped[List["PublishedSnapshot"]] = relationship(
        "PublishedSnapshot",
        back_populates="assessment",
        cascade="all, delete-orphan"
    )

    audit_logs: Mapped[List["CalculationAuditLog"]] = relationship(
        "CalculationAuditLog",
        back_populates="assessment",
        cascade="all, delete-orphan"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_assessment_startup_status', 'startup_id', 'status'),
        Index('ix_assessment_score_band', 'score_band', 'computed_score'),
    )

    def __repr__(self) -> str:
        return (
            f"<Assessment(id={self.id}, startup_id={self.startup_id}, "
            f"score={self.computed_score}, status={self.status})>"
        )


class EvidenceUpload(Base, UUIDMixin, TimestampMixin):
    """
    Document uploads for evidence-based confidence scoring

    Tracks metadata needed for time-decay calculations and verification.
    """

    __tablename__ = "evidence_uploads"

    # Foreign Keys
    assessment_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Evidence Details
    kpi_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="KPI this evidence supports (e.g., 'fc_fulltime_founder')"
    )

    file_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Storage path or S3 URL"
    )

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Verification & Decay
    verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Manual/AI verification status"
    )

    verification_notes: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True
    )

    decay_lambda: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.005,
        comment="Time-decay rate: High volatility = 0.1, Low = 0.001"
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Relationships
    assessment: Mapped["Assessment"] = relationship(
        "Assessment",
        back_populates="evidence_uploads"
    )

    __table_args__ = (
        Index('ix_evidence_assessment_kpi', 'assessment_id', 'kpi_id'),
    )

    def __repr__(self) -> str:
        return (
            f"<EvidenceUpload(id={self.id}, kpi_id='{self.kpi_id}', "
            f"verified={self.verified})>"
        )


class PublishedSnapshot(Base, UUIDMixin, TimestampMixin):
    """
    Bi-monthly frozen score snapshots (1st and 15th)

    Immutable record of published scores for stability and audit trail.
    """

    __tablename__ = "published_snapshots"

    # Foreign Keys
    assessment_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Snapshot Data
    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )

    score_band: Mapped[ScoreBand] = mapped_column(
        SQLEnum(ScoreBand),
        nullable=False
    )

    breakdown: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Full explainability payload at time of snapshot"
    )

    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Should be 1st or 15th of month at midnight UTC"
    )

    framework_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    # Relationships
    assessment: Mapped["Assessment"] = relationship(
        "Assessment",
        back_populates="snapshots"
    )

    __table_args__ = (
        Index('ix_snapshot_published_at', 'published_at'),
        Index('ix_snapshot_assessment_published', 'assessment_id', 'published_at'),
    )

    def __repr__(self) -> str:
        return (
            f"<PublishedSnapshot(id={self.id}, score={self.score}, "
            f"published_at={self.published_at})>"
        )


class CalculationStep(str, enum.Enum):
    """Steps in the scoring pipeline for audit logging"""
    INPUT_VALIDATION = "input_validation"
    LOAD_CONFIG = "load_config"
    RESOLVE_DEPENDENCIES = "resolve_dependencies"
    CALCULATE_KPI_SCORES = "calculate_kpi_scores"
    AGGREGATE_SUBCATEGORIES = "aggregate_subcategories"
    AGGREGATE_CATEGORIES = "aggregate_categories"
    CHECK_FATAL_FLAGS = "check_fatal_flags"
    CALCULATE_FINAL_SCORE = "calculate_final_score"
    GENERATE_EXPLAINABILITY = "generate_explainability"


class CalculationAuditLog(Base, UUIDMixin, TimestampMixin):
    """
    Granular audit trail of scoring calculations

    Enables debugging, dispute resolution, and algorithm improvement.
    """

    __tablename__ = "calculation_audit_logs"

    # Foreign Keys
    assessment_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Log Details
    calculation_step: Mapped[CalculationStep] = mapped_column(
        SQLEnum(CalculationStep),
        nullable=False
    )

    input_values: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Inputs to this calculation step"
    )

    output_values: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Outputs from this calculation step"
    )

    execution_time_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Performance profiling"
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )

    # Relationships
    assessment: Mapped["Assessment"] = relationship(
        "Assessment",
        back_populates="audit_logs"
    )

    __table_args__ = (
        Index('ix_audit_assessment_step', 'assessment_id', 'calculation_step'),
    )

    def __repr__(self) -> str:
        return (
            f"<CalculationAuditLog(id={self.id}, step={self.calculation_step}, "
            f"timestamp={self.timestamp})>"
        )
