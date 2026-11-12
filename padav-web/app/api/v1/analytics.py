from typing import List

from fastapi import APIRouter, Query

from app.core.dependencies import AnalyticsServiceDep, CurrentUser
from app.schemas.analytics import AnalyticsOverview, SubjectPerformance, TrendPoint

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def get_overview(
    current_user: CurrentUser,
    service: AnalyticsServiceDep,
    tz_offset: int = Query(0, ge=-840, le=840, description="Minutes east of UTC, e.g. 330 for India"),
):
    return service.overview(current_user, tz_offset)


@router.get("/subjects", response_model=List[SubjectPerformance])
def get_subject_performance(current_user: CurrentUser, service: AnalyticsServiceDep):
    return service.subjects(current_user)


@router.get("/trends", response_model=List[TrendPoint])
def get_trends(current_user: CurrentUser, service: AnalyticsServiceDep):
    return service.trends(current_user)
