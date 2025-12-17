"""Startup-investor matching system"""

from uuid import UUID

from sqlalchemy import ForeignKey, Index, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, GUID, TimestampMixin, UUIDMixin


class StartupInvestorMatch(Base, UUIDMixin, TimestampMixin):
    """
    Stores computed matches between startups and investors

    This table serves as a cache for ML-based or rule-based matching results.
    Benefits:
    - A/B testing: Compare different matching algorithms
    - Manual override: Allow manual match curation
    - Explainability: Store reasoning for each match
    - Performance: Avoid recalculating matches on every query
    - Audit trail: Track match history and changes

    The UNIQUE constraint ensures one match record per startup-investor pair.
    """

    __tablename__ = "startup_investor_matches"

    # Foreign Keys
    startup_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("startups.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    investor_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("investors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Match score and reasoning
    match_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        index=True,
        comment="Computed match score (0-100 or normalized 0-1)"
    )

    match_reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Explainability: Why this match was made (for investor transparency)"
    )

    # Optional metadata for algorithm tracking
    algorithm_version: Mapped[str] = mapped_column(
        nullable=True,
        comment="Version/ID of matching algorithm used"
    )

    is_manual_override: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        comment="Whether this match was manually curated vs algorithmically generated"
    )

    # Relationships
    startup: Mapped["Startup"] = relationship(
        "Startup",
        back_populates="matches"
    )

    investor: Mapped["Investor"] = relationship(
        "Investor",
        back_populates="matches"
    )

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint(
            'startup_id',
            'investor_id',
            name='uq_startup_investor_match'
        ),
        Index('ix_matches_startup_score', 'startup_id', 'match_score'),
        Index('ix_matches_investor_score', 'investor_id', 'match_score'),
        Index('ix_matches_score', 'match_score'),
    )

    def __repr__(self) -> str:
        return (
            f"<StartupInvestorMatch(id={self.id}, startup_id={self.startup_id}, "
            f"investor_id={self.investor_id}, score={self.match_score})>"
        )
