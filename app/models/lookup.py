"""Lookup tables for normalization"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from .base import Base, TimestampMixin, UUIDMixin


class Industry(Base, UUIDMixin, TimestampMixin):
    """Industry/sector classification"""

    __tablename__ = "industries"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True
    )

    # Relationships
    investor_preferences: Mapped[List["InvestorPreference"]] = relationship(
        "InvestorPreference",
        back_populates="industry",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Industry(id={self.id}, name='{self.name}')>"
