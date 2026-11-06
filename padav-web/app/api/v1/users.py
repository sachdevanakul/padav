from fastapi import APIRouter, HTTPException
from typing import List

from app.core.dependencies import DbSession, CurrentUser
from app.models.user_profile import UserProfile
from app.models.user_exam import UserExam
from app.models.exam import Exam
from app.schemas.auth import UserOut, UserUpdate
from app.schemas.user import UserProfileOut, UserExamOut, UserExamCreate, UserProfileBase

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: CurrentUser):
    """Get current user profile."""
    return current_user


@router.put("/me", response_model=UserOut)
def update_me(
    user_in: UserUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    """Update current user profile."""
    for field, value in user_in.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/profile", response_model=UserProfileOut)
def get_my_profile(db: DbSession, current_user: CurrentUser):
    """Get user profile details."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/me/profile", response_model=UserProfileOut)
def update_my_profile(
    profile_in: UserProfileBase,
    db: DbSession,
    current_user: CurrentUser,
):
    """Update user profile details."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    for field, value in profile_in.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me/exams", response_model=List[UserExamOut])
def get_my_exams(db: DbSession, current_user: CurrentUser):
    """Get user's selected exams."""
    return db.query(UserExam).filter(UserExam.user_id == current_user.id).all()


@router.post("/me/exams", response_model=UserExamOut)
def add_my_exam(
    exam_in: UserExamCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    """Add an exam to user's preferences."""
    exam = db.query(Exam).filter(Exam.id == exam_in.exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    existing = (
        db.query(UserExam)
        .filter(UserExam.user_id == current_user.id, UserExam.exam_id == exam_in.exam_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Exam already added")

    user_exam = UserExam(user_id=current_user.id, **exam_in.model_dump())
    db.add(user_exam)
    db.commit()
    db.refresh(user_exam)
    return user_exam


@router.delete("/me/exams/{exam_id}")
def remove_my_exam(exam_id: str, db: DbSession, current_user: CurrentUser):
    """Remove an exam from user's preferences."""
    user_exam = (
        db.query(UserExam)
        .filter(UserExam.user_id == current_user.id, UserExam.exam_id == exam_id)
        .first()
    )
    if not user_exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    db.delete(user_exam)
    db.commit()
    return {"message": "Exam removed"}
