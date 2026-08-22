import numpy as np
import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# 1. PAGE SETUP
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Technical Stock Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📈 Technical Stock Scanner")
st.markdown(
    "Real-time technical indicator scanner with signal badges, RSI coloring, and volume breakout metrics."
)

# -----------------------------------------------------------------------------
# 2. SAMPLE DATA / DATA FETCHING
# -----------------------------------------------------------------------------
# Sample DataFrame matching your scanner layout for testing
raw_data = {
    "STOCK NAME": ["AEROFLEX", "BLSE", "DATAPATTNS", "ZOMATO", "RELIANCE"],
    "PRICE": [
        "\\n\\n₹475.30\\n\\n",
        "\\n\\n₹321.10\\n\\n",
        "\\n\\n₹4,829.90\\n\\n",
        "\\n\\n₹265.50\\n\\n",
        "\\n\\n₹2,980.00\\n\\n",
    ],
    "AI SIGNAL": [
        "\\n\\n6.5 / 9.0\\n\\nBUY\\n\\n",
        "\\n\\n9.0 / 9.0\\n\\nSTRONG BUY\\n\\n",
        "\\n\\n7.5 / 9.0\\n\\nSTRONG BUY\\n\\n",
        "\\n\\n5.0 / 9.0\\n\\nNEUTRAL\\n\\n",
        "\\n\\n3.0 / 9.0\\n\\nWEAK\\n\\n",
    ],
    "AVG VOL": [690000, 1501000, 2315000, 4500000, 1200000],
    "CURRENT VOL": [850000, 3200000, 4800000, 4100000, 950000],
    "SUPERTREND": [
        "\\n\\n₹413.6\\n\\nBULLISH\\n\\n",
        "\\n\\n₹287.9\\n\\nBULLISH\\n\\n",
        "\\n\\n₹4,294.9\\n\\nBULLISH\\n\\n",
        "\\n\\n₹250.0\\n\\nBULLISH\\n\\n",
        "\\n\\n₹3,100.0\\n\\nBEARISH\\n\\n",
    ],
    "ADX (14)": [
        "18.7\\n\\nWEAK",
        "42.0\\n\\nSTRONG",
        "12.8\\n\\nWEAK",
        "28.5\\n\\nMODERATE",
        "15.2\\n\\nWEAK",
    ],
    "DAILY RSI": [60.04, 70.43, 62.62, 54.20, 28.50],
    "WEEKLY RSI": [66.45, 84.22, 65.46, 58.10, 34.10],
    "MONTHLY RSI": [78.85, 69.79, 72.08, 61.30, 41.20],
    "EMA 20": [449.20, 304.20, 4548.50, 258.00, 3010.00],
    "EMA 50": [433.00, 277.20, 4418.70, 248.00, 3050.00],
    "EMA 100": [393.90, 247.60, 4155.90, 230.00, 2980.00],
    "EMA 200": [332.50, 222.20, 3727.00, 210.00, 2850.00],
}


def load_scanner_data():
    # Replace this with your actual data loader / CSV / API call
    return pd.DataFrame(raw_data)


df = load_scanner_data()

# -----------------------------------------------------------------------------
# 3. DATA CLEANING & PREPROCESSING PIPELINE
# -----------------------------------------------------------------------------
# Step A: Strip raw '\n' strings across all text cells
df = df.map(lambda x: str(x).replace("\\n", " ").replace("\n", " ").strip())

# Step B: Parse Price to float
df["PRICE_NUM"] = (
    df["PRICE"].str.replace("₹", "").str.replace(",", "").astype(float)
)

# Step C: Parse Volume & calculate Spike % + Ratio
df["CURRENT VOL"] = pd.to_numeric(df["CURRENT VOL"], errors="coerce")
df["AVG VOL"] = pd.to_numeric(df["AVG VOL"], errors="coerce")
df["VOL_SPIKE_PCT"] = (
    (df["CURRENT VOL"] - df["AVG VOL"]) / df["AVG VOL"]
) * 100
df["VOL_RATIO"] = df["CURRENT VOL"] / df["AVG VOL"]


def to_indian_unit(val):
    if pd.isna(val) or not isinstance(val, (int, float)):
        return val
    if val >= 10_000_000:
        return f"{val / 10_000_000:.2f} Cr"
    elif val >= 100_000:
        return f"{val / 100_000:.2f} L"
    elif val >= 1_000:
        return f"{val / 1_000:.1f} k"
    return f"{val:.0f}"


df["VOL_DISPLAY"] = df["CURRENT VOL"].apply(to_indian_unit)

# Step D: Ensure RSI columns are numeric floats
rsi_cols = [c for c in df.columns if "RSI" in c.upper()]
for col in rsi_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# -----------------------------------------------------------------------------
# 4. SIDEBAR CONTROLS & FILTERS
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 Breakout Filters")

min_rsi = st.sidebar.slider("Min Daily RSI", 0, 100, 50)
min_spike = st.sidebar.slider("Min Vol Spike (%)", -50, 300, 0)
signal_filter = st.sidebar.multiselect(
    "Filter Signals",
    ["STRONG BUY", "BUY", "BULLISH", "WEAK"],
    default=[],
)

# Filter dataframe
filtered_df = df[
    (df["DAILY RSI"] >= min_rsi) & (df["VOL_SPIKE_PCT"] >= min_spike)
]

if signal_filter:
    pattern = "|".join(signal_filter)
    filtered_df = filtered_df[
        filtered_df["AI SIGNAL"].str.contains(pattern, case=False, na=False)
        | filtered_df["SUPERTREND"].str.contains(pattern, case=False, na=False)
    ]


# -----------------------------------------------------------------------------
# 5. STYLING LOGIC (PANDAS STYLER)
# -----------------------------------------------------------------------------
def style_signals(val):
    val_str = str(val).upper()
    if any(k in val_str for k in ["STRONG BUY", "STRONG"]):
        return "background-color: #064e3b; color: #34d399; font-weight: bold;"
    elif any(k in val_str for k in ["BUY", "BULLISH", "UP", "SPIKE", "YES"]):
        return "background-color: #022c22; color: #6ee7b7;"
    elif any(k in val_str for k in ["WEAK", "LOW VOL", "BEARISH", "NO"]):
        return "background-color: #450a0a; color: #fca5a5;"
    return ""


def style_rsi(val):
    if pd.isna(val):
        return ""
    if val >= 70:
        return "background-color: #064e3b; color: #34d399; font-weight: bold;"
    elif val >= 60:
        return "background-color: #022c22; color: #6ee7b7;"
    elif val <= 30:
        return "background-color: #450a0a; color: #fca5a5; font-weight: bold;"
    return "background-color: #1f2937; color: #9ca3af;"


def style_spike(val):
    if pd.isna(val):
        return ""
    if val >= 100:
        return "background-color: #064e3b; color: #34d399; font-weight: bold;"
    elif val >= 50:
        return "background-color: #022c22; color: #6ee7b7;"
    elif val < 0:
        return "background-color: #450a0a; color: #fca5a5;"
    return ""


signal_cols = ["AI SIGNAL", "SUPERTREND", "ADX (14)"]

styled_df = (
    filtered_df.style.map(style_signals, subset=signal_cols)
    .map(style_rsi, subset=rsi_cols)
    .map(style_spike, subset=["VOL_SPIKE_PCT"])
    .format({col: "{:.2f}" for col in rsi_cols})
)

# -----------------------------------------------------------------------------
# 6. RENDER TABLE IN STREAMLIT
# -----------------------------------------------------------------------------
st.dataframe(
    styled_df,
    column_order=[
        "STOCK NAME",
        "PRICE_NUM",
        "AI SIGNAL",
        "VOL_DISPLAY",
        "VOL_SPIKE_PCT",
        "VOL_RATIO",
        "SUPERTREND",
        "ADX (14)",
        "DAILY RSI",
        "WEEKLY RSI",
        "MONTHLY RSI",
        "EMA 20",
        "EMA 50",
        "EMA 100",
        "EMA 200",
    ],
    column_config={
        "STOCK NAME": st.column_config.TextColumn("Stock Name"),
        "PRICE_NUM": st.column_config.NumberColumn("Price", format="₹%.2f"),
        "VOL_DISPLAY": st.column_config.TextColumn("Current Vol"),
        "VOL_SPIKE_PCT": st.column_config.NumberColumn(
            "Vol Spike (%)", format="%+.1f%%"
        ),
        "VOL_RATIO": st.column_config.NumberColumn(
            "Vol Ratio", format="%.2fx"
        ),
        "EMA 20": st.column_config.NumberColumn("EMA 20", format="₹%.2f"),
        "EMA 50": st.column_config.NumberColumn("EMA 50", format="₹%.2f"),
        "EMA 100": st.column_config.NumberColumn("EMA 100", format="₹%.2f"),
        "EMA 200": st.column_config.NumberColumn("EMA 200", format="₹%.2f"),
    },
    use_container_width=True,
    hide_index=True,
)
