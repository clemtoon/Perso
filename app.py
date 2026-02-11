import os
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import altair as alt
import streamlit as st
from dotenv import load_dotenv

import hevy_client
from hevy_client import (
    HevyApiError,
    get_api_key as get_env_api_key,
    get_user_info,
    get_workouts,
)


st.set_page_config(
    page_title="Hevy Dashboard",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load .env so HEVY_API_KEY can be stored locally in a file
load_dotenv()

# Modern dark UI theme
st.markdown(
    """
<style>
    /* Base */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > div {
        background-color: #0f172a;
        color: #e2e8f0;
    }
    [data-testid="stHeader"] { background: rgba(15, 23, 42, 0.9); }

    /* Main content padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    /* Sidebar — all text readable (white) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        border-right: 1px solid rgba(51, 65, 85, 0.6);
    }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {
        color: #f1f5f9 !important;
    }

    /* Title */
    h1 {
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #f1f5f9;
        margin-bottom: 0.5rem;
    }

    /* Section headings (sidebar Filters, etc.) */
    h2, h3 {
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        color: #f1f5f9 !important;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }

    /* Metric cards — modern glass-style */
    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(71, 85, 105, 0.5);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    [data-testid="stMetric"] label {
        font-size: 0.7rem;
        font-weight: 500;
        letter-spacing: 0.04em;
        color: #f1f5f9 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f1f5f9;
        letter-spacing: -0.02em;
    }
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-size: 0.8rem;
        font-weight: 500;
        padding: 0.2em 0.5em;
        border-radius: 6px;
        background: rgba(51, 65, 85, 0.4);
    }

    /* Buttons */
    .stButton > button {
        background: rgba(59, 130, 246, 0.15);
        color: #93c5fd;
        border-radius: 10px;
        border: 1px solid rgba(59, 130, 246, 0.4);
        padding: 0.5rem 1rem;
        font-weight: 600;
        font-size: 0.8rem;
        transition: background 0.2s, border-color 0.2s;
    }
    .stButton > button:hover {
        background: rgba(59, 130, 246, 0.3);
        border-color: #3b82f6;
        color: #e0f2fe;
    }

    /* Selects — label and dropdown text white */
    div[data-baseweb="select"] > div {
        border-radius: 10px;
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(71, 85, 105, 0.6);
        color: #f1f5f9 !important;
    }
    .stSelectbox label,
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div {
        color: #f1f5f9 !important;
    }
    /* Dropdown option list (when open) */
    ul[role="listbox"] li, [data-baseweb="popover"] {
        background: #1e293b !important;
        color: #f1f5f9 !important;
    }

    /* Expander (Debug) */
    .streamlit-expanderHeader {
        background: rgba(30, 41, 59, 0.4);
        border-radius: 8px;
        color: #f1f5f9 !important;
    }
    .streamlit-expanderHeader p, .streamlit-expanderHeader span {
        color: #f1f5f9 !important;
    }
    /* Main area widget labels (e.g. above chart) */
    .stMarkdown label, .block-container label {
        color: #e2e8f0 !important;
    }

    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(71, 85, 105, 0.5), transparent);
        margin: 1.5rem 0;
    }

    /* Caption / small text */
    .stCaption {
        color: #cbd5e1 !important;
        font-size: 0.8rem;
    }

    /* Info box */
    [data-testid="stAlert"] {
        border-radius: 10px;
        border: 1px solid rgba(71, 85, 105, 0.5);
    }

    a { color: #60a5fa; }
</style>
""",
    unsafe_allow_html=True,
)


def resolve_api_key() -> Optional[str]:
    """
    Resolve the API key from environment or .env file.
    """
    return get_env_api_key()


def _format_date_short(ymd: str) -> str:
    """Format '2026-02-08' -> '8 Feb 26'."""
    try:
        dt = pd.to_datetime(ymd)
        return f"{dt.day} {dt.strftime('%b')} {dt.strftime('%y')}"
    except Exception:
        return ymd


def _this_week_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_inclusive) for this calendar week (Mon–today)."""
    this_monday = (now.normalize() - pd.Timedelta(days=now.weekday()))
    return this_monday.normalize(), now


def _last_week_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_exclusive) for the last calendar week (Mon–Sun)."""
    this_monday = (now.normalize() - pd.Timedelta(days=now.weekday()))
    last_week_monday = this_monday - pd.Timedelta(days=7)
    last_week_end_exclusive = this_monday
    return last_week_monday.normalize(), last_week_end_exclusive.normalize()


def _prior_week_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end) for the calendar week before last (Mon–Sun). end is exclusive."""
    this_monday = (now.normalize() - pd.Timedelta(days=now.weekday()))
    prior_week_monday = this_monday - pd.Timedelta(days=14)
    prior_week_end_exclusive = this_monday - pd.Timedelta(days=7)
    return prior_week_monday.normalize(), prior_week_end_exclusive.normalize()


def _this_month_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_inclusive) for this calendar month (1st–today)."""
    start = pd.Timestamp(year=now.year, month=now.month, day=1, tz=now.tz).normalize()
    return start, now


def _last_month_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_exclusive) for the previous full calendar month."""
    year, month = now.year, now.month
    if month == 1:
        last_month_start = pd.Timestamp(year=year - 1, month=12, day=1, tz=now.tz)
    else:
        last_month_start = pd.Timestamp(year=year, month=month - 1, day=1, tz=now.tz)
    this_month_start = pd.Timestamp(year=year, month=month, day=1, tz=now.tz)
    return last_month_start.normalize(), this_month_start.normalize()


def _prior_month_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_exclusive) for the calendar month before last."""
    last_start, last_end_excl = _last_month_bounds(now)
    prior_end_excl = last_start
    prior_start = last_start - pd.Timedelta(days=1)  # last day of prior month
    prior_start = pd.Timestamp(year=prior_start.year, month=prior_start.month, day=1, tz=now.tz)
    return prior_start.normalize(), prior_end_excl.normalize()


def _this_year_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_inclusive) for this calendar year (1 Jan–today)."""
    start = pd.Timestamp(year=now.year, month=1, day=1, tz=now.tz).normalize()
    return start, now


def _last_year_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_exclusive) for the previous full calendar year."""
    year = now.year
    last_year_start = pd.Timestamp(year=year - 1, month=1, day=1, tz=now.tz)
    this_year_start = pd.Timestamp(year=year, month=1, day=1, tz=now.tz)
    return last_year_start.normalize(), this_year_start.normalize()


def _prior_year_bounds(now: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (start, end_exclusive) for the calendar year before last."""
    last_start, last_end_excl = _last_year_bounds(now)
    prior_end_excl = last_start
    prior_start = pd.Timestamp(year=now.year - 2, month=1, day=1, tz=now.tz)
    return prior_start.normalize(), prior_end_excl.normalize()


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


def _first_present(d: Dict[str, Any], keys: Iterable[str]) -> Optional[Any]:
    for k in keys:
        if k in d and d.get(k) is not None:
            return d.get(k)
    return None


def _normalize_name(s: str) -> str:
    # Lowercase and strip non-alphanumerics for fuzzy matching.
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _exercise_display_name(ex: Dict[str, Any]) -> str:
    """
    Try to get a human-friendly exercise name from a workout exercise object.
    """
    # Common shapes across different responses:
    # - exerciseTemplate.name / template.name / exercise.name
    # - title
    # - name
    tmpl = ex.get("exerciseTemplate") or ex.get("template") or ex.get("exercise") or {}
    if isinstance(tmpl, dict):
        name = tmpl.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    # Title field on the exercise object (used by /v1/workouts)
    title = ex.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()

    # Direct name field on the exercise object
    direct_name = ex.get("name")
    if isinstance(direct_name, str) and direct_name.strip():
        return direct_name.strip()
    # Fallback: any string field whose key contains "name"
    for k, v in ex.items():
        if "name" in str(k).lower() and isinstance(v, str) and v.strip():
            return v.strip()
    return "Unknown exercise"


def _set_reps(set_obj: Dict[str, Any]) -> int:
    """
    Extract reps from a set object.
    """
    reps = _first_present(set_obj, ("reps", "repCount"))
    try:
        return int(reps) if reps is not None else 0
    except (TypeError, ValueError):
        return 0


def _set_completed(set_obj: Dict[str, Any]) -> bool:
    """
    Determine whether a set should be counted.
    Defaults to True when the API doesn't provide a completion flag.
    """
    completed = _first_present(set_obj, ("completed", "isCompleted", "done"))
    if completed is None:
        return True
    return bool(completed)


def _workout_datetime(workout: Dict[str, Any]) -> Optional[pd.Timestamp]:
    # Support both camelCase and snake_case timestamp fields from the API.
    dt_raw = _first_present(
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
    # Handle both naive and tz-aware timestamps safely.
    ts = pd.to_datetime(dt_raw, errors="coerce")
    if pd.isna(ts):
        return None
    # If no timezone, assume UTC; if tz-aware, convert to UTC.
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts


# Fetch all workouts. Trust API page_count when present; also stop when we get a short page.
WORKOUTS_PER_PAGE = 50
MAX_WORKOUT_PAGES = 500  # safety cap (~25k workouts)


@st.cache_data(show_spinner=False, ttl=300)
def fetch_user_and_workouts(api_key: str) -> Dict[str, Any]:
    """
    Fetch user info and all workouts. Requests at least page_count pages (when
    the API provides it) so we don't miss data if an intermediate page returns
    empty/short. Also stops when a page has fewer than WORKOUTS_PER_PAGE items.
    """
    user = get_user_info(api_key)

    first = get_workouts(api_key=api_key, page=1, limit=WORKOUTS_PER_PAGE)
    all_workouts = first.get("workouts", []) or extract_items(first)
    page_count = first.get("page_count")
    if page_count is not None:
        try:
            page_count = int(page_count)
        except (TypeError, ValueError):
            page_count = None

    for page in range(2, MAX_WORKOUT_PAGES + 1):
        resp = get_workouts(api_key=api_key, page=page, limit=WORKOUTS_PER_PAGE)
        more = resp.get("workouts", []) or extract_items(resp)
        all_workouts.extend(more)
        # Stop when we get a short page, but only if we've requested at least page_count pages
        # (so we don't stop early when the API sometimes returns empty for a valid page)
        got_short_page = len(more) < WORKOUTS_PER_PAGE
        if got_short_page and (page_count is None or page >= page_count):
            break

    workouts_raw = {**first, "workouts": all_workouts}
    df = pd.json_normalize(all_workouts) if all_workouts else pd.DataFrame()

    return {
        "user": user,
        "workouts_raw": workouts_raw,
        "workouts": all_workouts,
        "workouts_df": df,
    }


def main() -> None:
    api_key = resolve_api_key()
    if not api_key:
        st.warning(
            "Set the `HEVY_API_KEY` in a `.env` file or as an environment variable "
            "to continue."
        )
        st.stop()

    loading = st.empty()
    with loading.container():
        st.markdown("## 💪 Hevy")
        st.markdown("### Loading your workouts…")
        st.caption("Fetching data from the API. One moment.")

    try:
        data = fetch_user_and_workouts(api_key)
    except HevyApiError as exc:
        loading.empty()
        st.error(f"Error talking to Hevy API: {exc}")
        st.stop()

    loading.empty()

    user = data["user"]
    workouts_df: pd.DataFrame = data["workouts_df"]
    raw_workouts = data["workouts_raw"].get("workouts", [])

    with st.sidebar:
        if st.button("Refresh data", width="stretch"):
            st.cache_data.clear()
            st.rerun()
        with st.expander("Debug", expanded=False):
            key = resolve_api_key()
            if key:
                r = f"{key[:4]}…{key[-4:]}" if len(key) > 8 else "***"
                st.caption(f"Key: `{r}`")
            st.json(user)
            st.json(data["workouts_raw"])

    st.title("Hevy")
    st.caption("Workout volume and trends from Hevy")

    exercise_rows: List[Dict[str, Any]] = []
    for w in raw_workouts:
        w_id = w.get("id")
        w_title = w.get("title")
        w_start = w.get("start_time") or w.get("startTime")

        exercises = w.get("exercises") or []
        if not isinstance(exercises, list):
            continue

        for ex in exercises:
            if not isinstance(ex, dict):
                continue
            # Compute total reps for this exercise across all its sets
            total_reps = 0
            for s in ex.get("sets") or []:
                if not isinstance(s, dict):
                    continue
                reps = s.get("reps")
                try:
                    total_reps += int(reps) if reps is not None else 0
                except (TypeError, ValueError):
                    continue

            row: Dict[str, Any] = {
                "workout_id": w_id,
                "workout_title": w_title,
                "workout_start_time": w_start,
                "exercise_title": ex.get("title"),
                "exercise_total_reps": total_reps,
            }
            # Keep all exercise-level fields, they will be column-expanded by json_normalize.
            for k, v in ex.items():
                row[f"exercise.{k}"] = v
            exercise_rows.append(row)

    if not exercise_rows:
        st.info("No exercises found in the API response.")
    else:
        exercises_flat = pd.json_normalize(exercise_rows)
        # Full data for metric cards (all exercises, with dt)
        exercises_all = exercises_flat.copy()
        exercises_all["workout_dt"] = pd.to_datetime(
            exercises_all["workout_start_time"], utc=True, errors="coerce"
        )
        # Focus on a few exercises only (match by substring, case-insensitive)
        FOCUS_EXERCISES = ("tractions", "dips", "curl biceps", "biceps", "leg raise", "hanging leg", "reverse crunch")
        titles = exercises_flat["exercise_title"].astype(str).str.strip()
        mask = titles.str.lower().str.contains(
            "|".join(FOCUS_EXERCISES), regex=True, na=False
        )
        exercises_flat = exercises_flat.loc[mask].copy()
        exercise_names = sorted(
            [str(n) for n in exercises_flat["exercise_title"].dropna().unique().tolist()]
        )

        # Sidebar filters (reused for chart)
        with st.sidebar:
            st.markdown("---")
            st.subheader("Filters")
            period = st.selectbox(
                "Time period",
                options=[
                    "All",
                    "This week",
                    "This month",
                    "This year",
                    "Last week",
                    "Last month",
                    "Last year",
                ],
                index=2,
                key="time_period",
            )
            selected = st.selectbox(
                "Exercise",
                options=["All"] + exercise_names,
                index=0,
                key="exercise_filter",
            )

        # Apply period filter (this / last week / month / year or all)
        now_utc = pd.Timestamp.now(tz="UTC")
        workout_dt = pd.to_datetime(exercises_flat["workout_start_time"], utc=True, errors="coerce")
        if period == "This week":
            start, end_incl = _this_week_bounds(now_utc)
            mask = (workout_dt >= start) & (workout_dt <= end_incl)
            exercises_flat = exercises_flat[mask]
        elif period == "This month":
            start, end_incl = _this_month_bounds(now_utc)
            mask = (workout_dt >= start) & (workout_dt <= end_incl)
            exercises_flat = exercises_flat[mask]
        elif period == "This year":
            start, end_incl = _this_year_bounds(now_utc)
            mask = (workout_dt >= start) & (workout_dt <= end_incl)
            exercises_flat = exercises_flat[mask]
        elif period == "Last week":
            start, end_excl = _last_week_bounds(now_utc)
            mask = (workout_dt >= start) & (workout_dt < end_excl)
            exercises_flat = exercises_flat[mask]
        elif period == "Last month":
            start, end_excl = _last_month_bounds(now_utc)
            mask = (workout_dt >= start) & (workout_dt < end_excl)
            exercises_flat = exercises_flat[mask]
        elif period == "Last year":
            start, end_excl = _last_year_bounds(now_utc)
            mask = (workout_dt >= start) & (workout_dt < end_excl)
            exercises_flat = exercises_flat[mask]

        if selected != "All":
            exercises_filtered = exercises_flat[
                exercises_flat["exercise_title"].astype(str) == selected
            ]
        else:
            exercises_filtered = exercises_flat

        # Date range (full range so rest days show as 0)
        now = pd.Timestamp.now(tz="UTC")
        if period == "This week":
            week_start, week_end = _this_week_bounds(now)
            full_dates = pd.date_range(
                start=week_start, end=week_end.normalize(), freq="D", tz="UTC"
            )
        elif period == "This month":
            month_start, month_end = _this_month_bounds(now)
            full_dates = pd.date_range(
                start=month_start, end=month_end.normalize(), freq="D", tz="UTC"
            )
        elif period == "This year":
            year_start, year_end = _this_year_bounds(now)
            full_dates = pd.date_range(
                start=year_start, end=year_end.normalize(), freq="D", tz="UTC"
            )
        elif period == "Last week":
            week_start, week_end_excl = _last_week_bounds(now)
            full_dates = pd.date_range(
                start=week_start, end=week_end_excl - pd.Timedelta(days=1), freq="D", tz="UTC"
            )
        elif period == "Last month":
            month_start, month_end_excl = _last_month_bounds(now)
            full_dates = pd.date_range(
                start=month_start, end=month_end_excl - pd.Timedelta(days=1), freq="D", tz="UTC"
            )
        elif period == "Last year":
            year_start, year_end_excl = _last_year_bounds(now)
            full_dates = pd.date_range(
                start=year_start, end=year_end_excl - pd.Timedelta(days=1), freq="D", tz="UTC"
            )
        else:
            workout_dt = pd.to_datetime(exercises_filtered["workout_start_time"], utc=True, errors="coerce")
            valid = exercises_filtered.loc[workout_dt.notna()]
            if valid.empty:
                full_dates = pd.DatetimeIndex([], tz="UTC")
            else:
                start = workout_dt.min().normalize()
                end = workout_dt.max().normalize()
                full_dates = pd.date_range(start=start, end=end, freq="D", tz="UTC")
        date_strs = [d.strftime("%Y-%m-%d") for d in full_dates]
        date_labels = [_format_date_short(s) for s in date_strs]

        if not date_strs:
            st.info("No data for the selected filters.")
        else:
            # Metric cards: value = selected period, delta = vs previous period
            now = pd.Timestamp.now(tz="UTC")
            if period == "This week":
                current_start, current_end = _this_week_bounds(now)
                prior_start, prior_end_excl = _last_week_bounds(now)
                prior_end = prior_end_excl - pd.Timedelta(microseconds=1)
                period_label = "vs last week"
            elif period == "This month":
                current_start, current_end = _this_month_bounds(now)
                prior_start, prior_end_excl = _last_month_bounds(now)
                prior_end = prior_end_excl - pd.Timedelta(microseconds=1)
                period_label = "vs last month"
            elif period == "This year":
                current_start, current_end = _this_year_bounds(now)
                prior_start, prior_end_excl = _last_year_bounds(now)
                prior_end = prior_end_excl - pd.Timedelta(microseconds=1)
                period_label = "vs last year"
            elif period == "Last week":
                current_start, current_end_excl = _last_week_bounds(now)
                current_end = current_end_excl - pd.Timedelta(microseconds=1)
                prior_start, prior_end_excl = _prior_week_bounds(now)
                prior_end = prior_end_excl - pd.Timedelta(microseconds=1)
                period_label = "vs prev. week"
            elif period == "Last month":
                current_start, current_end_excl = _last_month_bounds(now)
                current_end = current_end_excl - pd.Timedelta(microseconds=1)
                prior_start, prior_end_excl = _prior_month_bounds(now)
                prior_end = prior_end_excl - pd.Timedelta(microseconds=1)
                period_label = "vs prev. month"
            elif period == "Last year":
                current_start, current_end_excl = _last_year_bounds(now)
                current_end = current_end_excl - pd.Timedelta(microseconds=1)
                prior_start, prior_end_excl = _prior_year_bounds(now)
                prior_end = prior_end_excl - pd.Timedelta(microseconds=1)
                period_label = "vs prev. year"
            else:
                # period == "All": last 365 days vs previous 365 days
                n_days = 365
                current_start = (now - pd.Timedelta(days=n_days)).normalize()
                current_end = now
                prior_end = current_start
                prior_start = (current_start - pd.Timedelta(days=n_days)).normalize()
                period_label = "vs prev. 365d"

            def _in_period(dt_series: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
                return (dt_series >= start) & (dt_series <= end)

            current_df = exercises_all.loc[_in_period(exercises_all["workout_dt"], current_start, current_end)]
            prior_df = exercises_all.loc[_in_period(exercises_all["workout_dt"], prior_start, prior_end)]

            def _reps_for(df: pd.DataFrame, pattern: str) -> int:
                m = df["exercise_title"].astype(str).str.lower().str.contains(pattern, regex=True, na=False)
                return int(df.loc[m, "exercise_total_reps"].sum())

            def _pct_vs_prior(prior_val: float, current_val: float, label: str) -> str:
                if prior_val == 0:
                    return "+100%" if current_val > 0 else "—"
                pct = ((current_val - prior_val) / prior_val) * 100
                if pct >= 0:
                    return f"+{pct:.0f}% {label}"
                return f"{pct:.0f}% {label}"

            # Dips: all types (bench, tricep, chest, ring, weighted, barres parallèles, etc.)
            DIPS_PATTERN = r"dip|parallèle|parallel bar"
            n_workouts_now = current_df["workout_id"].nunique()
            n_workouts_prior = prior_df["workout_id"].nunique()
            pullups_now = _reps_for(current_df, "traction|pullup")
            pullups_prior = _reps_for(prior_df, "traction|pullup")
            dips_now = _reps_for(current_df, DIPS_PATTERN)
            dips_prior = _reps_for(prior_df, DIPS_PATTERN)
            leg_raises_now = _reps_for(current_df, "leg raise")
            leg_raises_prior = _reps_for(prior_df, "leg raise")

            # No delta for "All" (comparison not meaningful)
            delta_workouts = None if period == "All" else _pct_vs_prior(n_workouts_prior, n_workouts_now, period_label)
            delta_pullups = None if period == "All" else _pct_vs_prior(pullups_prior, pullups_now, period_label)
            delta_dips = None if period == "All" else _pct_vs_prior(dips_prior, dips_now, period_label)
            delta_leg_raises = None if period == "All" else _pct_vs_prior(leg_raises_prior, leg_raises_now, period_label)
            total_now = pullups_now + dips_now + leg_raises_now
            total_prior = pullups_prior + dips_prior + leg_raises_prior
            delta_total = None if period == "All" else _pct_vs_prior(total_prior, total_now, period_label)

            st.markdown("#### Overview")
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                st.metric("Workouts", n_workouts_now, delta_workouts)
            with m2:
                st.metric("Pullups", pullups_now, delta_pullups)
            with m3:
                st.metric("Dips", dips_now, delta_dips)
            with m4:
                st.metric("Leg raises", leg_raises_now, delta_leg_raises)
            with m5:
                st.metric("Total reps", total_now, delta_total)

            st.markdown("")
            st.markdown("#### Reps over time")

            exercises_filtered = exercises_filtered.copy()
            exercises_filtered["workout_dt"] = pd.to_datetime(
                exercises_filtered["workout_start_time"], utc=True, errors="coerce"
            )
            exercises_filtered["date"] = exercises_filtered["workout_dt"].dt.strftime("%Y-%m-%d")

            # Bar size: smaller when many dates so the chart doesn't explode
            n_dates = len(date_strs)
            bar_size = min(60, max(4, 5000 // max(1, n_dates)))

            # Altair chart, styled for dark "alpha" theme
            def _bar_chart():
                if selected != "All":
                    agg = (
                        exercises_filtered.groupby("date", as_index=False)["exercise_total_reps"]
                        .sum()
                        .rename(columns={"exercise_total_reps": "reps"})
                    )
                    agg = agg.set_index("date").reindex(date_strs, fill_value=0).reset_index()
                    agg["date_label"] = agg["date"].map(_format_date_short)
                    agg["trend"] = agg["reps"].rolling(7, min_periods=1).mean()
                    bars = (
                        alt.Chart(agg)
                        .mark_bar(size=bar_size, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
                        .encode(
                            x=alt.X(
                                "date_label",
                                title=None,
                                sort=date_labels,
                                scale=alt.Scale(paddingInner=0, paddingOuter=0.1),
                            ),
                            y=alt.Y("reps", title="Reps"),
                            color=alt.value("#3b82f6"),
                        )
                    )
                    trend_line = (
                        alt.Chart(agg)
                        .mark_line(color="#94a3b8", strokeWidth=2, point=False)
                        .encode(
                            x=alt.X(
                                "date_label",
                                sort=date_labels,
                                scale=alt.Scale(paddingInner=0, paddingOuter=0.1),
                            ),
                            y=alt.Y("trend", title="Reps"),
                        )
                    )
                    c = (
                        (bars + trend_line)
                        .properties(background="transparent", height=280)
                        .configure_axis(
                            labelFontSize=11,
                            titleFontSize=12,
                            labelColor="#e5e7eb",
                            titleColor="#e5e7eb",
                            domainColor="#4b5563",
                            gridColor="#020617",
                        )
                        .configure_view(strokeWidth=0)
                    )
                else:
                    agg = exercises_filtered.groupby(
                        ["date", "exercise_title"], as_index=False
                    )["exercise_total_reps"].sum()
                    pivot = (
                        agg.pivot(
                            index="date",
                            columns="exercise_title",
                            values="exercise_total_reps",
                        )
                        .reindex(date_strs, fill_value=0)
                    )
                    pivot = pivot.reset_index()
                    pivot["date_label"] = pivot["date"].map(_format_date_short)
                    value_vars = [c for c in pivot.columns if c not in ("date", "date_label")]
                    pivot["total_reps"] = pivot[value_vars].sum(axis=1)
                    pivot["trend"] = pivot["total_reps"].rolling(7, min_periods=1).mean()
                    long = pivot.melt(
                        id_vars=["date", "date_label", "trend"],
                        value_vars=value_vars,
                        var_name="exercise",
                        value_name="reps",
                    )
                    bars = (
                        alt.Chart(long)
                        .mark_bar(size=bar_size, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
                        .encode(
                            x=alt.X(
                                "date_label",
                                title=None,
                                sort=date_labels,
                                scale=alt.Scale(paddingInner=0, paddingOuter=0.1),
                            ),
                            y=alt.Y("reps", title="Reps"),
                            color=alt.Color(
                                "exercise",
                                legend=alt.Legend(title="Exercise", labelColor="#e5e7eb", titleColor="#e5e7eb"),
                                scale=alt.Scale(range=["#3b82f6", "#0d9488", "#475569", "#0f766e", "#1e40af"]),
                            ),
                        )
                    )
                    trend_df = pivot[["date_label", "trend"]].copy()
                    trend_line = (
                        alt.Chart(trend_df)
                        .mark_line(color="#94a3b8", strokeWidth=2, point=False)
                        .encode(
                            x=alt.X(
                                "date_label",
                                sort=date_labels,
                                scale=alt.Scale(paddingInner=0, paddingOuter=0.1),
                            ),
                            y=alt.Y("trend", title="Reps"),
                        )
                    )
                    c = (
                        (bars + trend_line)
                        .properties(background="transparent", height=280)
                        .configure_axis(
                            labelFontSize=11,
                            titleFontSize=12,
                            labelColor="#e5e7eb",
                            titleColor="#e5e7eb",
                            domainColor="#4b5563",
                            gridColor="#020617",
                        )
                        .configure_view(strokeWidth=0)
                    )
                return c

            st.altair_chart(_bar_chart(), width="stretch")
            st.caption("Line = 7-day rolling average (trend)")


if __name__ == "__main__":
    main()