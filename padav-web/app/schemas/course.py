from datetime import datetime
from typing import List, Optional

from app.schemas.base import ORMModel


class CourseBase(ORMModel):
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


class LessonSummary(ORMModel):
    """Listing view: no body or video URL, so locked content cannot leak via the outline."""

    id: str
    chapter_id: str
    title: str
    title_hi: Optional[str] = None
    sort_order: int = 0
    is_free: bool = True
    video_duration_seconds: Optional[int] = None


class ChapterOut(ORMModel):
    id: str
    course_id: str
    title: str
    title_hi: Optional[str] = None
    description: Optional[str] = None
    description_hi: Optional[str] = None
    sort_order: int = 0
    lessons: List[LessonSummary] = []


class LessonOut(LessonSummary):
    content: Optional[str] = None
    content_hi: Optional[str] = None
    video_url: Optional[str] = None
    is_active: bool
    created_at: datetime
