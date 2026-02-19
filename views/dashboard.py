"""Dashboard view: sidebar, dedication, filters, metrics, bar chart."""

import random
from datetime import date
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from config import ATHLETE_QUOTES, FOCUS_EXERCISES
import charts
import dates
import data_fetch
import workout_parsing


def render_dashboard(data: Dict[str, Any]) -> None:
    """Render the main dashboard: sidebar, title, quote, dedication, filters, metrics, chart."""
    user = data["user"]
    workouts_df = data["workouts_df"]
    raw_workouts = data["workouts_raw"].get("workouts", [])

    # Storage debug in main area so it’s visible (sidebar is collapsed by default)
    if "storage_debug" in st.session_state:
        d = st.session_state["storage_debug"]
        with st.container():
            st.markdown("---")
            st.markdown("**Storage debug** (last save to Supabase)")
            if d.get("fetch_failed"):
                st.error("Fetch failed before save: " + str(d.get("error", "")))
            else:
                st.write(
                    "Supabase used:", d.get("use_supabase"),
                    "| success:", d.get("success"),
                    "| has URL:", d.get("has_url"),
                    "| has KEY:", d.get("has_key"),
                )
                if d.get("error"):
                    st.error("Upsert error: " + str(d["error"]))
                st.json(d)
            st.markdown("---")

    with st.sidebar:
        if st.button("Refresh Supabase", width="stretch"):
            st.cache_data.clear()
            st.session_state["fetch_requested"] = True
            st.rerun()
        with st.expander("Debug", expanded=False):
            if "storage_debug" in st.session_state:
                st.caption("Last storage save:")
                st.json(st.session_state["storage_debug"])
            key = data_fetch.resolve_api_key()
            if key:
                r = f"{key[:4]}…{key[-4:]}" if len(key) > 8 else "***"
                st.caption(f"Key: `{r}`")
            st.json(user)
            st.json(data["workouts_raw"])

    st.title("STRONGER DAY BY DAY")
    if "quote_idx" not in st.session_state:
        st.session_state["quote_idx"] = random.randint(0, len(ATHLETE_QUOTES) - 1)
    name, quote = ATHLETE_QUOTES[st.session_state["quote_idx"]]
    st.markdown(f'*"{quote}"* — **{name}**')

    bodyweight_kg = 0.0
    if isinstance(user, dict):
        bw = workout_parsing.first_present(
            user,
            ("weight", "body_weight", "bodyWeight", "bodyweight", "weight_kg", "mass"),
        )
        if bw is not None:
            try:
                bodyweight_kg = float(bw)
            except (TypeError, ValueError):
                pass
        if bodyweight_kg <= 0 and isinstance(user.get("profile"), dict):
            bw = workout_parsing.first_present(
                user["profile"],
                ("weight", "body_weight", "bodyWeight", "weight_kg"),
            )
            if bw is not None:
                try:
                    bodyweight_kg = float(bw)
                except (TypeError, ValueError):
                    pass
    if bodyweight_kg <= 0:
        bodyweight_kg = 62.0

    exercises_bodyweight_plus_load = workout_parsing.load_exercises_bodyweight_plus_load()
    exercises_no_bodyweight = workout_parsing.load_exercises_no_bodyweight()
    exercise_rows: List[Dict[str, Any]] = []
    workouts_by_date = sorted(
        raw_workouts,
        key=lambda w: w.get("start_time") or w.get("startTime") or "",
    )
    for w in workouts_by_date:
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
            title_lower = (exercise_title or "").strip().lower()
            title_normalized = title_lower.replace("é", "e").replace("è", "e")
            patterns_normalized = [p.lower().replace("é", "e").replace("è", "e") for p in exercises_bodyweight_plus_load]
            use_bodyweight_plus_load = any(pat in title_normalized for pat in patterns_normalized)
            no_bw_patterns = [p.lower().replace("é", "e").replace("è", "e") for p in exercises_no_bodyweight]
            use_no_bodyweight = any(pat in title_normalized for pat in no_bw_patterns)
            is_leste_other = "leste" in title_normalized and not use_bodyweight_plus_load and not use_no_bodyweight
            total_reps = 0
            total_volume = 0.0
            weight_kg_per_set: List[Any] = []
            for s in ex.get("sets") or []:
                if not isinstance(s, dict):
                    continue
                reps_val = workout_parsing.set_reps(s)
                total_reps += reps_val
                raw_kg = workout_parsing.first_present(s, ("weight_kg", "weightKg", "weight", "load"))
                try:
                    extra_kg = float(raw_kg) if raw_kg is not None else 0.0
                except (TypeError, ValueError):
                    extra_kg = 0.0
                if use_bodyweight_plus_load:
                    load_kg = bodyweight_kg + extra_kg
                    set_vol = load_kg * reps_val
                    weight_kg_per_set.append(f"bw+load({bodyweight_kg}+{extra_kg})")
                elif is_leste_other or use_no_bodyweight:
                    set_vol = extra_kg * reps_val
                    weight_kg_per_set.append(extra_kg if raw_kg is not None else "0")
                else:
                    set_vol = workout_parsing.set_volume_kg(s, bodyweight_kg)
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
            for k, v in ex.items():
                row[f"exercise.{k}"] = v
            exercise_rows.append(row)

    if not exercise_rows:
        st.info("No exercises found in the API response.")
    else:
        exercises_flat = pd.json_normalize(exercise_rows)
        exercises_all = exercises_flat.copy()
        exercises_all["workout_dt"] = pd.to_datetime(
            exercises_all["workout_start_time"], utc=True, errors="coerce"
        )
        titles = exercises_flat["exercise_title"].astype(str).str.strip()
        mask = titles.str.lower().str.contains(
            "|".join(FOCUS_EXERCISES), regex=True, na=False
        )
        exercises_flat = exercises_flat.loc[mask].copy()
        exercise_names = sorted(
            [str(n) for n in exercises_flat["exercise_title"].dropna().unique().tolist()]
        )

        st.subheader("Dedication")
        dates_dedication = workout_parsing.workout_dates_sorted(raw_workouts)
        today_d = date.today()
        if not dates_dedication:
            st.caption("No workouts yet.")
        else:
            longest = workout_parsing.longest_streak(dates_dedication)
            current = workout_parsing.current_streak(dates_dedication, today_d)
            first_date = dates_dedication[0]
            n_days = len(dates_dedication)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Current streak", f"{current} days", None)
            with c2:
                st.metric("Longest streak", f"{longest} days", None)
            with c3:
                st.metric("Total workout days", n_days, None)
            with c4:
                st.metric("First workout", first_date.strftime("%d %b %Y"), None)

            heatmap_df = workout_parsing.dedication_heatmap_grid(dates_dedication)
            if not heatmap_df.empty:
                heatmap_df = heatmap_df.copy()
                heatmap_df["label"] = heatmap_df["count"].apply(
                    lambda c: "Workout" if c else "No workout"
                )
                day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                heatmap_df["day_name"] = heatmap_df["day_of_week"].map(
                    lambda i: day_names[i] if 0 <= i < 7 else ""
                )
                first_date = dates_dedication[0]
                end_date = date.today() if date.today() > dates_dedication[-1] else dates_dedication[-1]
                heatmap_chart = charts.dedication_heatmap(heatmap_df, first_date, end_date)
                st.altair_chart(heatmap_chart, use_container_width=True)
            st.markdown("")

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

        now_utc = pd.Timestamp.now(tz="UTC")
        workout_dt = pd.to_datetime(exercises_flat["workout_start_time"], utc=True, errors="coerce")
        if period == "This week":
            start, end_incl = dates.this_week_bounds(now_utc)
            mask = (workout_dt >= start) & (workout_dt <= end_incl)
            exercises_flat = exercises_flat[mask]
        elif period == "This month":
            start, end_incl = dates.this_month_bounds(now_utc)
            mask = (workout_dt >= start) & (workout_dt <= end_incl)
            exercises_flat = exercises_flat[mask]
        elif period == "This year":
            start, end_incl = dates.this_year_bounds(now_utc)
            mask = (workout_dt >= start) & (workout_dt <= end_incl)
            exercises_flat = exercises_flat[mask]
        elif period == "Last week":
            start, end_excl = dates.last_week_bounds(now_utc)
            mask = (workout_dt >= start) & (workout_dt < end_excl)
            exercises_flat = exercises_flat[mask]
        elif period == "Last month":
            start, end_excl = dates.last_month_bounds(now_utc)
            mask = (workout_dt >= start) & (workout_dt < end_excl)
            exercises_flat = exercises_flat[mask]
        elif period == "Last year":
            start, end_excl = dates.last_year_bounds(now_utc)
            mask = (workout_dt >= start) & (workout_dt < end_excl)
            exercises_flat = exercises_flat[mask]

        if selected != "All":
            exercises_filtered = exercises_flat[
                exercises_flat["exercise_title"].astype(str) == selected
            ]
        else:
            exercises_filtered = exercises_flat

        now = pd.Timestamp.now(tz="UTC")
        if period == "This week":
            week_start, week_end = dates.this_week_bounds(now)
            full_dates = pd.date_range(
                start=week_start, end=week_end.normalize(), freq="D", tz="UTC"
            )
        elif period == "This month":
            month_start, month_end = dates.this_month_bounds(now)
            full_dates = pd.date_range(
                start=month_start, end=month_end.normalize(), freq="D", tz="UTC"
            )
        elif period == "This year":
            year_start, year_end = dates.this_year_bounds(now)
            full_dates = pd.date_range(
                start=year_start, end=year_end.normalize(), freq="D", tz="UTC"
            )
        elif period == "Last week":
            week_start, week_end_excl = dates.last_week_bounds(now)
            full_dates = pd.date_range(
                start=week_start, end=week_end_excl - pd.Timedelta(days=1), freq="D", tz="UTC"
            )
        elif period == "Last month":
            month_start, month_end_excl = dates.last_month_bounds(now)
            full_dates = pd.date_range(
                start=month_start, end=month_end_excl - pd.Timedelta(days=1), freq="D", tz="UTC"
            )
        elif period == "Last year":
            year_start, year_end_excl = dates.last_year_bounds(now)
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
        date_labels = [dates.format_date_short(s) for s in date_strs]

        if not date_strs:
            st.info("No data for the selected filters.")
        else:
            now = pd.Timestamp.now(tz="UTC")
            if period == "This week":
                current_start, current_end = dates.this_week_bounds(now)
                prior_start, prior_end = dates.last_week_same_weekday_bounds(now)
                period_label = "vs last week"
            elif period == "This month":
                current_start, current_end = dates.this_month_bounds(now)
                prior_start, prior_end = dates.last_month_same_day_bounds(now)
                period_label = "vs last month"
            elif period == "This year":
                current_start, current_end = dates.this_year_bounds(now)
                prior_start, prior_end = dates.last_year_same_date_bounds(now)
                period_label = "vs last year"
            elif period == "Last week":
                current_start, current_end_excl = dates.last_week_bounds(now)
                current_end = current_end_excl - pd.Timedelta(microseconds=1)
                prior_start, prior_end_excl = dates.prior_week_bounds(now)
                prior_end = prior_end_excl - pd.Timedelta(microseconds=1)
                period_label = "vs prev. week"
            elif period == "Last month":
                current_start, current_end_excl = dates.last_month_bounds(now)
                current_end = current_end_excl - pd.Timedelta(microseconds=1)
                prior_start, prior_end_excl = dates.prior_month_bounds(now)
                prior_end = prior_end_excl - pd.Timedelta(microseconds=1)
                period_label = "vs prev. month"
            elif period == "Last year":
                current_start, current_end_excl = dates.last_year_bounds(now)
                current_end = current_end_excl - pd.Timedelta(microseconds=1)
                prior_start, prior_end_excl = dates.prior_year_bounds(now)
                prior_end = prior_end_excl - pd.Timedelta(microseconds=1)
                period_label = "vs prev. year"
            else:
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

            DIPS_PATTERN = r"dip|parallèle|parallel bar"
            workout_duration_seconds: Dict[Any, float] = {}
            for w in raw_workouts:
                wid = w.get("id")
                if wid is not None:
                    workout_duration_seconds[wid] = workout_parsing.workout_duration_seconds(w)

            n_workouts_now = current_df["workout_id"].nunique()
            n_workouts_prior = prior_df["workout_id"].nunique()
            current_wids = current_df["workout_id"].dropna().unique()
            prior_wids = prior_df["workout_id"].dropna().unique()
            duration_now_sec = sum(workout_duration_seconds.get(wid, 0) for wid in current_wids)
            duration_prior_sec = sum(workout_duration_seconds.get(wid, 0) for wid in prior_wids)
            time_display = workout_parsing.format_duration_hours_min(duration_now_sec)
            delta_duration = None if period == "All" else _pct_vs_prior(duration_prior_sec, duration_now_sec, period_label)

            pullups_now = _reps_for(current_df, "traction|pullup")
            pullups_prior = _reps_for(prior_df, "traction|pullup")
            dips_now = _reps_for(current_df, DIPS_PATTERN)
            dips_prior = _reps_for(prior_df, DIPS_PATTERN)
            leg_raises_now = _reps_for(current_df, "leg raise")
            leg_raises_prior = _reps_for(prior_df, "leg raise")
            bicep_curls_now = _reps_for(current_df, r"bicep|curl biceps|biceps curl")
            bicep_curls_prior = _reps_for(prior_df, r"bicep|curl biceps|biceps curl")

            delta_workouts = None if period == "All" else _pct_vs_prior(n_workouts_prior, n_workouts_now, period_label)
            delta_pullups = None if period == "All" else _pct_vs_prior(pullups_prior, pullups_now, period_label)
            delta_dips = None if period == "All" else _pct_vs_prior(dips_prior, dips_now, period_label)
            delta_leg_raises = None if period == "All" else _pct_vs_prior(leg_raises_prior, leg_raises_now, period_label)
            delta_bicep_curls = None if period == "All" else _pct_vs_prior(bicep_curls_prior, bicep_curls_now, period_label)

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

            bar_chart = charts.reps_bar_chart(
                exercises_filtered, date_strs, date_labels, selected, dates.format_date_short
            )
            st.altair_chart(bar_chart, width="stretch")
            st.caption("Line = 7-day rolling average (trend)")

    st.markdown("---")
    if st.button("Refresh Supabase", type="secondary", help="Fetch latest from Hevy API and save to Supabase"):
        st.cache_data.clear()
        st.session_state["fetch_requested"] = True
        st.rerun()
