"""Loading view: progress bar and status while fetching workouts."""

import time
from typing import Callable

import streamlit as st

LOADING_GIF_URL = "https://media1.tenor.com/m/iN395jeb1dEAAAAd/rock-lee-training.gif"


def render_fake_loading(duration_seconds: float = 5.0) -> None:
    """
    Show GIF and a progress bar that fills over duration_seconds.
    Uses session state + reruns so the bar updates live.
    """
    n_steps = 50
    step = st.session_state.get("_fake_loading_step", 0)
    progress = (step + 1) / n_steps if step < n_steps else 1.0

    st.markdown("## STRONGER DAY BY DAY")
    st.image(LOADING_GIF_URL, use_container_width=True)
    st.markdown("### Loading from Supabase…")
    progress_bar = st.progress(progress)
    st.caption(f"Preparing your dashboard… {int(100 * progress)}%")

    if step < n_steps - 1:
        st.session_state["_fake_loading_step"] = step + 1
        time.sleep(duration_seconds / n_steps)
        st.rerun()
    else:
        st.session_state.pop("_fake_loading_step", None)


def render_loading_ui() -> Callable[[float, str], None]:
    """
    Render the loading container (title, progress bar, status caption).
    Must be called inside a streamlit container (e.g. with loading.container():).
    Returns the on_progress callback to pass to the fetch implementation.
    """
    st.markdown("## STRONGER DAY BY DAY")
    st.image(LOADING_GIF_URL, use_container_width=True)
    st.markdown("### Fetching all workouts…")
    progress_bar = st.progress(0)
    status_text = st.caption("Starting…")
    st.caption("*First load can take 1–2 minutes depending on your history.*")

    def on_progress(p: float, msg: str) -> None:
        progress_bar.progress(p)
        status_text.caption(msg)

    return on_progress
