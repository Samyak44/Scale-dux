"""Investor and investor preference models"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import Enum as SQLEnum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, GUID, TimestampMixin, UUIDMixin
from .startup import StartupStage


class Investor(Base, UUIDMixin, TimestampMixin):
    """
    Investor entity

    Stores investor profile information and preferences for matching.
    Can represent individual investors, VC firms, or angel groups.
    """

    __tablename__ = "investors"

    # User from external auth backend
    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        unique=True,
        comment="User ID from external authentication system"
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Investor or firm name"
    )

    # Profile information
    firm_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Investment firm/organization name"
    )

    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Investor bio or description"
    )

    website: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Investor or firm website URL"
    )

    linkedin_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="LinkedIn profile URL"
    )

    # Investment criteria (high-level)
    min_check_size: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Minimum investment amount"
    )

    max_check_size: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Maximum investment amount"
    )

    # Relationships
    preferences: Mapped[List["InvestorPreference"]] = relationship(
        "InvestorPreference",
        back_populates="investor",
        cascade="all, delete-orphan"
    )

    matches: Mapped[List["StartupInvestorMatch"]] = relationship(
        "StartupInvestorMatch",
        back_populates="investor",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Investor(id={self.id}, name='{self.name}', firm='{self.firm_name}')>"


class InvestorPreference(Base, UUIDMixin, TimestampMixin):
    """
    Investor preferences for startup matching

    Allows investors to specify multiple preferences across different dimensions:
    - Industry/sector preferences
    - Stage preferences
    - Ticket size ranges

    Multiple rows per investor enable complex preference modeling.
    """

    __tablename__ = "investor_preferences"

    investor_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("investors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Preference dimensions (all optional to allow flexible combinations)
    industry_id: Mapped[Optional[UUID]] = mapped_column(
        GUID(),
        ForeignKey("industries.id", ondelete="CASCADE"),
        nullable=True,
        comment="Preferred industry/sector"
    )

    stage: Mapped[Optional[StartupStage]] = mapped_column(
        SQLEnum(StartupStage),
        nullable=True,
        comment="Preferred startup stage"
    )

    ticket_min: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Minimum ticket size for this preference"
    )

    ticket_max: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Maximum ticket size for this preference"
    )

    # Weighting and priority
    weight: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=1.0,
        comment="Relative importance of this preference (for scoring)"
    )

    # Relationships
    investor: Mapped["Investor"] = relationship(
        "Investor",
        back_populates="preferences"
    )

    industry: Mapped[Optional["Industry"]] = relationship(
        "Industry",
        back_populates="investor_preferences"
    )

    # Indexes
    __table_args__ = (
        Index('ix_investor_preferences_investor', 'investor_id'),
        Index('ix_investor_preferences_industry', 'industry_id'),
        Index('ix_investor_preferences_stage', 'stage'),
    )

    def __repr__(self) -> str:
        return (
            f"<InvestorPreference(id={self.id}, investor_id={self.investor_id}, "
            f"industry_id={self.industry_id}, stage={self.stage})>"
        )
