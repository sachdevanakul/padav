"""Schema for importable content files (strictly validated: bad files never half-import)."""
from typing import Dict, List, Literal, Optional

from pydantic import Field, field_validator, model_validator

from app.schemas.base import StrictInput

OptionKey = Literal["a", "b", "c", "d", "e"]


class ContentQuestion(StrictInput):
    subject: str = Field(min_length=1, max_length=255)
    text: str = Field(min_length=1, max_length=5000)
    text_hi: Optional[str] = Field(default=None, max_length=5000)
    options: Dict[OptionKey, str]
    options_hi: Dict[OptionKey, str] = {}
    correct: OptionKey
    explanation: Optional[str] = Field(default=None, max_length=5000)
    explanation_hi: Optional[str] = Field(default=None, max_length=5000)
    difficulty: Literal["easy", "medium", "hard"] = "easy"

    @field_validator("options")
    @classmethod
    def _enough_options(cls, value):
        if len(value) < 2 or any(not text.strip() for text in value.values()):
            raise ValueError("A question needs at least two non-empty options")
        return value

    @model_validator(mode="after")
    def _correct_is_an_option(self):
        if self.correct not in self.options:
            raise ValueError(f"correct option '{self.correct}' is not among the options")
        if not set(self.options_hi) <= set(self.options):
            raise ValueError("options_hi has keys that are not in options")
        return self


class ContentTest(StrictInput):
    title: str = Field(min_length=1, max_length=255)
    title_hi: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    duration_minutes: int = Field(default=30, ge=1, le=360)
    marks_per_question: float = Field(default=1.0, gt=0, le=100)
    negative_marks_per_question: float = Field(default=0.0, ge=0, le=100)
    is_free: bool = True
    questions: List[ContentQuestion] = Field(min_length=1, max_length=500)


class ContentFile(StrictInput):
    exam: str = Field(min_length=1, max_length=50, description="Exam code, e.g. 'ssc-cgl'")
    tests: List[ContentTest] = Field(min_length=1)
