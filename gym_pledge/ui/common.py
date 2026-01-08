import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import pandas as pd


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


def alt_weekday_bubble(counts: pd.DataFrame, weekday_order: list[str], color: str = "#4fa3ff", height: int = 260, size_range: tuple[int, int] = (600, 6500)):
    """Return an Altair bubble chart for weekday counts.

    Expects `counts` to have columns ['Weekday', 'count'] and uses `weekday_order`
    to ensure consistent ordering.
    """
    try:
        import altair as alt
    except Exception:
        raise

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

    names = base.mark_text(dy=56, color="#ffffff", fontSize=13, fontWeight=700).encode(
        x=alt.X("Weekday:N", sort=weekday_order),
        y=alt.value(center_y),
        text=alt.Text("Weekday:N"),
    )

    chart = (backdrop + bubbles + labels + names).properties(height=chart_height)
    chart = chart.configure_view(strokeOpacity=0)
    chart = chart.configure_axis(labelColor="#9aa0ab", domainColor="rgba(255,255,255,0.06)")
    chart = chart.configure_title(color="#fff")
    return chart


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
    