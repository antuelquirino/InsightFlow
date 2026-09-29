"""Small calendar helpers shared by the generator modules."""
from __future__ import annotations

import calendar
from datetime import date, timedelta


def add_months(d: date, months: int) -> date:
    """Shift a date by whole months, clamping the day to the target month's length."""
    total = d.year * 12 + (d.month - 1) + months
    year, month = divmod(total, 12)
    month += 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def month_end(d: date) -> date:
    return date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])


def months_between(start: date, end: date) -> int:
    """Whole calendar months from start's month to end's month."""
    return (end.year - start.year) * 12 + (end.month - start.month)


def last_complete_month(today: date) -> date:
    """First day of the month before `today`'s month."""
    return add_months(today.replace(day=1), -1)


def monday_on_or_before(d: date) -> date:
    return d - timedelta(days=d.weekday())
