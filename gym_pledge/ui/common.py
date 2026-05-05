import math

import altair as alt
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

ALT_TEXT = "#E4E6EB"
ALT_MUTED = "#9AA0AB"
ALT_GRID = "rgba(255,255,255,0.08)"
ALT_PRIMARY = "#60A5FA"
ALT_FOCUS = "#F59E0B"
ALT_WORKOUT = "#64748B"
ALT_CUTOFF = "#34D399"
ALT_TRACK = "rgba(255,255,255,0.12)"
ALT_SAGE = "#5FA68D"
ALT_COPPER = "#B7835A"
ALT_STEEL = "#6E88A6"
ALT_SLATE = "#5D6B7C"
ALT_MOSS = "#7B8C5A"


def style_plots():
    sns.set_theme(style="darkgrid", palette="muted")
    mpl.rcParams["figure.dpi"] = 150
    plt.rcParams["font.family"] = "Roboto"


def set_title_labels(ax, title, xlabel="", ylabel=""):
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=9, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=9, fontweight="bold")


def render_styled_table(df: pd.DataFrame, max_rows: int | None = None) -> None:
    """Render a styled HTML table with white bold headers to match page style.

    This helper centralizes HTML/CSS table rendering so pages can reuse it
    and keep styling consistent.
    """
    if df is None or df.empty:
        st.caption("No data to display.")
        return

    display_df = df.copy()
    if max_rows is not None:
        display_df = display_df.head(max_rows)

    table_html = """
    <style>
        .styled-table { width:100%; border-collapse:collapse; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; border-radius:8px; overflow:hidden; }
        .styled-table thead th { background: #0b1220; color: #fff; padding:12px 14px; text-align:left; font-weight:800; font-size:14px; }
        .styled-table tbody td { padding:12px 14px; border-bottom:1px solid rgba(255,255,255,0.04); color: #e6eef8; background-color: rgba(255,255,255,0.10); }
        .styled-table tbody tr:hover td { background: rgba(255,255,255,0.06); }
        .styled-table tbody tr:last-child td { border-bottom: none; }
    </style>
    <table class="styled-table">
        <thead><tr>
    """

    for col in display_df.columns:
        table_html += f"<th>{col}</th>"

    table_html += """
        </tr></thead><tbody>
    """

    for _, row in display_df.iterrows():
        table_html += "<tr>"
        for val in row:
            table_html += f"<td>{val}</td>"
        table_html += "</tr>"

    table_html += "</tbody></table>"

    st.markdown(table_html, unsafe_allow_html=True)


def render_card_start(title: str | None = None, subtitle: str | None = None) -> None:
    """Render opening HTML for a card-like container with optional title/subtitle."""
    if title:
        st.markdown(f"<div class='card'><h3>{title}</h3>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='small-muted'>{subtitle}</div>", unsafe_allow_html=True)


def render_card_end() -> None:
    """Close a card container previously opened with `render_card_start`."""
    st.markdown("</div>", unsafe_allow_html=True)


def render_seaborn_line(data, x: str, y: str, title: str, xlabel: str, ylabel: str, figsize=(7.2, 3.2)):
    """Create a seaborn line plot and return the Matplotlib figure.

    This centralizes styling, axis labels and tick rotation used in multiple pages.
    """
    style_plots()
    fig, ax = plt.subplots(figsize=figsize)
    sns.lineplot(data=data, x=x, y=y, marker="o", ax=ax)
    set_title_labels(ax, title, xlabel, ylabel)
    ax.tick_params(axis="x", labelrotation=18)
    return fig


def alt_chart_height(row_count: int, *, min_height: int = 240, max_height: int = 560, row_step: int = 34, padding: int = 28) -> int:
    rows = max(int(row_count), 1)
    return max(min_height, min(max_height, padding + rows * row_step))


def _configure_altair(chart):
    return (
        chart.configure_view(strokeOpacity=0)
        .configure_axis(
            labelColor=ALT_MUTED,
            titleColor=ALT_TEXT,
            domainColor=ALT_GRID,
            gridColor=ALT_GRID,
            tickColor=ALT_GRID,
            labelFontSize=12,
            titleFontSize=12,
            labelLimit=220,
        )
        .configure_title(color=ALT_TEXT, anchor="start")
    )


def alt_ranked_bar_chart(
    df: pd.DataFrame,
    *,
    label_col: str,
    value_col: str,
    tooltip_title: str,
    highlight_name: str | None = None,
    height: int | None = None,
    value_format: str = ".1f",
    bar_color: str = ALT_PRIMARY,
    highlight_color: str = ALT_FOCUS,
):
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame())

    chart_df = df.copy().reset_index(drop=True)
    chart_df["_highlight"] = chart_df[label_col].astype(str) == str(highlight_name)
    y_order = chart_df[label_col].tolist()
    domain_max = max(float(chart_df[value_col].max()), 1.0)
    padding = max(0.75, domain_max * 0.16)
    chart_height = height or alt_chart_height(len(chart_df))

    base = alt.Chart(chart_df)
    bars = base.mark_bar(cornerRadiusEnd=7, size=22).encode(
        x=alt.X(
            f"{value_col}:Q",
            title=tooltip_title,
            scale=alt.Scale(domain=[0, domain_max + padding], nice=False),
        ),
        y=alt.Y(
            f"{label_col}:N",
            sort=y_order,
            title=None,
            axis=alt.Axis(labelPadding=8),
        ),
        color=alt.condition(
            alt.datum._highlight,
            alt.value(highlight_color),
            alt.value(bar_color),
        ),
        tooltip=[
            alt.Tooltip(f"{label_col}:N", title="Participant"),
            alt.Tooltip(f"{value_col}:Q", title=tooltip_title, format=value_format),
        ],
    )

    labels = base.mark_text(
        align="left",
        baseline="middle",
        dx=6,
        color=ALT_TEXT,
        fontSize=12,
        fontWeight=700,
    ).encode(
        x=alt.X(f"{value_col}:Q", scale=alt.Scale(domain=[0, domain_max + padding], nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        text=alt.Text(f"{value_col}:Q", format=value_format),
    )

    return _configure_altair((bars + labels).properties(height=chart_height))


def alt_cutoff_progress_ladder(
    df: pd.DataFrame,
    *,
    label_col: str,
    qualifying_col: str,
    workout_col: str,
    cutoff: int,
    highlight_name: str | None = None,
    height: int | None = None,
):
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame())

    chart_df = df.copy().reset_index(drop=True)
    chart_df["_highlight"] = chart_df[label_col].astype(str) == str(highlight_name)
    chart_df["Progress label"] = (
        chart_df[qualifying_col].astype(int).astype(str)
        + "Q / "
        + chart_df[workout_col].astype(int).astype(str)
        + "W"
    )
    y_order = chart_df[label_col].tolist()
    domain_base = max(float(chart_df[[qualifying_col, workout_col]].max().max()), float(cutoff), 1.0)
    padding = max(1.0, domain_base * 0.16)
    domain = [0, domain_base + padding]
    chart_height = height or alt_chart_height(len(chart_df))

    base = alt.Chart(chart_df)
    workout_bars = base.mark_bar(cornerRadiusEnd=7, size=22, opacity=0.42).encode(
        x=alt.X(f"{workout_col}:Q", title="Days", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order, title=None, axis=alt.Axis(labelPadding=8)),
        color=alt.value(ALT_WORKOUT),
        tooltip=[
            alt.Tooltip(f"{label_col}:N", title="Participant"),
            alt.Tooltip(f"{qualifying_col}:Q", title="Qualifying days"),
            alt.Tooltip(f"{workout_col}:Q", title="Workout days"),
        ],
    )

    qualifying_bars = base.mark_bar(cornerRadiusEnd=7, size=14).encode(
        x=alt.X(f"{qualifying_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        color=alt.condition(
            alt.datum._highlight,
            alt.value(ALT_FOCUS),
            alt.value(ALT_PRIMARY),
        ),
    )

    cutoff_rule = alt.Chart(pd.DataFrame({"Cutoff": [cutoff]})).mark_rule(
        color=ALT_CUTOFF,
        strokeDash=[5, 4],
        strokeWidth=2,
    ).encode(x=alt.X("Cutoff:Q", scale=alt.Scale(domain=domain, nice=False)))

    cutoff_label = alt.Chart(pd.DataFrame({"Cutoff": [cutoff], "Label": [f"Cutoff {cutoff}"]})).mark_text(
        align="left",
        baseline="top",
        dx=6,
        dy=4,
        color=ALT_CUTOFF,
        fontSize=11,
        fontWeight=700,
    ).encode(
        x=alt.X("Cutoff:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.value(6),
        text="Label:N",
    )

    labels = base.mark_text(
        align="left",
        baseline="middle",
        dx=6,
        color=ALT_TEXT,
        fontSize=11,
        fontWeight=700,
    ).encode(
        x=alt.X(f"{workout_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        text="Progress label:N",
    )

    chart = (workout_bars + qualifying_bars + cutoff_rule + cutoff_label + labels).properties(height=chart_height)
    return _configure_altair(chart)


def alt_status_mix_bar(
    df: pd.DataFrame,
    *,
    category_col: str,
    count_col: str,
    share_col: str,
    highlight_name: str | None = None,
    height: int = 86,
):
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame())

    chart_df = df.copy().reset_index(drop=True)
    chart_df["_row"] = "Participants"
    chart_df["Segment label"] = chart_df.apply(
        lambda row: f"{row[category_col]} {int(row[count_col])}" if float(row[share_col]) >= 0.12 else "",
        axis=1,
    )

    color_scale = alt.Scale(
        domain=["Winner", "1-2 away", "Workout-rich", "Other"],
        range=["#34D399", "#F59E0B", "#60A5FA", "#475569"],
    )

    base = alt.Chart(chart_df)
    bars = base.mark_bar(cornerRadius=999).encode(
        x=alt.X(
            f"{share_col}:Q",
            stack="normalize",
            title=None,
            axis=alt.Axis(format="%"),
        ),
        y=alt.Y("_row:N", title=None, axis=None),
        color=alt.Color(f"{category_col}:N", scale=color_scale, legend=None),
        tooltip=[
            alt.Tooltip(f"{category_col}:N", title="Status"),
            alt.Tooltip(f"{count_col}:Q", title="Participants"),
            alt.Tooltip(f"{share_col}:Q", title="Share", format=".0%"),
        ],
    )

    labels = base.mark_text(
        color=ALT_TEXT,
        fontSize=11,
        fontWeight=700,
        baseline="middle",
    ).encode(
        x=alt.X(f"{share_col}:Q", stack="normalize"),
        y=alt.Y("_row:N"),
        detail=f"{category_col}:N",
        text="Segment label:N",
    )

    return _configure_altair((bars + labels).properties(height=height))


def alt_clinch_timeline(
    df: pd.DataFrame,
    *,
    label_col: str,
    date_col: str,
    highlight_name: str | None = None,
    height: int | None = None,
):
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame())

    chart_df = df.copy().reset_index(drop=True)
    dates = pd.to_datetime(chart_df[date_col], errors="coerce")
    chart_df["Clinch Day"] = dates.dt.day.fillna(0).astype(int)
    chart_df["Date label"] = dates.dt.strftime("%b %d").str.replace(" 0", " ", regex=False)
    chart_df["_highlight"] = chart_df[label_col].astype(str) == str(highlight_name)
    y_order = chart_df[label_col].tolist()
    domain_max = max(int(chart_df["Clinch Day"].max()), 1)
    chart_height = height or alt_chart_height(len(chart_df))

    base = alt.Chart(chart_df)
    points = base.mark_circle(size=180, opacity=0.95).encode(
        x=alt.X(
            "Clinch Day:Q",
            title="Day of month",
            scale=alt.Scale(domain=[1, domain_max + 2], nice=False),
        ),
        y=alt.Y(f"{label_col}:N", sort=y_order, title=None, axis=alt.Axis(labelPadding=8)),
        color=alt.condition(
            alt.datum._highlight,
            alt.value(ALT_FOCUS),
            alt.value(ALT_CUTOFF),
        ),
        tooltip=[
            alt.Tooltip(f"{label_col}:N", title="Winner"),
            alt.Tooltip(f"{date_col}:T", title="Hit cutoff on"),
        ],
    )

    labels = base.mark_text(
        align="left",
        baseline="middle",
        dx=10,
        color=ALT_TEXT,
        fontSize=11,
        fontWeight=700,
    ).encode(
        x=alt.X("Clinch Day:Q", scale=alt.Scale(domain=[1, domain_max + 2], nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        text="Date label:N",
    )

    return _configure_altair((points + labels).properties(height=chart_height))


def alt_diverging_half_chart(
    df: pd.DataFrame,
    *,
    category_col: str,
    value_col: str,
    absolute_col: str,
    highlight_name: str | None = None,
    height: int = 150,
):
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame())

    chart_df = df.copy().reset_index(drop=True)
    chart_df["_highlight"] = chart_df[category_col].astype(str) == str(highlight_name)
    y_order = chart_df[category_col].tolist()
    extent = max(float(chart_df[absolute_col].max()), 1.0)
    domain = [-(extent + 1), extent + 1]

    base = alt.Chart(chart_df)
    center = alt.Chart(pd.DataFrame({"Center": [0]})).mark_rule(
        color=ALT_GRID,
        strokeWidth=2,
    ).encode(x=alt.X("Center:Q", scale=alt.Scale(domain=domain, nice=False)))

    bars = base.mark_bar(cornerRadiusEnd=7, size=26).encode(
        x=alt.X(f"{value_col}:Q", title="Qualifying days", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{category_col}:N", sort=y_order, title=None),
        color=alt.condition(
            alt.datum._highlight,
            alt.value(ALT_FOCUS),
            alt.value(ALT_PRIMARY),
        ),
        tooltip=[
            alt.Tooltip(f"{category_col}:N", title="Half"),
            alt.Tooltip(f"{absolute_col}:Q", title="Qualifying days"),
        ],
    )

    neg_labels = base.transform_filter(alt.datum[value_col] < 0).mark_text(
        baseline="middle",
        align="right",
        dx=-12,
        color=ALT_TEXT,
        fontSize=12,
        fontWeight=700,
    ).encode(
        x=alt.X(f"{value_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{category_col}:N", sort=y_order),
        text=alt.Text(f"{absolute_col}:Q", format=".0f"),
    )

    pos_labels = base.transform_filter(alt.datum[value_col] >= 0).mark_text(
        baseline="middle",
        align="left",
        dx=12,
        color=ALT_TEXT,
        fontSize=12,
        fontWeight=700,
    ).encode(
        x=alt.X(f"{value_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{category_col}:N", sort=y_order),
        text=alt.Text(f"{absolute_col}:Q", format=".0f"),
    )

    return _configure_altair((center + bars + neg_labels + pos_labels).properties(height=height))


def alt_status_bucket_chart(
    df: pd.DataFrame,
    *,
    category_col: str,
    count_col: str,
    share_col: str,
    color_col: str,
    height: int = 220,
):
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame())

    chart_df = df.copy().reset_index(drop=True)
    total_people = max(int(chart_df[count_col].sum()), 1)
    chart_df["_track"] = total_people
    chart_df["Label"] = chart_df.apply(
        lambda row: f"{int(row[count_col])} people  |  {float(row[share_col]) * 100:.0f}%",
        axis=1,
    )
    y_order = chart_df[category_col].tolist()
    domain = [0, total_people + max(1, total_people * 0.22)]

    base = alt.Chart(chart_df)
    track = base.mark_bar(cornerRadiusEnd=9, size=24, opacity=0.24).encode(
        x=alt.X("_track:Q", title="Participants", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{category_col}:N", sort=y_order, title=None, axis=alt.Axis(labelPadding=10)),
        color=alt.value(ALT_TRACK),
    )

    bars = base.mark_bar(cornerRadiusEnd=9, size=18).encode(
        x=alt.X(f"{count_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{category_col}:N", sort=y_order),
        color=alt.Color(f"{color_col}:N", scale=None, legend=None),
        tooltip=[
            alt.Tooltip(f"{category_col}:N", title="Bucket"),
            alt.Tooltip(f"{count_col}:Q", title="Participants"),
            alt.Tooltip(f"{share_col}:Q", title="Share", format=".0%"),
        ],
    )

    labels = base.mark_text(
        align="left",
        baseline="middle",
        dx=10,
        color=ALT_TEXT,
        fontSize=12,
        fontWeight=700,
    ).encode(
        x=alt.X(f"{count_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{category_col}:N", sort=y_order),
        text="Label:N",
    )

    return _configure_altair((track + bars + labels).properties(height=height))


def alt_goal_ladder_chart(
    df: pd.DataFrame,
    *,
    label_col: str,
    qualifying_col: str,
    workout_col: str,
    cutoff: int,
    height: int | None = None,
):
    """Modernized horizontal goal-ladder chart.

    Visual language matches the modernized radar / race chart:
    - Pill-shaped track behind every row (very faint).
    - Glow halo under each qualifying bar (broad, low alpha).
    - Crisp top bar with bright accent (mint for winners, coral for in-progress).
    - Workout-day marker rendered as a halo + solid dot (no more harsh diamond).
    - Goal line is a dashed mint rule with a small "GOAL" chip on top.
    - Top three by qualifying days get medal emojis on their summary chip.
    """
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame())

    # Accent system, in the same vocabulary as the radar/race chart.
    MINT = "#5FE1C7"           # winners (active glow)
    MINT_GLOW = "rgba(95,225,199,0.18)"
    CORAL = "#FFB57A"          # in-progress
    CORAL_GLOW = "rgba(255,181,122,0.16)"
    TRACK = "rgba(255,255,255,0.05)"
    MARKER = "#9DCEFF"         # workout-day dot (cool blue, complementary)
    GOAL_COLOR = "#5FE1C7"
    LABEL_WHITE = "#FFFFFF"
    LABEL_SHADOW = "#0B1220"

    chart_df = df.copy().reset_index(drop=True)
    domain_end = max(
        float(chart_df[[qualifying_col, workout_col]].max().max()),
        float(cutoff),
        1.0,
    )
    chart_df["_track"] = domain_end
    chart_df["_is_winner"] = chart_df[qualifying_col].astype(int) >= cutoff

    # Medal emoji for top three qualifying-day counts (ties broken by row order
    # since `df` arrives sorted by the caller).
    medal_lookup = {0: "🥇 ", 1: "🥈 ", 2: "🥉 "}
    rank_order = (
        chart_df.sort_values(qualifying_col, ascending=False, kind="stable")
        .index.tolist()
    )
    medal_by_idx = {idx: medal_lookup.get(rank, "") for rank, idx in enumerate(rank_order)}
    chart_df["_medal"] = [medal_by_idx.get(i, "") for i in chart_df.index]

    chart_df["Summary"] = (
        chart_df["_medal"]
        + chart_df[qualifying_col].astype(int).astype(str)
        + "Q"
        + "  •  "
        + chart_df[workout_col].astype(int).astype(str)
        + "W"
    )
    chart_df["_label_x"] = chart_df[[qualifying_col, workout_col]].max(axis=1) + 0.25
    y_order = chart_df[label_col].tolist()
    domain = [0, domain_end + 3.5]
    x_tick_count = int(domain_end) + 4
    chart_height = height or alt_chart_height(
        len(chart_df), min_height=360, max_height=860, row_step=38
    )

    base = alt.Chart(chart_df)

    # 1. Faint pill track behind every row.
    track = base.mark_bar(cornerRadius=14, size=22, opacity=1.0).encode(
        x=alt.X(
            "_track:Q",
            title="Days",
            scale=alt.Scale(domain=domain, nice=False),
        ),
        y=alt.Y(
            f"{label_col}:N",
            sort=y_order,
            title=None,
            axis=alt.Axis(labelPadding=14),
        ),
        color=alt.value(TRACK),
    )

    # 2. Glow halo under the qualifying bar.
    qualifying_glow = base.mark_bar(cornerRadius=14, size=28, opacity=1.0).encode(
        x=alt.X(f"{qualifying_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        color=alt.condition(
            alt.datum._is_winner,
            alt.value(MINT_GLOW),
            alt.value(CORAL_GLOW),
        ),
    )

    # 3. Crisp accent bar on top.
    qualifying = base.mark_bar(cornerRadius=8, size=14).encode(
        x=alt.X(f"{qualifying_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        color=alt.condition(
            alt.datum._is_winner,
            alt.value(MINT),
            alt.value(CORAL),
        ),
        tooltip=[
            alt.Tooltip(f"{label_col}:N", title="Participant"),
            alt.Tooltip(f"{qualifying_col}:Q", title="Qualifying days"),
            alt.Tooltip(f"{workout_col}:Q", title="Workout days"),
        ],
    )

    # 4. Workout-day marker — halo + solid dot (radar/race vocabulary).
    workout_halo = base.mark_point(
        filled=True, size=320, opacity=0.18, strokeWidth=0,
    ).encode(
        x=alt.X(f"{workout_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        color=alt.value(MARKER),
    )
    workout_dot = base.mark_point(
        filled=True, size=110, opacity=1.0, stroke="#0B1220", strokeWidth=1.6,
    ).encode(
        x=alt.X(f"{workout_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        color=alt.value(MARKER),
        tooltip=[
            alt.Tooltip(f"{label_col}:N", title="Participant"),
            alt.Tooltip(f"{workout_col}:Q", title="Workout days"),
        ],
    )

    # 5. Goal rule + chip.
    cutoff_rule = alt.Chart(pd.DataFrame({"Cutoff": [cutoff]})).mark_rule(
        color=GOAL_COLOR,
        strokeDash=[6, 4],
        strokeWidth=2,
        opacity=0.85,
    ).encode(x=alt.X("Cutoff:Q", scale=alt.Scale(domain=domain, nice=False)))

    cutoff_label_shadow = alt.Chart(
        pd.DataFrame({"Cutoff": [cutoff], "Label": [f"GOAL · {cutoff}"]})
    ).mark_text(
        align="left", baseline="top", dx=8, dy=6,
        color=LABEL_SHADOW, stroke=LABEL_SHADOW, strokeWidth=4, strokeOpacity=0.85,
        fontSize=12, fontWeight=800,
    ).encode(
        x=alt.X("Cutoff:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.value(0),
        text="Label:N",
    )
    cutoff_label = alt.Chart(
        pd.DataFrame({"Cutoff": [cutoff], "Label": [f"GOAL · {cutoff}"]})
    ).mark_text(
        align="left", baseline="top", dx=8, dy=6,
        color=GOAL_COLOR, fontSize=12, fontWeight=800,
    ).encode(
        x=alt.X("Cutoff:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.value(0),
        text="Label:N",
    )

    # 6. Summary chip at the end of each row (with dark stroke shadow).
    label_shadow = base.mark_text(
        align="left", baseline="middle", dx=10, fontSize=13, fontWeight=800,
        color=LABEL_SHADOW, stroke=LABEL_SHADOW, strokeWidth=4, strokeOpacity=0.85,
    ).encode(
        x=alt.X("_label_x:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        text="Summary:N",
    )
    labels = base.mark_text(
        align="left", baseline="middle", dx=10, fontSize=13, fontWeight=800,
        color=LABEL_WHITE,
    ).encode(
        x=alt.X("_label_x:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        text="Summary:N",
    )

    chart = (
        track
        + qualifying_glow
        + qualifying
        + workout_halo
        + workout_dot
        + cutoff_rule
        + cutoff_label_shadow
        + cutoff_label
        + label_shadow
        + labels
    ).properties(height=chart_height, background="#0B1220")

    return (
        chart.configure_view(strokeOpacity=0, fill="#0B1220")
        .configure_axis(
            labelColor="#9AA0AB",
            titleColor="#E4E6EB",
            domainColor="rgba(255,255,255,0.15)",
            gridColor="rgba(255,255,255,0.05)",
            gridDash=[2, 4],
            tickColor="rgba(0,0,0,0)",
            labelFontSize=13,
            titleFontSize=12,
            titleFontWeight=700,
            labelLimit=240,
        )
        .configure_axisY(
            labelFontSize=14,
            labelColor="#FFFFFF",
            labelFontWeight="bold",
            grid=False,
            domainOpacity=0,
        )
        .configure_axisX(
            tickMinStep=1,
            tickCount=x_tick_count,
            format="d",
            titlePadding=12,
        )
        .configure_title(color="#FFFFFF", anchor="start")
    )


def alt_streak_heartbeat_chart(
    df: pd.DataFrame,
    *,
    day_col: str,
    streak_col: str,
    qualifying_col: str,
    day_label_col: str,
    month_days: int = 31,
    background_streaks: pd.DataFrame | None = None,  # deprecated, ignored
    height: int = 340,
):
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame())

    STREAK_LINE = "#34D399"
    STREAK_GLOW = "rgba(52,211,153,0.35)"
    POINT_ACTIVE = "#34D399"
    POINT_REST = "rgba(255,255,255,0.35)"
    LABEL_WHITE = "#FFFFFF"

    chart_df = df.copy().reset_index(drop=True)
    max_day = max(int(chart_df[day_col].max()), month_days)
    max_streak = max(int(chart_df[streak_col].max()), 1)

    x_domain = [0.5, max_day + 0.5]
    y_domain = [0, max_streak + 2]

    layers = []

    base = alt.Chart(chart_df)

    area = base.mark_area(
        line={"color": STREAK_LINE, "strokeWidth": 3.5},
        color=alt.Gradient(
            gradient="linear",
            stops=[
                alt.GradientStop(color=STREAK_GLOW, offset=0),
                alt.GradientStop(color="rgba(52,211,153,0.05)", offset=1),
            ],
            x1=0, y1=0, x2=0, y2=1,
        ),
        interpolate="monotone",
        opacity=1.0,
    ).encode(
        x=alt.X(
            f"{day_col}:Q",
            title="Day of Month",
            scale=alt.Scale(domain=x_domain, nice=False),
        ),
        y=alt.Y(
            f"{streak_col}:Q",
            title="Streak Length",
            scale=alt.Scale(domain=y_domain, nice=False),
        ),
        tooltip=[
            alt.Tooltip(f"{day_label_col}:N", title="Day"),
            alt.Tooltip(f"{streak_col}:Q", title="Streak"),
        ],
    )
    layers.append(area)

    rest_points = base.transform_filter(~alt.datum[qualifying_col]).mark_circle(
        size=55,
        color=POINT_REST,
        strokeWidth=0,
        opacity=0.7,
    ).encode(
        x=alt.X(f"{day_col}:Q", scale=alt.Scale(domain=x_domain, nice=False)),
        y=alt.Y(f"{streak_col}:Q", scale=alt.Scale(domain=y_domain, nice=False)),
    )
    layers.append(rest_points)

    active_points = base.transform_filter(alt.datum[qualifying_col]).mark_circle(
        size=160,
        color=POINT_ACTIVE,
        stroke="#0B1220",
        strokeWidth=2,
        opacity=1.0,
    ).encode(
        x=alt.X(f"{day_col}:Q", scale=alt.Scale(domain=x_domain, nice=False)),
        y=alt.Y(f"{streak_col}:Q", scale=alt.Scale(domain=y_domain, nice=False)),
        tooltip=[
            alt.Tooltip(f"{day_label_col}:N", title="Day"),
            alt.Tooltip(f"{streak_col}:Q", title="Streak"),
        ],
    )
    layers.append(active_points)

    chart = alt.layer(*layers).properties(height=height)

    return (
        chart.configure_view(strokeOpacity=0)
        .configure_axis(
            labelColor=LABEL_WHITE,
            titleColor=LABEL_WHITE,
            domainColor="rgba(255,255,255,0.08)",
            gridColor="rgba(255,255,255,0.06)",
            tickColor="rgba(255,255,255,0.08)",
            labelFontSize=14,
            titleFontSize=14,
            labelLimit=240,
        )
        .configure_axisX(
            tickMinStep=1,
            tickCount=max_day,
            format="d",
        )
        .configure_axisY(
            tickMinStep=1,
            tickCount=max_streak + 3,
            format="d",
        )
        .configure_title(color=LABEL_WHITE, anchor="start")
    )


def alt_race_lane_chart(
    df: pd.DataFrame,
    *,
    label_col: str,
    finish_col: str,
    total_days: int,
    finish_label_col: str,
    height: int | None = None,
):
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame())

    chart_df = df.copy().reset_index(drop=True)
    chart_df["_track"] = total_days
    chart_df["_label_x"] = chart_df[finish_col] + 0.7
    y_order = chart_df[label_col].tolist()
    domain = [0, total_days + 4]
    chart_height = height or alt_chart_height(len(chart_df), min_height=280, max_height=760, row_step=34)

    base = alt.Chart(chart_df)
    track = base.mark_bar(cornerRadiusEnd=10, size=22, opacity=0.18).encode(
        x=alt.X("_track:Q", title="Day of month", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order, title=None, axis=alt.Axis(labelPadding=10)),
        color=alt.value(ALT_TRACK),
    )

    race = base.mark_bar(cornerRadiusEnd=10, size=16).encode(
        x=alt.X(f"{finish_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        color=alt.value(ALT_SAGE),
        tooltip=[
            alt.Tooltip(f"{label_col}:N", title="Winner"),
            alt.Tooltip(f"{finish_col}:Q", title="Clinch day"),
        ],
    )

    marker = base.mark_point(
        filled=True,
        size=120,
        shape="diamond",
        color=ALT_COPPER,
        stroke="#0B1220",
        strokeWidth=1.5,
    ).encode(
        x=alt.X(f"{finish_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
    )

    labels = base.mark_text(
        align="left",
        baseline="middle",
        dx=10,
        color=ALT_TEXT,
        fontSize=11,
        fontWeight=700,
    ).encode(
        x=alt.X("_label_x:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        text=f"{finish_label_col}:N",
    )

    return _configure_altair((track + race + marker + labels).properties(height=chart_height))


def alt_delay_runway_chart(
    df: pd.DataFrame,
    *,
    label_col: str,
    delay_col: str,
    size_col: str | None = None,
    label_value_col: str,
    height: int | None = None,
):
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame())

    ZONE_ORDER = ["Same Day", "Â½â€“1 day", "2+ days"]
    ZONE_COLORS = [ALT_SAGE, ALT_COPPER, "#B56B6D"]
    ZONE_BG = ["#38534A", "#4E4A3E", "#513B3D"]

    chart_df = df.copy().reset_index(drop=True)
    chart_df = chart_df.dropna(subset=[delay_col]).reset_index(drop=True)
    if chart_df.empty:
        return alt.Chart(pd.DataFrame())
    chart_df[delay_col] = chart_df[delay_col].clip(lower=0.0)
    chart_df["Zone"] = pd.cut(
        chart_df[delay_col],
        bins=[-0.01, 0.5, 1.5, float("inf")],
        labels=ZONE_ORDER,
    ).astype(str)
    chart_df["Label"] = chart_df[label_value_col].map(lambda v: f"{v:.2f}d")
    chart_df["Zone"] = pd.Categorical(chart_df["Zone"], categories=ZONE_ORDER, ordered=True)
    chart_df = chart_df.sort_values(["Zone", delay_col], ascending=[True, True]).reset_index(drop=True)
    chart_df["_rank"] = chart_df.groupby("Zone", observed=True).cumcount()

    max_per_zone = max(int(chart_df.groupby("Zone", observed=True).size().max()), 1)
    chart_height = height or max(340, max_per_zone * 90 + 80)

    # Background bands
    bg_df = pd.DataFrame([{"Zone": z, "Color": c} for z, c in zip(ZONE_ORDER, ZONE_BG, strict=False)])
    bg_df["Zone"] = pd.Categorical(bg_df["Zone"], categories=ZONE_ORDER, ordered=True)
    bg_df["y1"] = -0.5
    bg_df["y2"] = max_per_zone - 0.5

    background = alt.Chart(bg_df).mark_rect(opacity=0.22).encode(
        x=alt.X("Zone:N", sort=ZONE_ORDER, axis=None),
        y=alt.Y("y1:Q", scale=alt.Scale(domain=[-0.5, max_per_zone - 0.5], nice=False), axis=None),
        y2="y2:Q",
        color=alt.Color("Color:N", scale=None, legend=None),
    )

    base = alt.Chart(chart_df)

    tooltip_fields = [
        alt.Tooltip(f"{label_col}:N", title="Participant"),
        alt.Tooltip(f"{delay_col}:Q", title="Avg log delay", format=".2f"),
    ]
    if size_col is not None:
        tooltip_fields.append(alt.Tooltip(f"{size_col}:Q", title="Logged workouts"))

    bubble_size = (
        alt.Size(f"{size_col}:Q", legend=None, scale=alt.Scale(range=[900, 4000]))
        if size_col is not None
        else alt.value(2000)
    )

    bubbles = base.mark_circle(
        filled=True,
        stroke="#0B1220",
        strokeWidth=2,
        opacity=0.92,
    ).encode(
        x=alt.X("Zone:N", sort=ZONE_ORDER, title=None,
                 axis=alt.Axis(labelAngle=0, labelColor="#FFFFFF", labelFontSize=15, labelFontWeight="bold",
                               domainOpacity=0, tickOpacity=0)),
        y=alt.Y("_rank:Q", scale=alt.Scale(domain=[-0.5, max_per_zone - 0.5], nice=False), axis=None,
                 sort="descending"),
        size=bubble_size,
        color=alt.Color(
            "Zone:N",
            scale=alt.Scale(domain=ZONE_ORDER, range=ZONE_COLORS),
            legend=None,
        ),
        tooltip=tooltip_fields,
    )

    name_labels = base.mark_text(
        color="#FFFFFF",
        fontSize=13,
        fontWeight=700,
        dy=-9,
    ).encode(
        x=alt.X("Zone:N", sort=ZONE_ORDER),
        y=alt.Y("_rank:Q", sort="descending"),
        text=f"{label_col}:N",
    )

    delay_labels = base.mark_text(
        color="rgba(255,255,255,0.7)",
        fontSize=11,
        fontWeight=600,
        dy=9,
    ).encode(
        x=alt.X("Zone:N", sort=ZONE_ORDER),
        y=alt.Y("_rank:Q", sort="descending"),
        text="Label:N",
    )

    chart = (background + bubbles + name_labels + delay_labels).properties(height=chart_height)
    return (
        chart.configure_view(strokeOpacity=0)
        .configure_axis(
            grid=False,
            domain=False,
            ticks=False,
            labels=False,
        )
        .configure_axisX(
            labels=True,
            labelColor="#FFFFFF",
            labelFontSize=15,
            labelFontWeight="bold",
        )
        .configure_title(color="#FFFFFF", anchor="start")
    )


def alt_group_split_chart(
    df: pd.DataFrame,
    *,
    label_col: str,
    left_col: str,
    right_col: str,
    style_col: str,
    height: int | None = None,
):
    """Diverging bar chart: first-half vs second-half qualifying workouts.

    Modernized to match the radar / race / ladder visual language:
    - Left half (Brick by Brick) uses mint glow ``#5FE1C7``.
    - Right half (All-Nighter) uses coral glow ``#FFB57A``.
    - Each bar sits on a soft glow underlay for depth.
    - A medal emoji is prepended to the top three rows by total workouts.
    - The style label on the right becomes a colored chip whose color
      reflects the participant's commitment style.
    """
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame())

    # --- Palette (matches the rest of the dashboard) ---
    MINT = "#5FE1C7"          # Brick by Brick / first-half
    MINT_GLOW = "#1F8C7A"
    CORAL = "#FFB57A"         # All-Nighter / second-half
    CORAL_GLOW = "#C77744"
    RASPBERRY = "#F47A8E"     # Crammer chip
    GRAY = "rgba(255,255,255,0.35)"

    style_chip_color = {
        "Front-loader": MINT,
        "Balanced": "#9DCEFF",
        "Crammer": RASPBERRY,
        "No qualifying": GRAY,
    }

    chart_df = df.copy().reset_index(drop=True)
    chart_df["_left_signed"] = -chart_df[left_col].astype(float)
    chart_df["_total"] = chart_df[left_col].astype(float) + chart_df[right_col].astype(float)

    # Medal emoji prefix for top 3 by total qualifying days.
    ranks = chart_df["_total"].rank(method="min", ascending=False)
    medal_map = {1: "🥇 ", 2: "🥈 ", 3: "🥉 "}
    chart_df["_display_label"] = [
        medal_map.get(int(r), "") + str(n)
        for r, n in zip(ranks, chart_df[label_col], strict=False)
    ]
    chart_df["_style_chip_color"] = chart_df[style_col].map(
        lambda s: style_chip_color.get(s, GRAY)
    )

    extent = max(float(chart_df[[left_col, right_col]].max().max()), 1.0)
    # Reserve a bit more right-side room for the style chip.
    domain = [-(extent + 2.6), extent + 5.2]
    chart_df["_style_label_x"] = chart_df[right_col].astype(float) + 1.1
    y_order = chart_df["_display_label"].tolist()
    chart_height = height or alt_chart_height(len(chart_df), min_height=340, max_height=860, row_step=34)

    base = alt.Chart(chart_df)

    # Center spine.
    center = alt.Chart(pd.DataFrame({"Center": [0]})).mark_rule(
        color="rgba(255,255,255,0.18)",
        strokeWidth=1.5,
    ).encode(x=alt.X("Center:Q", scale=alt.Scale(domain=domain, nice=False)))

    y_axis = alt.Axis(labelPadding=12, labelFontWeight="bold", labelFontSize=15)
    x_axis = alt.Axis(
        labels=False,
        ticks=False,
        domain=False,
        grid=False,
        title="First half  ←  |  →  Second half",
    )

    # Glow underlays: thicker, semi-transparent bars sitting behind the main
    # bars to fake an outer-glow halo.
    left_glow = base.mark_bar(cornerRadiusEnd=10, size=28, opacity=0.35).encode(
        x=alt.X(
            "_left_signed:Q",
            scale=alt.Scale(domain=domain, nice=False),
            axis=x_axis,
        ),
        y=alt.Y("_display_label:N", sort=y_order, title=None, axis=y_axis),
        color=alt.value(MINT_GLOW),
    )
    right_glow = base.mark_bar(cornerRadiusEnd=10, size=28, opacity=0.35).encode(
        x=alt.X(f"{right_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y("_display_label:N", sort=y_order),
        color=alt.value(CORAL_GLOW),
    )

    # Crisp main bars on top of the glow.
    left_bars = base.mark_bar(cornerRadiusEnd=8, size=18).encode(
        x=alt.X("_left_signed:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y("_display_label:N", sort=y_order),
        color=alt.value(MINT),
        tooltip=[
            alt.Tooltip(f"{label_col}:N", title="Participant"),
            alt.Tooltip(f"{left_col}:Q", title="First half"),
            alt.Tooltip(f"{right_col}:Q", title="Second half"),
            alt.Tooltip(f"{style_col}:N", title="Style"),
        ],
    )

    right_bars = base.mark_bar(cornerRadiusEnd=8, size=18).encode(
        x=alt.X(f"{right_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y("_display_label:N", sort=y_order),
        color=alt.value(CORAL),
    )

    # Numeric labels at bar tips with a dark text-stroke shadow so they read
    # against either palette.
    # Numeric labels at bar tips. We render the dark "chip" stroke as a
    # separate underlay layer so the colored fill stays vivid -- if we set
    # both fill and stroke on a single mark, Vega-Lite paints the stroke
    # on top of the fill and tiny digits look muddy.
    left_label_shadow = base.mark_text(
        align="right",
        baseline="middle",
        dx=-10,
        color="#0B1220",
        fontSize=14,
        fontWeight=800,
        stroke="#0B1220",
        strokeWidth=4,
        strokeOpacity=0.9,
    ).encode(
        x=alt.X("_left_signed:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y("_display_label:N", sort=y_order),
        text=alt.Text(f"{left_col}:Q", format=".0f"),
    )
    left_labels = base.mark_text(
        align="right",
        baseline="middle",
        dx=-10,
        color=MINT,
        fontSize=14,
        fontWeight=800,
    ).encode(
        x=alt.X("_left_signed:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y("_display_label:N", sort=y_order),
        text=alt.Text(f"{left_col}:Q", format=".0f"),
    )

    right_label_shadow = base.mark_text(
        align="left",
        baseline="middle",
        dx=10,
        color="#0B1220",
        fontSize=14,
        fontWeight=800,
        stroke="#0B1220",
        strokeWidth=4,
        strokeOpacity=0.9,
    ).encode(
        x=alt.X(f"{right_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y("_display_label:N", sort=y_order),
        text=alt.Text(f"{right_col}:Q", format=".0f"),
    )
    right_labels = base.mark_text(
        align="left",
        baseline="middle",
        dx=10,
        color=CORAL,
        fontSize=14,
        fontWeight=800,
    ).encode(
        x=alt.X(f"{right_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y("_display_label:N", sort=y_order),
        text=alt.Text(f"{right_col}:Q", format=".0f"),
    )

    # Style chip: dark shadow underlay then per-row colored text on top.
    style_label_shadow = base.mark_text(
        align="left",
        baseline="middle",
        dx=14,
        fontSize=13,
        fontWeight=700,
        color="#0B1220",
        stroke="#0B1220",
        strokeWidth=4,
        strokeOpacity=0.9,
    ).encode(
        x=alt.X("_style_label_x:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y("_display_label:N", sort=y_order),
        text=f"{style_col}:N",
    )
    style_labels = base.mark_text(
        align="left",
        baseline="middle",
        dx=14,
        fontSize=13,
        fontWeight=700,
    ).encode(
        x=alt.X("_style_label_x:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y("_display_label:N", sort=y_order),
        text=f"{style_col}:N",
        color=alt.Color("_style_chip_color:N", scale=None),
    )

    chart = (
        center
        + left_glow
        + right_glow
        + left_bars
        + right_bars
        + left_label_shadow
        + left_labels
        + right_label_shadow
        + right_labels
        + style_label_shadow
        + style_labels
    ).properties(
        height=chart_height,
        background="#0B1220",
        padding={"left": 8, "right": 8, "top": 8, "bottom": 8},
    )
    return (
        chart.configure_view(strokeOpacity=0, fill="#0B1220")
        .configure_axis(
            labelColor="#FFFFFF",
            titleColor="rgba(255,255,255,0.7)",
            domainColor="rgba(255,255,255,0.10)",
            gridColor="rgba(255,255,255,0.06)",
            tickColor="rgba(255,255,255,0.10)",
            labelFontSize=14,
            titleFontSize=13,
            titleFontWeight="bold",
            labelLimit=260,
        )
        .configure_axisY(
            labelFontSize=15,
            labelColor="#FFFFFF",
            labelFontWeight="bold",
        )
        .configure_title(color="#FFFFFF", anchor="start")
    )


def alt_goal_gap_chart(
    df: pd.DataFrame,
    *,
    label_col: str,
    qualifying_col: str,
    gap_col: str,
    cutoff: int,
    lower_bound: int | None = None,
    height: int | None = None,
):
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame())

    chart_df = df.copy().reset_index(drop=True)
    chart_df["_cutoff"] = cutoff
    chart_df["Gap label"] = chart_df[gap_col].map(lambda gap: f"{int(gap)} away")
    chart_df["_label_x"] = cutoff + 0.35
    min_value = int(chart_df[qualifying_col].min())
    domain_start = max(0, min_value - 1) if lower_bound is None else lower_bound
    domain = [domain_start, cutoff + 1.6]
    y_order = chart_df[label_col].tolist()
    chart_height = height or alt_chart_height(len(chart_df), min_height=240, max_height=520, row_step=34)

    base = alt.Chart(chart_df)
    gap_line = base.mark_rule(strokeWidth=3, opacity=0.85).encode(
        x=alt.X(f"{qualifying_col}:Q", title="Qualifying days near the goal", scale=alt.Scale(domain=domain, nice=False)),
        x2="_cutoff:Q",
        y=alt.Y(f"{label_col}:N", sort=y_order, title=None, axis=alt.Axis(labelPadding=10)),
        color=alt.value(ALT_COPPER),
        tooltip=[
            alt.Tooltip(f"{label_col}:N", title="Participant"),
            alt.Tooltip(f"{qualifying_col}:Q", title="Qualifying days"),
            alt.Tooltip(f"{gap_col}:Q", title="Days short"),
        ],
    )

    point = base.mark_circle(
        size=110,
        filled=True,
        color=ALT_SAGE,
        stroke="#0B1220",
        strokeWidth=1.5,
    ).encode(
        x=alt.X(f"{qualifying_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
    )

    cutoff_rule = alt.Chart(pd.DataFrame({"Cutoff": [cutoff]})).mark_rule(
        color=ALT_COPPER,
        strokeDash=[4, 4],
        strokeWidth=2,
    ).encode(x=alt.X("Cutoff:Q", scale=alt.Scale(domain=domain, nice=False)))

    cutoff_label = alt.Chart(pd.DataFrame({"Cutoff": [cutoff], "Label": [f"Goal {cutoff}"]})).mark_text(
        align="left",
        baseline="top",
        dx=8,
        dy=6,
        color=ALT_COPPER,
        fontSize=13,
        fontWeight=800,
    ).encode(
        x=alt.X("Cutoff:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.value(0),
        text="Label:N",
    )

    labels = base.mark_text(
        align="left",
        baseline="middle",
        dx=12,
        color="#FFFFFF",
        fontSize=14,
        fontWeight=700,
    ).encode(
        x=alt.X("_label_x:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        text="Gap label:N",
    )

    chart = (gap_line + point + cutoff_rule + cutoff_label + labels).properties(height=chart_height)
    return (
        chart.configure_view(strokeOpacity=0)
        .configure_axis(
            labelColor="#FFFFFF",
            titleColor="#FFFFFF",
            domainColor=ALT_GRID,
            gridColor=ALT_GRID,
            tickColor=ALT_GRID,
            labelFontSize=14,
            titleFontSize=14,
            labelLimit=240,
        )
        .configure_axisY(
            labelFontSize=15,
            labelColor="#FFFFFF",
            labelFontWeight="bold",
        )
        .configure_title(color="#FFFFFF", anchor="start")
    )


def alt_weekday_cadence_chart(
    df: pd.DataFrame,
    *,
    weekday_col: str,
    total_col: str,
    qualifying_col: str,
    weekday_order: list[str],
    height: int = 320,
):
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame())

    chart_df = df.copy().reset_index(drop=True)
    base = alt.Chart(chart_df)

    bars = base.mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, size=34, color=ALT_STEEL, opacity=0.82).encode(
        x=alt.X(f"{weekday_col}:N", sort=weekday_order, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y(f"{total_col}:Q", title="Workout count"),
        tooltip=[
            alt.Tooltip(f"{weekday_col}:N", title="Weekday"),
            alt.Tooltip(f"{total_col}:Q", title="All workouts"),
            alt.Tooltip(f"{qualifying_col}:Q", title="Qualifying workouts"),
        ],
    )

    line = base.mark_line(color=ALT_SAGE, strokeWidth=3, point={"filled": True, "size": 85}).encode(
        x=alt.X(f"{weekday_col}:N", sort=weekday_order),
        y=alt.Y(f"{qualifying_col}:Q"),
    )

    labels = base.mark_text(
        dy=-10,
        color="#FFFFFF",
        fontSize=14,
        fontWeight=700,
    ).encode(
        x=alt.X(f"{weekday_col}:N", sort=weekday_order),
        y=alt.Y(f"{total_col}:Q"),
        text=alt.Text(f"{total_col}:Q", format=".0f"),
    )

    chart = (bars + line + labels).properties(height=height)
    return (
        chart.configure_view(strokeOpacity=0)
        .configure_axis(
            labelColor="#FFFFFF",
            titleColor="#FFFFFF",
            domainColor=ALT_GRID,
            gridColor=ALT_GRID,
            tickColor=ALT_GRID,
            labelFontSize=14,
            titleFontSize=14,
            labelLimit=240,
        )
        .configure_axisY(
            labelFontSize=15,
            labelColor="#FFFFFF",
            labelFontWeight="bold",
        )
        .configure_title(color="#FFFFFF", anchor="start")
    )


def alt_weekday_bubble(counts: pd.DataFrame, weekday_order: list[str], color: str = "#4fa3ff", height: int = 260, size_range: tuple[int, int] = (300, 10000)):
    """Return an Altair bubble chart for weekday counts.

    Expects `counts` to have columns ['Weekday', 'count'] and uses `weekday_order`
    to ensure consistent ordering.
    """
    base = alt.Chart(counts)
    chart_height = height
    center_y = chart_height / 2

    backdrop = base.mark_circle(opacity=0.12, fillOpacity=0.12).encode(
        x=alt.X("Weekday:N", sort=weekday_order, title=None, axis=alt.Axis(labels=False, ticks=False, domain=False)),
        y=alt.value(center_y),
        size=alt.Size("count:Q", scale=alt.Scale(range=list(size_range)), legend=None),
        color=alt.value("#000"),
    )

    bubbles = base.mark_circle(opacity=0.95).encode(
        x=alt.X("Weekday:N", sort=weekday_order, title=None, axis=alt.Axis(labelAngle=0, labelColor="#9aa0ab")),
        y=alt.value(center_y),
        size=alt.Size("count:Q", title=None, legend=None, scale=alt.Scale(range=list(size_range))),
        color=alt.value(color),
        tooltip=[alt.Tooltip("Weekday:N"), alt.Tooltip("count:Q", title="Workouts")],
    )

    labels = base.mark_text(dy=0, color="#ffffff", fontSize=12, fontWeight=700).encode(
        x=alt.X("Weekday:N", sort=weekday_order),
        y=alt.value(center_y),
        text=alt.Text("count:Q"),
    )

    names = base.mark_text(dy=72, color="#ffffff", fontSize=13, fontWeight=700).encode(
        x=alt.X("Weekday:N", sort=weekday_order),
        y=alt.value(center_y),
        text=alt.Text("Weekday:N"),
    )

    return _configure_altair((backdrop + bubbles + labels + names).properties(height=chart_height))


def render_donut_days_left(completed: int, cutoff: int):
    """Render the small donut showing remaining days until cutoff and return a Matplotlib figure."""
    remaining = max(cutoff - completed, 0)

    fig, ax = plt.subplots()
    ax.pie(
        [completed, remaining],
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.2, edgecolor="none"),
    )

    ax.text(
        0,
        0.05,
        f"{remaining}",
        ha="center",
        va="center",
        fontsize=30,
        fontweight="800",
        color="#E4E6EB",
    )
    ax.text(
        0,
        -0.18,
        "days left",
        ha="center",
        va="center",
        fontsize=15,
        color="#A0A4B3",
    )
    ax.axis("equal")
    return fig, remaining


# ---------------------------------------------------------------------------
# Weekday Spider/Radar â€” matplotlib polar plot with dark theme
# ---------------------------------------------------------------------------

def weekday_radar_figure(
    *,
    weekday_order: list[str],
    group_qualifying: list[float],
    candidate_qualifying: list[float] | None = None,
    candidate_label: str | None = None,
    r_max: int | None = None,
    show_legend: bool = True,
):
    """Modern dark-theme radar (spider) chart for weekday cadence.

    Visual language:
    - Concentric circles drawn ourselves at major ticks (no harsh radial
      spokes), at very low alpha so the data shape leads.
    - Weekday labels rendered as soft uppercase pill chips on the outer ring.
    - Polygon fill is a multi-stop "glow": three stacked fills with decreasing
      alpha give a soft, modern luminous look instead of a flat translucent
      patch.
    - Vertex markers get a subtle outer halo so they pop against the fill.
    """
    weekdays = list(weekday_order)
    n = len(weekdays)
    if len(group_qualifying) != n:
        raise ValueError("group_qualifying length must match weekday_order length")
    group = [float(v) for v in group_qualifying]
    candidate = (
        [float(v) for v in candidate_qualifying] if candidate_qualifying is not None else None
    )
    if candidate is not None and len(candidate) != n:
        raise ValueError("candidate_qualifying length must match weekday_order length")

    angles = [2 * math.pi * i / n for i in range(n)]
    angles_closed = angles + angles[:1]
    group_closed = group + group[:1]

    fig, ax = plt.subplots(figsize=(7.0, 7.0), subplot_kw={"projection": "polar"})
    fig.patch.set_alpha(0)
    ax.set_facecolor("#0B1220")

    # Rotate so Monday sits at the top, going clockwise.
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)

    # Radial scale: integer ticks up to the data max (or caller-supplied r_max).
    if r_max is None:
        data_max = max(max(group, default=0), max(candidate or [0], default=0), 1)
        r_max = max(int(math.ceil(data_max * 1.1)), 2)
    r_max = max(int(r_max), 2)
    step = max(1, r_max // 4)
    ring_levels = list(range(step, r_max + 1, step))
    ax.set_ylim(0, r_max)

    # --- Strip out matplotlib's default polar chrome ---
    ax.set_yticks([])
    ax.set_yticklabels([])
    ax.set_xticks([])
    ax.set_xticklabels([])
    ax.spines["polar"].set_visible(False)
    ax.grid(False)

    # --- Custom concentric ring backdrop ---
    ring_theta = [2 * math.pi * i / 200 for i in range(201)]
    for level in ring_levels:
        is_outer = level == ring_levels[-1]
        ax.plot(
            ring_theta,
            [level] * len(ring_theta),
            color=(1, 1, 1, 0.18 if is_outer else 0.07),
            linewidth=1.1 if is_outer else 0.9,
            zorder=1,
        )
        # Faint numeric chip on the right side of each ring (~3 o'clock).
        ax.text(
            math.radians(102),
            level,
            f"{level}",
            color="#5D6B7C",
            fontsize=9,
            ha="center",
            va="center",
            zorder=2,
        )

    # --- Weekday labels as soft pill chips on the outer ring ---
    chip_r = r_max * 1.18
    for ang, name in zip(angles, weekdays, strict=False):
        ax.text(
            ang,
            chip_r,
            name[:3].upper(),
            color="#E4E6EB",
            fontsize=11,
            fontweight="bold",
            ha="center",
            va="center",
            bbox={
                "boxstyle": "round,pad=0.4",
                "facecolor": (0.42, 0.53, 0.65, 0.16),  # steel @ low alpha
                "edgecolor": (1, 1, 1, 0.10),
                "linewidth": 0.8,
            },
            zorder=8,
        )

    teal = "#6E88A6"           # group accent (cool steel) â€” used when overlay
    glow = "#5FE1C7"           # mint glow accent
    glow_dark = "#1F8C7A"
    coral = "#FFB57A"          # warm accent for the group-only (left) chart
    coral_dark = "#C77744"

    # When there's no overlay, treat the group polygon as the *feature* and
    # render it with the modern glow style (warm coral) so a single-spider
    # chart still feels alive. When a candidate polygon is present, the group
    # backdrop dims into the cool steel role and the candidate gets the glow.
    overlay_mode = candidate is not None

    if overlay_mode:
        # --- Group backdrop (cool steel, dim) ---
        for alpha in (0.05, 0.08, 0.10):
            ax.fill(angles_closed, group_closed, color=teal, alpha=alpha, zorder=2)
        ax.plot(angles_closed, group_closed, color=teal, linewidth=1.6,
                label="Group qualifying", alpha=0.85, zorder=3)
        for ang, val in zip(angles, group, strict=False):
            if val > 0:
                ax.plot(ang, val, "o", color=teal, markersize=5,
                        markeredgecolor=(1, 1, 1, 0.25), markeredgewidth=1.0, zorder=4)
    else:
        # --- Group is the only polygon: glow it in coral ---
        for alpha in (0.06, 0.12, 0.22):
            ax.fill(angles_closed, group_closed, color=coral, alpha=alpha, zorder=5)
        ax.plot(angles_closed, group_closed, color=coral, linewidth=2.6,
                label="Group qualifying", zorder=6,
                solid_joinstyle="round", solid_capstyle="round")
        for ang, val in zip(angles, group, strict=False):
            if val > 0:
                ax.plot(ang, val, "o", color=coral, markersize=14,
                        alpha=0.18, markeredgecolor="none", zorder=6.5)
                ax.plot(ang, val, "o", color=coral, markersize=7,
                        markeredgecolor=coral_dark, markeredgewidth=1.4, zorder=7)
                ax.text(ang, val + r_max * 0.08, f"{int(val)}",
                        ha="center", va="center",
                        color="#FFFFFF", fontsize=11, fontweight="bold",
                        bbox={
                            "boxstyle": "round,pad=0.25",
                            "facecolor": (0.04, 0.07, 0.13, 0.85),
                            "edgecolor": (1.0, 0.71, 0.48, 0.55),
                            "linewidth": 0.9,
                        },
                        zorder=9)

    # --- Candidate polygon overlay (mint glow) ---
    if candidate is not None:
        candidate_closed = candidate + candidate[:1]
        cand_label = f"{candidate_label or 'Candidate'} qualifying"
        for alpha in (0.06, 0.12, 0.22):
            ax.fill(angles_closed, candidate_closed, color=glow, alpha=alpha, zorder=5)
        ax.plot(angles_closed, candidate_closed, color=glow,
                linewidth=2.6, label=cand_label, zorder=6,
                solid_joinstyle="round", solid_capstyle="round")
        for ang, val in zip(angles, candidate, strict=False):
            if val > 0:
                ax.plot(ang, val, "o", color=glow, markersize=14,
                        alpha=0.18, markeredgecolor="none", zorder=6.5)
                ax.plot(ang, val, "o", color=glow, markersize=7,
                        markeredgecolor=glow_dark, markeredgewidth=1.4, zorder=7)
                ax.text(ang, val + r_max * 0.08, f"{int(val)}",
                        ha="center", va="center",
                        color="#FFFFFF", fontsize=11, fontweight="bold",
                        bbox={
                            "boxstyle": "round,pad=0.25",
                            "facecolor": (0.04, 0.07, 0.13, 0.85),
                            "edgecolor": (0.37, 0.88, 0.78, 0.55),
                            "linewidth": 0.9,
                        },
                        zorder=9)

    legend = ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.18, 1.10),
        frameon=False,
        fontsize=11,
        labelcolor="#FFFFFF",
    )
    for text in legend.get_texts():
        text.set_fontweight("bold")
    if not show_legend:
        legend.set_visible(False)

    # Pad the radial axis so chip labels don't get clipped.
    ax.set_ylim(0, r_max * 1.32)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Fastest Winner â€” podium + finish-line timeline
# ---------------------------------------------------------------------------

PODIUM_THEMES = [
    # (medal emoji, gradient, accent)
    ("\U0001F947", "linear-gradient(160deg, #FFD75A 0%, #C99216 100%)", "#FFD75A"),  # gold
    ("\U0001F948", "linear-gradient(160deg, #DCE3EA 0%, #8A95A1 100%)", "#DCE3EA"),  # silver
    ("\U0001F949", "linear-gradient(160deg, #E3A37D 0%, #8C5A36 100%)", "#E3A37D"),  # bronze
]


def render_fastest_winner_podium(
    df: pd.DataFrame,
    *,
    name_col: str = "Name",
    day_col: str = "Clinch Day",
    date_col: str = "Hit cutoff on",
    cutoff: int | None = None,
) -> None:
    """Render top-3 podium cards (gold / silver / bronze) for fastest finishers.

    Visual emphasis on the gold winner via a slightly taller card and crown
    glyph. Falls back gracefully when fewer than 3 winners exist.
    """
    if df is None or df.empty:
        return

    top = df.head(3).reset_index(drop=True)

    # Render order matches podium feel: silver | gold | bronze (gold tallest, center)
    if len(top) == 3:
        order = [1, 0, 2]
        heights = ["220px", "260px", "200px"]
        crowns = ["", "\U0001F451", ""]
    elif len(top) == 2:
        order = [1, 0]
        heights = ["220px", "260px"]
        crowns = ["", "\U0001F451"]
    else:
        order = [0]
        heights = ["260px"]
        crowns = ["\U0001F451"]

    cols = st.columns(len(order), gap="medium")
    for col, slot, height, crown in zip(cols, order, heights, crowns, strict=False):
        row = top.iloc[slot]
        rank = slot + 1  # 1-based rank: gold=1
        medal, gradient, accent = PODIUM_THEMES[slot]
        date_val = row[date_col]
        date_str = pd.to_datetime(date_val, errors="coerce")
        date_str = date_str.strftime("%b %d") if pd.notna(date_str) else ""
        cutoff_text = f"{cutoff} qualifying days" if cutoff else "Cutoff"
        crown_html = (
            f"<div style='font-size:22px;line-height:1;margin-bottom:4px;'>{crown}</div>"
            if crown
            else ""
        )

        # NOTE: Streamlit's markdown processor treats lines indented 4+ spaces
        # as a code block. Keep this HTML on a single line so it renders as
        # raw HTML on every column (not just the first one).
        card_html = (
            f"<div style=\"position:relative;background:rgba(15,22,40,0.9);"
            f"border:1px solid rgba(255,255,255,0.10);border-radius:18px;"
            f"padding:18px 16px 14px;text-align:center;height:{height};"
            f"display:flex;flex-direction:column;justify-content:flex-end;"
            f"box-shadow:0 6px 24px rgba(0,0,0,0.45);border-top:4px solid {accent};\">"
            f"<div style='position:absolute;top:-22px;left:50%;transform:translateX(-50%);"
            f"background:{gradient};color:#1a1a1a;width:48px;height:48px;border-radius:50%;"
            f"display:flex;align-items:center;justify-content:center;font-size:24px;"
            f"box-shadow:0 4px 12px rgba(0,0,0,0.5);"
            f"border:2px solid rgba(255,255,255,0.25);'>{medal}</div>"
            f"{crown_html}"
            f"<div style='font-size:13px;color:{accent};font-weight:800;letter-spacing:0.12em;"
            f"text-transform:uppercase;'>Rank #{rank}</div>"
            f"<div style='font-size:22px;font-weight:800;color:#fff;margin:6px 0 4px;"
            f"letter-spacing:-0.01em;'>{row[name_col]}</div>"
            f"<div style='font-size:13px;color:#9aa0ab;'>Hit {cutoff_text} on</div>"
            f"<div style='font-size:18px;font-weight:700;color:#fff;margin-top:2px;'>{date_str}</div>"
            f"<div style='margin-top:10px;padding:6px 10px;border-radius:999px;"
            f"background:rgba(255,255,255,0.06);font-size:12px;font-weight:700;"
            f"color:{accent};display:inline-block;align-self:center;'>"
            f"Day {int(row[day_col])}</div>"
            f"</div>"
        )
        with col:
            st.markdown(card_html, unsafe_allow_html=True)


def alt_finish_line_chart(
    df: pd.DataFrame,
    *,
    label_col: str,
    finish_col: str,
    total_days: int,
    height: int = 180,
):
    """Horizontal day-of-month timeline showing every finisher as a medal.

    Used below the top-3 podium to give the rest of the field their moment.
    Skips the top-3 so the podium stays focused.
    """
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame())

    chart_df = df.iloc[3:].copy().reset_index(drop=True)
    if chart_df.empty:
        return alt.Chart(pd.DataFrame())

    chart_df["_y"] = 0
    domain = [0.5, total_days + 0.5]

    base = alt.Chart(chart_df)

    # Finish line marker at right edge
    finish_rule = alt.Chart(pd.DataFrame({"x": [total_days + 0.5]})).mark_rule(
        color="#F472B6", strokeDash=[4, 4], strokeWidth=2,
    ).encode(x=alt.X("x:Q", scale=alt.Scale(domain=domain, nice=False)))

    track = alt.Chart(pd.DataFrame({"x": [0.5], "x2": [total_days + 0.5], "y": [0]})).mark_rule(
        color="rgba(255,255,255,0.10)", strokeWidth=10,
    ).encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=domain, nice=False), axis=alt.Axis(title="Day of month")),
        x2="x2:Q",
        y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[-1, 1])),
    )

    medals = base.mark_text(
        text="\U0001F3C5",  # sports medal
        fontSize=26,
    ).encode(
        x=alt.X(f"{finish_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y("_y:Q", scale=alt.Scale(domain=[-1, 1]), axis=None),
        tooltip=[
            alt.Tooltip(f"{label_col}:N", title="Finisher"),
            alt.Tooltip(f"{finish_col}:Q", title="Clinch day"),
        ],
    )

    name_labels = base.mark_text(
        color="#FFFFFF",
        fontSize=12,
        fontWeight=700,
        dy=-26,
    ).encode(
        x=alt.X(f"{finish_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y("_y:Q", scale=alt.Scale(domain=[-1, 1]), axis=None),
        text=f"{label_col}:N",
    )

    day_labels = base.mark_text(
        color="rgba(255,255,255,0.7)",
        fontSize=11,
        dy=24,
    ).encode(
        x=alt.X(f"{finish_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y("_y:Q", scale=alt.Scale(domain=[-1, 1]), axis=None),
        text=alt.Text(f"{finish_col}:Q", format="d"),
    )

    chart = (track + finish_rule + medals + name_labels + day_labels).properties(height=height)
    return (
        chart.configure_view(strokeOpacity=0)
        .configure_axis(
            labelColor="#FFFFFF",
            titleColor="#FFFFFF",
            domainColor="rgba(255,255,255,0.08)",
            gridColor="rgba(255,255,255,0.06)",
            tickColor="rgba(255,255,255,0.08)",
            labelFontSize=12,
            titleFontSize=12,
        )
        .configure_axisX(tickMinStep=1, tickCount=min(total_days, 16), format="d")
    )


# ---------------------------------------------------------------------------
# Lazy Logger â€” labeled bubble clusters
# ---------------------------------------------------------------------------

LAZY_ZONES = [
    # (zone_id, short_label, headline, subtitle, color, icon)
    ("on_it",       "On It",          "Same-day loggers",     "Logged the day they trained", "#5FE1C7", "⚡"),
    ("catching_up", "Catching Up",    "Half a day to a day late",  "Usually logged the next morning", "#FFB57A", "⏱️"),
    ("falling_behind", "Falling Behind", "Two or more days late", "Catching up in batches", "#F47A8E", "🐢"),
]
LAZY_ZONE_IDS = [z[0] for z in LAZY_ZONES]
LAZY_ZONE_LABELS = {z[0]: z[1] for z in LAZY_ZONES}
LAZY_ZONE_COLORS = {z[0]: z[4] for z in LAZY_ZONES}


def classify_lazy_zone(delay_days: float) -> str:
    """Bucket an average log delay (days) into one of three zones.

    Bucket boundaries match the legacy implementation exactly so backward-
    compatible counts stay stable: <= 0.5d -> on_it, <= 1.5d -> catching_up,
    > 1.5d -> falling_behind.
    """
    try:
        d = float(delay_days)
    except (TypeError, ValueError):
        return "on_it"
    if d <= 0.5:
        return "on_it"
    if d <= 1.5:
        return "catching_up"
    return "falling_behind"


def pack_lazy_bubbles(df: pd.DataFrame, *, name_col: str, delay_col: str, size_col: str) -> pd.DataFrame:
    """Return df with deterministic (x, y) positions inside each zone.

    Layout strategy: per zone, sort participants by size desc, then place on
    a centered honeycomb-ish grid. cols = ceil(sqrt(N)), rows wrap. Adds a
    tiny deterministic jitter (seeded by name hash) for organic clustering.

    Output columns added: ``Zone``, ``ZoneLabel``, ``Color``, ``FirstName``,
    ``x`` (within-zone column index, centered), ``y`` (row index, centered).
    """
    if df is None or df.empty:
        cols = list(df.columns) if df is not None else []
        return pd.DataFrame(columns=[*cols, "Zone", "ZoneLabel", "Color", "FirstName", "x", "y"])

    out = df.copy().reset_index(drop=True)
    out["Zone"] = out[delay_col].map(classify_lazy_zone)
    out["ZoneLabel"] = out["Zone"].map(LAZY_ZONE_LABELS)
    out["Color"] = out["Zone"].map(LAZY_ZONE_COLORS)
    out["FirstName"] = out[name_col].astype(str).str.split().str[0]

    pieces: list[pd.DataFrame] = []
    for zone_id in LAZY_ZONE_IDS:
        z = out[out["Zone"] == zone_id].copy()
        if z.empty:
            continue
        # Larger bubbles placed first so the cluster reads center-heavy.
        z = z.sort_values([size_col, name_col], ascending=[False, True]).reset_index(drop=True)
        n = len(z)
        cols_per_row = max(1, math.ceil(math.sqrt(n)))
        positions: list[tuple[float, float]] = []
        for i in range(n):
            row = i // cols_per_row
            col = i % cols_per_row
            # Center each row horizontally.
            row_count = min(cols_per_row, n - row * cols_per_row)
            x = (col - (row_count - 1) / 2.0)
            # Stagger alternate rows for a honeycomb feel.
            if row % 2 == 1:
                x += 0.5
            y = -row  # rows go downward
            # Deterministic jitter from name hash so layout is stable per name.
            seed = sum(ord(c) for c in str(z.iloc[i][name_col]))
            jitter_x = ((seed % 17) - 8) / 60.0   # ~+-0.13
            jitter_y = ((seed % 13) - 6) / 60.0   # ~+-0.10
            positions.append((x + jitter_x, y + jitter_y))
        z["x"], z["y"] = zip(*positions, strict=False)
        pieces.append(z)

    if not pieces:
        return out.assign(x=0.0, y=0.0)
    return pd.concat(pieces, ignore_index=True)


def alt_lazy_zone_clusters(
    df: pd.DataFrame,
    *,
    name_col: str = "Name",
    delay_col: str = "Avg. Log Delay (Days)",
    size_col: str = "Logged Workouts",
    height: int = 460,
):
    """Three labeled zones with bubble clusters of participants inside each.

    Expects ``df`` already enriched by :func:`pack_lazy_bubbles`. All layers
    use a shared quantitative x/y scale so Altair can merge them cleanly â€”
    mixing pixel coordinates (``alt.value(...)``) with quantitative encodings
    in a layered chart silently produces a blank chart.
    """
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame())

    # --- compute zone bands along x ---
    zone_width = 10.0
    zone_gap = 1.6
    total_w = len(LAZY_ZONES) * zone_width + (len(LAZY_ZONES) - 1) * zone_gap

    # --- map each bubble's within-zone (x,y) to absolute chart coords ---
    bubble_df = df.copy()
    zone_cx_map: dict[str, float] = {}
    band_rows: list[dict] = []
    for idx, (zone_id, _label, _headline, _subtitle, color, _icon) in enumerate(LAZY_ZONES):
        x0 = idx * (zone_width + zone_gap)
        x1 = x0 + zone_width
        zone_cx_map[zone_id] = (x0 + x1) / 2
        band_rows.append({"Zone": zone_id, "x0": x0, "x1": x1, "Color": color})

    bubble_df["_zone_cx"] = bubble_df["Zone"].map(zone_cx_map)
    half_band = zone_width / 2 - 1.0
    max_abs_x = (
        bubble_df.groupby("Zone", observed=True)["x"]
        .apply(lambda s: max(abs(s.min()), abs(s.max()), 1.0))
        .to_dict()
    )
    bubble_df["_scale"] = bubble_df["Zone"].map(lambda z: half_band / max(max_abs_x.get(z, 1.0), 1.0))
    bubble_df["abs_x"] = bubble_df["_zone_cx"] + bubble_df["x"] * bubble_df["_scale"]
    bubble_df["abs_y"] = bubble_df["y"]

    # Y axis: top reserved for headline text, bottom reserved for count text.
    cluster_min = float(bubble_df["abs_y"].min())
    cluster_max = float(bubble_df["abs_y"].max())
    headline_y = cluster_max + 4.0
    subtitle_y = cluster_max + 3.2
    sub2_y = cluster_max + 2.6
    count_y = cluster_min - 1.6

    y_domain = [count_y - 0.6, headline_y + 0.8]
    x_domain = [-0.6, total_w + 0.6]

    counts = bubble_df.groupby("Zone", observed=True).size().to_dict()
    bands_df = pd.DataFrame(band_rows)
    bands_df["y0"] = y_domain[0]
    bands_df["y1"] = y_domain[1]

    name_df = pd.DataFrame(
        [
            {
                "Zone": zid,
                "x": zone_cx_map[zid],
                "Headline": headline,
                "Subtitle": subtitle,
                "Label": label,
                "Color": color,
            }
            for (zid, label, headline, subtitle, color, _icon) in LAZY_ZONES
        ]
    )
    count_df = pd.DataFrame(
        [
            {"Zone": zid, "x": zone_cx_map[zid], "Count": int(counts.get(zid, 0))}
            for (zid, _l, _h, _s, _c, _i) in LAZY_ZONES
        ]
    )

    x_enc = alt.X("abs_x:Q", scale=alt.Scale(domain=x_domain, nice=False), axis=None)
    y_enc = alt.Y("abs_y:Q", scale=alt.Scale(domain=y_domain, nice=False), axis=None)

    bands = alt.Chart(bands_df).mark_rect(opacity=0.10, cornerRadius=18).encode(
        x=alt.X("x0:Q", scale=alt.Scale(domain=x_domain, nice=False), axis=None),
        x2="x1:Q",
        y=alt.Y("y0:Q", scale=alt.Scale(domain=y_domain, nice=False), axis=None),
        y2="y1:Q",
        color=alt.Color("Color:N", scale=None, legend=None),
    )

    band_borders = alt.Chart(bands_df).mark_rect(
        filled=False, strokeWidth=1.5, cornerRadius=18, opacity=0.55
    ).encode(
        x=alt.X("x0:Q", scale=alt.Scale(domain=x_domain, nice=False), axis=None),
        x2="x1:Q",
        y=alt.Y("y0:Q", scale=alt.Scale(domain=y_domain, nice=False), axis=None),
        y2="y1:Q",
        stroke=alt.Color("Color:N", scale=None, legend=None),
    )

    headline_labels = alt.Chart(name_df.assign(_y=headline_y)).mark_text(
        align="center", fontSize=18, fontWeight=800,
    ).encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=x_domain, nice=False), axis=None),
        y=alt.Y("_y:Q", scale=alt.Scale(domain=y_domain, nice=False), axis=None),
        text="Label:N",
        color=alt.Color("Color:N", scale=None, legend=None),
    )

    subtitle_labels = alt.Chart(name_df.assign(_y=subtitle_y)).mark_text(
        align="center", fontSize=12, fontWeight=600, color="rgba(255,255,255,0.78)",
    ).encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=x_domain, nice=False), axis=None),
        y=alt.Y("_y:Q", scale=alt.Scale(domain=y_domain, nice=False), axis=None),
        text="Headline:N",
    )

    sub2_labels = alt.Chart(name_df.assign(_y=sub2_y)).mark_text(
        align="center", fontSize=11, color="rgba(255,255,255,0.55)",
    ).encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=x_domain, nice=False), axis=None),
        y=alt.Y("_y:Q", scale=alt.Scale(domain=y_domain, nice=False), axis=None),
        text="Subtitle:N",
    )

    count_labels = alt.Chart(count_df.assign(_y=count_y)).mark_text(
        align="center", fontSize=13, fontWeight=800, color="rgba(255,255,255,0.55)",
    ).encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=x_domain, nice=False), axis=None),
        y=alt.Y("_y:Q", scale=alt.Scale(domain=y_domain, nice=False), axis=None),
        text=alt.Text("Count:Q", format="d"),
    )

    bubbles = alt.Chart(bubble_df).mark_circle(
        opacity=0.92, stroke="#0B1220", strokeWidth=2,
    ).encode(
        x=x_enc,
        y=y_enc,
        size=alt.Size(f"{size_col}:Q", legend=None, scale=alt.Scale(range=[1400, 5200])),
        color=alt.Color("Color:N", scale=None, legend=None),
        tooltip=[
            alt.Tooltip(f"{name_col}:N", title="Participant"),
            alt.Tooltip("ZoneLabel:N", title="Zone"),
            alt.Tooltip(f"{delay_col}:Q", title="Avg log delay", format=".2f"),
            alt.Tooltip(f"{size_col}:Q", title="Logged workouts"),
        ],
    )

    bubble_labels = alt.Chart(bubble_df).mark_text(
        color="#FFFFFF", fontSize=12, fontWeight=700,
    ).encode(
        x=x_enc,
        y=y_enc,
        text="FirstName:N",
    )

    chart = (
        bands + band_borders
        + headline_labels + subtitle_labels + sub2_labels + count_labels
        + bubbles + bubble_labels
    ).properties(height=height)

    return (
        chart.configure_view(strokeOpacity=0)
        .configure_axis(grid=False, domain=False, ticks=False, labels=False)
    )


# ---------------------------------------------------------------------------
# Lazy Logger â€” HTML bubble clusters (true tight packing per zone)
# ---------------------------------------------------------------------------

LAZY_BUBBLE_GAP = 6              # px gap between bubbles
LAZY_BUBBLE_MIN_R = 26           # px
LAZY_BUBBLE_MAX_R = 56           # px
# Pixels added per character beyond the minimum. Tuned so a 10-char name still
# fits inside the bubble at the chosen font ratio without overflow.
LAZY_BUBBLE_PER_CHAR = 3.6
LAZY_BUBBLE_BASE = 18


def _lazy_bubble_radius(first_name: str) -> float:
    """Choose a bubble radius (px) that comfortably fits the first name."""
    name_len = max(len(str(first_name)), 1)
    candidate = LAZY_BUBBLE_BASE + name_len * LAZY_BUBBLE_PER_CHAR
    return float(max(LAZY_BUBBLE_MIN_R, min(LAZY_BUBBLE_MAX_R, candidate)))


def _lazy_bubble_font_size(first_name: str, radius: float) -> int:
    """Pick the largest font size whose rendered width still fits the bubble."""
    name_len = max(len(str(first_name)), 1)
    diameter = 2 * radius
    horizontal_pad = 8  # 4px padding either side
    avail = max(diameter - horizontal_pad, 12)
    # avg glyph width ~= 0.55 * font_size for Inter/Segoe weight 700
    by_width = avail / (name_len * 0.55)
    by_height = radius * 0.85
    return int(max(11, min(by_width, by_height)))


def _greedy_pack_circles(radii: list[float], gap: float = LAZY_BUBBLE_GAP) -> list[tuple[float, float]]:
    """Front-chain greedy circle packing.

    Largest bubble at the origin; each subsequent bubble is placed tangent to
    an already-placed bubble, picking the candidate position whose center is
    closest to the running centroid. Produces a tight, organic cluster like
    classic packed-bubble charts (e.g. Tableau).
    """
    if not radii:
        return []

    placed: list[tuple[float, float, float]] = [(0.0, 0.0, radii[0])]
    angle_steps = 60  # candidate angles per existing bubble

    for r in radii[1:]:
        candidates: list[tuple[float, float, float]] = []  # (score, x, y)
        for px, py, pr in placed:
            d = pr + r + gap
            for k in range(angle_steps):
                ang = 2 * math.pi * k / angle_steps
                x = px + d * math.cos(ang)
                y = py + d * math.sin(ang)
                # Reject if it overlaps any placed circle.
                ok = True
                for qx, qy, qr in placed:
                    min_d = r + qr + gap - 0.5  # 0.5 px tolerance
                    if (x - qx) ** 2 + (y - qy) ** 2 < min_d * min_d:
                        ok = False
                        break
                if not ok:
                    continue
                cx = sum(p[0] for p in placed) / len(placed)
                cy = sum(p[1] for p in placed) / len(placed)
                candidates.append(((x - cx) ** 2 + (y - cy) ** 2, x, y))
        if candidates:
            candidates.sort(key=lambda c: c[0])
            _, x, y = candidates[0]
            placed.append((x, y, r))
        else:
            # Pathological fallback: place to the right of the rightmost bubble.
            far_right = max(p[0] + p[2] for p in placed)
            placed.append((far_right + r + gap, 0.0, r))

    return [(x, y) for x, y, _ in placed]


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert ``#rrggbb`` to an (r, g, b) tuple of ints in 0..255."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def render_lazy_bubble_clusters(
    df: pd.DataFrame,
    *,
    name_col: str = "Name",
    delay_col: str = "Avg. Log Delay (Days)",
    size_col: str = "Logged Workouts",
    card_height: int = 480,
) -> None:
    """Render three side-by-side cards with tight bubble clusters in each.

    Modernized visual treatment matches the rest of the dashboard:
    - Each card has a subtle gradient backdrop, an accent-colored top edge,
      and a rounded border that picks up the zone color at low alpha.
    - Zone header pairs an emoji icon, the zone label, and a count badge
      showing how many participants live in that zone.
    - Bubbles are rendered with an SVG radial gradient (lighter top-left,
      darker bottom-right) for depth, plus a soft outer glow filter so the
      cluster reads as a "constellation" rather than flat circles.
    """
    if df is None or df.empty:
        st.caption("Need timestamps to score logging delay.")
        return

    cols = st.columns(3, gap="medium")
    for col, (zone_id, label, headline, subtitle, color, icon) in zip(
        cols, LAZY_ZONES, strict=False
    ):
        zone_df = df[df["Zone"] == zone_id].copy()
        zone_df = zone_df.sort_values([size_col, name_col], ascending=[False, True]).reset_index(drop=True)

        radii = [_lazy_bubble_radius(fn) for fn in zone_df["FirstName"]]
        positions = _greedy_pack_circles(radii)
        if positions:
            mean_x = sum(x for x, _ in positions) / len(positions)
            mean_y = sum(y for _, y in positions) / len(positions)
            positions = [(x - mean_x, y - mean_y) for x, y in positions]

        # Compute lighter / darker variants of the accent color for the
        # radial-gradient stops. Light = blend toward white, dark = blend
        # toward the dashboard background.
        r0, g0, b0 = _hex_to_rgb(color)
        light = f"rgb({min(255, r0 + 60)},{min(255, g0 + 60)},{min(255, b0 + 60)})"
        dark = f"rgb({max(0, int(r0 * 0.65))},{max(0, int(g0 * 0.65))},{max(0, int(b0 * 0.65))})"

        zone_count = len(zone_df)

        # --- Card chrome: gradient backdrop, accent top edge, count badge ---
        card_open = (
            f"<div style=\""
            f"position:relative;"
            f"background:linear-gradient(160deg,rgba(15,22,40,0.92) 0%,rgba(11,18,32,0.95) 100%);"
            f"border:1px solid {color}33;"
            f"border-radius:18px;"
            f"padding:0;"
            f"height:{card_height}px;"
            f"overflow:hidden;"
            f"box-shadow:0 4px 18px rgba(0,0,0,0.35), inset 0 0 60px {color}10;"
            f"\">"
            # Accent top edge strip
            f"<div style='height:3px;background:linear-gradient(90deg,transparent 0%,{color} 50%,transparent 100%);'></div>"
            # Header block
            f"<div style='padding:18px 18px 12px;'>"
            f"<div style='display:flex;align-items:center;justify-content:center;gap:8px;'>"
            f"<span style='font-size:20px;'>{icon}</span>"
            f"<span style='font-size:20px;font-weight:800;color:{color};letter-spacing:0.04em;text-transform:uppercase;'>{label}</span>"
            f"<span style='font-size:11px;font-weight:800;color:{color};"
            f"background:{color}22;border:1px solid {color}55;border-radius:999px;"
            f"padding:2px 9px;letter-spacing:0.05em;'>{zone_count}</span>"
            f"</div>"
            f"<div style='text-align:center;font-size:13px;font-weight:600;color:#E4E6EB;margin-top:8px;'>{headline}</div>"
            f"<div style='text-align:center;font-size:11px;color:rgba(255,255,255,0.50);margin-top:2px;'>{subtitle}</div>"
            f"</div>"
        )

        canvas_top = 96   # px reserved above for header block + edge strip
        canvas_h = card_height - canvas_top - 18

        # SVG with viewBox for fluid scaling. We define a per-card radial
        # gradient and a soft outer-glow filter once in <defs>, then reuse
        # them for every bubble.
        VB = 300.0
        if positions:
            half_ext = max(
                max(abs(x) + r for (x, _y), r in zip(positions, radii, strict=False)),
                max(abs(y) + r for (_x, y), r in zip(positions, radii, strict=False)),
            )
            scale_to_vb = (VB / 2 - 6) / max(half_ext, 1.0)
        else:
            scale_to_vb = 1.0
        cx0, cy0 = VB / 2, VB / 2

        def _vb_font(name: str, r_vb: float) -> float:
            name_len = max(len(str(name)), 1)
            avail = max(2 * r_vb - 6, 6)
            by_width = avail / (name_len * 0.55)
            by_height = r_vb * 0.85
            return max(7.0, min(by_width, by_height))

        grad_id = f"bubbleGrad_{zone_id}"
        glow_id = f"bubbleGlow_{zone_id}"

        defs = (
            f"<defs>"
            f"<radialGradient id='{grad_id}' cx='35%' cy='30%' r='75%'>"
            f"<stop offset='0%' stop-color='{light}' stop-opacity='1'/>"
            f"<stop offset='60%' stop-color='{color}' stop-opacity='1'/>"
            f"<stop offset='100%' stop-color='{dark}' stop-opacity='1'/>"
            f"</radialGradient>"
            f"<filter id='{glow_id}' x='-50%' y='-50%' width='200%' height='200%'>"
            f"<feGaussianBlur stdDeviation='2.2'/>"
            f"</filter>"
            f"</defs>"
        )

        svg_parts: list[str] = []
        for (_, row), (x, y), r in zip(
            zone_df.iterrows(), positions, radii, strict=False
        ):
            cx = cx0 + x * scale_to_vb
            cy = cy0 + y * scale_to_vb
            r_vb = r * scale_to_vb
            font_vb = _vb_font(row["FirstName"], r_vb)
            tip = f"{row[name_col]} \u2022 {row[delay_col]:.2f}d \u2022 {int(row[size_col])} logs"
            svg_parts.append(
                f"<g><title>{tip}</title>"
                # Soft outer glow circle (blurred, behind the bubble)
                f"<circle cx='{cx:.2f}' cy='{cy:.2f}' r='{r_vb:.2f}' "
                f"fill='{color}' opacity='0.32' filter='url(#{glow_id})'/>"
                # Main bubble with radial gradient
                f"<circle cx='{cx:.2f}' cy='{cy:.2f}' r='{r_vb:.2f}' "
                f"fill='url(#{grad_id})' stroke='{dark}' stroke-width='1'/>"
                # Subtle highlight rim to imply a glassy surface
                f"<ellipse cx='{cx - r_vb * 0.30:.2f}' cy='{cy - r_vb * 0.40:.2f}' "
                f"rx='{r_vb * 0.45:.2f}' ry='{r_vb * 0.20:.2f}' "
                f"fill='rgba(255,255,255,0.18)'/>"
                # Name text
                f"<text x='{cx:.2f}' y='{cy:.2f}' fill='#FFFFFF' "
                f"font-size='{font_vb:.2f}' font-weight='700' "
                f"text-anchor='middle' dominant-baseline='central' "
                f"font-family='Inter, Segoe UI, sans-serif' "
                f"style='paint-order:stroke;stroke:rgba(11,18,32,0.55);stroke-width:1.2;'>"
                f"{row['FirstName']}</text>"
                f"</g>"
            )

        if not svg_parts:
            svg_parts.append(
                f"<text x='{cx0}' y='{cy0}' fill='rgba(255,255,255,0.45)' "
                f"font-size='14' font-style='italic' text-anchor='middle' "
                f"dominant-baseline='central'>nobody here</text>"
            )

        canvas_html = (
            f"<div style='display:flex;justify-content:center;align-items:center;"
            f"height:{canvas_h}px;'>"
            f"<svg viewBox='0 0 {VB:.0f} {VB:.0f}' "
            f"preserveAspectRatio='xMidYMid meet' "
            f"style='width:100%;height:100%;max-width:{canvas_h}px;display:block;'>"
            f"{defs}{''.join(svg_parts)}"
            f"</svg></div>"
        )

        card_close = "</div>"

        with col:
            st.markdown(
                card_open + canvas_html + card_close,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Cumulative Calorie Race
# ---------------------------------------------------------------------------

# Distinct, dark-theme-friendly palette. Cycled if there are more participants
# than colors. Avoids reds (collide with "missed" red elsewhere) and dim greys.
CALORIE_RACE_PALETTE = [
    "#5FA68D", "#6E88A6", "#C58A4F", "#A36BA6", "#4FA9C5",
    "#D4B45A", "#7FA85E", "#E07A8B", "#8C9EFF", "#B07A4A",
    "#46B5A0", "#9C7FB0", "#5C9FD4", "#D49A4F", "#7FBF7B",
    "#FF9F6B", "#9DCEFF", "#C2A878", "#7DB9A1", "#B59ED1",
]


def build_cumulative_calories_long(
    df_month: pd.DataFrame,
    *,
    start_date,
    end_date,
) -> pd.DataFrame:
    """Return long-format dataframe of cumulative calories per (name, date).

    Builds a complete name x day grid across [start_date, end_date], joins
    actual calorie totals (summed if multiple logs share a date), forward-fills
    to a cumulative sum so the line steps and stays flat on rest days.

    Returns columns: ``name``, ``workout_date`` (date), ``dom`` (int day of
    month), ``daily_calories`` (float), ``cum_calories`` (float).
    """
    empty_cols = ["name", "workout_date", "dom", "daily_calories", "cum_calories"]
    if df_month is None or df_month.empty or "calories_burned" not in df_month.columns:
        return pd.DataFrame(columns=empty_cols)

    cal = df_month.dropna(subset=["calories_burned"]).copy()
    if cal.empty:
        return pd.DataFrame(columns=empty_cols)

    cal["workout_date"] = pd.to_datetime(cal["workout_date"], errors="coerce").dt.date
    cal = cal.dropna(subset=["workout_date"])
    if cal.empty:
        return pd.DataFrame(columns=empty_cols)

    daily = (
        cal.groupby(["name", "workout_date"], as_index=False)["calories_burned"]
        .sum()
        .rename(columns={"calories_burned": "daily_calories"})
    )

    days = list(pd.date_range(start_date, end_date, freq="D").date)
    names = sorted(daily["name"].astype(str).unique().tolist())
    grid = pd.MultiIndex.from_product(
        [names, days], names=["name", "workout_date"]
    ).to_frame(index=False)

    merged = grid.merge(daily, on=["name", "workout_date"], how="left")
    merged["daily_calories"] = merged["daily_calories"].fillna(0.0).astype(float)
    merged = merged.sort_values(["name", "workout_date"]).reset_index(drop=True)
    merged["cum_calories"] = (
        merged.groupby("name")["daily_calories"].cumsum().astype(float)
    )
    merged["dom"] = pd.to_datetime(merged["workout_date"]).dt.day.astype(int)
    return merged[["name", "workout_date", "dom", "daily_calories", "cum_calories"]]


def alt_cumulative_calorie_race_chart(
    long_df: pd.DataFrame,
    *,
    height: int = 460,
):
    """Modern, glow-styled Altair race chart of cumulative calories.

    Visual language matches the modernized radar:
    - Each line gets a softer "halo" under-stroke for a subtle glow.
    - The leader's curve also gets a faint area-fill that fades to nothing,
      anchoring the eye to the front-runner without burying the rest.
    - End-of-line markers have a halo + solid core dot, like the radar
      vertices.
    - End labels are rendered as dark "chips" with an accent border so they
      stay readable on top of any line.
    - Top three participants are tagged with medal emojis on the chip.
    - Axes lose harsh tick marks and grid; baseline ring is the only chrome.
    """
    if long_df is None or long_df.empty:
        return None

    df = long_df.copy()
    df["name"] = df["name"].astype(str)

    final_totals = (
        df.sort_values("workout_date")
        .groupby("name", as_index=False)["cum_calories"]
        .last()
        .sort_values("cum_calories", ascending=False)
        .reset_index(drop=True)
    )
    name_order = final_totals["name"].tolist()
    color_map = {
        n: CALORIE_RACE_PALETTE[i % len(CALORIE_RACE_PALETTE)]
        for i, n in enumerate(name_order)
    }
    df["color"] = df["name"].map(color_map)

    leader_name = name_order[0] if name_order else None
    leader_df = df[df["name"] == leader_name].copy() if leader_name else df.iloc[0:0]

    last_rows = (
        df.sort_values("workout_date")
        .groupby("name", as_index=False)
        .tail(1)
        .copy()
    )
    medals = {0: "🥇 ", 1: "🥈 ", 2: "🥉 "}
    last_rows["rank"] = last_rows["name"].map({n: i for i, n in enumerate(name_order)})
    last_rows["label"] = last_rows.apply(
        lambda r: f"{medals.get(int(r['rank']), '')}{r['name']}  {int(round(r['cum_calories'])):,}",
        axis=1,
    )

    color_scale = alt.Scale(domain=name_order, range=[color_map[n] for n in name_order])
    color_enc = alt.Color("name:N", scale=color_scale, sort=name_order, legend=None)

    x_enc = alt.X(
        "workout_date:T",
        title=None,
        axis=alt.Axis(
            format="%b %d",
            labelColor="#9AA0AB",
            labelFontSize=11,
            grid=False,
            tickColor="rgba(0,0,0,0)",
            domainColor="rgba(255,255,255,0.18)",
        ),
    )
    y_enc = alt.Y(
        "cum_calories:Q",
        title="Cumulative calories",
        axis=alt.Axis(
            labelColor="#9AA0AB",
            labelFontSize=11,
            titleColor="#E4E6EB",
            titleFontWeight=700,
            titleFontSize=12,
            titlePadding=14,
            gridColor="rgba(255,255,255,0.05)",
            gridDash=[2, 4],
            tickColor="rgba(0,0,0,0)",
            domainOpacity=0,
            format=",.0f",
        ),
    )

    # --- Leader area glow (sits under everything) ---
    leader_color = color_map.get(leader_name) if leader_name else None
    leader_area = None
    if leader_color is not None and not leader_df.empty:
        leader_area = alt.Chart(leader_df).mark_area(
            interpolate="monotone",
            color=leader_color,
            opacity=0.10,
            line=False,
        ).encode(x="workout_date:T", y="cum_calories:Q")

    # --- Glow under-strokes for every line (broad, low alpha) ---
    glow_stroke = alt.Chart(df).mark_line(
        interpolate="monotone",
        strokeWidth=8,
        opacity=0.18,
        strokeCap="round",
        strokeJoin="round",
    ).encode(x=x_enc, y=y_enc, color=color_enc)

    # --- Main strokes (sharp, on top of the glow) ---
    lines = alt.Chart(df).mark_line(
        interpolate="monotone",
        strokeWidth=2.6,
        strokeCap="round",
        strokeJoin="round",
    ).encode(
        x=x_enc,
        y=y_enc,
        color=color_enc,
        tooltip=[
            alt.Tooltip("name:N", title="Participant"),
            alt.Tooltip("workout_date:T", title="Date", format="%b %d"),
            alt.Tooltip("daily_calories:Q", title="Day", format=",.0f"),
            alt.Tooltip("cum_calories:Q", title="Total so far", format=",.0f"),
        ],
    )

    # --- End-of-line halo + core dot ---
    end_halo = alt.Chart(last_rows).mark_point(
        filled=True, size=380, opacity=0.18, strokeWidth=0,
    ).encode(x="workout_date:T", y="cum_calories:Q", color=color_enc)

    end_dot = alt.Chart(last_rows).mark_point(
        filled=True, size=130, opacity=1.0,
        stroke="#0B1220", strokeWidth=1.6,
    ).encode(x="workout_date:T", y="cum_calories:Q", color=color_enc)

    # --- Stagger labels vertically so they don't overlap ---
    y_span = max(float(df["cum_calories"].max()) - float(df["cum_calories"].min()), 1.0)
    min_gap = max(y_span * 0.055, 1.0)
    last_rows = last_rows.sort_values("cum_calories", ascending=False).reset_index(drop=True)
    label_ys: list[float] = []
    for raw_y in last_rows["cum_calories"].astype(float):
        if not label_ys:
            label_ys.append(raw_y)
        else:
            label_ys.append(min(raw_y, label_ys[-1] - min_gap))
    last_rows["label_y"] = label_ys

    leader_lines = alt.Chart(last_rows).mark_rule(
        strokeWidth=1, opacity=0.35, strokeDash=[3, 3],
    ).encode(
        x="workout_date:T",
        x2="workout_date:T",
        y="cum_calories:Q",
        y2="label_y:Q",
        color=color_enc,
    )

    # Dark chip behind label (rendered as a text mark with bgcolor not
    # supported, so use a thicker dark text "shadow" + bright text on top
    # to mimic a chip with accent border).
    end_labels_shadow = alt.Chart(last_rows).mark_text(
        align="left", dx=14, dy=0, fontSize=12, fontWeight=700,
        color="#0B1220",
        stroke="#0B1220", strokeWidth=4, strokeOpacity=0.85,
    ).encode(x="workout_date:T", y="label_y:Q", text="label:N")

    end_labels = alt.Chart(last_rows).mark_text(
        align="left", dx=14, dy=0, fontSize=12, fontWeight=700,
    ).encode(
        x="workout_date:T",
        y="label_y:Q",
        text="label:N",
        color=color_enc,
    )

    layers = [layer for layer in [
        leader_area,
        glow_stroke,
        lines,
        leader_lines,
        end_halo,
        end_dot,
        end_labels_shadow,
        end_labels,
    ] if layer is not None]

    chart = (
        alt.layer(*layers)
        .properties(
            height=height,
            padding={"right": 130, "top": 12, "bottom": 8, "left": 8},
            background="#0B1220",
        )
        .configure_view(strokeOpacity=0, fill="#0B1220")
        .configure_axis(domain=False)
    )
    return chart

