from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC "now" matching the DateTime columns (replaces deprecated utcnow())."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
