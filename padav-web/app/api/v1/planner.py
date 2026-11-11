from datetime import date

from fastapi import APIRouter, Query, Response, status

from app.core.dependencies import CurrentUser, PlannerServiceDep
from app.schemas.planner import PlannerBlockCreate, PlannerBlockOut, PlannerBlockUpdate

router = APIRouter(prefix="/planner", tags=["planner"])


@router.get("", response_model=list[PlannerBlockOut])
def list_blocks(
    current_user: CurrentUser,
    service: PlannerServiceDep,
    start_date: date = Query(...),
    end_date: date = Query(...),
):
    return service.list_range(current_user, start_date, end_date)


@router.post("", response_model=PlannerBlockOut, status_code=status.HTTP_201_CREATED)
def create_block(payload: PlannerBlockCreate, current_user: CurrentUser, service: PlannerServiceDep):
    return service.create(current_user, payload)


@router.patch("/{block_id}", response_model=PlannerBlockOut)
def update_block(block_id: str, payload: PlannerBlockUpdate, current_user: CurrentUser, service: PlannerServiceDep):
    return service.set_completed(current_user, block_id, payload.completed)


@router.delete("/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_block(block_id: str, current_user: CurrentUser, service: PlannerServiceDep):
    service.delete(current_user, block_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
