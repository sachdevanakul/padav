"""Password hashing and JWT handling as small, injectable classes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from hashlib import sha256
from uuid import uuid4

import bcrypt
import jwt

from app.core.config import Settings, settings
from app.core.exceptions import AuthenticationError


class PasswordHasher:
    """bcrypt wrapper. Hashes stay compatible with those produced by passlib."""

    MAX_BYTES = 72  # bcrypt silently truncates beyond this; reject instead

    def __init__(self, rounds: int) -> None:
        self._rounds = rounds
        # Verified against when the account does not exist, so that response time
        # does not reveal which e-mail addresses are registered.
        self._dummy_hash = bcrypt.hashpw(b"padav-timing-equaliser", bcrypt.gensalt(rounds)).decode()

    @classmethod
    def fits(cls, password: str) -> bool:
        return len(password.encode("utf-8")) <= cls.MAX_BYTES

    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(self._rounds)).decode()

    def verify(self, password: str, hashed: str | None) -> bool:
        target = hashed or self._dummy_hash
        try:
            ok = bcrypt.checkpw(password.encode("utf-8")[: self.MAX_BYTES], target.encode("utf-8"))
        except ValueError:  # malformed stored hash
            return False
        return ok and hashed is not None

    def needs_rehash(self, hashed: str) -> bool:
        try:
            return int(hashed.split("$")[2]) < self._rounds
        except (IndexError, ValueError):
            return False


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


@dataclass(frozen=True)
class TokenClaims:
    subject: str
    type: TokenType
    jti: str | None
    expires_at: datetime


@dataclass(frozen=True)
class IssuedToken:
    token: str
    claims: TokenClaims


class TokenService:
    """Creates and validates signed tokens. Always pins algorithm, issuer, audience."""

    def __init__(self, config: Settings) -> None:
        self._cfg = config

    def _encode(self, subject: str, token_type: TokenType, lifetime: timedelta) -> IssuedToken:
        now = datetime.now(timezone.utc)
        expires = now + lifetime
        jti = uuid4().hex
        payload = {
            "sub": str(subject),
            "type": token_type.value,
            "jti": jti,
            "iat": now,
            "nbf": now,
            "exp": expires,
            "iss": self._cfg.jwt_issuer,
            "aud": self._cfg.jwt_audience,
        }
        token = jwt.encode(payload, self._cfg.secret_key, algorithm=self._cfg.algorithm)
        return IssuedToken(token, TokenClaims(str(subject), token_type, jti, expires.replace(tzinfo=None)))

    def create_access_token(self, subject: str) -> IssuedToken:
        return self._encode(subject, TokenType.ACCESS, timedelta(minutes=self._cfg.access_token_expire_minutes))

    def create_refresh_token(self, subject: str) -> IssuedToken:
        return self._encode(subject, TokenType.REFRESH, timedelta(days=self._cfg.refresh_token_expire_days))

    def decode(self, token: str, expected: TokenType) -> TokenClaims:
        """Return validated claims or raise ``AuthenticationError`` (never leaks why)."""
        try:
            payload = jwt.decode(
                token,
                self._cfg.secret_key,
                algorithms=[self._cfg.algorithm],
                audience=self._cfg.jwt_audience,
                issuer=self._cfg.jwt_issuer,
                options={"require": ["exp", "iat", "sub", "iss", "aud", "jti"]},
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationError() from exc
        if payload.get("type") != expected.value or not isinstance(payload.get("sub"), str):
            raise AuthenticationError()
        return TokenClaims(
            subject=payload["sub"],
            type=expected,
            jti=payload.get("jti"),
            expires_at=datetime.fromtimestamp(payload["exp"], timezone.utc).replace(tzinfo=None),
        )

    @staticmethod
    def fingerprint(token: str) -> str:
        """Stable digest stored instead of the refresh token itself."""
        return sha256(token.encode("utf-8")).hexdigest()


password_hasher = PasswordHasher(settings.bcrypt_rounds)
token_service = TokenService(settings)
