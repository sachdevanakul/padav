import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, Integer, ForeignKey, Boolean, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.subject import Subject
    from app.models.chapter import Chapter


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    title_hi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_hi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instructor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    level: Mapped[str] = mapped_column(String(50), default="beginner")  # beginner, intermediate, advanced
    total_lessons: Mapped[int] = mapped_column(Integer, default=0)
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    subject: Mapped["Subject"] = relationship("Subject", back_populates="courses")
    chapters: Mapped[List["Chapter"]] = relationship("Chapter", back_populates="course", cascade="all, delete-orphan")