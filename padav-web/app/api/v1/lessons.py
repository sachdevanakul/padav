from fastapi import APIRouter, HTTPException

from app.core.dependencies import DbSession
from app.models.lesson import Lesson
from app.schemas.course import LessonOut

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/{lesson_id}", response_model=LessonOut)
def get_lesson(lesson_id: str, db: DbSession):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id, Lesson.is_active.is_(True)).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson
