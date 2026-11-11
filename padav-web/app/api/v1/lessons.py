from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.dependencies import CatalogServiceDep, OptionalUser
from app.schemas.course import LessonOut

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/{lesson_id}", response_model=LessonOut)
def get_lesson(lesson_id: str, service: CatalogServiceDep, viewer: OptionalUser):
    return service.get_lesson(lesson_id, viewer)
