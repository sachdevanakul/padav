from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CourseBase(BaseModel):
    subject_id: str
    title: str
    title_hi: Optional[str] = None
    description: Optional[str] = None
    description_hi: Optional[str] = None
    instructor: Optional[str] = None
    level: str = "beginner"
    estimated_hours: Optional[float] = None
    thumbnail_url: Optional[str] = None
    is_free: bool = True


class CourseOut(CourseBase):
    id: str
    total_lessons: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LessonBase(BaseModel):
    chapter_id: str
    title: str
    title_hi: Optional[str] = None
    content: Optional[str] = None
    content_hi: Optional[str] = None
    video_url: Optional[str] = None
    video_duration_seconds: Optional[int] = None
    sort_order: int = 0
    is_free: bool = True


class LessonOut(LessonBase):
    id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True