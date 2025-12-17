"""Scoring rules and computed scores for startups"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, GUID, TimestampMixin, UUIDMixin


class ScoringRule(Base, UUIDMixin, TimestampMixin):
    """
    Defines scoring rules for questions

    Allows flexible configuration of how answers are converted to scores.
    Supports range-based scoring (e.g., revenue between min/max gets certain weight).
    """

    __tablename__ = "scoring_rules"

    question_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    weight: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=1.0,
        comment="Scoring weight/multiplier for this rule"
    )

    min_value: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Minimum value for range-based scoring (inclusive)"
    )

    max_value: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Maximum value for range-based scoring (inclusive)"
    )

    # Relationships
    question: Mapped["Question"] = relationship(
        "Question",
        back_populates="scoring_rules"
    )

    def __repr__(self) -> str:
        return (
            f"<ScoringRule(id={self.id}, question_id={self.question_id}, "
            f"weight={self.weight}, range=[{self.min_value}, {self.max_value}])>"
        )


class StartupScore(Base, UUIDMixin, TimestampMixin):
    """
    Computed and cached scores for startups

    Cache table that stores aggregated scores to avoid recalculation.
    Updated whenever answers change or scoring rules are modified.
    Includes category breakdowns for explainability.
    """

    __tablename__ = "startup_scores"

    # Use startup_id as primary key for 1:1 relationship
    startup_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("startups.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )

    # Aggregate scores
    total_score: Mapped[float] = mapped_column(
        Numeric(8, 2),
        nullable=False,
        default=0.0,
        index=True,
        comment="Overall computed score"
    )

    traction_score: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        comment="Score for traction category"
    )

    team_score: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        comment="Score for team category"
    )

    finance_score: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        comment="Score for finance category"
    )

    market_score: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        comment="Score for market category"
    )

    # Metadata
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
        comment="Last time scores were recalculated"
    )

    # Relationships
    startup: Mapped["Startup"] = relationship(
        "Startup",
        back_populates="score"
    )

    # Indexes
    __table_args__ = (
        Index('ix_startup_scores_total', 'total_score'),
        Index('ix_startup_scores_updated', 'last_updated_at'),
    )

    def __repr__(self) -> str:
        return (
            f"<StartupScore(startup_id={self.startup_id}, total={self.total_score}, "
            f"updated_at={self.last_updated_at})>"
        )
