import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, Integer, ForeignKey, Boolean, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.lesson import Lesson
    from app.models.question_option import QuestionOption
    from app.models.test_answer import TestAnswer


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)
    subject_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_hi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation_hi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="easy")  # easy, medium, hard
    marks: Mapped[float] = mapped_column(default=1.0)
    negative_marks: Mapped[float] = mapped_column(default=0.0)
    correct_option_key: Mapped[str] = mapped_column(String(10), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    lesson: Mapped[Optional["Lesson"]] = relationship("Lesson", back_populates="questions")
    options: Mapped[List["QuestionOption"]] = relationship(
        "QuestionOption", back_populates="question", cascade="all, delete-orphan"
    )
    test_answers: Mapped[List["TestAnswer"]] = relationship("TestAnswer", back_populates="question")