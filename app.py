import base64
import os
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
# --- ADD THIS IMPORT ---
from streamlit_autorefresh import st_autorefresh

# -----------------------------------------------------------------------------
# PAGE SETUP & REFRESH TIMER CONTROL
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Technical Stock Scanner Ultra HD",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- AUTO REFRESH CONTROLLER IN SIDEBAR ---
st.sidebar.markdown("### 🔄 Auto-Refresh Data")
refresh_option = st.sidebar.selectbox(
    "Select Refresh Rate",
    options=["Off", "30 Seconds", "1 Minute", "3 Minutes", "5 Minutes"],
    index=2,  # Defaults to 1 Minute
)

# Map human-readable options to milliseconds
refresh_map = {
    "30 Seconds": 30000,
    "1 Minute": 60000,
    "3 Minutes": 180000,
    "5 Minutes": 300000,
}

if refresh_option != "Off":
    # Trigger silent page re-run at specified millisecond interval
    st_autorefresh(interval=refresh_map[refresh_option], key="data_autorefresh")
