"""Landing page: title, quote, Fetch from Supabase / Fetch from Hevy."""

import random
import streamlit as st

import storage
from config import ATHLETE_QUOTES


def render_empty_state(api_key: str) -> None:
    """Show landing page when no data is in session. Button loads from Supabase or triggers Hevy fetch."""
    st.title("STRONGER DAY BY DAY")
    st.markdown("Your workout dashboard — load cached data or sync from Hevy.")
    st.markdown("")

    if "quote_idx" not in st.session_state:
        st.session_state["quote_idx"] = random.randint(0, len(ATHLETE_QUOTES) - 1)
    name, quote = ATHLETE_QUOTES[st.session_state["quote_idx"]]
    st.markdown(f'*"{quote}"* — **{name}**')
    st.markdown("")

    if st.button("Fetch from Supabase", type="primary", help="Load your cached workouts from Supabase"):
        data = storage.load(api_key)
        if data is not None:
            st.session_state["fake_loading"] = True
            st.session_state["fake_loading_data"] = data
            st.session_state.pop("supabase_empty", None)
            st.session_state.pop("_fake_loading_step", None)
            st.rerun()
        else:
            st.session_state["supabase_empty"] = True
            st.rerun()

    if st.session_state.get("supabase_empty"):
        st.info("No cached data in Supabase yet. Fetch from Hevy API to sync and save to Supabase.")
        if st.button("Fetch from Hevy API", type="secondary", help="Fetch workouts from Hevy and save to Supabase"):
            st.session_state["fetch_requested"] = True
            st.session_state.pop("supabase_empty", None)
            st.rerun()
    else:
        st.caption("Load your last saved data from Supabase. First time? Use the Hevy API button after clicking above.")

    st.stop()
