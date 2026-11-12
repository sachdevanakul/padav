from datetime import date, datetime, timedelta

from app.core.clock import utcnow
from app.models.planner_block import PlannerBlock
from app.models.test_attempt import TestAttempt
from app.models.user import User
from app.services.analytics import AnalyticsService

API = "/api/v1"


def _user_id(db):
    return db.query(User).one().id


def _attempt(db, user_id, completed_at):
    db.add(TestAttempt(user_id=user_id, test_id="t", status="completed", is_submitted=True, started_at=completed_at,
                       completed_at=completed_at, total_questions=1, attempted_questions=1, correct_answers=1, accuracy=100.0))


def test_streak_logic():
    today = date(2026, 11, 11)
    day = lambda n: today - timedelta(days=n)
    streak = AnalyticsService._streak
    assert streak(set(), today) == 0
    assert streak({day(0), day(1), day(2)}, today) == 3
    assert streak({day(1), day(2)}, today) == 2          # not yet active today: streak still alive
    assert streak({day(2), day(3)}, today) == 0          # missed yesterday: broken
    assert streak({day(0), day(2)}, today) == 1          # gap ends the run


def test_overview_streak_uses_attempts_and_planner(client, db, user):
    uid = _user_id(db)
    now = utcnow()
    _attempt(db, uid, now)                       # today
    _attempt(db, uid, now - timedelta(days=1))   # yesterday
    db.add(PlannerBlock(user_id=uid, title="x", study_date=(now - timedelta(days=2)).date(),
                        start_time=datetime(2000, 1, 1, 9).time(), end_time=datetime(2000, 1, 1, 10).time(), completed=True))
    db.add(PlannerBlock(user_id=uid, title="skipped", study_date=(now - timedelta(days=3)).date(),
                        start_time=datetime(2000, 1, 1, 9).time(), end_time=datetime(2000, 1, 1, 10).time(), completed=False))
    db.commit()
    data = client.get(f"{API}/analytics/overview", headers=user["headers"]).json()
    assert data["current_streak"] == 3           # planned-but-not-completed does not count
    assert len(data["active_dates"]) == 3


def test_timezone_offset_moves_the_day(client, db, user):
    uid = _user_id(db)
    now = (utcnow() - timedelta(days=1)).replace(hour=22, minute=0)  # yesterday 22:00 UTC = 03:30 today in IST
    _attempt(db, uid, now)
    db.commit()
    utc = client.get(f"{API}/analytics/overview?tz_offset=0", headers=user["headers"]).json()
    ist = client.get(f"{API}/analytics/overview?tz_offset=330", headers=user["headers"]).json()
    assert utc["active_dates"] == [now.date().isoformat()]
    assert ist["active_dates"] == [(now.date() + timedelta(days=1)).isoformat()]  # same instant, next local day
    assert client.get(f"{API}/analytics/overview?tz_offset=99999", headers=user["headers"]).status_code == 422


def test_overview_is_per_user(client, db, user, other_user):
    _attempt(db, db.query(User).filter(User.email == "user@example.com").one().id, utcnow())
    db.commit()
    assert client.get(f"{API}/analytics/overview", headers=user["headers"]).json()["current_streak"] == 1
    assert client.get(f"{API}/analytics/overview", headers=other_user["headers"]).json()["current_streak"] == 0
