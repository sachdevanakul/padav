from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.security import TokenType, token_service
from app.database.session import get_db
from app.models.user import User
from app.repositories import UserRepository
from app.services.analytics import AnalyticsService
from app.services.assessment import TestService
from app.services.auth import AuthService
from app.services.catalog import CatalogService
from app.services.personal import BookmarkService, PlannerService
from app.services.users import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_str}/auth/login")
_optional_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def _user_from_token(db: Session, token: str) -> User:
    claims = token_service.decode(token, TokenType.ACCESS)
    user = UserRepository(db).get(claims.subject)
    # Deactivating an account must take effect immediately, not when the token expires.
    if user is None or not user.is_active:
        raise AuthenticationError()
    return user


def get_current_user(db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    return _user_from_token(db, token)


def get_optional_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_optional_bearer)],
) -> User | None:
    """Anonymous callers get ``None``; a *present but invalid* token is still rejected."""
    return _user_from_token(db, credentials.credentials) if credentials else None


def get_client_id(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def provide(service_cls: type):
    """Build a dependency that instantiates ``service_cls`` with the request's DB session."""

    def dependency(db: DbSession):
        return service_cls(db)

    return Depends(dependency)


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
ClientId = Annotated[str, Depends(get_client_id)]

AuthServiceDep = Annotated[AuthService, provide(AuthService)]
UserServiceDep = Annotated[UserService, provide(UserService)]
CatalogServiceDep = Annotated[CatalogService, provide(CatalogService)]
TestServiceDep = Annotated[TestService, provide(TestService)]
BookmarkServiceDep = Annotated[BookmarkService, provide(BookmarkService)]
PlannerServiceDep = Annotated[PlannerService, provide(PlannerService)]
AnalyticsServiceDep = Annotated[AnalyticsService, provide(AnalyticsService)]
