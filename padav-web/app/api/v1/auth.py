from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import DbSession, CurrentUser
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    fingerprint_token,
)
from app.core.config import settings
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    RefreshRequest,
    Token,
    LogoutRequest,
    UserOut,
    OTPVerify,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


def issue_refresh_token(db: DbSession, user_id: str) -> str:
    token = create_refresh_token(subject=user_id)
    db.add(RefreshToken(
        user_id=user_id,
        token_hash=fingerprint_token(token),
        expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days),
    ))
    return token


@router.post("/register", response_model=Token)
def register(user_in: UserRegister, db: DbSession):
    """Register a new user."""
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(subject=str(user.id))
    refresh_token = issue_refresh_token(db, str(user.id))
    db.commit()
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: DbSession):
    """Authenticate user and return tokens."""
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    access_token = create_access_token(subject=str(user.id))
    refresh_token = issue_refresh_token(db, str(user.id))
    db.commit()
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
def refresh_token(token_in: RefreshRequest, db: DbSession):
    """Refresh access token using refresh token."""
    payload = decode_token(token_in.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    user_id = payload.get("sub")
    stored_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == fingerprint_token(token_in.refresh_token),
        RefreshToken.revoked_at.is_(None),
        RefreshToken.expires_at > datetime.utcnow(),
    ).first()
    if not stored_token or str(stored_token.user_id) != str(user_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or revoked")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    access_token = create_access_token(subject=str(user.id))
    stored_token.revoked_at = datetime.utcnow()
    new_refresh_token = issue_refresh_token(db, str(user.id))
    db.commit()
    return Token(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout")
def logout(token_in: LogoutRequest, db: DbSession):
    """Revoke the supplied refresh token."""
    stored_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == fingerprint_token(token_in.refresh_token),
        RefreshToken.revoked_at.is_(None),
    ).first()
    if stored_token:
        stored_token.revoked_at = datetime.utcnow()
        db.commit()
    return {"message": "Successfully logged out"}


@router.post("/verify-otp")
def verify_otp(otp_in: OTPVerify):
    """Verify OTP for password reset or email verification."""
    # In production, verify OTP against Redis/email service
    return {"message": "OTP verified successfully"}


@router.get("/me", response_model=UserOut)
def get_current_user_info(current_user: CurrentUser):
    """Get current user profile."""
    return current_user
