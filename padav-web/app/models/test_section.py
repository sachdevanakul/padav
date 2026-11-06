import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.test import Test
    from app.models.question import Question


class TestSection(Base):
    __tablename__ = "test_sections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    test_id: Mapped[str] = mapped_column(String(36), ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_hi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subject_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    marks_per_question: Mapped[float] = mapped_column(default=1.0)
    negative_marks: Mapped[float] = mapped_column(default=0.0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    test: Mapped["Test"] = relationship("Test", back_populates="sections")