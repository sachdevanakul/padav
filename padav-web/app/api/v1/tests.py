from typing import List

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, TestServiceDep
from app.core.rate_limit import write_rate_limit
from app.schemas.question import QuestionPublic
from app.schemas.test import (
    AnswerSubmit,
    AttemptDetail,
    AttemptSummary,
    ReviewItem,
    SubmitResult,
    TestOut,
    TestStartResponse,
)

router = APIRouter(prefix="/tests", tags=["tests"])


@router.get("", response_model=List[TestOut])
@router.get("/", response_model=List[TestOut], include_in_schema=False)
def list_tests(service: TestServiceDep, exam_id: str | None = None):
    return service.list_tests(exam_id)


# NOTE: the static "/attempts" routes must be declared before "/{test_id}",
# otherwise "attempts" is captured as a test id.
@router.get("/attempts", response_model=List[AttemptSummary])
def list_my_attempts(current_user: CurrentUser, service: TestServiceDep):
    return service.list_attempts(current_user)


@router.get("/attempts/{attempt_id}", response_model=AttemptDetail)
def get_attempt(attempt_id: str, current_user: CurrentUser, service: TestServiceDep):
    return service.detail(current_user, attempt_id)


@router.get("/attempts/{attempt_id}/questions", response_model=List[QuestionPublic])
def get_attempt_questions(attempt_id: str, current_user: CurrentUser, service: TestServiceDep):
    """Questions of an open attempt (no answers)."""
    return service.attempt_questions(current_user, attempt_id)


@router.get("/attempts/{attempt_id}/review", response_model=List[ReviewItem])
def get_attempt_review(attempt_id: str, current_user: CurrentUser, service: TestServiceDep):
    """Answer key and explanations; available only after submission."""
    return service.review(current_user, attempt_id)


@router.put("/attempts/{attempt_id}/answers", dependencies=[Depends(write_rate_limit)])
def save_answer(attempt_id: str, answer: AnswerSubmit, current_user: CurrentUser, service: TestServiceDep):
    service.save_answer(current_user, attempt_id, answer)
    return {"message": "Answer saved"}


@router.post("/attempts/{attempt_id}/submit", response_model=SubmitResult)
def submit_test(attempt_id: str, current_user: CurrentUser, service: TestServiceDep):
    return service.submit(current_user, attempt_id)


@router.get("/{test_id}", response_model=TestOut)
def get_test(test_id: str, service: TestServiceDep):
    return service.get_test(test_id)


@router.post("/{test_id}/start", response_model=TestStartResponse, dependencies=[Depends(write_rate_limit)])
def start_test(test_id: str, current_user: CurrentUser, service: TestServiceDep):
    return service.start(current_user, test_id)
