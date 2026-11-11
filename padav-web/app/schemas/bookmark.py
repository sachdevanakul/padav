from datetime import datetime
from typing import Optional

from pydantic import Field, model_validator

from app.schemas.base import ORMModel, StrictInput


class BookmarkCreate(StrictInput):
    question_id: Optional[str] = Field(default=None, max_length=36)
    lesson_id: Optional[str] = Field(default=None, max_length=36)

    @model_validator(mode="after")
    def _exactly_one_target(self):
        if bool(self.question_id) == bool(self.lesson_id):
            raise ValueError("Provide exactly one of question_id or lesson_id")
        return self


class BookmarkOut(ORMModel):
    id: str
    user_id: str
    question_id: Optional[str] = None
    lesson_id: Optional[str] = None
    created_at: datetime
