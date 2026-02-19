"""Workout and exercise parsing from Hevy API payloads; streaks and dedication helpers."""

import os
import re
from datetime import date, timedelta
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd


def extract_items(payload: Any) -> List[Dict[str, Any]]:
    """
    The Hevy API uses a paginated response for workouts. The exact key
    may change, so this helper tries a few common options and falls back
    to a bare list.
    """
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]

    if not isinstance(payload, dict):
        return []

    for key in ("items", "data", "workouts", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]

    return []


def first_present(d: Dict[str, Any], keys: Iterable[str]) -> Optional[Any]:
    """Return the first value present for the given keys in the dict."""
    for k in keys:
        if k in d and d.get(k) is not None:
            return d.get(k)
    return None


def _normalize_name(s: str) -> str:
    # Lowercase and strip non-alphanumerics for fuzzy matching.
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def exercise_display_name(ex: Dict[str, Any]) -> str:
    """
    Try to get a human-friendly exercise name from a workout exercise object.
    """
    tmpl = ex.get("exerciseTemplate") or ex.get("template") or ex.get("exercise") or {}
    if isinstance(tmpl, dict):
        name = tmpl.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    title = ex.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    direct_name = ex.get("name")
    if isinstance(direct_name, str) and direct_name.strip():
        return direct_name.strip()
    for k, v in ex.items():
        if "name" in str(k).lower() and isinstance(v, str) and v.strip():
            return v.strip()
    return "Unknown exercise"


def set_reps(set_obj: Dict[str, Any]) -> int:
    """Extract reps from a set object."""
    reps = first_present(set_obj, ("reps", "repCount"))
    try:
        return int(reps) if reps is not None else 0
    except (TypeError, ValueError):
        return 0


def set_volume_kg(set_obj: Dict[str, Any], bodyweight_kg: float = 0) -> float:
    """
    Volume for one set = weight_kg × reps.
    Uses set's weight_kg (or weightKg, load, etc.); if missing or 0, uses bodyweight_kg.
    """
    reps = set_reps(set_obj)
    if reps <= 0:
        return 0.0
    weight = first_present(set_obj, ("weight_kg", "weightKg", "weight", "load"))
    try:
        weight_kg = float(weight) if weight is not None else bodyweight_kg
    except (TypeError, ValueError):
        weight_kg = bodyweight_kg
    if weight_kg <= 0:
        weight_kg = bodyweight_kg
    return weight_kg * reps


def set_completed(set_obj: Dict[str, Any]) -> bool:
    """
    Determine whether a set should be counted.
    Defaults to True when the API doesn't provide a completion flag.
    """
    completed = first_present(set_obj, ("completed", "isCompleted", "done"))
    if completed is None:
        return True
    return bool(completed)


def workout_datetime(workout: Dict[str, Any]) -> Optional[pd.Timestamp]:
    """Parse workout start datetime from API payload (supports camelCase and snake_case)."""
    dt_raw = first_present(
        workout,
        (
            "startTime",
            "startedAt",
            "createdAt",
            "date",
            "start_time",
            "started_at",
            "created_at",
            "end_time",
        ),
    )
    if dt_raw is None:
        return None
    ts = pd.to_datetime(dt_raw, errors="coerce")
    if pd.isna(ts):
        return None
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts


def workout_duration_seconds(workout: Dict[str, Any]) -> float:
    """
    Get workout duration in seconds from API payload.
    Tries: duration (seconds), then end_time - start_time.
    """
    dur = first_present(workout, ("duration", "duration_seconds", "length"))
    if dur is not None:
        try:
            sec = float(dur)
            return max(0, sec)
        except (TypeError, ValueError):
            pass
    start_raw = first_present(workout, ("start_time", "startTime", "startedAt", "createdAt"))
    end_raw = first_present(workout, ("end_time", "endTime", "endedAt", "completedAt"))
    if start_raw is not None and end_raw is not None:
        try:
            start_ts = pd.to_datetime(start_raw, errors="coerce")
            end_ts = pd.to_datetime(end_raw, errors="coerce")
            if pd.notna(start_ts) and pd.notna(end_ts):
                delta = (end_ts - start_ts).total_seconds()
                return max(0, delta)
        except Exception:
            pass
    return 0.0


def workout_dates_sorted(raw_workouts: List[Dict[str, Any]]) -> List[date]:
    """Return sorted list of unique dates that have at least one workout."""
    seen: set = set()
    for w in raw_workouts:
        ts = workout_datetime(w)
        if ts is not None:
            d = ts.normalize().date()
            seen.add(d)
    return sorted(seen)


def longest_streak(dates: List[date]) -> int:
    """Longest run of consecutive days with a workout."""
    if not dates:
        return 0
    best = 1
    current = 1
    for i in range(1, len(dates)):
        if (dates[i] - dates[i - 1]).days == 1:
            current += 1
        else:
            best = max(best, current)
            current = 1
    return max(best, current)


def current_streak(dates: List[date], today: date) -> int:
    """From today (or yesterday if today not in list), count backwards while consecutive."""
    if not dates:
        return 0
    dates_set = set(dates)
    start = today if today in dates_set else (today - timedelta(days=1) if (today - timedelta(days=1)) in dates_set else None)
    if start is None:
        return 0
    count = 0
    d = start
    while d in dates_set:
        count += 1
        d -= timedelta(days=1)
    return count


def cumulative_workouts_series(dates: List[date]) -> pd.DataFrame:
    """DataFrame: date (every day from first workout to today), cumulative (running count)."""
    if not dates:
        return pd.DataFrame(columns=["date", "cumulative"])
    first = dates[0]
    today_d = date.today()
    end = today_d if today_d > dates[-1] else dates[-1]
    dates_set = set(dates)
    rows = []
    cum = 0
    d = first
    while d <= end:
        if d in dates_set:
            cum += 1
        rows.append({"date": d.isoformat(), "cumulative": cum})
        d += timedelta(days=1)
    return pd.DataFrame(rows)


def workouts_per_week_series(dates: List[date]) -> pd.DataFrame:
    """DataFrame: week_start (Monday), workouts (count of workout days that week)."""
    if not dates:
        return pd.DataFrame(columns=["week_start", "workouts"])
    week_counts: Dict[date, int] = {}
    for d in dates:
        week_start = d - timedelta(days=d.weekday())
        week_counts[week_start] = week_counts.get(week_start, 0) + 1
    first_week = dates[0] - timedelta(days=dates[0].weekday())
    last_week = dates[-1] - timedelta(days=dates[-1].weekday())
    today_d = date.today()
    end_week = today_d - timedelta(days=today_d.weekday())
    last_week = max(last_week, end_week)
    rows = []
    w = first_week
    while w <= last_week:
        rows.append({"week_start": w.isoformat(), "workouts": week_counts.get(w, 0)})
        w += timedelta(days=7)
    return pd.DataFrame(rows)


def dedication_heatmap_grid(dates: List[date]) -> pd.DataFrame:
    """GitHub-style heatmap: one row per day from first workout to today; week, day_of_week, date, count (0 or 1)."""
    if not dates:
        return pd.DataFrame(columns=["week", "day_of_week", "date", "count"])
    first = dates[0]
    today_d = date.today()
    end = today_d if today_d > dates[-1] else dates[-1]
    dates_set = set(dates)
    rows = []
    d = first
    while d <= end:
        week_idx = (d - first).days // 7
        dow = d.weekday()
        count = 1 if d in dates_set else 0
        rows.append({"week": week_idx, "day_of_week": dow, "date": d.isoformat(), "count": count})
        d += timedelta(days=1)
    return pd.DataFrame(rows)


def format_duration_hours_min(total_seconds: float) -> str:
    """Format seconds as 'x Hours y min' or 'x min' if under an hour."""
    total_seconds = max(0, int(round(total_seconds)))
    if total_seconds == 0:
        return "0 min"
    minutes = total_seconds // 60
    if minutes < 60:
        return f"{minutes} min"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours} Hour" + ("s" if hours != 1 else "") + " 0 min"
    return f"{hours} Hour{'s' if hours != 1 else ''} {mins} min"


EXERCISES_BODYWEIGHT_PLUS_LOAD_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "exercises_bodyweight_plus_load.txt"
)
EXERCISES_NO_BODYWEIGHT_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "exercises_no_bodyweight.txt"
)


def load_exercises_bodyweight_plus_load() -> List[str]:
    """Load exercise patterns from the config file. One pattern per line; # and empty lines ignored."""
    default = ["dips torse (lesté)", "tractions (lesté)"]
    path = EXERCISES_BODYWEIGHT_PLUS_LOAD_FILE
    if not os.path.isfile(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
        return lines if lines else default
    except Exception:
        return default


def load_exercises_no_bodyweight() -> List[str]:
    """Load exercise patterns that must not use bodyweight (only set weight × reps)."""
    path = EXERCISES_NO_BODYWEIGHT_FILE
    if not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
        return lines
    except Exception:
        return []
