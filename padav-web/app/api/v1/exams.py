from fastapi import APIRouter, HTTPException
from typing import List

from app.core.dependencies import DbSession
from app.models.exam import Exam
from app.schemas.exam import ExamOut

router = APIRouter(prefix="/exams", tags=["exams"])


@router.get("", response_model=List[ExamOut])
@router.get("/", response_model=List[ExamOut], include_in_schema=False)
def list_exams(db: DbSession):
    """List all active exams."""
    return db.query(Exam).filter(Exam.is_active == True).all()


@router.get("/{exam_id}", response_model=ExamOut)
def get_exam(exam_id: str, db: DbSession):
    """Get a single exam by ID."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam
