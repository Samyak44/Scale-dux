"""Startup model"""

from sqlalchemy import String, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
import enum

from .base import Base, TimestampMixin, UUIDMixin


class StartupStage(str, enum.Enum):
    """Startup maturity stages"""
    IDEA = "idea"
    MVP_NO_TRACTION = "mvp_no_traction"
    MVP_EARLY_TRACTION = "mvp_early_traction"
    GROWTH = "growth"
    SCALE = "scale"


class Startup(Base, UUIDMixin, TimestampMixin):
    """Startup entity"""

    __tablename__ = "startups"

    # User from external auth backend
    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="User ID from external authentication system"
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[StartupStage] = mapped_column(
        SQLEnum(StartupStage),
        nullable=False,
        default=StartupStage.IDEA
    )

    # Relationships
    assessments: Mapped[List["Assessment"]] = relationship(
        "Assessment",
        back_populates="startup",
        cascade="all, delete-orphan"
    )

    answers: Mapped[List["StartupAnswer"]] = relationship(
        "StartupAnswer",
        back_populates="startup",
        cascade="all, delete-orphan"
    )

    score: Mapped["StartupScore"] = relationship(
        "StartupScore",
        back_populates="startup",
        uselist=False,
        cascade="all, delete-orphan"
    )

    matches: Mapped[List["StartupInvestorMatch"]] = relationship(
        "StartupInvestorMatch",
        back_populates="startup",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Startup(id={self.id}, name='{self.name}', stage={self.stage})>"
