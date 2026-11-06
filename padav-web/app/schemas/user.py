from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserProfileBase(BaseModel):
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    education_level: Optional[str] = None
    target_exams: Optional[str] = None
    study_goal_hours_per_week: Optional[int] = 10


class UserProfileOut(UserProfileBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserExamBase(BaseModel):
    exam_id: str
    is_primary: bool = False


class UserExamCreate(UserExamBase):
    pass


class UserExamOut(UserExamBase):
    id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True