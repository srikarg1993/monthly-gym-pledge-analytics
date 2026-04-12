import pandas as pd
import streamlit as st

from app_time import current_month_str, today_app
from data.metrics import (
    fastest_winner_date,
    frontload_vs_cram,
    longest_streak,
    month_bounds,
)
from ui.common import (
    alt_goal_gap_chart,
    alt_goal_ladder_chart,
    alt_group_split_chart,
    alt_race_lane_chart,
    alt_streak_heartbeat_chart,
    alt_weekday_cadence_chart,
    alt_delay_runway_chart,
)


STREAK_KEY = "scorecard_streak_participant"
STATUS_ORDER = ["Winner", "1-2 away", "Workout-rich", "Other"]
STATUS_COLORS = {
    "Winner": "#5FA68D",
    "1-2 away": "#B7835A",
    "Workout-rich": "#6E88A6",
    "Other": "#5D6B7C",
}
WEEKDAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def _chunks(df: pd.DataFrame, size: int):
    for i in range(0, len(df), size):
        yield df.iloc[i:i + size]


def _close_targets(cutoff: int) -> set[int]:
    return {days for days in (cutoff - 2, cutoff - 1) if days >= 0}


def _participant_status(row: pd.Series, cutoff: int) -> str:
    qualifying_days = int(row.get("qualifying_days", 0))
    workout_days = int(row.get("workout_days", 0))
    close_targets = _close_targets(cutoff)

    if qualifying_days >= cutoff:
        return "Winner"
    if qualifying_days in close_targets:
        return "1-2 away"
    if workout_days >= cutoff:
        return "Workout-rich"
    return "Other"


def _build_status_mix_df(lb: pd.DataFrame, cutoff: int) -> pd.DataFrame:
    if lb is None or lb.empty:
        return pd.DataFrame(columns=["Status", "People", "Share", "Color"])

    mix = lb.copy()
    mix["Status"] = mix.apply(_participant_status, cutoff=cutoff, axis=1)
    counts = (
        mix["Status"]
        .value_counts()
        .reindex(STATUS_ORDER, fill_value=0)
        .rename_axis("Status")
        .reset_index(name="People")
    )
    total_people = int(counts["People"].sum())
    counts["Share"] = counts["People"] / total_people if total_people else 0.0
    counts["Color"] = counts["Status"].map(STATUS_COLORS)
    return counts


def _build_close_call_data(lb: pd.DataFrame, cutoff: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    if lb is None or lb.empty:
        empty = pd.DataFrame(columns=["Name", "Qualifying Days", "Workout Days", "Days to Cutoff", "Bucket"])
        return empty, empty.copy()

    base = lb.copy()
    base["Status"] = base.apply(_participant_status, cutoff=cutoff, axis=1)
    base["Days to Cutoff"] = (cutoff - base["qualifying_days"]).clip(lower=0).astype(int)
    base["Bucket"] = base["Days to Cutoff"].map({1: "1 away", 2: "2 away"}).fillna(base["Status"])
    base = base.rename(
        columns={
            "name": "Name",
            "qualifying_days": "Qualifying Days",
            "workout_days": "Workout Days",
        }
    )

    close_calls = base[base["Bucket"].isin(["1 away", "2 away"])].copy()
    close_calls = close_calls.sort_values(
        ["Days to Cutoff", "Qualifying Days", "Workout Days", "Name"],
        ascending=[True, False, False, True],
    ).reset_index(drop=True)

    workout_rich = base[base["Status"] == "Workout-rich"].copy()
    workout_rich = workout_rich.sort_values(
        ["Days to Cutoff", "Qualifying Days", "Workout Days", "Name"],
        ascending=[True, False, False, True],
    ).reset_index(drop=True)

    cols = ["Name", "Qualifying Days", "Workout Days", "Days to Cutoff", "Bucket"]
    return close_calls[cols], workout_rich[cols]


def _build_progress_ladder_df(lb: pd.DataFrame) -> pd.DataFrame:
    if lb is None or lb.empty:
        return pd.DataFrame(columns=["Name", "Qualifying Days", "Workout Days"])

    progress = lb.rename(
        columns={
            "name": "Name",
            "qualifying_days": "Qualifying Days",
            "workout_days": "Workout Days",
        }
    )[["Name", "Qualifying Days", "Workout Days"]].copy()

    return progress.sort_values(
        ["Qualifying Days", "Workout Days", "Name"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def _build_streak_df(df_month: pd.DataFrame) -> pd.DataFrame:
    if df_month is None or df_month.empty:
        return pd.DataFrame(columns=["Name", "Longest Streak"])

    rows = []
    for name, group in df_month[df_month["burnt_250"]].groupby("name"):
        rows.append(
            {
                "Name": str(name),
                "Longest Streak": longest_streak(group["workout_date"].dropna().tolist()),
            }
        )

    if not rows:
        return pd.DataFrame(columns=["Name", "Longest Streak"])

    out = pd.DataFrame(rows)
    return out.sort_values(["Longest Streak", "Name"], ascending=[False, True]).reset_index(drop=True)


def _resolve_streak_focus(lb: pd.DataFrame, streak_df: pd.DataFrame) -> str | None:
    people = sorted(lb["name"].dropna().astype(str).unique().tolist()) if lb is not None and not lb.empty else []
    if not people:
        return None

    current_focus = st.session_state.get(STREAK_KEY)
    if current_focus not in people:
        if not streak_df.empty:
            current_focus = str(streak_df.iloc[0]["Name"])
        else:
            current_focus = people[0]
        st.session_state[STREAK_KEY] = current_focus

    return st.selectbox("Choose participant", people, index=people.index(current_focus), key=STREAK_KEY, label_visibility="collapsed")


def _build_all_streaks_df(df_month: pd.DataFrame, exclude_name: str | None = None) -> pd.DataFrame:
    if df_month is None or df_month.empty:
        return pd.DataFrame(columns=["Day", "Streak", "Name"])

    month_values = df_month["month"].dropna().astype(str)
    if month_values.empty:
        return pd.DataFrame(columns=["Day", "Streak", "Name"])

    month_str = month_values.iloc[0]
    start, end = month_bounds(month_str)
    if month_str == current_month_str():
        end = min(end, today_app())

    names = sorted(df_month["name"].dropna().astype(str).unique().tolist())
    all_rows = []
    for name in names:
        if name == exclude_name:
            continue
        qualifying_dates = set(
            pd.to_datetime(
                df_month[(df_month["name"].astype(str) == name) & (df_month["burnt_250"])]["workout_date"],
                errors="coerce",
            ).dt.date.dropna().tolist()
        )
        streak = 0
        for day in pd.date_range(start=start, end=end, freq="D"):
            current_day = day.date()
            qualifying = current_day in qualifying_dates
            streak = streak + 1 if qualifying else 0
            all_rows.append({"Day": int(day.day), "Streak": streak, "Name": name})

    return pd.DataFrame(all_rows) if all_rows else pd.DataFrame(columns=["Day", "Streak", "Name"])


def _build_streak_wave_df(df_month: pd.DataFrame, focus_name: str) -> pd.DataFrame:
    if df_month is None or df_month.empty or not focus_name:
        return pd.DataFrame(columns=["Day", "Streak", "Qualifying", "Day Label"])

    month_values = df_month["month"].dropna().astype(str)
    if month_values.empty:
        return pd.DataFrame(columns=["Day", "Streak", "Qualifying", "Day Label"])

    month_str = month_values.iloc[0]
    start, end = month_bounds(month_str)
    if month_str == current_month_str():
        end = min(end, today_app())

    qualifying_dates = set(
        pd.to_datetime(
            df_month[(df_month["name"].astype(str) == str(focus_name)) & (df_month["burnt_250"])]["workout_date"],
            errors="coerce",
        ).dt.date.dropna().tolist()
    )

    rows = []
    streak = 0
    for day in pd.date_range(start=start, end=end, freq="D"):
        current_day = day.date()
        qualifying = current_day in qualifying_dates
        streak = streak + 1 if qualifying else 0
        rows.append(
            {
                "Day": int(day.day),
                "Streak": streak,
                "Qualifying": qualifying,
                "Day Label": day.strftime("%b %d"),
            }
        )

    return pd.DataFrame(rows)


def _build_fastest_winner_df(df_month: pd.DataFrame, cutoff: int) -> tuple[pd.DataFrame, int]:
    if df_month is None or df_month.empty:
        return pd.DataFrame(columns=["Name", "Clinch Day", "Finish Label", "Hit cutoff on"]), 31

    month_values = df_month["month"].dropna().astype(str)
    month_days = month_bounds(month_values.iloc[0])[1].day if not month_values.empty else 31

    rows = []
    for name in sorted(df_month["name"].dropna().astype(str).unique().tolist()):
        winner_date = fastest_winner_date(df_month, name, cutoff)
        if winner_date:
            rows.append(
                {
                    "Name": name,
                    "Clinch Day": int(winner_date.day),
                    "Finish Label": f"Day {winner_date.day}",
                    "Hit cutoff on": winner_date,
                }
            )

    if not rows:
        return pd.DataFrame(columns=["Name", "Clinch Day", "Finish Label", "Hit cutoff on"]), month_days

    out = pd.DataFrame(rows)
    out = out.sort_values(["Clinch Day", "Name"], ascending=[True, True]).reset_index(drop=True)
    return out, month_days


def _build_lazy_df(df_month: pd.DataFrame) -> pd.DataFrame | None:
    if df_month is None or df_month.empty:
        return None

    logged = df_month.dropna(subset=["workout_date", "timestamp"]).copy()
    if logged.empty:
        return None

    out = (
        logged.groupby("name")
        .agg(
            **{
                "Avg. Log Delay (Days)": ("log_delay_days", "mean"),
                "Logged Workouts": ("workout_date", "nunique"),
            }
        )
        .reset_index()
        .rename(columns={"name": "Name"})
    )
    out["Avg. Log Delay (Days)"] = out["Avg. Log Delay (Days)"].round(2)
    return out.sort_values(["Avg. Log Delay (Days)", "Name"], ascending=[False, True]).reset_index(drop=True)


def _build_style_balance_df(fl: pd.DataFrame) -> pd.DataFrame:
    if fl is None or fl.empty:
        return pd.DataFrame(columns=["Name", "First Half", "Second Half", "Style", "Balance"])

    out = fl.rename(
        columns={
            "name": "Name",
            "first_half": "First Half",
            "second_half": "Second Half",
            "style": "Style",
        }
    ).copy()
    out["Balance"] = out["Second Half"] - out["First Half"]
    return out.sort_values(["Balance", "Name"], ascending=[True, True]).reset_index(drop=True)


def _build_weekday_mix_df(df_month: pd.DataFrame) -> pd.DataFrame:
    if df_month is None or df_month.empty:
        return pd.DataFrame(
            {
                "Weekday": WEEKDAY_ORDER,
                "All Workouts": [0] * len(WEEKDAY_ORDER),
                "Qualifying Workouts": [0] * len(WEEKDAY_ORDER),
            }
        )

    dates = pd.to_datetime(df_month["workout_date"], errors="coerce")
    overall = (
        dates.dt.day_name().rename("Weekday").to_frame().assign(count=1)
        .groupby("Weekday")["count"]
        .sum()
        .reindex(WEEKDAY_ORDER, fill_value=0)
    )
    qualifying = (
        pd.to_datetime(df_month[df_month["burnt_250"]]["workout_date"], errors="coerce")
        .dt.day_name()
        .rename("Weekday")
        .to_frame()
        .assign(count=1)
        .groupby("Weekday")["count"]
        .sum()
        .reindex(WEEKDAY_ORDER, fill_value=0)
    )

    out = pd.DataFrame(
        {
            "Weekday": WEEKDAY_ORDER,
            "All Workouts": overall.values,
            "Qualifying Workouts": qualifying.values,
        }
    )
    out["Weekday"] = pd.Categorical(out["Weekday"], categories=WEEKDAY_ORDER, ordered=True)
    return out.sort_values("Weekday").reset_index(drop=True)


def render(*, lb, df_month, cutoff: int) -> None:
    winner_df = lb[lb["is_winner"]].copy()
    progress_df = _build_progress_ladder_df(lb)
    streak_df = _build_streak_df(df_month)
    fastest_df, month_days = _build_fastest_winner_df(df_month, cutoff)
    lazy_df = _build_lazy_df(df_month)
    style_df = _build_style_balance_df(frontload_vs_cram(df_month))
    close_calls, workout_rich = _build_close_call_data(lb, cutoff)
    weekday_mix = _build_weekday_mix_df(df_month)

    st.markdown("### This month's winners!! ")
    st.markdown("Congratulations guys!! Each one of you burnt 4000 + calories this month.")

    if winner_df.empty:
        st.caption("No winners yet.")
    else:
        for chunk in _chunks(winner_df, 4):
            cols = st.columns(4, gap="large")
            for i, (_, row) in enumerate(chunk.iterrows()):
                with cols[i]:
                    st.markdown(
                        f"""
                        <div style="border-radius:8px; padding:12px; text-align:center; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
                          <div style="font-size:60px">&#127942;</div>
                          <div style="font-weight:600; margin-top:6px">{row['name']}</div>
                          <div style="color:#9aa0ab;">{int(row['qualifying_days'])} qualifying workouts</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    total_participants = int(lb["name"].nunique()) if "name" in lb.columns else int(len(lb))
    total_winners = int(lb.get("is_winner", pd.Series(dtype=int)).sum()) if not lb.empty else 0
    total_workouts = int(lb.get("workout_days", pd.Series(dtype=int)).sum()) if not lb.empty else 0
    total_calories = int(lb.get("total_calories", pd.Series(dtype=int)).sum()) if not lb.empty else 0

    st.markdown("<hr>", unsafe_allow_html=True)
    with st.container(key="pledge_pulse"):
        st.markdown("### Pledge Pulse")

        stat_cols = st.columns(4, gap="small")
        stats = [
            ("Total Participants", f"{total_participants}", "#6366F1"),
            ("Total Winners", f"{total_winners}", "#10B981"),
            ("Total Workouts", f"{total_workouts}", "#3B82F6"),
            ("Calories Burned", f"{total_calories:,} Cal", "#F59E0B"),
        ]
        for col, (label, value, accent) in zip(stat_cols, stats):
            with col:
                st.markdown(
                    f"""
                    <div style='
                      background: rgba(28,36,60,0.96);
                      border: 1px solid rgba(255,255,255,0.12);
                      padding: 20px 16px;
                      border-radius: 14px;
                      text-align: center;
                      box-shadow: 0 4px 16px rgba(0,0,0,0.4);
                      border-top: 3px solid {accent};
                    '>
                      <div style='font-size:26px; font-weight:800; color:#fff; letter-spacing:-0.02em;'>{value}</div>
                      <div style='font-size:12px; color:#9aa0ab; margin-top:8px; text-transform:uppercase; letter-spacing:0.06em;'>{label}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("<hr>", unsafe_allow_html=True)
    with st.container(key="qualifying_progress"):
        st.markdown("### Qualifying Progress Ladder")
        if progress_df.empty:
            st.caption("No participant progress to show yet.")
        else:
            st.altair_chart(
                alt_goal_ladder_chart(
                    progress_df,
                    label_col="Name",
                    qualifying_col="Qualifying Days",
                    workout_col="Workout Days",
                    cutoff=cutoff,
                    height=max(420, min(920, 70 + len(progress_df) * 38)),
                ),
                use_container_width=True,
            )

    st.markdown("<hr>", unsafe_allow_html=True)
    with st.container(key="longest_streak"):
        title_col, pick_col = st.columns([5, 2], gap="small", vertical_alignment="center")
        with title_col:
            st.markdown("### Longest Streak")
        with pick_col:
            streak_focus = _resolve_streak_focus(lb, streak_df)

        if streak_focus is None:
            st.caption("No participants available for streak tracking.")
        else:
            streak_wave_df = _build_streak_wave_df(df_month, streak_focus)
            bg_streaks = _build_all_streaks_df(df_month, exclude_name=streak_focus)

            if streak_wave_df.empty or int(streak_wave_df["Streak"].max()) == 0:
                st.caption(f"{streak_focus} has not built a qualifying streak yet.")
            else:
                focus_peak = int(streak_wave_df["Streak"].max())
                leader_note = ""
                if not streak_df.empty:
                    leader = streak_df.iloc[0]
                    leader_note = f"Group leader: {leader['Name']} with {int(leader['Longest Streak'])} days."
                st.markdown(f"**{streak_focus}** peaked at **{focus_peak} days**. {leader_note}".strip())
                st.altair_chart(
                    alt_streak_heartbeat_chart(
                        streak_wave_df,
                        day_col="Day",
                        streak_col="Streak",
                        qualifying_col="Qualifying",
                        day_label_col="Day Label",
                        month_days=month_days,
                        background_streaks=bg_streaks if not bg_streaks.empty else None,
                        height=360,
                    ),
                    use_container_width=True,
                )

    st.markdown("<hr>", unsafe_allow_html=True)
    with st.container(key="fastest_winner"):
        st.markdown("### Fastest Winner")
        st.caption("Each lane runs from day 1 to the moment a winner crossed the goal line. Everyone who finished is shown.")
        if fastest_df.empty:
            st.caption("No winners yet (or nobody has reached the cutoff in the selected month).")
        else:
            top = fastest_df.iloc[0]
            st.markdown(f"**Earliest finisher:** {top['Name']} on **{top['Hit cutoff on']}**")
            st.altair_chart(
                alt_race_lane_chart(
                    fastest_df,
                    label_col="Name",
                    finish_col="Clinch Day",
                    total_days=month_days,
                    finish_label_col="Finish Label",
                    height=max(280, min(760, 60 + len(fastest_df) * 34)),
                ),
                use_container_width=True,
            )

    st.markdown("<hr>", unsafe_allow_html=True)
    with st.container(key="lazy_logger"):
        st.markdown("### Lazy Logger")
        st.caption("Each bubble sits in the zone matching its average logging delay. Bigger bubbles mean more logged workouts.")
        if lazy_df is None or lazy_df.empty:
            st.caption("Need timestamps to score logging delay.")
        else:
            n = len(lazy_df)
            max_zone = max(n // 3, 1)
            chart_h = max(340, min(760, max_zone * 90 + 120))
            st.altair_chart(
                alt_delay_runway_chart(
                    lazy_df,
                    label_col="Name",
                    delay_col="Avg. Log Delay (Days)",
                    size_col="Logged Workouts",
                    label_value_col="Avg. Log Delay (Days)",
                    height=chart_h,
                ),
                use_container_width=True,
            )

    st.markdown("<hr>", unsafe_allow_html=True)
    with st.container(key="front_loading"):
        st.markdown("### Brick by Brick vs All-Nighters")
        st.caption("Left bars are first-half qualifying workouts. Right bars are second-half qualifying workouts. Balanced rows stay centered.")
        if style_df.empty:
            st.caption("No qualifying workouts yet for workout-style analysis.")
        else:
            st.altair_chart(
                alt_group_split_chart(
                    style_df,
                    label_col="Name",
                    left_col="First Half",
                    right_col="Second Half",
                    style_col="Style",
                    height=max(360, min(880, 80 + len(style_df) * 34)),
                ),
                use_container_width=True,
            )

    st.markdown("<hr>", unsafe_allow_html=True)
    with st.container(key="close_calls"):
        st.markdown("### Missed by a Hair")
        st.caption("This view zooms in around the goal line so the gap, not the full month, gets the visual emphasis.")
        if close_calls.empty:
            st.caption("Nobody finished just one or two days short this month.")
        else:
            st.altair_chart(
                alt_goal_gap_chart(
                    close_calls,
                    label_col="Name",
                    qualifying_col="Qualifying Days",
                    gap_col="Days to Cutoff",
                    cutoff=cutoff,
                    lower_bound=max(cutoff - 3, 0),
                    height=max(240, min(480, 60 + len(close_calls) * 34)),
                ),
                use_container_width=True,
            )

        st.markdown("### Building the Habit")
        st.caption("These participants showed up often enough. The gap chart shows how many qualifying days still separate them from the line.")
        if workout_rich.empty:
            st.caption("No workout-rich participants are sitting below the cutoff this month.")
        else:
            lower_bound = max(min(int(workout_rich["Qualifying Days"].min()) - 1, cutoff - 2), 0)
            st.altair_chart(
                alt_goal_gap_chart(
                    workout_rich,
                    label_col="Name",
                    qualifying_col="Qualifying Days",
                    gap_col="Days to Cutoff",
                    cutoff=cutoff,
                    lower_bound=lower_bound,
                    height=max(240, min(520, 60 + len(workout_rich) * 34)),
                ),
                use_container_width=True,
            )

    st.markdown("<hr>", unsafe_allow_html=True)
    with st.container(key="weekday_cadence"):
        st.markdown("### Workouts by Day of the Week")
        st.caption("Steel bars show all logged workouts. The sage line shows how many of those were qualifying workouts.")
        if df_month is None or df_month.empty:
            st.caption("No workout data for the selected month.")
        else:
            st.altair_chart(
                alt_weekday_cadence_chart(
                    weekday_mix,
                    weekday_col="Weekday",
                    total_col="All Workouts",
                    qualifying_col="Qualifying Workouts",
                    weekday_order=WEEKDAY_ORDER,
                    height=320,
                ),
                use_container_width=True,
            )
