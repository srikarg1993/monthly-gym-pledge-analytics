from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .theme import apply_theme, set_title_labels


def bar_qualifying_by_dom(df_month: pd.DataFrame, name: str):
    apply_theme()
    q = df_month[(df_month["name"] == name) & (df_month["burnt_250"])].copy()
    if q.empty:
        return None

    g = q.groupby("dom")["workout_date"].count().reset_index(name="count")
    fig, ax = plt.subplots(figsize=(6.2, 2.7))
    sns.barplot(data=g, x="dom", y="count", ax=ax)
    set_title_labels(ax, "Qualifying workouts by day-of-month", "Day", "Count")
    ax.tick_params(axis="x", labelrotation=0)
    return fig


def count_styles(fl: pd.DataFrame):
    apply_theme()
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    sns.countplot(data=fl, x="style", ax=ax)
    set_title_labels(ax, "Distribution of styles", "Style", "People")
    return fig


def bar_weekday(df_month: pd.DataFrame, *, name: str | None = None, title: str = ""):
    apply_theme()
    weekday_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    d = df_month[df_month["any_workout"]].copy()
    if name is not None:
        d = d[d["name"] == name]

    agg = (
        d.groupby("dow")["workout_date"]
        .nunique()
        .reindex(weekday_order)
        .reset_index(name="Unique workout days")
    )

    fig, ax = plt.subplots(figsize=(6.9, 3.2))
    sns.barplot(data=agg, x="dow", y="Unique workout days", ax=ax)
    set_title_labels(ax, title or "Workouts by weekday", "Weekday", "Unique days")
    ax.tick_params(axis="x", labelrotation=18)
    return fig


def line_mom(mom: pd.DataFrame, y: str, title: str, ylabel: str):
    apply_theme()
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    sns.lineplot(data=mom, x="month", y=y, marker="o", ax=ax)
    set_title_labels(ax, title, "Month", ylabel)
    ax.tick_params(axis="x", labelrotation=18)
    return fig
