import os
import random
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
    get_workout_by_id,
)


st.set_page_config(
    page_title="Day by Day",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inspiring quotes from top athletes (motivation, dedication)
ATHLETE_QUOTES = [
    ("Muhammad Ali", "Don't count the days. Make the days count."),
    ("Michael Jordan", "I've failed over and over and over again in my life. And that is why I succeed."),
    ("Serena Williams", "I really think a champion is defined not by their wins but by how they can recover when they fall."),
    ("Usain Bolt", "I don't think limits."),
    ("Kobe Bryant", "The moment you give up is the moment you let someone else win."),
    ("Arnold Schwarzenegger", "The last three or four reps is what makes the muscle grow. This area of pain divides a champion from someone who is not a champion."),
    ("David Goggins", "You are in danger of living a life so comfortable that you will die without ever realizing your true potential."),
    ("Simone Biles", "I'd rather regret the risks that didn't work out than the chances I didn't take at all."),
    ("LeBron James", "Nothing is given. Everything is earned."),
    ("Ronaldo", "Your love makes you fight for it. Your love makes you work hard for it."),
    ("Nadia Comăneci", "I don't run away from a challenge because I am afraid. I run toward it because the only way to escape fear is to trample it beneath your feet."),
    ("Carl Lewis", "It's all about the journey, not the outcome."),
    ("Wilma Rudolph", "Never underestimate the power of dreams and the influence of the human spirit. We are all the same in this notion: The potential for greatness lives within each of us."),
    # Conor McGregor
    ("Conor McGregor", "We're not just here to take part. We're here to take over."),
    ("Conor McGregor", "There's no talent here, this is hard work. This is an obsession."),
    ("Conor McGregor", "Doubt is only removed by action."),
    ("Conor McGregor", "Excellence is not a destination; it is a continuous journey that never ends."),
    ("Conor McGregor", "I am cocky in prediction. I am confident in preparation."),
    # Naruto
    ("Naruto Uzumaki", "If you don't like your destiny, don't accept it. Instead have the courage to change it the way you want it to be."),
    ("Naruto Uzumaki", "When people are protecting something truly precious to them, they truly can become... as strong as they can be."),
    ("Rock Lee", "A dropout will beat a genius through hard work."),
    ("Rock Lee", "I will prove that a dropout can beat a genius through hard work."),
    ("Might Guy", "Do not give up! That's the ninja way!"),
    ("Might Guy", "The difference between the novice and the master is that the master has failed more times than the novice has tried."),
    ("Jiraiya", "A place where someone still thinks about you is a place you can call home."),
]

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

    /* ——— Mobile-friendly (max-width 768px) ——— */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 1rem 2rem;
            max-width: 100%;
        }
        h1 {
            font-size: 1.35rem;
        }
        /* Metric row: wrap; at least 2 cards per row on mobile */
        .block-container [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 0.5rem;
        }
        .block-container [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > div {
            min-width: calc(50% - 0.25rem) !important;
            flex: 1 1 calc(50% - 0.25rem) !important;
        }
        [data-testid="stMetric"] {
            padding: 0.75rem 1rem;
        }
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 1.35rem;
        }
        /* Touch-friendly buttons and controls (min ~44px) */
        .stButton > button {
            min-height: 44px;
            padding: 0.6rem 1rem;
            font-size: 0.85rem;
        }
        div[data-baseweb="select"] > div {
            min-height: 44px;
        }
        /* Sidebar overlay: full-width on very small screens */
        [data-testid="stSidebar"] {
            min-width: 280px;
        }
    }
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


def _set_volume_kg(set_obj: Dict[str, Any], bodyweight_kg: float = 0) -> float:
    """
    Volume for one set = weight_kg × reps.
    Uses set's weight_kg (or weightKg, load, etc.); if missing or 0, uses bodyweight_kg.
    """
    reps = _set_reps(set_obj)
    if reps <= 0:
        return 0.0
    weight = _first_present(set_obj, ("weight_kg", "weightKg", "weight", "load"))
    try:
        weight_kg = float(weight) if weight is not None else bodyweight_kg
    except (TypeError, ValueError):
        weight_kg = bodyweight_kg
    if weight_kg <= 0:
        weight_kg = bodyweight_kg
    return weight_kg * reps


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


def _workout_duration_seconds(workout: Dict[str, Any]) -> float:
    """
    Get workout duration in seconds from API payload.
    Tries: duration (seconds), then end_time - start_time.
    """
    # Explicit duration field (often in seconds)
    dur = _first_present(workout, ("duration", "duration_seconds", "length"))
    if dur is not None:
        try:
            sec = float(dur)
            return max(0, sec)
        except (TypeError, ValueError):
            pass
    start_raw = _first_present(workout, ("start_time", "startTime", "startedAt", "createdAt"))
    end_raw = _first_present(workout, ("end_time", "endTime", "endedAt", "completedAt"))
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


def _format_duration_hours_min(total_seconds: float) -> str:
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

    # Enrich workouts with full details (list endpoint may omit set weight_kg/reps)
    def _workout_has_set_data(w: Dict[str, Any]) -> bool:
        for ex in w.get("exercises") or []:
            for s in ex.get("sets") or []:
                if not isinstance(s, dict):
                    continue
                reps = _first_present(s, ("reps", "repCount"))
                weight = _first_present(s, ("weight_kg", "weightKg", "weight", "load"))
                if reps is not None or weight is not None:
                    return True
        return False

    enriched: List[Dict[str, Any]] = []
    for w in all_workouts:
        wid = w.get("id")
        if wid and not _workout_has_set_data(w):
            try:
                full = get_workout_by_id(api_key, wid)
                if isinstance(full, dict):
                    enriched.append(full)
                else:
                    enriched.append(w)
            except Exception:
                enriched.append(w)
        else:
            enriched.append(w)
    all_workouts = enriched

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

    # Data is only fetched when user clicks "Load" or "Refresh"; otherwise use session state
    if "hevy_data" not in st.session_state:
        st.session_state["hevy_data"] = None

    # Refetch when user requested (Load my workouts or Refresh data)
    if st.session_state.get("fetch_requested"):
        st.session_state["fetch_requested"] = False
        loading = st.empty()
        with loading.container():
            st.markdown("## 💪 STRONGER DAY BY DAY")
            st.markdown("### Loading my workouts…")
            st.caption("Fetching data from the API. One moment.")
        try:
            st.cache_data.clear()
            data = fetch_user_and_workouts(api_key)
            st.session_state["hevy_data"] = data
            loading.empty()
            st.rerun()
        except HevyApiError as exc:
            loading.empty()
            st.error(f"Error talking to Hevy API: {exc}")
            st.stop()

    data = st.session_state["hevy_data"]
    if data is None:
        # No data loaded yet: show prompt to load
        st.title("STRONGER DAY BY DAY")
        if "quote_idx" not in st.session_state:
            st.session_state["quote_idx"] = random.randint(0, len(ATHLETE_QUOTES) - 1)
        name, quote = ATHLETE_QUOTES[st.session_state["quote_idx"]]
        st.markdown(f'*"{quote}"* — **{name}**')
        st.caption("Workout volume and trends from Hevy")
        st.markdown("Your workout data has not been loaded yet. Click below to fetch your workouts from Hevy.")
        if st.button("Load my workouts", type="primary"):
            st.session_state["fetch_requested"] = True
            st.rerun()
        st.stop()

    user = data["user"]
    workouts_df: pd.DataFrame = data["workouts_df"]
    raw_workouts = data["workouts_raw"].get("workouts", [])

    with st.sidebar:
        if st.button("Refresh data", width="stretch"):
            st.cache_data.clear()
            st.session_state["fetch_requested"] = True
            st.rerun()
        with st.expander("Debug", expanded=False):
            key = resolve_api_key()
            if key:
                r = f"{key[:4]}…{key[-4:]}" if len(key) > 8 else "***"
                st.caption(f"Key: `{r}`")
            st.json(user)
            st.json(data["workouts_raw"])

    st.title("STRONGER DAY BY DAY")
    # Show one inspiring quote per session (stable across reruns)
    if "quote_idx" not in st.session_state:
        st.session_state["quote_idx"] = random.randint(0, len(ATHLETE_QUOTES) - 1)
    name, quote = ATHLETE_QUOTES[st.session_state["quote_idx"]]
    st.markdown(f'*"{quote}"* — **{name}**')
    st.caption("Workout volume and trends from Hevy")

    # Bodyweight (kg) for volume when set has no weight (bodyweight exercises)
    bodyweight_kg = 0.0
    if isinstance(user, dict):
        bw = _first_present(
            user,
            ("weight", "body_weight", "bodyWeight", "bodyweight", "weight_kg", "mass"),
        )
        if bw is not None:
            try:
                bodyweight_kg = float(bw)
            except (TypeError, ValueError):
                pass
        if bodyweight_kg <= 0 and isinstance(user.get("profile"), dict):
            bw = _first_present(
                user["profile"],
                ("weight", "body_weight", "bodyWeight", "weight_kg"),
            )
            if bw is not None:
                try:
                    bodyweight_kg = float(bw)
                except (TypeError, ValueError):
                    pass
    if bodyweight_kg <= 0:
        bodyweight_kg = 62.0  # default for bodyweight exercises when API has no weight

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
            exercise_title = ex.get("title") or "Unknown"
            is_leste = "leste" in (exercise_title or "").strip().lower()
            # Compute total reps and total volume (weight_kg × reps) for this exercise
            total_reps = 0
            total_volume = 0.0
            weight_kg_per_set: List[Any] = []
            for s in ex.get("sets") or []:
                if not isinstance(s, dict):
                    continue
                reps_val = _set_reps(s)
                total_reps += reps_val
                raw_kg = _first_present(s, ("weight_kg", "weightKg", "weight", "load"))
                try:
                    lest_kg = float(raw_kg) if raw_kg is not None else 0.0
                except (TypeError, ValueError):
                    lest_kg = 0.0
                if is_leste:
                    # Leste: (bodyweight + lest) × reps
                    load_kg = bodyweight_kg + lest_kg
                    set_vol = load_kg * reps_val
                    weight_kg_per_set.append(f"bw+lest({bodyweight_kg}+{lest_kg})")
                else:
                    set_vol = _set_volume_kg(s, bodyweight_kg)
                    weight_kg_per_set.append(raw_kg if raw_kg is not None else f"bw({bodyweight_kg})")
                total_volume += set_vol

            row: Dict[str, Any] = {
                "workout_id": w_id,
                "workout_title": w_title,
                "workout_start_time": w_start,
                "exercise_title": exercise_title,
                "exercise_total_reps": total_reps,
                "exercise_total_volume": total_volume,
            }
            # Debug: date, name, reps, total_volume for each exercise
            try:
                date_str = w_start[:10] if isinstance(w_start, str) and len(w_start) >= 10 else str(w_start)
            except Exception:
                date_str = "?"
            print(f"[volume] date={date_str} | name={exercise_title!r} | reps={total_reps} | total_volume={total_volume:,.0f} kg")
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

        # Filters above the cards (main area)
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
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
        with filter_col2:
            selected = st.selectbox(
                "Exercise",
                options=["All"] + exercise_names,
                index=0,
                key="exercise_filter",
            )
        st.markdown("")

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
            # Workout duration (seconds) per workout_id from raw payloads
            workout_duration_seconds: Dict[Any, float] = {}
            for w in raw_workouts:
                wid = w.get("id")
                if wid is not None:
                    workout_duration_seconds[wid] = _workout_duration_seconds(w)

            n_workouts_now = current_df["workout_id"].nunique()
            n_workouts_prior = prior_df["workout_id"].nunique()
            current_wids = current_df["workout_id"].dropna().unique()
            prior_wids = prior_df["workout_id"].dropna().unique()
            duration_now_sec = sum(workout_duration_seconds.get(wid, 0) for wid in current_wids)
            duration_prior_sec = sum(workout_duration_seconds.get(wid, 0) for wid in prior_wids)
            time_display = _format_duration_hours_min(duration_now_sec)
            delta_duration = None if period == "All" else _pct_vs_prior(duration_prior_sec, duration_now_sec, period_label)

            pullups_now = _reps_for(current_df, "traction|pullup")
            pullups_prior = _reps_for(prior_df, "traction|pullup")
            dips_now = _reps_for(current_df, DIPS_PATTERN)
            dips_prior = _reps_for(prior_df, DIPS_PATTERN)
            leg_raises_now = _reps_for(current_df, "leg raise")
            leg_raises_prior = _reps_for(prior_df, "leg raise")
            bicep_curls_now = _reps_for(current_df, r"bicep|curl biceps|biceps curl")
            bicep_curls_prior = _reps_for(prior_df, r"bicep|curl biceps|biceps curl")

            # No delta for "All" (comparison not meaningful)
            delta_workouts = None if period == "All" else _pct_vs_prior(n_workouts_prior, n_workouts_now, period_label)
            delta_pullups = None if period == "All" else _pct_vs_prior(pullups_prior, pullups_now, period_label)
            delta_dips = None if period == "All" else _pct_vs_prior(dips_prior, dips_now, period_label)
            delta_leg_raises = None if period == "All" else _pct_vs_prior(leg_raises_prior, leg_raises_now, period_label)
            delta_bicep_curls = None if period == "All" else _pct_vs_prior(bicep_curls_prior, bicep_curls_now, period_label)

            # Total volume (sum of weight_kg × reps over all sets in period)
            volume_now = current_df["exercise_total_volume"].sum()
            volume_prior = prior_df["exercise_total_volume"].sum()
            delta_volume = None if period == "All" else _pct_vs_prior(volume_prior, volume_now, period_label)
            volume_display = f"{volume_now:,.0f} kg"

            m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
            with m1:
                st.metric("Workouts", n_workouts_now, delta_workouts)
            with m2:
                st.metric("Time", time_display, delta_duration)
            with m3:
                st.metric("Pullups", pullups_now, delta_pullups)
            with m4:
                st.metric("Dips", dips_now, delta_dips)
            with m5:
                st.metric("Leg raises", leg_raises_now, delta_leg_raises)
            with m6:
                st.metric("Bicep curls", bicep_curls_now, delta_bicep_curls)
            with m7:
                st.metric("Total volume", volume_display, delta_volume)

            st.markdown("")

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
                    bar_labels = (
                        alt.Chart(agg)
                        .mark_text(color="white", align="center", baseline="bottom", dy=-4, fontSize=11, fontWeight=500)
                        .encode(
                            x=alt.X(
                                "date_label",
                                title=None,
                                sort=date_labels,
                                scale=alt.Scale(paddingInner=0, paddingOuter=0.1),
                            ),
                            y=alt.Y("reps", title="Reps"),
                            text=alt.Text("reps:Q", format="d"),
                        )
                        .transform_filter(alt.datum.reps > 0)
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
                        (bars + bar_labels + trend_line)
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
                    # For stacked bars: y_center = midpoint of each segment for text labels
                    long = long.sort_values(["date", "exercise"])
                    long["y_center"] = long.groupby("date")["reps"].transform(
                        lambda s: s.cumsum() - s / 2
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
                                legend=alt.Legend(title="Exercise", orient="top", labelColor="#e5e7eb", titleColor="#e5e7eb"),
                                scale=alt.Scale(range=["#3b82f6", "#0d9488", "#475569", "#0f766e", "#1e40af"]),
                            ),
                        )
                    )
                    bar_labels_stacked = (
                        alt.Chart(long)
                        .mark_text(color="white", align="center", baseline="middle", fontSize=10, fontWeight=500)
                        .encode(
                            x=alt.X(
                                "date_label",
                                title=None,
                                sort=date_labels,
                                scale=alt.Scale(paddingInner=0, paddingOuter=0.1),
                            ),
                            y=alt.Y("y_center:Q", title="Reps"),
                            text=alt.Text("reps:Q", format="d"),
                        )
                        .transform_filter(alt.datum.reps > 0)
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
                        (bars + bar_labels_stacked + trend_line)
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