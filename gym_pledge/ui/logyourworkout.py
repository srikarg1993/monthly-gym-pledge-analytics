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

    st.link_button(
        "🚀 Log my workout now",
        WORKOUT_FORM_URL,
        use_container_width=True,
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
