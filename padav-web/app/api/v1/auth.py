from fastapi import APIRouter, Depends

from app.core.dependencies import AuthServiceDep, ClientId, CurrentUser
from app.core.rate_limit import auth_rate_limit
from app.schemas.auth import ChangePassword, LogoutRequest, RefreshRequest, Token, UserLogin, UserOut, UserRegister

router = APIRouter(prefix="/auth", tags=["authentication"])
throttled = [Depends(auth_rate_limit)]


@router.post("/register", response_model=Token, dependencies=throttled)
def register(user_in: UserRegister, service: AuthServiceDep):
    """Register a new user."""
    return service.register(user_in)


@router.post("/login", response_model=Token, dependencies=throttled)
def login(user_in: UserLogin, service: AuthServiceDep, client_id: ClientId):
    """Authenticate user and return tokens."""
    return service.login(user_in, client_id)


@router.post("/refresh", response_model=Token, dependencies=throttled)
def refresh_token(token_in: RefreshRequest, service: AuthServiceDep):
    """Rotate the refresh token and issue a new access token."""
    return service.refresh(token_in.refresh_token)


@router.post("/logout", dependencies=throttled)
def logout(token_in: LogoutRequest, service: AuthServiceDep):
    """Revoke the supplied refresh token."""
    service.logout(token_in.refresh_token)
    return {"message": "Successfully logged out"}


@router.post("/change-password", response_model=Token, dependencies=throttled)
def change_password(data: ChangePassword, current_user: CurrentUser, service: AuthServiceDep):
    """Change password; all other sessions are revoked and fresh tokens are returned."""
    return service.change_password(current_user, data)


@router.get("/me", response_model=UserOut)
def get_current_user_info(current_user: CurrentUser):
    """Get current user profile."""
    return current_user
