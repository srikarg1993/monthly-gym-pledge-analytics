import streamlit as st

WORKOUT_FORM_URL = (
    "https://docs.google.com/forms/d/e/"
    "1FAIpQLSeaWgRsPcMfZjwzZ-6pH6qRr4Ev_BgKchxIDPEmHAbGVdbe8Q/viewform?usp=dialog"
)


def render():
    st.markdown("## 🏋️ Log your workout")

    st.markdown(
        """
        Great job showing up today 👏  
        Whether it was a heavy lift, a quick run, or just getting some movement in —
        **it all counts**.

        Logging your workout helps:
        - Keep your streak alive 🔥  
        - Track consistency over the month 📈  
        - Stay accountable to yourself (and the group 😉)

        Don’t overthink it — just log it and move on with your day.
        """
    )

    st.write("")  # spacing

    # Prominent styled CTA button
    st.markdown(
        f"""
        <style>
          .cta-btn {{
            display: inline-block;
            background: linear-gradient(90deg, #06b6d4 0%, #7c3aed 100%);
            color: #fff !important;
            padding: 14px 26px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 16px;
            text-decoration: none;
            box-shadow: 0 8px 20px rgba(124,58,237,0.18);
            transition: transform 0.12s ease, box-shadow 0.12s ease;
          }}
          .cta-btn:hover {{
            transform: translateY(-3px);
            box-shadow: 0 12px 28px rgba(124,58,237,0.22);
          }}
          .cta-wrap {{ text-align: center; margin: 10px 0 18px 0; }}
        </style>
        <div class="cta-wrap">
          <a class="cta-btn" href="{WORKOUT_FORM_URL}" target="_blank" rel="noopener noreferrer">🚀 Log my workout now</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")  # spacing

    st.markdown(
        """
        <div class="small-muted">
        Takes less than a minute. Your future self will thank you.
        </div>
        """,
        unsafe_allow_html=True,
    )
