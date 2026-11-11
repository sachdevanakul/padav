from typing import List

from fastapi import APIRouter

from app.core.dependencies import AnalyticsServiceDep, CurrentUser
from app.schemas.analytics import AnalyticsOverview, SubjectPerformance, TrendPoint

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def get_overview(current_user: CurrentUser, service: AnalyticsServiceDep):
    return service.overview(current_user)


@router.get("/subjects", response_model=List[SubjectPerformance])
def get_subject_performance(current_user: CurrentUser, service: AnalyticsServiceDep):
    return service.subjects(current_user)


@router.get("/trends", response_model=List[TrendPoint])
def get_trends(current_user: CurrentUser, service: AnalyticsServiceDep):
    return service.trends(current_user)
