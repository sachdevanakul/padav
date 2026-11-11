from datetime import datetime
from typing import Optional

from app.schemas.base import ORMModel


class ExamBase(ORMModel):
    name: str
    name_hi: Optional[str] = None
    code: str
    description: Optional[str] = None
    description_hi: Optional[str] = None
    category: str


class ExamOut(ExamBase):
    id: str
    is_active: bool
    created_at: datetime
