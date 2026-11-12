from typing import List

from fastapi import APIRouter, Depends, Response, status

from app.core.exceptions import NotFoundError
from app.core.dependencies import CurrentUser, PiaServiceDep
from app.core.rate_limit import write_rate_limit
from app.schemas.pia import (
    AnswerIn, AnswerOut, BlueprintOut, ConsentIn, ConsentOut, EventIn, PiaItemPublic, ReportOut,
    SessionCreate, SessionOut,
)
from app.services.pia_blueprint import DOMAINS

router = APIRouter(prefix="/pia", tags=["pia"])


def _domain(domain: str) -> str:
    if domain not in DOMAINS:
        raise NotFoundError.for_resource("Subtest")
    return domain


@router.get("/blueprint", response_model=BlueprintOut)
def blueprint(service: PiaServiceDep):
    return service.blueprint()


@router.post("/consent", response_model=ConsentOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(write_rate_limit)])
def give_consent(body: ConsentIn, current_user: CurrentUser, service: PiaServiceDep):
    return service.record_consent(current_user, body)


@router.post("/sessions", response_model=SessionOut, dependencies=[Depends(write_rate_limit)])
def start_session(body: SessionCreate, current_user: CurrentUser, service: PiaServiceDep):
    return service.start_session(current_user, body)


@router.get("/sessions/{session_id}", response_model=SessionOut)
def get_session(session_id: str, current_user: CurrentUser, service: PiaServiceDep):
    return service.get_session(current_user, session_id)


@router.post("/sessions/{session_id}/subtests/{domain}/start", response_model=List[PiaItemPublic], dependencies=[Depends(write_rate_limit)])
def start_subtest(session_id: str, domain: str, current_user: CurrentUser, service: PiaServiceDep):
    return service.start_subtest(current_user, session_id, _domain(domain))


@router.get("/sessions/{session_id}/subtests/{domain}/items", response_model=List[PiaItemPublic])
def subtest_items(session_id: str, domain: str, current_user: CurrentUser, service: PiaServiceDep):
    return service.items(current_user, session_id, _domain(domain))


@router.put("/sessions/{session_id}/subtests/{domain}/answers", response_model=AnswerOut, dependencies=[Depends(write_rate_limit)])
def save_answer(session_id: str, domain: str, body: AnswerIn, current_user: CurrentUser, service: PiaServiceDep):
    return service.answer(current_user, session_id, _domain(domain), body)


@router.post("/sessions/{session_id}/subtests/{domain}/events", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(write_rate_limit)])
def subtest_event(session_id: str, domain: str, body: EventIn, current_user: CurrentUser, service: PiaServiceDep):
    service.record_event(current_user, session_id, _domain(domain), body)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/sessions/{session_id}/subtests/{domain}/complete", response_model=SessionOut, dependencies=[Depends(write_rate_limit)])
def complete_subtest(session_id: str, domain: str, current_user: CurrentUser, service: PiaServiceDep):
    return service.complete_subtest(current_user, session_id, _domain(domain))


@router.post("/sessions/{session_id}/finish", response_model=ReportOut, dependencies=[Depends(write_rate_limit)])
def finish(session_id: str, current_user: CurrentUser, service: PiaServiceDep):
    return service.finish(current_user, session_id)


@router.get("/sessions/{session_id}/report", response_model=ReportOut)
def report(session_id: str, current_user: CurrentUser, service: PiaServiceDep):
    return service.get_report(current_user, session_id)
