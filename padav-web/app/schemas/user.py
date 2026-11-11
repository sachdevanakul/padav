import re
from datetime import date, datetime
from typing import Optional

from pydantic import Field, field_validator

from app.schemas.base import ORMModel, StrictInput

_PHONE = re.compile(r"^\+?[0-9 ()\-]{7,20}$")


class UserProfileBase(ORMModel):
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    education_level: Optional[str] = None
    target_exams: Optional[str] = None
    study_goal_hours_per_week: Optional[int] = 10


class UserProfileUpdate(StrictInput):
    phone: Optional[str] = Field(default=None, max_length=20)
    date_of_birth: Optional[str] = Field(default=None, max_length=10)
    education_level: Optional[str] = Field(default=None, max_length=100)
    target_exams: Optional[str] = Field(default=None, max_length=2000)
    study_goal_hours_per_week: Optional[int] = Field(default=None, ge=0, le=168)

    @field_validator("phone")
    @classmethod
    def _phone(cls, value: Optional[str]) -> Optional[str]:
        if value and not _PHONE.match(value):
            raise ValueError("Invalid phone number")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def _dob(cls, value: Optional[str]) -> Optional[str]:
        if value:
            try:
                parsed = date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError("date_of_birth must be YYYY-MM-DD") from exc
            if not date(1900, 1, 1) <= parsed <= date.today():
                raise ValueError("date_of_birth is out of range")
        return value


class UserProfileOut(UserProfileBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class UserExamCreate(StrictInput):
    exam_id: str = Field(min_length=1, max_length=36)
    is_primary: bool = False


class UserExamOut(ORMModel):
    id: str
    user_id: str
    exam_id: str
    is_primary: bool
    created_at: datetime
