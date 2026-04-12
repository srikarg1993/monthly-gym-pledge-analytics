import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import pandas as pd
import altair as alt


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
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame())

    BAR_WINNER = "#34D399"
    BAR_PROGRESS = "#60A5FA"
    GLOW_WINNER = "rgba(52,211,153,0.15)"
    GLOW_PROGRESS = "rgba(96,165,250,0.12)"
    GLOW_TRACK = "rgba(255,255,255,0.05)"
    MARKER_COLOR = "#A78BFA"
    GOAL_COLOR = "#F472B6"
    LABEL_WHITE = "#FFFFFF"

    chart_df = df.copy().reset_index(drop=True)
    domain_end = max(float(chart_df[[qualifying_col, workout_col]].max().max()), float(cutoff), 1.0)
    chart_df["_track"] = domain_end
    chart_df["Summary"] = (
        chart_df[qualifying_col].astype(int).astype(str)
        + "Q"
        + "  |  "
        + chart_df[workout_col].astype(int).astype(str)
        + "W"
    )
    chart_df["_label_x"] = chart_df[[qualifying_col, workout_col]].max(axis=1) + 0.25
    chart_df["_is_winner"] = chart_df[qualifying_col].astype(int) >= cutoff
    y_order = chart_df[label_col].tolist()
    domain = [0, domain_end + 3.0]
    x_tick_count = int(domain_end) + 4
    chart_height = height or alt_chart_height(len(chart_df), min_height=360, max_height=860, row_step=38)

    base = alt.Chart(chart_df)

    track = base.mark_bar(cornerRadiusEnd=14, size=26, opacity=0.08).encode(
        x=alt.X("_track:Q", title="Days", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order, title=None, axis=alt.Axis(labelPadding=14)),
        color=alt.value(GLOW_TRACK),
    )

    qualifying_glow = base.mark_bar(cornerRadiusEnd=14, size=30, opacity=0.18).encode(
        x=alt.X(f"{qualifying_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        color=alt.condition(
            alt.datum._is_winner,
            alt.value(GLOW_WINNER),
            alt.value(GLOW_PROGRESS),
        ),
    )

    qualifying = base.mark_bar(cornerRadiusEnd=14, size=16).encode(
        x=alt.X(f"{qualifying_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        color=alt.condition(
            alt.datum._is_winner,
            alt.value(BAR_WINNER),
            alt.value(BAR_PROGRESS),
        ),
        tooltip=[
            alt.Tooltip(f"{label_col}:N", title="Participant"),
            alt.Tooltip(f"{qualifying_col}:Q", title="Qualifying days"),
            alt.Tooltip(f"{workout_col}:Q", title="Workout days"),
        ],
    )

    workout_marker = base.mark_point(
        filled=True,
        size=110,
        shape="diamond",
        stroke="#0B1220",
        strokeWidth=2,
    ).encode(
        x=alt.X(f"{workout_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        color=alt.value(MARKER_COLOR),
    )

    cutoff_rule = alt.Chart(pd.DataFrame({"Cutoff": [cutoff]})).mark_rule(
        color=GOAL_COLOR,
        strokeDash=[6, 4],
        strokeWidth=2.5,
    ).encode(x=alt.X("Cutoff:Q", scale=alt.Scale(domain=domain, nice=False)))

    cutoff_label = alt.Chart(pd.DataFrame({"Cutoff": [cutoff], "Label": [f"GOAL {cutoff}"]})).mark_text(
        align="left",
        baseline="top",
        dx=8,
        dy=6,
        color=GOAL_COLOR,
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
        color=LABEL_WHITE,
        dx=10,
        fontSize=14,
        fontWeight=700,
    ).encode(
        x=alt.X("_label_x:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        text="Summary:N",
    )

    chart = (track + qualifying_glow + qualifying + workout_marker + cutoff_rule + cutoff_label + labels).properties(height=chart_height)

    return (
        chart.configure_view(strokeOpacity=0)
        .configure_axis(
            labelColor="#FFFFFF",
            titleColor="#FFFFFF",
            domainColor="rgba(255,255,255,0.08)",
            gridColor="rgba(255,255,255,0.04)",
            tickColor="rgba(255,255,255,0.08)",
            labelFontSize=14,
            titleFontSize=14,
            labelLimit=240,
        )
        .configure_axisY(
            labelFontSize=15,
            labelColor="#FFFFFF",
            labelFontWeight="bold",
        )
        .configure_axisX(
            tickMinStep=1,
            tickCount=x_tick_count,
            format="d",
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

    ZONE_ORDER = ["Same Day", "½–1 day", "2+ days"]
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
    bg_df = pd.DataFrame([{"Zone": z, "Color": c} for z, c in zip(ZONE_ORDER, ZONE_BG)])
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
    if df is None or df.empty:
        return alt.Chart(pd.DataFrame())

    chart_df = df.copy().reset_index(drop=True)
    chart_df["_left_signed"] = -chart_df[left_col].astype(float)
    chart_df["_style_label_x"] = chart_df[right_col].astype(float) + 0.85
    extent = max(float(chart_df[[left_col, right_col]].max().max()), 1.0)
    domain = [-(extent + 2.6), extent + 3.8]
    y_order = chart_df[label_col].tolist()
    chart_height = height or alt_chart_height(len(chart_df), min_height=340, max_height=860, row_step=34)

    base = alt.Chart(chart_df)
    center = alt.Chart(pd.DataFrame({"Center": [0]})).mark_rule(
        color=ALT_TRACK,
        strokeWidth=2,
    ).encode(x=alt.X("Center:Q", scale=alt.Scale(domain=domain, nice=False)))

    left_bars = base.mark_bar(cornerRadiusEnd=8, size=20).encode(
        x=alt.X("_left_signed:Q", title="First half  |  Second half", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order, title=None, axis=alt.Axis(labelPadding=10)),
        color=alt.value(ALT_SAGE),
        tooltip=[
            alt.Tooltip(f"{label_col}:N", title="Participant"),
            alt.Tooltip(f"{left_col}:Q", title="First half"),
            alt.Tooltip(f"{right_col}:Q", title="Second half"),
            alt.Tooltip(f"{style_col}:N", title="Style"),
        ],
    )

    right_bars = base.mark_bar(cornerRadiusEnd=8, size=20).encode(
        x=alt.X(f"{right_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        color=alt.value(ALT_COPPER),
    )

    left_labels = base.mark_text(
        align="right",
        baseline="middle",
        dx=-8,
        color="#FFFFFF",
        fontSize=14,
        fontWeight=700,
    ).encode(
        x=alt.X("_left_signed:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        text=alt.Text(f"{left_col}:Q", format=".0f"),
    )

    right_labels = base.mark_text(
        align="left",
        baseline="middle",
        dx=8,
        color="#FFFFFF",
        fontSize=14,
        fontWeight=700,
    ).encode(
        x=alt.X(f"{right_col}:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        text=alt.Text(f"{right_col}:Q", format=".0f"),
    )

    style_labels = base.mark_text(
        align="left",
        baseline="middle",
        dx=10,
        color="#FFFFFF",
        fontSize=14,
        fontWeight=600,
    ).encode(
        x=alt.X("_style_label_x:Q", scale=alt.Scale(domain=domain, nice=False)),
        y=alt.Y(f"{label_col}:N", sort=y_order),
        text=f"{style_col}:N",
    )

    chart = (center + left_bars + right_bars + left_labels + right_labels + style_labels).properties(height=chart_height)
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
    
