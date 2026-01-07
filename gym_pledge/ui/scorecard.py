import pandas as pd
import matplotlib.pyplot as plt

from config.globals import *
from data.source import *
from data.metrics import *
from ui.common import *
import altair as alt


def render(*, lb, df_month) -> None:
    # st.markdown("<hr>", unsafe_allow_html=True)

    winner_df = lb[lb["rank"] <= 4].reset_index(drop=True)

    streak_rows = []
    for name, g in df_month[df_month["burnt_250"]].groupby("name"):
        streak_rows.append({"Name": name, "Longest Streak": longest_streak(g["workout_date"].dropna().tolist())})
    streak_df = pd.DataFrame(streak_rows).sort_values("Longest Streak", ascending=False)

    fw_rows = []
    for name in df_month["name"].dropna().unique():
        fw = fastest_winner_date(df_month, name, WINNER_CUTOFF)
        if fw:
            fw_rows.append({"Name": name, "Hit cutoff on": fw})
    fw_df = pd.DataFrame(fw_rows).sort_values("Hit cutoff on") if fw_rows else pd.DataFrame(columns=["Name","Hit cutoff on"])

    lazy_df = lazy_logger_score(df_month)
    fl = frontload_vs_cram(df_month)

    barely_missed = lb[(~lb["is_winner"]) & (lb["qualifying_days"].isin([WINNER_CUTOFF-2, WINNER_CUTOFF-1]))].copy()
    barely_missed = barely_missed.rename(columns={"name":"Name","qualifying_days":"Qualifying Days","workouts_left":"Workouts Left","workout_days":"Workout Days"})

    consistent_not_qual = lb[(~lb["is_winner"]) & (lb["workout_days"] >= WINNER_CUTOFF)].copy()
    consistent_not_qual = consistent_not_qual.rename(columns={"name":"Name","qualifying_days":"Qualifying Days","workouts_left":"Workouts Left","workout_days":"Workout Days"})

    st.markdown("### This month's winners!! ")
    st.markdown("Congratulations guys!! You burnt 4000 + calories this month.")

    def _chunks(df, n):
        for i in range(0, len(df), n):
            yield df.iloc[i:i + n]

    def render_styled_table(df: pd.DataFrame, max_rows: int | None = None) -> None:
        """Render a styled HTML table with white bold headers to match page style."""
        if df is None or df.empty:
            st.caption("No data to display.")
            return

        display_df = df.copy()
        if max_rows is not None:
            display_df = display_df.head(max_rows)

        # Build HTML table
        table_html = """
        <style>
            .styled-table { width:100%; border-collapse:collapse; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            .styled-table th { background: #0b1220; color: #fff; padding:10px 12px; text-align:left; font-weight:700; font-size:14px; }
            .styled-table td { padding:10px 12px; border-bottom:1px solid rgba(255,255,255,0.04); color: #d1d5db; }
            .styled-table tr:hover td { background: rgba(255,255,255,0.02); }
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

    # st.markdown("<hr>", unsafe_allow_html=True)

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
        st.markdown("### Monthly Summary")
        # st.markdown(
        #     "<div style='border-radius:10px; padding:16px; background-color: rgba(255,255,255,0.09) !important; border:1px solid rgba(255,255,255,0.12); box-shadow: 0 2px 6px rgba(0,0,0,0.15);'>",
        #     unsafe_allow_html=True,
        # )
        render_styled_table(summary_table)
        st.markdown("</div>", unsafe_allow_html=True)

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

                # chart = (
                #     alt.Chart(counts)
                #     .mark_bar(
                #         size=28,
                #         cornerRadiusTopLeft=6,
                #         cornerRadiusTopRight=6,
                #     )
                #     .encode(
                #         x=alt.X(
                #             "Style:N",
                #             sort="-y",
                #             title="Style",
                #             axis=alt.Axis(labelAngle=0),
                #         ),
                #         y=alt.Y(
                #             "People:Q",
                #             title="People",
                #             scale=alt.Scale(nice=True),
                #         ),
                #         tooltip=["Style:N", "People:Q"],
                #     )
                #     .properties(
                #         height=260,
                #     )
                # )

                # Disabled distribution-of-styles chart per request
                # st.markdown("### Distribution of styles")
                # st.altair_chart(chart, use_container_width=True)
            else:
                st.caption("Not enough data.")

    with right:
        with st.container( key="barely_missed"):
            st.markdown("### Missed by a hair")
            st.caption("Legends who missed the qualifying cutoff by 1 or 2 days.")
            render_styled_table(barely_missed[["Name","Qualifying Days","Workouts Left","Workout Days"]])
            st.markdown("### Building the Habit")    
            st.caption("Strong consistency this month — qualifying days are the next unlock.")
            render_styled_table(consistent_not_qual[["Name","Qualifying Days","Workouts Left","Workout Days"]])
