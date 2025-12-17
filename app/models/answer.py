"""Startup answer model for storing assessment responses"""

from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, GUID, TimestampMixin, UUIDMixin


class StartupAnswer(Base, UUIDMixin, TimestampMixin):
    """
    Stores startup responses to assessment questions

    Uses a polymorphic approach with nullable columns to handle different answer types:
    - number: stored in answer_number
    - boolean: stored in answer_number (0/1)
    - enum: stored via selected_option_id FK
    - text: stored in answer_text

    The UNIQUE constraint ensures one answer per startup per question.
    """

    __tablename__ = "startup_answers"

    # Foreign Keys
    startup_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("startups.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    question_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Polymorphic answer fields (only one should be populated based on question.answer_type)
    answer_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Used for text-type answers"
    )

    answer_number: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Used for number and boolean (0/1) answers"
    )

    selected_option_id: Mapped[Optional[UUID]] = mapped_column(
        GUID(),
        ForeignKey("question_options.id", ondelete="SET NULL"),
        nullable=True,
        comment="Used for enum-type answers"
    )

    # Relationships
    startup: Mapped["Startup"] = relationship(
        "Startup",
        back_populates="answers"
    )

    question: Mapped["Question"] = relationship(
        "Question",
        back_populates="answers"
    )

    selected_option: Mapped[Optional["QuestionOption"]] = relationship(
        "QuestionOption",
        back_populates="selected_answers"
    )

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint(
            'startup_id',
            'question_id',
            name='uq_startup_question'
        ),
        Index('ix_startup_answers_startup_question', 'startup_id', 'question_id'),
    )

    def __repr__(self) -> str:
        return (
            f"<StartupAnswer(id={self.id}, startup_id={self.startup_id}, "
            f"question_id={self.question_id})>"
        )

    @property
    def display_value(self) -> str:
        """Get the answer value in a human-readable format"""
        if self.answer_text is not None:
            return self.answer_text
        elif self.answer_number is not None:
            return str(self.answer_number)
        elif self.selected_option is not None:
            return self.selected_option.value
        return "N/A"
