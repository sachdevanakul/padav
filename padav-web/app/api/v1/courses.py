from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import joinedload
from typing import List

from app.core.dependencies import DbSession
from app.models.course import Course
from app.models.chapter import Chapter
from app.schemas.course import CourseOut

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=List[CourseOut])
@router.get("/", response_model=List[CourseOut], include_in_schema=False)
def list_courses(db: DbSession, subject_id: str | None = None):
    """List courses, optionally filtered by subject."""
    query = db.query(Course).filter(Course.is_active == True)
    if subject_id:
        query = query.filter(Course.subject_id == subject_id)
    return query.all()


@router.get("/{course_id}", response_model=CourseOut)
def get_course(course_id: str, db: DbSession):
    """Get a single course by ID."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/{course_id}/chapters")
def get_course_chapters(course_id: str, db: DbSession):
    """Get chapters for a course with lessons."""
    chapters = (
        db.query(Chapter)
        .filter(Chapter.course_id == course_id, Chapter.is_active == True)
        .options(joinedload(Chapter.lessons))
        .order_by(Chapter.sort_order)
        .all()
    )
    return chapters


