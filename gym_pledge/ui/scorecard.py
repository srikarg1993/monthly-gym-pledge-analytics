import pandas as pd
import matplotlib.pyplot as plt

from config.globals import *
from data.source import *
from data.metrics import *
from ui.common import *
import altair as alt


def render(*, lb, df_month) -> None:
    st.markdown("<hr>", unsafe_allow_html=True)

    winner_df = lb[lb["rank"] == 2].reset_index(drop=True)

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

    st.markdown("### Winners!! ")
    st.markdown("Congratulations guys!! You have spent atleast 4000 + calories in this month.")
    for _, row in winner_df.iterrows():
        winner_class = "winner" if row["is_winner"] else ""

        st.markdown(
            f"""
            <div class="lb-row {winner_class}">
            <div class="lb-rank">🏆</div>
            <div class="lb-name">{row['name']}</div>
            <div class="lb-workouts">{row['qualifying_days']} workouts</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown("<hr>", unsafe_allow_html=True)

    a, b, c = st.columns(3, gap="large")

    with a:
        with st.container( key="longest_streak"):
            
            st.markdown("### Longest streak")

            if not streak_df.empty:
                top = streak_df.iloc[0]
                st.markdown(f"**Leader:** {top['Name']} — **{int(top['Longest Streak'])} days**")
                st.dataframe(streak_df.head(12), hide_index=True, use_container_width=True)
            else:
                st.caption("No qualifying streaks yet.")

    with b:
        with st.container( key="fastest_winner"):
            st.markdown("### Fastest winner")
            if not fw_df.empty:
                top = fw_df.iloc[0]
                st.markdown(f"**Fastest:** {top['Name']} — cutoff on **{top['Hit cutoff on']}**")
                st.dataframe(fw_df.head(12), hide_index=True, use_container_width=True)
            else:
                st.caption("No winners yet (or not enough qualifying days).")

    with c:
        with st.container( key="lazy_logger"):
            st.markdown("### Lazy logger")
            if lazy_df is not None and not lazy_df.empty:
                lazy_show = lazy_df.rename(columns={"name":"Name", "avg_log_delay_days":"Avg. Log Delay (Days)"})
                st.markdown(f"**Most delayed:** {lazy_show.iloc[0]['Name']} — avg **{lazy_show.iloc[0]['Avg. Log Delay (Days)']:.2f} days**")
                st.dataframe(lazy_show.head(12), hide_index=True, use_container_width=True)
            else:
                st.caption("Need timestamps to score logging delay.")

    st.markdown("<hr>", unsafe_allow_html=True)
    left, right = st.columns([1.2, 1.0], gap="large")

    with left:
        with st.container( key="front_loading"):
            st.markdown("### Front-loading vs cramming")
            if not fl.empty:
                st.dataframe(
                    fl.rename(columns={"name":"Name","first_half":"First half","second_half":"Second half","style":"Style"}),
                    hide_index=True,
                    use_container_width=True
                )
                
                counts = (
                    fl["style"]
                    .dropna()
                    .value_counts()
                    .rename_axis("Style")
                    .reset_index(name="People")
                )

                chart = (
                    alt.Chart(counts)
                    .mark_bar(
                        size=28,
                        cornerRadiusTopLeft=6,
                        cornerRadiusTopRight=6,
                    )
                    .encode(
                        x=alt.X(
                            "Style:N",
                            sort="-y",
                            title="Style",
                            axis=alt.Axis(labelAngle=0),
                        ),
                        y=alt.Y(
                            "People:Q",
                            title="People",
                            scale=alt.Scale(nice=True),
                        ),
                        tooltip=["Style:N", "People:Q"],
                    )
                    .properties(
                        height=260,
                    )
                )

                st.markdown("### Distribution of styles")
                st.altair_chart(chart, use_container_width=True)
            else:
                st.caption("Not enough data.")

    with right:
        with st.container( key="barely_missed"):
            st.markdown("### Barely missed & consistent-but-not-qualifying")
            st.caption("Barely missed = cutoff-2 or cutoff-1 qualifying days (not a winner).")
            st.dataframe(barely_missed[["Name","Qualifying Days","Workouts Left","Workout Days"]], hide_index=True, use_container_width=True)
            st.caption("Consistent but not qualifying = workout days ≥ cutoff but qualifying < cutoff.")
            st.dataframe(consistent_not_qual[["Name","Qualifying Days","Workouts Left","Workout Days"]], hide_index=True, use_container_width=True)
