from typing import List

from fastapi import APIRouter

from app.core.dependencies import CatalogServiceDep
from app.schemas.course import ChapterOut, CourseOut

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=List[CourseOut])
@router.get("/", response_model=List[CourseOut], include_in_schema=False)
def list_courses(service: CatalogServiceDep, subject_id: str | None = None):
    return service.list_courses(subject_id)


@router.get("/{course_id}", response_model=CourseOut)
def get_course(course_id: str, service: CatalogServiceDep):
    return service.get_course(course_id)


@router.get("/{course_id}/chapters", response_model=List[ChapterOut])
def get_course_chapters(course_id: str, service: CatalogServiceDep):
    """Course outline (lesson titles only; bodies come from /lessons/{id})."""
    return service.get_chapters(course_id)
