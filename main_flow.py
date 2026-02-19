"""Main app flow: session state, fetch vs empty vs dashboard."""

import streamlit as st

import data_fetch
import storage
from hevy_client import HevyApiError

from views import empty, loading, dashboard


def main() -> None:
    api_key = data_fetch.resolve_api_key()
    if not api_key:
        st.warning(
            "Set the `HEVY_API_KEY` in a `.env` file or as an environment variable "
            "to continue."
        )
        st.stop()

    if "hevy_data" not in st.session_state:
        st.session_state["hevy_data"] = None

    if st.session_state.get("fetch_requested"):
        st.session_state["fetch_requested"] = False
        is_first_load = st.session_state["hevy_data"] is None
        loading_placeholder = st.empty()
        with loading_placeholder.container():
            on_progress = loading.render_loading_ui()
        try:
            if not is_first_load:
                st.cache_data.clear()
            data = data_fetch._fetch_user_and_workouts_impl(api_key, on_progress)
            storage.save(api_key, data)
            st.session_state["hevy_data"] = data
            loading_placeholder.empty()
            st.rerun()
        except HevyApiError as exc:
            loading_placeholder.empty()
            st.error(f"Error talking to Hevy API: {exc}")
            st.stop()
        except Exception as exc:
            loading_placeholder.empty()
            st.error(f"Unexpected error: {exc}")
            st.stop()

    if st.session_state.get("fake_loading") and st.session_state.get("fake_loading_data"):
        loading.render_fake_loading(duration_seconds=5.0)
        st.session_state["hevy_data"] = st.session_state["fake_loading_data"]
        st.session_state.pop("fake_loading", None)
        st.session_state.pop("fake_loading_data", None)
        st.rerun()

    data = st.session_state["hevy_data"]
    if data is None:
        empty.render_empty_state(api_key)
        return

    st.session_state.pop("supabase_empty", None)
    dashboard.render_dashboard(data)
