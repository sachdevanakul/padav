import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, Integer, ForeignKey, Boolean, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.exam import Exam
    from app.models.test_section import TestSection
    from app.models.test_attempt import TestAttempt


class Test(Base):
    __tablename__ = "tests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exam_id: Mapped[str] = mapped_column(String(36), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    title_hi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_hi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    duration_minutes: Mapped[int] = mapped_column(default=60)
    total_marks: Mapped[float] = mapped_column(default=0.0)
    passing_marks: Mapped[float] = mapped_column(default=0.0)
    negative_marking: Mapped[bool] = mapped_column(default=True)
    marks_per_question: Mapped[float] = mapped_column(default=1.0)
    negative_marks_per_question: Mapped[float] = mapped_column(default=0.0)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    exam: Mapped["Exam"] = relationship("Exam", back_populates="tests")
    sections: Mapped[List["TestSection"]] = relationship("TestSection", back_populates="test", cascade="all, delete-orphan")
    attempts: Mapped[List["TestAttempt"]] = relationship("TestAttempt", back_populates="test")