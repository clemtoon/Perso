"""Date range and formatting helpers for workout filters and period logic."""

import calendar
from typing import Tuple

import pandas as pd


def format_date_short(ymd: str) -> str:
    """Format '2026-02-08' -> '8 Feb 26'."""
    try:
        dt = pd.to_datetime(ymd)
        return f"{dt.day} {dt.strftime('%b')} {dt.strftime('%y')}"
    except Exception:
        return ymd


def this_week_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_inclusive) for this calendar week (Mon–today)."""
    this_monday = (now.normalize() - pd.Timedelta(days=now.weekday()))
    return this_monday.normalize(), now


def last_week_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_exclusive) for the last calendar week (Mon–Sun)."""
    this_monday = (now.normalize() - pd.Timedelta(days=now.weekday()))
    last_week_monday = this_monday - pd.Timedelta(days=7)
    last_week_end_exclusive = this_monday
    return last_week_monday.normalize(), last_week_end_exclusive.normalize()


def prior_week_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end) for the calendar week before last (Mon–Sun). end is exclusive."""
    this_monday = (now.normalize() - pd.Timedelta(days=now.weekday()))
    prior_week_monday = this_monday - pd.Timedelta(days=14)
    prior_week_end_exclusive = this_monday - pd.Timedelta(days=7)
    return prior_week_monday.normalize(), prior_week_end_exclusive.normalize()


def this_month_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_inclusive) for this calendar month (1st–today)."""
    start = pd.Timestamp(year=now.year, month=now.month, day=1, tz=now.tz).normalize()
    return start, now


def last_month_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_exclusive) for the previous full calendar month."""
    year, month = now.year, now.month
    if month == 1:
        last_month_start = pd.Timestamp(year=year - 1, month=12, day=1, tz=now.tz)
    else:
        last_month_start = pd.Timestamp(year=year, month=month - 1, day=1, tz=now.tz)
    this_month_start = pd.Timestamp(year=year, month=month, day=1, tz=now.tz)
    return last_month_start.normalize(), this_month_start.normalize()


def prior_month_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_exclusive) for the calendar month before last."""
    last_start, last_end_excl = last_month_bounds(now)
    prior_end_excl = last_start
    prior_start = last_start - pd.Timedelta(days=1)  # last day of prior month
    prior_start = pd.Timestamp(year=prior_start.year, month=prior_start.month, day=1, tz=now.tz)
    return prior_start.normalize(), prior_end_excl.normalize()


def this_year_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_inclusive) for this calendar year (1 Jan–today)."""
    start = pd.Timestamp(year=now.year, month=1, day=1, tz=now.tz).normalize()
    return start, now


def last_year_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_exclusive) for the previous full calendar year."""
    year = now.year
    last_year_start = pd.Timestamp(year=year - 1, month=1, day=1, tz=now.tz)
    this_year_start = pd.Timestamp(year=year, month=1, day=1, tz=now.tz)
    return last_year_start.normalize(), this_year_start.normalize()


def prior_year_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_exclusive) for the calendar year before last."""
    last_start, last_end_excl = last_year_bounds(now)
    prior_end_excl = last_start
    prior_start = pd.Timestamp(year=now.year - 2, month=1, day=1, tz=now.tz)
    return prior_start.normalize(), prior_end_excl.normalize()


def last_week_same_weekday_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_inclusive) for last week Mon–same weekday (aligned with this week)."""
    this_monday = now.normalize() - pd.Timedelta(days=now.weekday())
    last_week_monday = this_monday - pd.Timedelta(days=7)
    last_week_same_weekday = last_week_monday + pd.Timedelta(days=now.weekday())
    end_of_day = last_week_same_weekday.normalize() + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    return last_week_monday.normalize(), end_of_day


def last_month_same_day_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_inclusive) for last month 1st–same day of month (aligned with this month)."""
    year, month = now.year, now.month
    if month == 1:
        last_year, last_month = year - 1, 12
    else:
        last_year, last_month = year, month - 1
    start = pd.Timestamp(year=last_year, month=last_month, day=1, tz=now.tz).normalize()
    _, last_day = calendar.monthrange(last_year, last_month)
    day = min(now.day, last_day)
    end_date = pd.Timestamp(year=last_year, month=last_month, day=day, tz=now.tz).normalize()
    end_of_day = end_date + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    return start, end_of_day


def last_year_same_date_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_inclusive) for last year 1 Jan–same month/day (aligned with this year)."""
    last_year = now.year - 1
    start = pd.Timestamp(year=last_year, month=1, day=1, tz=now.tz).normalize()
    _, last_day = calendar.monthrange(last_year, now.month)
    day = min(now.day, last_day)
    end_date = pd.Timestamp(year=last_year, month=now.month, day=day, tz=now.tz).normalize()
    end_of_day = end_date + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    return start, end_of_day
