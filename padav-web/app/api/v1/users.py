from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.dependencies import CurrentUser, UserServiceDep
from app.schemas.auth import UserOut, UserUpdate
from app.schemas.user import UserExamCreate, UserExamOut, UserProfileOut, UserProfileUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: CurrentUser):
    return current_user


@router.put("/me", response_model=UserOut)
def update_me(user_in: UserUpdate, current_user: CurrentUser, service: UserServiceDep):
    return service.update_me(current_user, user_in)


@router.get("/me/profile", response_model=UserProfileOut)
def get_my_profile(current_user: CurrentUser, service: UserServiceDep):
    return service.get_profile(current_user)


@router.put("/me/profile", response_model=UserProfileOut)
def update_my_profile(profile_in: UserProfileUpdate, current_user: CurrentUser, service: UserServiceDep):
    return service.update_profile(current_user, profile_in)


@router.get("/me/exams", response_model=List[UserExamOut])
def get_my_exams(current_user: CurrentUser, service: UserServiceDep):
    return service.list_exams(current_user)


@router.post("/me/exams", response_model=UserExamOut)
def add_my_exam(exam_in: UserExamCreate, current_user: CurrentUser, service: UserServiceDep):
    return service.add_exam(current_user, exam_in)


@router.delete("/me/exams/{exam_id}")
def remove_my_exam(exam_id: str, current_user: CurrentUser, service: UserServiceDep):
    service.remove_exam(current_user, exam_id)
    return {"message": "Exam removed"}
