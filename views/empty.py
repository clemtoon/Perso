"""Empty state view: title, quote, Load my workouts button."""

import random
import streamlit as st

from config import ATHLETE_QUOTES


def render_empty_state() -> None:
    """Show prompt to load when no data is in session."""
    st.title("STRONGER DAY BY DAY")
    if "quote_idx" not in st.session_state:
        st.session_state["quote_idx"] = random.randint(0, len(ATHLETE_QUOTES) - 1)
    name, quote = ATHLETE_QUOTES[st.session_state["quote_idx"]]
    st.markdown(f'*"{quote}"* — **{name}**')
    if st.button("Fetch workouts", type="primary"):
        st.session_state["fetch_requested"] = True
        st.rerun()
    st.stop()
