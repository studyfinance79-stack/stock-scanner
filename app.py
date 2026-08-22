import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# 1. PAGE SETUP & THEME CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Stock Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",  # Hides sidebar by default
)

# Custom CSS to restore the original dark navy grid theme and styled pill badges
st.markdown(
    """
<style>
    /* Dark Theme Background */
    .stApp {
        background-color: #0b1426;
        color: #e2e8f0;
    }
    
    /* Table Styling */
    .custom-table-container {
        width: 100%;
        overflow-x: auto;
        border: 1px solid #1e293b;
        border-radius: 8px;
        background-color: #0d192d;
    }
    
    .scanner-table {
        width: 100%;
        border-collapse: collapse;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 13px;
        text-align: center;
    }
    
    .scanner-table th {
        background-color: #112240;
        color: #38bdf8;
        font-weight: 700;
        padding: 12px 10px;
        border: 1px solid #1e293b;
        white-space: nowrap;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .scanner-table td {
        padding: 12px 8px;
        border: 1px solid #1e293b;
        vertical-align: middle;
        background-color: #0b1426;
    }

    .scanner-table tr:hover td {
        background-color: #132238;
    }

    /* Badge Pill Styles */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        margin-top: 4px;
        letter-spacing: 0.5px;
    }
    
    .badge-green {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid #059669;
    }
    
    .badge-purple {
        background-color: rgba(168, 85, 247, 0.15);
        color: #c084fc;
        border: 1px solid #7e22ce;
    }
    
    .badge-red {
        background-color: rgba(239, 68, 68, 0.15);
        color: #fca5a5;
        border: 1px solid #dc2626;
    }
    
    .cell-value {
        font-weight: 600;
        color: #f8fafc;
        font-size: 13px;
    }

    .stock-name {
        color: #38bdf8;
        font-weight: 700;
    }
</style>
""",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# 2. DATA CLEANER & BADGE FORMATTER
# -----------------------------------------------------------------------------
def format_cell_to_badge(cell_value):
    """Parses raw text containing '\n' and formats badges cleanly without raw string clutter."""
    if pd.isna(cell_value):
        return ""

    # Clean raw '\n' strings
    cleaned = (
        str(cell_value)
        .replace("\\n", "\n")
        .strip()
    )
    lines = [line.strip() for line in cleaned.split("\n") if line.strip()]

    if not lines:
        return ""

    value_part = lines[0]
    badge_part = lines[1] if len(lines) > 1 else ""

    # Determine badge color scheme
    badge_html = ""
    if badge_part:
        b_upper = badge_part.upper()
        if any(
            k in b_upper
            for k in [
                "STRONG BUY",
                "SPIKE",
            ]
        ):
            badge_class = "badge-purple"
        elif any(
            k in b_upper
            for k in [
                "BUY",
                "BULLISH",
                "UP",
                "STRONG",
                "YES",
            ]
        ):
            badge_class = "badge-green"
        elif any(
            k in b_upper
            for k in [
                "WEAK",
                "LOW VOL",
                "BEARISH",
                "NO",
            ]
        ):
            badge_class = "badge-red"
        else:
            badge_class = "badge-green"

        badge_html = f'<br><span class="badge {badge_class}">{badge_part}</span>'

    return f'<div class="cell-value">{value_part}</div>{badge_html}'


# -----------------------------------------------------------------------------
# 3. SAMPLE DATASET (Matching your original table structure)
# -----------------------------------------------------------------------------
raw_data = [
    {
        "#": 1,
        "STOCK NAME": "AEROFLEX",
        "PRICE": "₹475.30\nUP",
        "AI SIGNAL": "6.5 / 9.0\nBUY",
        "AVG. VOL & SPIKE": "6.90L\nLOW VOL",
        "SUPERTREND (10,3)": "₹413.6\nBULLISH",
        "ADX (14)": "18.7\nWEAK",
        "DAILY RSI (≥52)": "60.04\nBULLISH",
        "WEEKLY RSI (≥60)": "66.45\nBULLISH",
        "MONTHLY RSI (≥60)": "78.85\nBULLISH",
        "> EMA 20": "₹449.2\nYES",
        "> EMA 50": "₹433.0\nYES",
        "> EMA 100": "₹393.9\nYES",
        "> EMA 200": "₹332.5\nYES",
    },
    {
        "#": 2,
        "STOCK NAME": "BLSE",
        "PRICE": "₹321.10\nUP",
        "AI SIGNAL": "9.0 / 9.0\nSTRONG BUY",
        "AVG. VOL & SPIKE": "15.01L\nSPIKE",
        "SUPERTREND (10,3)": "₹287.9\nBULLISH",
        "ADX (14)": "42.0\nSTRONG",
        "DAILY RSI (≥52)": "70.43\nBULLISH",
        "WEEKLY RSI (≥60)": "84.22\nBULLISH",
        "MONTHLY RSI (≥60)": "69.79\nBULLISH",
        "> EMA 20": "₹304.2\nYES",
        "> EMA 50": "₹277.2\nYES",
        "> EMA 100": "₹247.6\nYES",
        "> EMA 200": "₹222.2\nYES",
    },
    {
        "#": 3,
        "STOCK NAME": "DATAPATTNS",
        "PRICE": "₹4,829.90\nUP",
        "AI SIGNAL": "7.5 / 9.0\nSTRONG BUY",
        "AVG. VOL & SPIKE": "23.15L\nSPIKE",
        "SUPERTREND (10,3)": "₹4,294.9\nBULLISH",
        "ADX (14)": "12.8\nWEAK",
        "DAILY RSI (≥52)": "62.62\nBULLISH",
        "WEEKLY RSI (≥60)": "65.46\nBULLISH",
        "MONTHLY RSI (≥60)": "72.08\nBULLISH",
        "> EMA 20": "₹4,548.5\nYES",
        "> EMA 50": "₹4,418.7\nYES",
        "> EMA 100": "₹4,155.9\nYES",
        "> EMA 200": "₹3,727.0\nYES",
    },
]

df = pd.DataFrame(raw_data)

# -----------------------------------------------------------------------------
# 4. RENDER HTML TABLE (ALL STOCKS AT ONCE)
# -----------------------------------------------------------------------------
columns = list(df.columns)

# Build Header
html_table = (
    '<div class="custom-table-container"><table class="scanner-table"><thead><tr>'
)
for col in columns:
    html_table += f"<th>{col}</th>"
html_table += "</tr></thead><tbody>"

# Build Rows
for _, row in df.iterrows():
    html_table += "<tr>"
    for col in columns:
        val = row[col]
        if col == "#":
            html_table += (
                f'<td style="color: #64748b; font-weight: bold;">{val}</td>'
            )
        elif col == "STOCK NAME":
            html_table += f'<td class="stock-name">{val}</td>'
        else:
            formatted_content = format_cell_to_badge(val)
            html_table += f"<td>{formatted_content}</td>"
    html_table += "</tr>"

html_table += "</tbody></table></div>"

# Render Table
st.markdown(html_table, unsafe_allow_html=True)
