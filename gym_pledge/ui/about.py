import matplotlib.pyplot as plt
import streamlit as st

PLEDGE_AMOUNT = 10
QUALIFYING_DAYS = 16
DAILY_CALORIE_TARGET = 250
VENMO_LINK = "https://venmo.com/u/maddaladivya3212"
VENMO_HANDLE = "@maddaladivya3212"


def _inject_about_styles() -> None:
    st.markdown(
        """
        <style>
          .about-hero{
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 18px;
            padding: 22px 22px;
            background:
              radial-gradient(700px 220px at 100% 0%, rgba(99,102,241,0.30), transparent 70%),
              radial-gradient(600px 200px at 0% 0%, rgba(16,185,129,0.24), transparent 70%),
              rgba(20,28,45,0.92);
            margin-bottom: 14px;
          }
          .about-chip{
            display: inline-block;
            font-size: 0.78rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: #9fb2ff;
            background: rgba(79,70,229,0.20);
            border: 1px solid rgba(99,102,241,0.45);
            border-radius: 999px;
            padding: 4px 10px;
            margin-bottom: 10px;
          }
          .about-hero h2{
            margin: 0;
            font-size: 1.65rem;
            line-height: 1.2;
            color: #e4e6eb;
          }
          .about-hero p{
            margin: 8px 0 0;
            color: #a0a4b3;
            font-size: 0.96rem;
          }
          .about-rule-grid{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin: 12px 0 16px;
          }
          .about-rule-card{
            display: flex;
            align-items: center;
            gap: 12px;
            background: rgba(28,36,60,0.9);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 14px;
            padding: 12px;
          }
          .about-ring{
            width: 72px;
            height: 72px;
            border-radius: 999px;
            display: grid;
            place-items: center;
            position: relative;
            flex-shrink: 0;
          }
          .about-ring::before{
            content: "";
            position: absolute;
            inset: 8px;
            border-radius: 999px;
            background: rgba(11,18,32,0.95);
          }
          .about-ring span{
            position: relative;
            z-index: 1;
            color: #e4e6eb;
            font-size: 1.05rem;
            font-weight: 800;
          }
          .about-ring-money{
            background: conic-gradient(#4f46e5 0 78%, rgba(255,255,255,0.10) 78% 100%);
          }
          .about-ring-days{
            background: conic-gradient(#10b981 0 86%, rgba(255,255,255,0.10) 86% 100%);
          }
          .about-ring-calories{
            background: conic-gradient(#38bdf8 0 74%, rgba(255,255,255,0.10) 74% 100%);
          }
          .about-rule-title{
            color: #e4e6eb;
            font-size: 1rem;
            font-weight: 700;
            line-height: 1.1;
            margin-bottom: 3px;
          }
          .about-rule-sub{
            color: #a0a4b3;
            font-size: 0.84rem;
            line-height: 1.3;
          }
          .about-flow-grid{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 10px;
            margin: 10px 0 16px;
          }
          .about-flow-step{
            background: rgba(28,36,60,0.82);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 14px;
            padding: 12px;
            min-height: 135px;
          }
          .about-step-index{
            width: 28px;
            height: 28px;
            border-radius: 999px;
            display: grid;
            place-items: center;
            font-size: 0.82rem;
            font-weight: 800;
            color: #dbe6ff;
            background: rgba(99,102,241,0.35);
            margin-bottom: 7px;
          }
          .about-flow-step h4{
            margin: 0 0 4px;
            color: #e4e6eb;
            font-size: 0.98rem;
          }
          .about-flow-step p{
            margin: 0;
            color: #a0a4b3;
            font-size: 0.86rem;
            line-height: 1.35;
          }
          .about-sim-shell{
            margin-top: 6px;
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.10);
            background: rgba(20,28,45,0.78);
            padding: 12px;
          }
          .about-sim-kpi-grid{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
          }
          .about-sim-kpi{
            background: rgba(28,36,60,0.9);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 10px;
            padding: 9px 10px;
          }
          .about-sim-kpi .label{
            color: #95a3bb;
            font-size: 0.74rem;
            line-height: 1.1;
            margin-bottom: 4px;
          }
          .about-sim-kpi .value{
            color: #e4e6eb;
            font-size: 1.12rem;
            font-weight: 800;
            line-height: 1.08;
          }
          .about-sim-footnote{
            margin-top: 7px;
            color: #93a0b6;
            font-size: 0.77rem;
          }
          .about-sim-legend{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 2px;
            justify-content: center;
          }
          .about-dot{
            width: 10px;
            height: 10px;
            border-radius: 999px;
            display: inline-block;
            margin-right: 6px;
          }
          .about-dot-win{background: #34d399;}
          .about-dot-non{background: #334155;}
          .about-legend-item{
            display: inline-flex;
            align-items: center;
            font-size: 0.75rem;
            color: #9facbf;
          }
          div.st-key-about_participants,
          div.st-key-about_winners{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin-bottom: 2px !important;
            overflow: visible !important;
          }
          div.st-key-about_participants div[data-testid="stSlider"],
          div.st-key-about_winners div[data-testid="stSlider"]{
            padding-top: 0 !important;
            padding-bottom: 0 !important;
          }
          .about-activity-grid{
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 8px;
            margin-top: 0;
            margin-bottom: 10px;
          }
          .about-activity-chip{
            text-align: center;
            padding: 10px 8px;
            font-size: 0.84rem;
            font-weight: 600;
            color: #d8deea;
            background: rgba(28,36,60,0.82);
            border: 1px solid rgba(255,255,255,0.09);
            border-radius: 10px;
          }
          .about-active-shell{
            margin-top: 10px;
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.10);
            background: rgba(20,28,45,0.78);
            padding: 12px;
            overflow: hidden;
          }
          .about-active-callout{
            border-radius: 11px;
            background: linear-gradient(90deg, rgba(56,189,248,0.18), rgba(16,185,129,0.13));
            border: 1px solid rgba(56,189,248,0.35);
            padding: 9px 10px;
            color: #d7e2f2;
            font-size: 0.9rem;
            margin-bottom: 10px;
            position: relative;
            z-index: 1;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
          }
          .about-active-callout .label{
            color: #d7e2f2;
            font-weight: 600;
          }
          .about-active-callout .target{
            color: #ffffff;
            font-weight: 800;
            background: rgba(11,18,32,0.58);
            border: 1px solid rgba(255,255,255,0.18);
            border-radius: 999px;
            padding: 3px 10px;
            font-size: 0.84rem;
          }
          .about-active-rules{
            display: grid;
            margin-top: 2px;
            gap: 8px;
          }
          .about-active-rule{
            display: grid;
            grid-template-columns: 30px 1fr;
            gap: 10px;
            align-items: start;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.09);
            background: rgba(28,36,60,0.9);
            padding: 10px;
          }
          .about-active-rule .num{
            width: 24px;
            height: 24px;
            border-radius: 999px;
            display: grid;
            place-items: center;
            font-size: 0.75rem;
            font-weight: 800;
            color: #dbe6ff;
            background: rgba(99,102,241,0.38);
            margin-top: 1px;
          }
          .about-active-rule .text{
            color: #d4dceb;
            font-size: 0.90rem;
            line-height: 1.3;
          }
          .about-active-rule .text b{
            color: #ffffff;
          }
          @media (max-width: 1000px){
            .about-rule-grid{grid-template-columns: 1fr;}
            .about-flow-grid{grid-template-columns: 1fr 1fr;}
            .about-activity-grid{grid-template-columns: repeat(3, minmax(0, 1fr));}
            .about-sim-kpi-grid{grid-template-columns: 1fr;}
          }
          @media (max-width: 700px){
            .about-flow-grid{grid-template-columns: 1fr;}
            .about-activity-grid{grid-template-columns: 1fr 1fr;}
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_rules() -> None:
    st.markdown(
        f"""
        <div class="about-rule-grid">
          <div class="about-rule-card">
            <div class="about-ring about-ring-money"><span>${PLEDGE_AMOUNT}</span></div>
            <div>
              <div class="about-rule-title">Monthly pledge</div>
              <div class="about-rule-sub">Each member contributes to one shared pot.</div>
            </div>
          </div>
          <div class="about-rule-card">
            <div class="about-ring about-ring-days"><span>{QUALIFYING_DAYS}</span></div>
            <div>
              <div class="about-rule-title">Qualifying days</div>
              <div class="about-rule-sub">Hit this monthly count to earn from the pot.</div>
            </div>
          </div>
          <div class="about-rule-card">
            <div class="about-ring about-ring-calories"><span>{DAILY_CALORIE_TARGET}+</span></div>
            <div>
              <div class="about-rule-title">Calories per day</div>
              <div class="about-rule-sub">Any activity is valid once daily burn crosses this mark.</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_flow() -> None:
    st.markdown("### How it runs")
    st.markdown(
        f"""
        <div class="about-flow-grid">
          <div class="about-flow-step">
            <div class="about-step-index">1</div>
            <h4>Join monthly pool</h4>
            <p>Send ${PLEDGE_AMOUNT} to <a href="{VENMO_LINK}" target="_blank">{VENMO_HANDLE}</a>.</p>
          </div>
          <div class="about-flow-step">
            <div class="about-step-index">2</div>
            <h4>Move your way</h4>
            <p>Gym, walking, running, sports, yoga, dance, or mixed sessions.</p>
          </div>
          <div class="about-flow-step">
            <div class="about-step-index">3</div>
            <h4>Log daily</h4>
            <p>Submit your workout day in the group Google Form.</p>
          </div>
          <div class="about-flow-step">
            <div class="about-step-index">4</div>
            <h4>Split payout</h4>
            <p>Only members at {QUALIFYING_DAYS}+ days share the total pool.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _build_payout_chart(participants: int, winners: int):
    winners = max(1, min(winners, participants))
    non_winners = max(participants - winners, 0)

    values = [winners, non_winners] if non_winners else [winners]
    colors = ["#34d399", "#334155"] if non_winners else ["#34d399"]

    fig, ax = plt.subplots(figsize=(1.8, 1.55))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")

    ax.pie(
        values,
        colors=colors,
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.26, "edgecolor": "none"},
    )
    fig.subplots_adjust(left=0.08, right=0.92, top=0.92, bottom=0.08)

    pool_total = participants * PLEDGE_AMOUNT
    payout_per_winner = pool_total / winners

    ax.text(
        0,
        0.06,
        f"${payout_per_winner:.2f}",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="800",
        color="#e4e6eb",
    )
    ax.text(
        0,
        -0.09,
        "per winner",
        ha="center",
        va="center",
        fontsize=6.5,
        color="#a0a4b3",
    )
    ax.axis("equal")
    return fig, pool_total, payout_per_winner


def _render_payout_simulator() -> None:
    st.markdown("### Payout simulator")

    slider_col1, slider_col2 = st.columns(2)
    with slider_col1:
        participants = st.slider(
            "Participants",
            min_value=5,
            max_value=40,
            value=10,
            step=1,
            key="about_participants",
        )
    with slider_col2:
        winners = st.slider(
            "Winners",
            min_value=1,
            max_value=participants,
            value=min(5, participants),
            step=1,
            key="about_winners",
        )

    chart_col, summary_col = st.columns([0.88, 1.42], gap="small")
    fig, pool_total, payout_per_winner = _build_payout_chart(participants, winners)
    non_winners = max(participants - winners, 0)
    qualifying_rate = (winners / participants) * 100 if participants else 0

    with chart_col:
        st.pyplot(fig, transparent=True)
        st.markdown(
            f"""
            <div class="about-sim-legend">
              <span class="about-legend-item"><span class="about-dot about-dot-win"></span>{winners} qualifiers</span>
              <span class="about-legend-item"><span class="about-dot about-dot-non"></span>{non_winners} non-qualifiers</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with summary_col:
        st.markdown(
            f"""
            <div class="about-sim-shell">
              <div class="about-sim-kpi-grid">
                <div class="about-sim-kpi">
                  <div class="label">Pool total</div>
                  <div class="value">${pool_total}</div>
                </div>
                <div class="about-sim-kpi">
                  <div class="label">Split among</div>
                  <div class="value">{winners} winners</div>
                </div>
                <div class="about-sim-kpi">
                  <div class="label">Non-qualifiers</div>
                  <div class="value">{non_winners}</div>
                </div>
                <div class="about-sim-kpi">
                  <div class="label">Qualifying rate</div>
                  <div class="value">{qualifying_rate:.0f}%</div>
                </div>
              </div>
              <div class="about-sim-footnote">
                Formula: ({participants} x ${PLEDGE_AMOUNT}) / {winners} = ${payout_per_winner:.2f} per winner
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_activity_and_ops() -> None:
    st.markdown("### What counts as an active day")
    st.markdown(
        f"""
        <div class="about-active-shell">
          <div class="about-active-callout">
            <span class="label">Qualifying day target</span>
            <span class="target">{DAILY_CALORIE_TARGET}+ calories/day</span>
          </div>
          <div class="about-activity-grid">
            <div class="about-activity-chip">Gym</div>
            <div class="about-activity-chip">Walking</div>
            <div class="about-activity-chip">Running</div>
            <div class="about-activity-chip">Sports</div>
            <div class="about-activity-chip">Yoga</div>
            <div class="about-activity-chip">Dance</div>
          </div>
          <div class="about-active-rules">
            <div class="about-active-rule">
              <div class="num">1</div>
              <div class="text"><b>Mix sessions if needed.</b> Multiple workouts on the same day can be combined to cross {DAILY_CALORIE_TARGET}+ calories.</div>
            </div>
            <div class="about-active-rule">
              <div class="num">2</div>
              <div class="text"><b>Each month resets.</b> Missed calories and missed days do not roll over into another day or month.</div>
            </div>
            <div class="about-active-rule">
              <div class="num">3</div>
              <div class="text"><b>Log honestly every day.</b> Tracking happens in the Google Form and runs on the honor system.</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render() -> None:
    _inject_about_styles()

    st.markdown(
        """
        <div class="about-hero">
          <span class="about-chip">About This Group</span>
          <h2>Monthly accountability with a simple fitness pledge</h2>
          <p>Small stake, consistent movement, and transparent shared rewards.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_rules()
    _render_flow()
    _render_payout_simulator()
    _render_activity_and_ops()
