import pandas as pd
import streamlit as st

from data.metrics import (
    longest_streak,
    fastest_winner_date,
    lazy_logger_score,
    frontload_vs_cram,
)
from ui.common import render_styled_table, alt_weekday_bubble, render_card_start, render_card_end
import altair as alt


def render(*, lb, df_month, cutoff: int) -> None:
    # st.markdown("<hr>", unsafe_allow_html=True)
    winner_df = lb[lb["is_winner"]].copy()

    # winner_df = lb[lb["rank"] <= 4].reset_index(drop=True)

    streak_rows = []
    for name, g in df_month[df_month["burnt_250"]].groupby("name"):
        streak_rows.append({"Name": name, "Longest Streak": longest_streak(g["workout_date"].dropna().tolist())})
    streak_df = pd.DataFrame(streak_rows).sort_values("Longest Streak", ascending=False)

    fw_rows = []
    for name in df_month["name"].dropna().unique():
        fw = fastest_winner_date(df_month, name, cutoff)
        if fw:
            fw_rows.append({"Name": name, "Hit cutoff on": fw})
    fw_df = pd.DataFrame(fw_rows).sort_values("Hit cutoff on") if fw_rows else pd.DataFrame(columns=["Name","Hit cutoff on"])

    lazy_df = lazy_logger_score(df_month)
    fl = frontload_vs_cram(df_month)

    barely_missed = lb[(~lb["is_winner"]) & (lb["qualifying_days"].isin([cutoff - 2, cutoff - 1]))].copy()
    barely_missed = barely_missed.rename(columns={"name":"Name","qualifying_days":"Qualifying Days","workouts_left":"Workouts Left","workout_days":"Workout Days"})

    consistent_not_qual = lb[(~lb["is_winner"]) & (lb["workout_days"] >= cutoff)].copy()
    consistent_not_qual = consistent_not_qual.rename(columns={"name":"Name","qualifying_days":"Qualifying Days","workouts_left":"Workouts Left","workout_days":"Workout Days"})

    st.markdown("### This month's winners!! ")
    st.markdown("Congratulations guys!! Each one of you burnt 4000 + calories this month.")

    def _chunks(df, n):
        for i in range(0, len(df), n):
            yield df.iloc[i:i + n]

    # use shared helper from ui.common: render_styled_table

    # Render winners as tiles in rows of 4 columns
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
                          <div style="font-size:60px">🏆</div>
                          <div style="font-weight:600; margin-top:6px">{row['name']}</div>
                          <div style="color:#666;">{int(row['qualifying_days'])} workouts</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
    # Big-picture group summary stats
    total_participants = int(lb["name"].nunique()) if "name" in lb.columns else int(len(lb))
    total_winners = int(lb.get("is_winner", pd.Series(dtype=int)).sum()) if not lb.empty else 0
    total_workouts = int(lb.get("workout_days", pd.Series(dtype=int)).sum()) if not lb.empty else 0
    total_calories = int(((lb.get("qualifying_days", 0) * 250) + ((lb.get("workout_days", 0) - lb.get("qualifying_days", 0)) * 150)).sum()) if not lb.empty else 0
    
    ### Group Summary Stats ###
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### Highlights of our group pledge this month:")

    stat_cols = st.columns(4, gap="small")
    stats = [
        ("Total Participants", f"{total_participants}"),
        ("Total Winners", f"{total_winners}"),
        ("Total Workouts", f"{total_workouts}"),
        ("Approx Calories Burned", f"{total_calories:,} Cal"),
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

    # Summary table with all participants
    summary_table = lb.copy()
    summary_table["Q/W%"] = (summary_table["qualifying_days"] / summary_table["workout_days"] * 100).round(1)
    summary_table = summary_table[["name", "workout_days", "qualifying_days", "Q/W%"]].sort_values("name")
    summary_table = summary_table.rename(columns={
        "name": "Participant",
        "workout_days": "# of Workouts [W]",
        "qualifying_days": "# of Qualifying Workouts [Q]"
    })
    
    st.markdown("<hr>", unsafe_allow_html=True)

    # Month summary in a card-like container (matches other small cards)
    with st.container(key="month_summary"):
        # render_card_start(title="Monthly Summary")
        st.markdown("### Monthly Individual Summary")
        render_styled_table(summary_table)
        render_card_end()

    st.markdown("<hr>", unsafe_allow_html=True)
    a, b, c = st.columns(3, gap="small")

    with a:
        with st.container(key="longest_streak"):
            st.markdown("### Longest streak")
            st.markdown("Day after day - Streak still alive")
            if not streak_df.empty:
                top = streak_df.iloc[0]
                st.markdown(f"**Leader:** {top['Name']} — **{int(top['Longest Streak'])} days**")
                render_styled_table(streak_df.head(12))
            else:
                st.caption("No qualifying streaks yet.")

    with b:
        with st.container(key="fastest_winner"):
            st.markdown("### Fastest winner")
            st.markdown("Wrapped it up while others were still planning !!")
            if not fw_df.empty:
                top = fw_df.iloc[0]
                st.markdown(f"**Fastest:** {top['Name']} — cutoff on **{top['Hit cutoff on']}**")
                render_styled_table(fw_df.head(12))
            else:
                st.caption("No winners yet (or not enough qualifying days).")

    with c:
        with st.container(key="lazy_logger"):
            st.markdown("### Lazy logger ;)")
            st.markdown("Trained like a beast - Logged like a sloth")
            if lazy_df is not None and not lazy_df.empty:
                lazy_show = lazy_df.rename(columns={"name":"Name", "avg_log_delay_days":"Avg. Log Delay (Days)"})
                lazy_show["Avg. Log Delay (Days)"] = lazy_show["Avg. Log Delay (Days)"].round(2)
                st.markdown(f"**Most delayed:** {lazy_show.iloc[0]['Name']} — avg **{lazy_show.iloc[0]['Avg. Log Delay (Days)']:.2f} days**")
                render_styled_table(lazy_show.head(12))
            else:
                st.caption("Need timestamps to score logging delay.")

    st.markdown("<hr>", unsafe_allow_html=True)
    left, right = st.columns([1.2, 1.0], gap="small")

    with left:
        with st.container( key="front_loading"):
            st.markdown("### Brick by Brick vs All-Nighters")
            st.markdown("Tracks how effort was distributed across the month, from steady builds to final-week bursts.")
            if not fl.empty:
                render_styled_table(fl.rename(columns={"name":"Name","first_half":"First half","second_half":"Second half","style":"Style"}))

                counts = (
                    fl["style"]
                    .dropna()
                    .value_counts()
                    .rename_axis("Style")
                    .reset_index(name="People")
                )

    with right:
        with st.container( key="barely_missed"):
            st.markdown("### Missed by a hair")
            st.caption("Legends who missed the qualifying cutoff by 1 or 2 days.")
            render_styled_table(barely_missed[["Name","Qualifying Days","Workouts Left","Workout Days"]])
            st.markdown("### Building the Habit")    
            st.caption("Strong consistency this month — qualifying days are the next unlock.")
            render_styled_table(consistent_not_qual[["Name","Qualifying Days","Workouts Left","Workout Days"]])

    # Bubble plot: workouts by weekday (delegated to helper)
    with st.container(key="weekday_bubble"):
        title_col, filter_col = st.columns([3.2, 1.2], gap="large")
        with title_col:
            st.markdown("### Workouts by Day of the Week")
            st.caption("Each bubble shows total workouts logged on that weekday (all workouts, not only qualifying).")
        with filter_col:
            candidate_options = sorted(df_month["name"].dropna().unique().tolist()) if df_month is not None else []
            candidate_options = ["All"] + candidate_options
            selected_candidate = st.selectbox(
                "Filter by participant",
                candidate_options,
                index=0,
                key="weekday_bubble_candidate",
            )
        if df_month is None or df_month.empty:
            st.caption("No workout data for the selected month.")
        else:
            filtered = df_month if selected_candidate == "All" else df_month[df_month["name"] == selected_candidate]
            try:
                dates = pd.to_datetime(filtered["workout_date"])
            except Exception:
                dates = filtered["workout_date"]

            wd = (
                dates.dt.day_name().rename("Weekday").to_frame().assign(count=1)
            )

            weekday_order = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            counts = (
                wd.groupby("Weekday")["count"]
                .sum()
                .reindex(weekday_order, fill_value=0)
                .rename_axis("Weekday")
                .reset_index()
            )
            counts["Weekday"] = pd.Categorical(counts["Weekday"], categories=weekday_order, ordered=True)
            counts = counts.sort_values("Weekday")

            chart = alt_weekday_bubble(counts=counts, weekday_order=weekday_order)
            st.altair_chart(chart, use_container_width=True)
