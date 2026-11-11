from typing import List

from fastapi import APIRouter

from app.core.dependencies import CatalogServiceDep
from app.schemas.exam import ExamOut

router = APIRouter(prefix="/exams", tags=["exams"])


@router.get("", response_model=List[ExamOut])
@router.get("/", response_model=List[ExamOut], include_in_schema=False)
def list_exams(service: CatalogServiceDep):
    return service.list_exams()


@router.get("/{exam_id}", response_model=ExamOut)
def get_exam(exam_id: str, service: CatalogServiceDep):
    return service.get_exam(exam_id)
