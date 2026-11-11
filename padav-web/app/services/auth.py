from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.exceptions import AuthenticationError, BadRequestError
from app.core.rate_limit import LoginThrottle, login_throttle
from app.core.security import PasswordHasher, TokenService, TokenType, password_hasher, token_service
from app.models.user import User
from app.repositories import RefreshTokenRepository, UserRepository
from app.schemas.auth import Token, UserLogin, UserRegister
from app.services.base import BaseService

_BAD_CREDENTIALS = "Incorrect email or password"


class AuthService(BaseService):
    def __init__(
        self,
        db: Session,
        hasher: PasswordHasher = password_hasher,
        tokens: TokenService = token_service,
        throttle: LoginThrottle = login_throttle,
    ) -> None:
        super().__init__(db)
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)
        self.hasher = hasher
        self.tokens = tokens
        self.throttle = throttle

    # -- use cases -------------------------------------------------------------
    def register(self, data: UserRegister) -> Token:
        email = data.email.lower()
        if self.users.get_by_email(email):
            raise BadRequestError("Email already registered")
        user = User(email=email, hashed_password=self.hasher.hash(data.password), full_name=data.full_name)
        self.users.add(user)
        try:
            self.users.flush()
        except IntegrityError:  # lost a race with a concurrent registration
            self.db.rollback()
            raise BadRequestError("Email already registered")
        tokens = self._issue_tokens(user.id)
        self.commit()
        return tokens

    def login(self, data: UserLogin, client_id: str) -> Token:
        email = data.email.lower()
        throttle_key = f"{email}|{client_id}"
        self.throttle.ensure_allowed(throttle_key)

        user = self.users.get_by_email(email)
        # verify() runs against a dummy hash when the user is unknown: constant-ish time.
        if not self.hasher.verify(data.password, user.hashed_password if user else None):
            self.throttle.record_failure(throttle_key)
            raise AuthenticationError(_BAD_CREDENTIALS)
        assert user is not None
        if not user.is_active:
            raise BadRequestError("Inactive user")

        self.throttle.clear(throttle_key)
        if self.hasher.needs_rehash(user.hashed_password):
            user.hashed_password = self.hasher.hash(data.password)
        tokens = self._issue_tokens(user.id)
        self.commit()
        return tokens

    def refresh(self, refresh_token: str) -> Token:
        claims = self.tokens.decode(refresh_token, TokenType.REFRESH)
        stored = self.refresh_tokens.get_by_hash(self.tokens.fingerprint(refresh_token))
        if stored is None or stored.user_id != claims.subject:
            raise AuthenticationError("Invalid refresh token")
        if stored.revoked_at is not None:
            # A rotated token is being replayed => it was probably stolen.
            # Kill every session for this user; they must sign in again.
            self.refresh_tokens.revoke_all_for_user(stored.user_id)
            self.commit()
            raise AuthenticationError("Refresh token expired or revoked")
        if stored.expires_at <= utcnow():
            raise AuthenticationError("Refresh token expired or revoked")

        user = self.users.get(claims.subject)
        if user is None or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        stored.revoked_at = utcnow()  # rotation: each refresh token works exactly once
        tokens = self._issue_tokens(user.id)
        self.commit()
        return tokens

    def logout(self, refresh_token: str) -> None:
        stored = self.refresh_tokens.get_by_hash(self.tokens.fingerprint(refresh_token))
        if stored is not None and stored.revoked_at is None:
            stored.revoked_at = utcnow()
            self.commit()

    # -- helpers ----------------------------------------------------------------
    def _issue_tokens(self, user_id: str) -> Token:
        access = self.tokens.create_access_token(user_id)
        refresh = self.tokens.create_refresh_token(user_id)
        self.refresh_tokens.store(user_id, self.tokens.fingerprint(refresh.token), refresh.claims.expires_at)
        return Token(access_token=access.token, refresh_token=refresh.token)
