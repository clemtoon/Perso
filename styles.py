"""Modern dark UI theme CSS for the Streamlit app."""


def get_app_css() -> str:
    """Return the app's custom CSS as a string for st.markdown(..., unsafe_allow_html=True)."""
    return """
<style>
    /* Base */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > div {
        background-color: #0f172a;
        color: #e2e8f0;
    }
    [data-testid="stHeader"] { background: rgba(15, 23, 42, 0.9); }

    /* Main content padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    /* Sidebar — all text readable (white) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        border-right: 1px solid rgba(51, 65, 85, 0.6);
    }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {
        color: #f1f5f9 !important;
    }

    /* Title */
    h1 {
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #f1f5f9;
        margin-bottom: 0.5rem;
    }

    /* Section headings (sidebar Filters, etc.) */
    h2, h3 {
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        color: #f1f5f9 !important;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }

    /* Metric cards — modern glass-style */
    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(71, 85, 105, 0.5);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    [data-testid="stMetric"] label {
        font-size: 0.7rem;
        font-weight: 500;
        letter-spacing: 0.04em;
        color: #f1f5f9 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f1f5f9;
        letter-spacing: -0.02em;
    }
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-size: 0.8rem;
        font-weight: 500;
        padding: 0.2em 0.5em;
        border-radius: 6px;
        background: rgba(51, 65, 85, 0.4);
    }

    /* Buttons */
    .stButton > button {
        background: rgba(59, 130, 246, 0.15);
        color: #93c5fd;
        border-radius: 10px;
        border: 1px solid rgba(59, 130, 246, 0.4);
        padding: 0.5rem 1rem;
        font-weight: 600;
        font-size: 0.8rem;
        transition: background 0.2s, border-color 0.2s;
    }
    .stButton > button:hover {
        background: rgba(59, 130, 246, 0.3);
        border-color: #3b82f6;
        color: #e0f2fe;
    }

    /* Selects — label and dropdown text white */
    div[data-baseweb="select"] > div {
        border-radius: 10px;
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(71, 85, 105, 0.6);
        color: #f1f5f9 !important;
    }
    .stSelectbox label,
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div {
        color: #f1f5f9 !important;
    }
    /* Dropdown option list (when open) */
    ul[role="listbox"] li, [data-baseweb="popover"] {
        background: #1e293b !important;
        color: #f1f5f9 !important;
    }

    /* Expander (Debug) */
    .streamlit-expanderHeader {
        background: rgba(30, 41, 59, 0.4);
        border-radius: 8px;
        color: #f1f5f9 !important;
    }
    .streamlit-expanderHeader p, .streamlit-expanderHeader span {
        color: #f1f5f9 !important;
    }
    /* Main area widget labels (e.g. above chart) */
    .stMarkdown label, .block-container label {
        color: #e2e8f0 !important;
    }

    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(71, 85, 105, 0.5), transparent);
        margin: 1.5rem 0;
    }

    /* Caption / small text */
    .stCaption {
        color: #cbd5e1 !important;
        font-size: 0.8rem;
    }

    /* Info box */
    [data-testid="stAlert"] {
        border-radius: 10px;
        border: 1px solid rgba(71, 85, 105, 0.5);
    }

    a { color: #60a5fa; }

    /* ——— Mobile-friendly (max-width 768px) ——— */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 1rem 2rem;
            max-width: 100%;
        }
        h1 {
            font-size: 1.35rem;
        }
        /* Metric row: wrap; at least 2 cards per row on mobile */
        .block-container [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 0.5rem;
        }
        .block-container [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > div {
            min-width: calc(50% - 0.25rem) !important;
            flex: 1 1 calc(50% - 0.25rem) !important;
        }
        [data-testid="stMetric"] {
            padding: 0.75rem 1rem;
        }
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 1.35rem;
        }
        /* Touch-friendly buttons and controls (min ~44px) */
        .stButton > button {
            min-height: 44px;
            padding: 0.6rem 1rem;
            font-size: 0.85rem;
        }
        div[data-baseweb="select"] > div {
            min-height: 44px;
        }
        /* Sidebar overlay: full-width on very small screens */
        [data-testid="stSidebar"] {
            min-width: 280px;
        }
    }
</style>
"""
