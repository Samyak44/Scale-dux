"""Question and answer option models for the assessment system"""

import enum
from typing import List, Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, GUID, TimestampMixin, UUIDMixin


class AnswerType(str, enum.Enum):
    """Supported answer types for questions"""
    NUMBER = "number"
    BOOLEAN = "boolean"
    ENUM = "enum"
    TEXT = "text"


class QuestionCategory(str, enum.Enum):
    """Question categories aligned with scoring categories"""
    TRACTION = "traction"
    TEAM = "team"
    FINANCE = "finance"
    MARKET = "market"


class Question(Base, UUIDMixin, TimestampMixin):
    """
    Master table for all assessment questions

    Normalized and reusable across different assessment contexts.
    Questions can be versioned and activated/deactivated without affecting historical data.
    """

    __tablename__ = "questions"

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The question text displayed to users"
    )

    category: Mapped[QuestionCategory] = mapped_column(
        SQLEnum(QuestionCategory),
        nullable=False,
        index=True,
        comment="Primary category: traction, team, finance, or market"
    )

    answer_type: Mapped[AnswerType] = mapped_column(
        SQLEnum(AnswerType),
        nullable=False,
        comment="Expected answer format: number, boolean, enum, or text"
    )

    base_weight: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=1.0,
        comment="Base scoring weight for this question"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether this question is currently active in assessments"
    )

    # Optional metadata
    help_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional guidance or explanation for the question"
    )

    # Relationships
    options: Mapped[List["QuestionOption"]] = relationship(
        "QuestionOption",
        back_populates="question",
        cascade="all, delete-orphan"
    )

    answers: Mapped[List["StartupAnswer"]] = relationship(
        "StartupAnswer",
        back_populates="question",
        cascade="all, delete-orphan"
    )

    scoring_rules: Mapped[List["ScoringRule"]] = relationship(
        "ScoringRule",
        back_populates="question",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Question(id={self.id}, category={self.category}, text='{self.text[:50]}...')>"


class QuestionOption(Base, UUIDMixin, TimestampMixin):
    """
    Answer options for multiple-choice/enum questions

    Stores predefined options with associated scoring weights.
    Only relevant for questions with answer_type='enum'.
    """

    __tablename__ = "question_options"

    question_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The option text/value"
    )

    score_weight: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=1.0,
        comment="Scoring multiplier for this option"
    )

    display_order: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="Optional ordering for display"
    )

    # Relationships
    question: Mapped["Question"] = relationship(
        "Question",
        back_populates="options"
    )

    selected_answers: Mapped[List["StartupAnswer"]] = relationship(
        "StartupAnswer",
        back_populates="selected_option"
    )

    def __repr__(self) -> str:
        return f"<QuestionOption(id={self.id}, value='{self.value}', weight={self.score_weight})>"
