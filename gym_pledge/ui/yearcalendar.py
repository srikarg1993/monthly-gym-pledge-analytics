"""Year calendar UI rendering helper."""

import calendar
import json
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from app_time import today_app
from data.metrics import longest_streak
from ui.common import render_styled_table

# ApexCharts CDN (no local install). Toggle: Bar / Area
APEXCHARTS_CDN = "https://cdn.jsdelivr.net/npm/apexcharts@3.45.2/dist/apexcharts.min.js"


def _name_col(df: pd.DataFrame) -> str:
    return "name" if df is not None and "name" in df.columns else "Name"


def _year_from_month_str(month_str: str | None) -> int:
    if month_str:
        try:
            return int(str(month_str).split("-")[0])
        except Exception:
            pass
    return today_app().year


def _status_by_day(df_month: pd.DataFrame, name: str, name_col: str) -> dict[int, str]:
    day_status: dict[int, str] = {}
    if df_month is None or df_month.empty:
        return day_status

    if name_col not in df_month.columns:
        return day_status

    person = df_month[df_month[name_col] == name]
    if person.empty:
        return day_status

    for _, row in person.iterrows():
        workout_date = row.get("workout_date")
        if pd.isna(workout_date):
            continue
        day = int(workout_date.day)
        if bool(row.get("burnt_250", False)):
            day_status[day] = "qualifying"
        else:
            day_status.setdefault(day, "regular")
    return day_status


def _calendar_html(*, year: int, month: int, status_by_day: dict[int, str], today, mini: bool = False) -> str:
    last_day_in_month = calendar.monthrange(year, month)[1]
    if (year, month) < (today.year, today.month):
        last_day_for_dots = last_day_in_month
    elif (year, month) > (today.year, today.month):
        last_day_for_dots = 0
    else:
        last_day_for_dots = today.day

    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)

    calendar_class = "calendar calendar-mini" if mini else "calendar"
    parts = [f"<div class='{calendar_class}'><div class='calendar-grid'>"]

    for wd in weekdays:
        parts.append(f"<div class='cal-head'>{wd}</div>")

    for week in weeks:
        for day in week:
            if day == 0:
                parts.append("<div class='cal-cell cal-empty'></div>")
                continue

            status = status_by_day.get(day, "none")
            if status == "none" and day > last_day_for_dots:
                status = "future"
            day_class = "cal-day"
            dot_class = "cal-dot cal-dot-none"
            if status == "qualifying":
                day_class += " cal-day-qualifying"
                dot_class = "cal-dot cal-dot-hidden"
            elif status == "regular":
                day_class += " cal-day-regular"
                dot_class = "cal-dot cal-dot-hidden"
            elif status == "future":
                day_class += " cal-day-future"
                dot_class = "cal-dot cal-dot-hidden"

            parts.append(
                f"<div class='cal-cell'>"
                f"<div class='{day_class}'>{day}</div>"
                f"<div class='{dot_class}'></div>"
                f"</div>"
            )

    parts.append("</div></div>")
    return "".join(parts)


def _year_stats_for_person(
    df_year: pd.DataFrame, name: str, name_col: str, year: int
) -> tuple[int, int, int, pd.DataFrame]:
    """Compute full-year stats for one person. Returns (workout_days, qualifying_days, longest_streak, monthly_df)."""
    if df_year is None or df_year.empty or name_col not in df_year.columns:
        return 0, 0, 0, pd.DataFrame()

    person = df_year[df_year[name_col] == name]
    if person.empty:
        return 0, 0, 0, pd.DataFrame()

    workout_days = int(person["workout_date"].nunique())
    qual = person[person["burnt_250"]]
    qualifying_days = int(qual["workout_date"].nunique())
    # Longest streak of consecutive qualifying days across the full year (can span months)
    streak = longest_streak(qual["workout_date"].dropna().tolist())

    monthly_rows = []
    if "month" in df_year.columns:
        for month in range(1, 13):
            month_str = f"{year:04d}-{month:02d}"
            m = person[person["month"] == month_str]
            w = int(m["workout_date"].nunique())
            q = int(m[m["burnt_250"]]["workout_date"].nunique())
            monthly_rows.append(
                {
                    "Month": datetime(year, month, 1).strftime("%b"),
                    "Workouts": w,
                    "Qualifying": q,
                }
            )
    monthly_df = pd.DataFrame(monthly_rows) if monthly_rows else pd.DataFrame()

    return workout_days, qualifying_days, streak, monthly_df


def _monthly_breakdown_chart_html(months: list, workouts: list, qualifying: list) -> str:
    """Build HTML/JS for ApexCharts (CDN) with Bar / Area icon toggle. No extra deps."""
    data_js = json.dumps({"categories": months, "workouts": workouts, "qualifying": qualifying})
    btn_style = (
        "border:none;background:rgba(28,36,60,0.9);color:#A0A4B3;cursor:pointer;padding:6px 10px;"
        "border-radius:6px;margin-right:4px;border:1px solid rgba(255,255,255,0.15);"
    )
    btn_active = "background:rgba(99,102,241,0.35);color:#E4E6EB;border-color:rgba(99,102,241,0.6);"
    return f"""
<div id="monthly-chart-toolbar" style="margin:0 0 8px 0;display:flex;align-items:center;gap:4px;">
  <span style="color:#A0A4B3;font-size:12px;margin-right:6px;">Chart:</span>
  <button type="button" class="chart-type-btn" data-type="bar" title="Bar chart" style="{btn_style}{btn_active}" id="btn-bar">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="1.5"><rect x="4" y="14" width="4" height="6"/><rect x="10" y="10" width="4" height="10"/><rect x="16" y="6" width="4" height="14"/></svg>
  </button>
  <button type="button" class="chart-type-btn" data-type="area" title="Area chart" style="{btn_style}" id="btn-area">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" fill-opacity="0.3" stroke="currentColor" stroke-width="1.5"><path d="M3 17l6-6 4 4 8-12v0" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </button>
</div>
<div id="monthly-apex-chart" style="min-height:280px;"></div>
<script src="{APEXCHARTS_CDN}"></script>
<script>
(function() {{
  var raw = {data_js};
  var categories = raw.categories;
  var series = [
    {{ name: "Workouts", data: raw.workouts }},
    {{ name: "Qualifying", data: raw.qualifying }}
  ];
  var chartEl = document.getElementById("monthly-apex-chart");
  var chart = null;
  var activeStyle = "{btn_active}";
  var defaultStyle = "{btn_style}";
  function setActive(type) {{
    document.querySelectorAll(".chart-type-btn").forEach(function(btn) {{
      btn.style.cssText = (btn.getAttribute("data-type") === type ? defaultStyle + activeStyle : defaultStyle);
    }});
  }}
  function render(type) {{
    if (chart) chart.destroy();
    var opts = {{
      chart: {{ type: type, height: 280, toolbar: {{ show: false }}, background: "transparent" }},
      series: series,
      xaxis: {{ categories: categories, labels: {{ style: {{ colors: "#A0A4B3" }} }} }},
      yaxis: {{ labels: {{ style: {{ colors: "#A0A4B3" }} }} }},
      legend: {{ labels: {{ colors: "#A0A4B3" }} }},
      colors: ["#6b9bd1", "#4caf50"],
      grid: {{ borderColor: "rgba(255,255,255,0.1)", strokeDashArray: 4 }},
      tooltip: {{ theme: "dark" }}
    }};
    if (type === "bar") {{
      opts.plotOptions = {{ bar: {{ horizontal: false, stacked: false, columnWidth: "45%" }} }};
    }}
    chart = new ApexCharts(chartEl, opts);
    chart.render();
    setActive(type);
  }}
  document.querySelectorAll(".chart-type-btn").forEach(function(btn) {{
    btn.addEventListener("click", function() {{ render(this.getAttribute("data-type")); }});
  }});
  render("bar");
}})();
</script>
"""


def _render_year_calendar(*, df_year: pd.DataFrame, name: str, year: int, name_col: str) -> None:
    today = today_app()
    parts = ["<div class='calendar-year'>"]

    for month in range(1, 13):
        month_str = f"{year:04d}-{month:02d}"
        if df_year is None or df_year.empty or "month" not in df_year.columns:
            month_df = pd.DataFrame(columns=df_year.columns if df_year is not None else [])
        else:
            month_df = df_year[df_year["month"] == month_str].copy()
        status_by_day = _status_by_day(month_df, name, name_col)
        month_label = datetime(year, month, 1).strftime("%b")

        parts.append("<div class='calendar-month'>")
        parts.append(f"<div class='calendar-month-title'>{month_label}</div>")
        parts.append(_calendar_html(year=year, month=month, status_by_day=status_by_day, today=today, mini=True))
        parts.append("</div>")

    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def render(*, df: pd.DataFrame, month_selected: str) -> None:
    year = _year_from_month_str(month_selected)
    st.subheader(f"{year} Fitness Yearbook")
    # st.markdown("<div class='small-muted'>All 12 months - per-person view</div>", unsafe_allow_html=True)

    name_col = _name_col(df)
    df_year = df.copy() if df is not None else pd.DataFrame()
    if df_year is not None and not df_year.empty and "workout_date" in df_year.columns:
        dates = pd.to_datetime(df_year["workout_date"], errors="coerce")
        df_year = df_year[(df_year["workout_date"].notna()) & (dates.dt.year == year)].copy()

    people_source = df_year if df_year is not None and not df_year.empty else df
    if people_source is None or people_source.empty or name_col not in people_source.columns:
        st.caption(f"No participants found for {year}.")
        return

    people = sorted(people_source[name_col].dropna().unique().tolist())
    who = st.selectbox("Select person", people, key="year_calendar_person")

    # Full year stats for selected person
    workout_days, qualifying_days, streak, monthly_df = _year_stats_for_person(
        df_year, who, name_col, year
    )
    q_pct = (qualifying_days / workout_days * 100) if workout_days else 0

    st.markdown("#### Full year stats")
    st.caption("Streak = longest run of consecutive qualifying days in the year (can span months).")
    stat_cols = st.columns(4, gap="small")
    stats = [
        ("Total workout days", f"{workout_days}"),
        ("Qualifying workouts", f"{qualifying_days}"),
        ("Q / W %", f"{q_pct:.1f}%"),
        ("Longest qualifying streak (across full year)", f"{streak} days"),
    ]
    for c, (label, value) in zip(stat_cols, stats):
        with c:
            st.markdown(
                f"""
                <div style='background: rgba(255,255,255,0.02); padding:14px; border-radius:8px; text-align:center;'>
                  <div style='font-size:20px; font-weight:700; color:#fff;'>{value}</div>
                  <div style='font-size:12px; color:#9aa0ab; margin-top:6px;'>{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if not monthly_df.empty:
        st.markdown("#### Monthly breakdown")
        months = monthly_df["Month"].tolist()
        workouts = monthly_df["Workouts"].tolist()
        qualifying = monthly_df["Qualifying"].tolist()
        html = _monthly_breakdown_chart_html(months, workouts, qualifying)
        components.html(html, height=340)
        with st.expander("View as table"):
            render_styled_table(monthly_df, max_rows=12)

    st.markdown(
        """
        <div class="calendar-legend">
          <span class="legend-item"><span class="legend-swatch legend-qualifying"></span>Qualifying</span>
          <span class="legend-item"><span class="legend-swatch legend-regular"></span>Workout</span>
          <span class="legend-item"><span class="legend-dot legend-missed"></span>Missed day</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _render_year_calendar(df_year=df_year, name=who, year=year, name_col=name_col)
