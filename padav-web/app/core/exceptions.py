"""Domain errors.

Services and repositories raise these; a single handler in ``app.main`` turns them
into HTTP responses. This removes the repeated ``raise HTTPException(...)`` blocks
from the routers and keeps the business layer free of HTTP concerns.
"""
from __future__ import annotations


class DomainError(Exception):
    status_code = 400
    default_detail = "Bad request"
    headers: dict[str, str] | None = None

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class NotFoundError(DomainError):
    status_code = 404
    default_detail = "Not found"

    @classmethod
    def for_resource(cls, label: str) -> "NotFoundError":
        return cls(f"{label} not found")


class ConflictError(DomainError):
    status_code = 409
    default_detail = "Conflict"


class BadRequestError(DomainError):
    status_code = 400


class AuthenticationError(DomainError):
    status_code = 401
    default_detail = "Could not validate credentials"
    headers = {"WWW-Authenticate": "Bearer"}


class PermissionDeniedError(DomainError):
    status_code = 403
    default_detail = "Not allowed"


class RateLimitedError(DomainError):
    status_code = 429
    default_detail = "Too many requests. Please try again later."

    def __init__(self, retry_after: int = 60, detail: str | None = None) -> None:
        super().__init__(detail)
        self.headers = {"Retry-After": str(max(1, retry_after))}
