from datetime import date

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import and_

from app.core.dependencies import CurrentUser, DbSession
from app.models.planner_block import PlannerBlock
from app.schemas.planner import PlannerBlockCreate, PlannerBlockOut, PlannerBlockUpdate

router = APIRouter(prefix="/planner", tags=["planner"])


@router.get("", response_model=list[PlannerBlockOut])
def list_blocks(
    current_user: CurrentUser,
    db: DbSession,
    start_date: date = Query(...),
    end_date: date = Query(...),
):
    if end_date < start_date or (end_date - start_date).days > 41:
        raise HTTPException(status_code=400, detail="Date range must be ordered and no longer than six weeks")
    return (
        db.query(PlannerBlock)
        .filter(
            PlannerBlock.user_id == current_user.id,
            PlannerBlock.study_date >= start_date,
            PlannerBlock.study_date <= end_date,
        )
        .order_by(PlannerBlock.study_date, PlannerBlock.start_time)
        .all()
    )


@router.post("", response_model=PlannerBlockOut, status_code=status.HTTP_201_CREATED)
def create_block(payload: PlannerBlockCreate, current_user: CurrentUser, db: DbSession):
    overlap = db.query(PlannerBlock).filter(
        PlannerBlock.user_id == current_user.id,
        PlannerBlock.study_date == payload.study_date,
        and_(PlannerBlock.start_time < payload.end_time, PlannerBlock.end_time > payload.start_time),
    ).first()
    if overlap:
        raise HTTPException(status_code=409, detail="This session overlaps another planned session")
    block = PlannerBlock(user_id=current_user.id, **payload.model_dump())
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


@router.patch("/{block_id}", response_model=PlannerBlockOut)
def update_block(block_id: str, payload: PlannerBlockUpdate, current_user: CurrentUser, db: DbSession):
    block = db.query(PlannerBlock).filter(
        PlannerBlock.id == block_id, PlannerBlock.user_id == current_user.id
    ).first()
    if not block:
        raise HTTPException(status_code=404, detail="Planned session not found")
    block.completed = payload.completed
    db.commit()
    db.refresh(block)
    return block


@router.delete("/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_block(block_id: str, current_user: CurrentUser, db: DbSession):
    block = db.query(PlannerBlock).filter(
        PlannerBlock.id == block_id, PlannerBlock.user_id == current_user.id
    ).first()
    if not block:
        raise HTTPException(status_code=404, detail="Planned session not found")
    db.delete(block)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
