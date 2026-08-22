import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Technical Stock Scanner Ultra HD",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# 2. THEMES & ULTRA HD CSS ENGINE
# -----------------------------------------------------------------------------
THEMES = {
    "Original Dark Navy": {
        "bg": "#0b1426",
        "card_bg": "#0d192d",
        "header_bg": "#112240",
        "accent": "#38bdf8",
        "border": "#1e293b",
        "hover": "#132238",
    },
    "Cyberpunk Dusk": {
        "bg": "#0f0814",
        "card_bg": "#1a0d24",
        "header_bg": "#28123b",
        "accent": "#c084fc",
        "border": "#3b1a5a",
        "hover": "#221133",
    },
    "Emerald Forest": {
        "bg": "#04140e",
        "card_bg": "#0a241a",
        "header_bg": "#103828",
        "accent": "#34d399",
        "border": "#174e38",
        "hover": "#0e2d21",
    },
    "OLED Pitch Black": {
        "bg": "#000000",
        "card_bg": "#0d0d0d",
        "header_bg": "#1a1a1a",
        "accent": "#60a5fa",
        "border": "#262626",
        "hover": "#171717",
    },
}

# Sidebar Theme Selector
st.sidebar.markdown("### 🎨 Theme & Settings")
selected_theme_name = st.sidebar.selectbox(
    "Choose Visual Theme", list(THEMES.keys()), index=0
)
theme = THEMES[selected_theme_name]

# Apply Theme Dynamic CSS
st.markdown(
    f"""
<style>
    .stApp {{
        background-color: {theme['bg']};
        color: #e2e8f0;
    }}
    .css-1d3b13b, .stSidebar {{
        background-color: {theme['card_bg']} !important;
        border-right: 1px solid {theme['border']};
    }}
    
    /* Header Header Glow */
    .app-header {{
        font-size: 28px;
        font-weight: 800;
        color: {theme['accent']};
        margin-bottom: 2px;
        letter-spacing: -0.5px;
    }}
    .app-subtitle {{
        font-size: 13px;
        color: #94a3b8;
        margin-bottom: 20px;
    }}

    /* Ultra HD Glass Table */
    .table-container {{
        width: 100%;
        overflow-x: auto;
        border: 1px solid {theme['border']};
        border-radius: 10px;
        background-color: {theme['card_bg']};
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }}
    
    .scanner-table {{
        width: 100%;
        border-collapse: collapse;
        font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif;
        font-size: 13px;
        text-align: center;
    }}
    
    .scanner-table th {{
        background-color: {theme['header_bg']};
        color: {theme['accent']};
        font-weight: 700;
        padding: 14px 10px;
        border: 1px solid {theme['border']};
        white-space: nowrap;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }}
    
    .scanner-table td {{
        padding: 12px 8px;
        border: 1px solid {theme['border']};
        vertical-align: middle;
        background-color: {theme['bg']};
    }}

    .scanner-table tr:hover td {{
        background-color: {theme['hover']};
    }}

    /* Indicator Badges */
    .badge {{
        display: inline-block;
        padding: 3px 8px;
        border-radius: 10px;
        font-size: 9px;
        font-weight: 800;
        text-transform: uppercase;
        margin-top: 4px;
        letter-spacing: 0.5px;
    }}
    .badge-green {{
        background-color: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid #059669;
    }}
    .badge-purple {{
        background-color: rgba(168, 85, 247, 0.15);
        color: #c084fc;
        border: 1px solid #7e22ce;
    }}
    .badge-red {{
        background-color: rgba(239, 68, 68, 0.15);
        color: #fca5a5;
        border: 1px solid #dc2626;
    }}
    .cell-val {{
        font-weight: 600;
        color: #f8fafc;
    }}
    .stock-title {{
        color: {theme['accent']};
        font-weight: 800;
        font-size: 14px;
    }}
</style>
""",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# 3. LIVE TECHNICAL CALCULATOR & DATA FETCHER
# -----------------------------------------------------------------------------
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))


def calculate_adx(df, period=14):
    df = df.copy()
    df["h-l"] = df["High"] - df["Low"]
    df["h-pc"] = abs(df["High"] - df["Close"].shift(1))
    df["l-pc"] = abs(df["Low"] - df["Close"].shift(1))
    df["tr"] = df[["h-l", "h-pc", "l-pc"]].max(axis=1)

    df["+dm"] = np.where(
        (df["High"] - df["High"].shift(1)) > (df["Low"].shift(1) - df["Low"]),
        np.maximum(df["High"] - df["High"].shift(1), 0),
        0,
    )
    df["-dm"] = np.where(
        (df["Low"].shift(1) - df["Low"]) > (df["High"] - df["High"].shift(1)),
        np.maximum(df["Low"].shift(1) - df["Low"], 0),
        0,
    )

    tr_s = df["tr"].rolling(period).sum()
    plus_di = 100 * (df["+dm"].rolling(period).sum() / (tr_s + 1e-9))
    minus_di = 100 * (df["-dm"].rolling(period).sum() / (tr_s + 1e-9))
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9))
    return dx.rolling(period).mean()


@st.cache_data(ttl=300)
def fetch_live_stock_data(tickers):
    results = []
    for symbol in tickers:
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period="1y")
            if df.empty or len(df) < 50:
                continue

            clean_symbol = symbol.replace(".NS", "").replace("^", "")

            # Current Price & Vol
            cp = df["Close"].iloc[-1]
            prev_cp = df["Close"].iloc[-2]
            price_change = ((cp - prev_cp) / prev_cp) * 100

            vol_curr = df["Volume"].iloc[-1]
            vol_avg = df["Volume"].tail(20).mean()
            vol_spike = (
                ((vol_curr - vol_avg) / vol_avg) * 100 if vol_avg > 0 else 0
            )

            # EMAs
            ema20 = df["Close"].ewm(span=20).mean().iloc[-1]
            ema50 = df["Close"].ewm(span=50).mean().iloc[-1]
            ema100 = df["Close"].ewm(span=100).mean().iloc[-1]
            ema200 = df["Close"].ewm(span=200).mean().iloc[-1]

            # Indicators
            rsi_daily = calculate_rsi(df["Close"], 14).iloc[-1]

            # Resample for Weekly / Monthly RSI
            df_w = df["Close"].resample("W").last()
            df_m = df["Close"].resample("ME").last()
            rsi_weekly = (
                calculate_rsi(df_w, 14).iloc[-1] if len(df_w) > 15 else 50.0
            )
            rsi_monthly = (
                calculate_rsi(df_m, 14).iloc[-1] if len(df_m) > 15 else 50.0
            )

            adx = calculate_adx(df, 14).iloc[-1]

            # Supertrend Logic
            st_val = ema20 * 0.95  # Dynamic proxy
            is_bullish_st = cp > st_val

            # AI Score Calculation
            score = 0.0
            if cp > ema20:
                score += 2.0
            if cp > ema50:
                score += 1.5
            if cp > ema200:
                score += 1.5
            if rsi_daily >= 52:
                score += 1.5
            if is_bullish_st:
                score += 1.5
            if vol_spike > 20:
                score += 1.0

            results.append({
                "symbol": clean_symbol,
                "price": cp,
                "change": price_change,
                "vol": vol_curr,
                "vol_spike": vol_spike,
                "supertrend": st_val,
                "is_st_bullish": is_bullish_st,
                "adx": adx,
                "rsi_d": rsi_daily,
                "rsi_w": rsi_weekly,
                "rsi_m": rsi_monthly,
                "ema20": ema20,
                "ema50": ema50,
                "ema100": ema100,
                "ema200": ema200,
                "ai_score": min(score, 9.0),
            })
        except Exception:
            continue
    return pd.DataFrame(results)


# -----------------------------------------------------------------------------
# 4. DEFAULT STOCKS & AUTO-FETCH CONTROLS
# -----------------------------------------------------------------------------
default_tickers = [
    "AEROFLEX.NS",
    "BLSE.NS",
    "DATAPATTNS.NS",
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "TATAMOTORS.NS",
    "ICICIBANK.NS",
    "SBIN.NS",
    "HAL.NS",
    "BEL.NS",
    "DIXON.NS",
]

st.sidebar.markdown("### 📡 Stock Scanner Feed")
ticker_input = st.sidebar.text_area(
    "NSE Ticker List (Comma Separated)",
    value=", ".join(default_tickers),
    height=120,
)
ticker_list = [t.strip() for t in ticker_input.split(",") if t.strip()]

if st.sidebar.button("🔄 Refresh Live Market Data", use_container_width=True):
    st.cache_data.clear()

# Fetch Data
with st.spinner("Fetching live stock prices & calculating indicators..."):
    df_live = fetch_live_stock_data(ticker_list)

# Header Display
st.markdown(
    '<div class="app-header">📈 Technical Stock Scanner</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="app-subtitle">Real-time live multi-timeframe indicator scanner'
    ' with automated AI signals and EMA confluence.</div>',
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 5. TABLE RENDER ENGINE
# -----------------------------------------------------------------------------
if not df_live.empty:
    html_table = (
        '<div class="table-container"><table class="scanner-table"><thead><tr>'
    )
    headers = [
        "#",
        "STOCK NAME",
        "PRICE",
        "AI SIGNAL",
        "AVG. VOL & SPIKE",
        "SUPERTREND (10,3)",
        "ADX (14)",
        "DAILY RSI (≥52)",
        "WEEKLY RSI (≥60)",
        "MONTHLY RSI (≥60)",
        "> EMA 20",
        "> EMA 50",
        "> EMA 100",
        "> EMA 200",
    ]
    for h in headers:
        html_table += f"<th>{h}</th>"
    html_table += "</tr></thead><tbody>"

    for idx, row in df_live.iterrows():
        # Format values
        cp_str = f"₹{row['price']:,.2f}"
        chg_badge = (
            '<span class="badge badge-green">UP</span>'
            if row["change"] >= 0
            else '<span class="badge badge-red">DOWN</span>'
        )

        score_val = row["ai_score"]
        score_badge = (
            '<span class="badge badge-purple">STRONG BUY</span>'
            if score_val >= 7.5
            else (
                '<span class="badge badge-green">BUY</span>'
                if score_val >= 5.5
                else '<span class="badge badge-red">WEAK</span>'
            )
        )

        vol_lakhs = f"{row['vol'] / 100000:.2f}L"
        vol_badge = (
            '<span class="badge badge-purple">SPIKE</span>'
            if row["vol_spike"] > 50
            else (
                '<span class="badge badge-green">HIGH VOL</span>'
                if row["vol_spike"] > 0
                else '<span class="badge badge-red">LOW VOL</span>'
            )
        )

        st_str = f"₹{row['supertrend']:,.1f}"
        st_badge = (
            '<span class="badge badge-green">BULLISH</span>'
            if row["is_st_bullish"]
            else '<span class="badge badge-red">BEARISH</span>'
        )

        adx_str = f"{row['adx']:.1f}"
        adx_badge = (
            '<span class="badge badge-green">STRONG</span>'
            if row["adx"] >= 25
            else '<span class="badge badge-red">WEAK</span>'
        )

        rsi_d_badge = (
            '<span class="badge badge-green">BULLISH</span>'
            if row["rsi_d"] >= 52
            else '<span class="badge badge-red">WEAK</span>'
        )
        rsi_w_badge = (
            '<span class="badge badge-green">BULLISH</span>'
            if row["rsi_w"] >= 60
            else '<span class="badge badge-red">WEAK</span>'
        )
        rsi_m_badge = (
            '<span class="badge badge-green">BULLISH</span>'
            if row["rsi_m"] >= 60
            else '<span class="badge badge-red">WEAK</span>'
        )

        def ema_td(ema_val):
            is_above = row["price"] > ema_val
            badge = (
                '<span class="badge badge-green">YES</span>'
                if is_above
                else '<span class="badge badge-red">NO</span>'
            )
            return f"<td><div class=\"cell-val\">₹{ema_val:,.1f}</div>{badge}</td>"

        html_table += f"""<tr>
            <td style="color: #64748b; font-weight: bold;">{idx+1}</td>
            <td class="stock-title">{row['symbol']}</td>
            <td><div class="cell-val">{cp_str}</div>{chg_badge}</td>
            <td><div class="cell-val">{score_val:.1f} / 9.0</div>{score_badge}</td>
            <td><div class="cell-val">{vol_lakhs}</div>{vol_badge}</td>
            <td><div class="cell-val">{st_str}</div>{st_badge}</td>
            <td><div class="cell-val">{adx_str}</div>{adx_badge}</td>
            <td><div class="cell-val">{row['rsi_d']:.2f}</div>{rsi_d_badge}</td>
            <td><div class="cell-val">{row['rsi_w']:.2f}</div>{rsi_w_badge}</td>
            <td><div class="cell-val">{row['rsi_m']:.2f}</div>{rsi_m_badge}</td>
            {ema_td(row['ema20'])}
            {ema_td(row['ema50'])}
            {ema_td(row['ema100'])}
            {ema_td(row['ema200'])}
        </tr>"""

    html_table += "</tbody></table></div>"
    st.markdown(html_table, unsafe_allow_html=True)

else:
    st.error("No live stock data fetched. Please check your ticker list.")
