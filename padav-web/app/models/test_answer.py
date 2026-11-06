import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, ForeignKey, Boolean, DateTime, Integer, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.test_attempt import TestAttempt
    from app.models.question import Question


class TestAnswer(Base):
    __tablename__ = "test_answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    attempt_id: Mapped[str] = mapped_column(String(36), ForeignKey("test_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[str] = mapped_column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    selected_option_key: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    marks_obtained: Mapped[float] = mapped_column(Float, default=0.0)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    answered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    attempt: Mapped["TestAttempt"] = relationship("TestAttempt", back_populates="answers")
    question: Mapped["Question"] = relationship("Question", back_populates="test_answers")