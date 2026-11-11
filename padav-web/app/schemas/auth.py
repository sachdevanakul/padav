from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import AfterValidator, EmailStr, Field

from app.core.security import PasswordHasher
from app.schemas.base import ORMModel, StrictInput


def _check_password_bytes(value: str) -> str:
    if not PasswordHasher.fits(value):
        raise ValueError(f"Password must be at most {PasswordHasher.MAX_BYTES} bytes")
    return value


NewPassword = Annotated[str, Field(min_length=8, max_length=128), AfterValidator(_check_password_bytes)]
# Login accepts any length up to the cap so legacy passwords keep working.
LoginPassword = Annotated[str, Field(min_length=1, max_length=128)]
RefreshTokenStr = Annotated[str, Field(min_length=20, max_length=2048)]
HttpsUrl = Annotated[str, Field(max_length=500)]


def _check_https(value: str) -> str:
    if not value.lower().startswith("https://"):
        raise ValueError("URL must start with https://")
    return value


class Token(ORMModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(StrictInput):
    refresh_token: RefreshTokenStr


class LogoutRequest(StrictInput):
    refresh_token: RefreshTokenStr


class UserRegister(StrictInput):
    email: EmailStr
    password: NewPassword
    full_name: str = Field(min_length=1, max_length=120)


class UserLogin(StrictInput):
    email: EmailStr
    password: LoginPassword


class UserOut(ORMModel):
    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    language: str
    theme: str
    created_at: datetime


class UserUpdate(StrictInput):
    """Only these fields can be changed by the user; role/active/verified flags cannot."""

    full_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    # Non-optional on purpose: omitted is fine, an explicit null is rejected.
    language: Literal["en", "hi"] = "en"
    theme: Literal["dark", "light"] = "dark"
    avatar_url: Optional[Annotated[HttpsUrl, AfterValidator(_check_https)]] = None
