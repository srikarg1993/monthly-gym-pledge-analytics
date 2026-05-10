import streamlit as st
import streamlit.components.v1 as components

WORKOUT_FORM_URL = (
    "https://docs.google.com/forms/d/e/1FAIpQLSeaWgRsPcMfZjwzZ-6pH6qRr4Ev_BgKchxIDPEmHAbGVdbe8Q/viewform?usp=dialog"
)

WORKOUT_FORM_EMBED_URL = (
    "https://docs.google.com/forms/d/e/1FAIpQLSeaWgRsPcMfZjwzZ-6pH6qRr4Ev_BgKchxIDPEmHAbGVdbe8Q/viewform?embedded=true"
)

FORM_EMBED_WIDTH = 900
FORM_EMBED_HEIGHT = 1000


def render():
    st.markdown("## Log your workout")

    st.markdown(
        """
        Great job showing up today.
        Whether it was a heavy lift, a quick run, or just getting some movement in - it all counts.

        Logging your workout helps:
        - Keep your streak alive
        - Track consistency over the month
        - Stay accountable to yourself (and the group)

        Do not overthink it - just log it and move on with your day.
        """
    )

    st.write("")  # spacing

    components.iframe(
        WORKOUT_FORM_EMBED_URL,
        width=FORM_EMBED_WIDTH,
        height=FORM_EMBED_HEIGHT,
        scrolling=False,
    )
