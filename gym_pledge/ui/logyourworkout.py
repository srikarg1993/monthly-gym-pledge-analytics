"""Log Your Workout page: short copy + responsive Google Form embed."""

import streamlit as st
import streamlit.components.v1 as components

from config.globals import WORKOUT_FORM_EMBED_URL, WORKOUT_FORM_URL

# Form embed sizing tuned for both desktop and mobile. Streamlit's
# ``components.iframe`` does not honor "%" widths reliably across browsers,
# so we wrap the iframe in our own responsive container and let the iframe
# stretch to 100% via CSS.
_FORM_HEIGHT_PX = 1100


def render() -> None:
    st.markdown("## Log your workout")

    st.markdown(
        """
        Whether it was a heavy lift, a quick run, or just getting some
        movement in — it all counts.

        - Keeps your streak alive
        - Tracks consistency over the month
        - Keeps you accountable to the group

        Don't overthink it. Log it and move on with your day.
        """
    )

    # Visible "Open in new tab" link as a fallback when the embedded form
    # doesn't render (CDN blocked, narrow phone, accessibility tools).
    # Adversarial finding P2-24.
    st.markdown(
        f"[Open the form in a new tab]({WORKOUT_FORM_URL})",
        unsafe_allow_html=False,
    )
    st.write("")

    # Use ``components.html`` instead of ``components.iframe`` so we can
    # wrap the iframe in our own width:100% shell. ``scrolling=True`` so
    # mobile users can scroll within the form when needed.
    components.html(
        f"""
        <div style="width:100%;max-width:900px;margin:0 auto;">
          <iframe
            src="{WORKOUT_FORM_EMBED_URL}"
            width="100%"
            height="{_FORM_HEIGHT_PX}"
            frameborder="0"
            marginheight="0"
            marginwidth="0"
            scrolling="auto"
            referrerpolicy="no-referrer"
            sandbox="allow-forms allow-scripts allow-same-origin allow-popups"
          >Loading…</iframe>
        </div>
        """,
        height=_FORM_HEIGHT_PX + 24,
        scrolling=False,
    )
