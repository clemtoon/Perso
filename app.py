"""
Day by Day — workout dashboard from Hevy.

Structure: app.py -> main_flow -> views (empty, loading, dashboard).
Constants in config, styles in styles, dates in dates, charts in charts,
fetch in data_fetch, parsing in workout_parsing.
"""

import streamlit as st
from dotenv import load_dotenv

from config import PAGE_ICON, PAGE_TITLE
from main_flow import main
from styles import get_app_css

load_dotenv()

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(get_app_css(), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
