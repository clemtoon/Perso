"""Altair chart builders: dedication heatmap and reps bar chart."""

from datetime import date
from typing import Callable, List

import altair as alt
import pandas as pd


def dedication_heatmap(
    heatmap_df: pd.DataFrame,
    first_date: date,
    end_date: date,
) -> alt.Chart:
    """
    Build the dedication heatmap chart (GitHub-style).
    heatmap_df must have columns: week, day_of_week, date, count, label, day_name.
    """
    year_labels_rows = []
    for y in range(first_date.year, end_date.year + 1):
        jan1 = date(y, 1, 1)
        dec31 = date(y, 12, 31)
        first_in_range = max(jan1, first_date)
        last_in_range = min(dec31, end_date)
        if first_in_range > last_in_range:
            continue
        first_week = (first_in_range - first_date).days // 7
        last_week = (last_in_range - first_date).days // 7
        week_center = (first_week + last_week) / 2.0
        year_labels_rows.append({"year_label": str(y), "week_center": week_center})
    year_labels_df = pd.DataFrame(year_labels_rows)
    max_week = int(heatmap_df["week"].max())
    year_boundaries = []
    for y in range(first_date.year + 1, end_date.year + 1):
        jan1 = date(y, 1, 1)
        if jan1 < first_date:
            continue
        week_idx = (jan1 - first_date).days // 7
        if 0 < week_idx <= max_week:
            year_boundaries.append({"week_idx": week_idx, "x_boundary": week_idx - 0.5})
    year_boundaries_df = pd.DataFrame(year_boundaries)

    heatmap_chart = (
        alt.Chart(heatmap_df)
        .mark_rect()
        .encode(
            x=alt.X(
                "week:O",
                title=None,
                axis=alt.Axis(labels=False),
                scale=alt.Scale(paddingInner=0, paddingOuter=0),
            ),
            y=alt.Y(
                "day_name:N",
                title=None,
                sort=[" ", "Sun", "Sat", "Fri", "Thu", "Wed", "Tue", "Mon"],
                scale=alt.Scale(paddingInner=0, paddingOuter=0),
                axis=alt.Axis(
                    values=["Sun", "Thu", "Mon"],
                    domain=False,
                    ticks=False,
                    labelColor="#e5e7eb",
                ),
            ),
            color=alt.Color(
                "count:Q",
                scale=alt.Scale(domain=[0, 1], range=["#1e293b", "#22c55e"]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("date:N", title="Date"),
                alt.Tooltip("label:N", title=""),
            ],
        )
        .properties(height=140)
    )
    if not year_labels_df.empty:
        year_labels_df = year_labels_df.copy()
        year_labels_df["y_row"] = " "
        year_text_layer = (
            alt.Chart(year_labels_df)
            .mark_text(align="center", baseline="middle", fontSize=11, color="#94a3b8")
            .encode(
                x=alt.X(
                    "week_center:Q",
                    title=None,
                    scale=alt.Scale(zero=True),
                    axis=alt.Axis(labels=False, domain=False, ticks=False),
                ),
                y=alt.Y(
                    "y_row:N",
                    title=None,
                    sort=[" ", "Sun", "Sat", "Fri", "Thu", "Wed", "Tue", "Mon"],
                    axis=alt.Axis(labels=False, domain=False, ticks=False),
                ),
                text=alt.Text("year_label:N"),
            )
        )
        layers = [heatmap_chart, year_text_layer]
        if not year_boundaries_df.empty:
            rule_layer = (
                alt.Chart(year_boundaries_df)
                .mark_rule(stroke="white", strokeWidth=1)
                .encode(
                    x=alt.X(
                        "x_boundary:Q",
                        title=None,
                        scale=alt.Scale(zero=True, paddingInner=0, paddingOuter=0),
                        axis=alt.Axis(labels=False, domain=False, ticks=False),
                    ),
                )
            )
            layers.append(rule_layer)
        heatmap_chart = (
            alt.layer(*layers)
            .resolve_scale(x="shared", y="shared")
            .properties(background="transparent", height=165)
            .configure_axis(labelColor="#e5e7eb", domainColor="#4b5563")
            .configure_view(strokeWidth=0)
        )
    else:
        heatmap_chart = heatmap_chart.properties(
            background="transparent"
        ).configure_axis(
            labelColor="#e5e7eb", domainColor="#4b5563"
        ).configure_view(strokeWidth=0)
    return heatmap_chart


def reps_bar_chart(
    exercises_filtered: pd.DataFrame,
    date_strs: List[str],
    date_labels: List[str],
    selected: str,
    format_date_short: Callable[[str], str],
) -> alt.Chart:
    """
    Build the reps bar chart (single exercise or stacked by exercise).
    exercises_filtered must have date, exercise_total_reps, exercise_title.
    """
    n_dates = len(date_strs)
    bar_size = min(60, max(4, 5000 // max(1, n_dates)))

    if selected != "All":
        agg = (
            exercises_filtered.groupby("date", as_index=False)["exercise_total_reps"]
            .sum()
            .rename(columns={"exercise_total_reps": "reps"})
        )
        agg = agg.set_index("date").reindex(date_strs, fill_value=0).reset_index()
        agg["date_label"] = agg["date"].map(format_date_short)
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
        pivot["date_label"] = pivot["date"].map(format_date_short)
        value_vars = [c for c in pivot.columns if c not in ("date", "date_label")]
        pivot["total_reps"] = pivot[value_vars].sum(axis=1)
        pivot["trend"] = pivot["total_reps"].rolling(7, min_periods=1).mean()
        long = pivot.melt(
            id_vars=["date", "date_label", "trend"],
            value_vars=value_vars,
            var_name="exercise",
            value_name="reps",
        )
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
