"""Loading view: progress bar and status while fetching workouts."""

from typing import Callable

import streamlit as st


def render_loading_ui() -> Callable[[float, str], None]:
    """
    Render the loading container (title, progress bar, status caption).
    Must be called inside a streamlit container (e.g. with loading.container():).
    Returns the on_progress callback to pass to the fetch implementation.
    """
    st.markdown("## STRONGER DAY BY DAY")
    st.image("https://media1.tenor.com/m/iN395jeb1dEAAAAd/rock-lee-training.gif", use_container_width=True)
    st.markdown("### Fetching all workouts…")
    progress_bar = st.progress(0)
    status_text = st.caption("Starting…")
    st.caption("*First load can take 1–2 minutes depending on your history.*")

    def on_progress(p: float, msg: str) -> None:
        progress_bar.progress(p)
        status_text.caption(msg)

    return on_progress
