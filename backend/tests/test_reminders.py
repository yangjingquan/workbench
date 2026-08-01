from datetime import datetime

from app.api.routes import _next_occurrence


def test_daily_weekday_filter():
    after = datetime(2026, 8, 1, 17, 0)  # Saturday
    assert _next_occurrence("daily", "00:05:00", [1, 2, 3, 4, 5], [], after) == datetime(2026, 8, 3, 0, 5)


def test_weekly_multiple_days():
    after = datetime(2026, 8, 1, 17, 0)
    assert _next_occurrence("weekly", "13:00:00", [3, 5], [], after) == datetime(2026, 8, 5, 13, 0)


def test_monthly_multiple_days():
    after = datetime(2026, 8, 1, 17, 0)
    assert _next_occurrence("monthly", "14:09:00", [], [1, 3], after) == datetime(2026, 8, 3, 14, 9)

