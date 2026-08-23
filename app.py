import base64
import os
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# -----------------------------------------------------------------------------
# 1. PAGE SETUP
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Technical Stock Scanner Ultra HD",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------------------------------------------------------
# 2. BASE64 IMAGE ENCODER FOR CSS BACKGROUNDS
# -----------------------------------------------------------------------------
def get_base64_image(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None


# -----------------------------------------------------------------------------
# 3. THEMES & ULTRA HD ENGINE
# -----------------------------------------------------------------------------
THEMES = {
    "Bodhi Leaf Luxe": {
        "image": "bodhi leaf.png",
        "card_bg": "rgba(11, 20, 38, 0.88)",
        "header_bg": "rgba(17, 34, 64, 0.95)",
        "accent": "#38bdf8",
        "border": "#0284c7",
    },
    "Royal Blue Honeycomb": {
        "image": "honey comb royal blue.png",
        "card_bg": "rgba(6, 18, 38, 0.88)",
        "header_bg": "rgba(12, 30, 62, 0.95)",
        "accent": "#38bdf8",
        "border": "#1d4ed8",
    },
    "Golden Honeycomb": {
        "image": "honey comb golden.png",
        "card_bg": "rgba(15, 12, 5, 0.88)",
        "header_bg": "rgba(35, 27, 8, 0.95)",
        "accent": "#fbbf24",
        "border": "#d97706",
    },
    "Rhombus Geometric": {
        "image": "rohmbus pattern.png",
        "card_bg": "rgba(10, 15, 26, 0.88)",
        "header_bg": "rgba(20, 30, 50, 0.95)",
        "accent": "#38bdf8",
        "border": "#0369a1",
    },
    "Glowing Ficus Leaf": {
        "image": "glowing ficus religosa leaf.png",
        "card_bg": "rgba(8, 14, 28, 0.88)",
        "header_bg": "rgba(18, 30, 56, 0.95)",
        "accent": "#60a5fa",
        "border": "#2563eb",
    },
    "Copper Vertical Strips": {
        "image": "copper strips vertical.png",
        "card_bg": "rgba(18, 12, 10, 0.88)",
        "header_bg": "rgba(38, 22, 16, 0.95)",
        "accent": "#f97316",
        "border": "#c2410c",
    },
    "Classic Dark Navy": {
        "image": "",
        "card_bg": "rgba(13, 25, 45, 0.95)",
        "header_bg": "rgba(17, 34, 64, 0.95)",
        "accent": "#38bdf8",
        "border": "#1e293b",
    },
}

st.sidebar.markdown("### 🎨 Select Background Theme")
selected_theme_name = st.sidebar.selectbox(
    "Choose Theme", list(THEMES.keys()), index=0
)
theme = THEMES[selected_theme_name]

# Convert image to Base64 string for HTML CSS injection
b64_str = get_base64_image(theme["image"]) if theme["image"] else None

if b64_str:
    bg_style = f"""
        background-image: linear-gradient(rgba(11, 20, 38, 0.65), rgba(11, 20, 38, 0.65)), url("data:image/png;base64,{b64_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    """
else:
    bg_style = f"background-color: #0b1426;"

st.markdown(
    f"""
<style>
    /* Ultra HD Background Injection */
    .stApp {{
        {bg_style}
        color: #f8fafc;
    }}
    
    .stSidebar {{
        background-color: {theme['card_bg']} !important;
        border-right: 2px solid {theme['border']} !important;
        backdrop-filter: blur(12px);
    }}

    .app-header {{
        font-size: 30px;
        font-weight: 800;
        color: {theme['accent']};
        margin-bottom: 4px;
        letter-spacing: -0.5px;
        text-shadow: 0 2px 10px rgba(0,0,0,0.8);
    }}
    .app-subtitle {{
        font-size: 13px;
        color: #cbd5e1;
        margin-bottom: 22px;
    }}

    .table-container {{
        width: 100%;
        overflow-x: auto;
        border: 2px solid {theme['border']};
        border-radius: 10px;
        background-color: {theme['card_bg']};
        backdrop-filter: blur(14px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.7);
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
        font-weight: 800;
        padding: 14px 10px;
        border: 2px solid {theme['border']} !important;
        white-space: nowrap;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .scanner-table td {{
        padding: 12px 10px;
        border: 2px solid {theme['border']} !important;
        vertical-align: middle;
        background-color: rgba(11, 20, 38, 0.60);
    }}

    .scanner-table tr:hover td {{
        background-color: rgba(30, 58, 138, 0.45) !important;
    }}

    .stock-title-cell {{
        text-align: left !important;
        padding-left: 16px !important;
    }}
    
    .stock-link {{
        color: {theme['accent']} !important;
        font-weight: 800;
        font-size: 14px;
        text-decoration: none;
    }}
    
    .stock-link:hover {{
        color: #ffffff !important;
        text-decoration: underline;
    }}

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
        background-color: rgba(16, 185, 129, 0.25);
        color: #34d399;
        border: 1px solid #10b981;
    }}
    .badge-purple {{
        background-color: rgba(168, 85, 247, 0.25);
        color: #c084fc;
        border: 1px solid #a855f7;
    }}
    .badge-red {{
        background-color: rgba(239, 68, 68, 0.25);
        color: #fca5a5;
        border: 1px solid #ef4444;
    }}
    
    .cell-val {{
        font-weight: 700;
        color: #f8fafc;
    }}
</style>
""",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# 4. TECHNICAL INDICATOR CALCULATOR
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

            cp = df["Close"].iloc[-1]
            prev_cp = df["Close"].iloc[-2]
            price_change = ((cp - prev_cp) / prev_cp) * 100

            vol_curr = df["Volume"].iloc[-1]
            vol_avg = df["Volume"].tail(20).mean()
            vol_spike = (
                ((vol_curr - vol_avg) / vol_avg) * 100 if vol_avg > 0 else 0
            )

            ema20 = df["Close"].ewm(span=20).mean().iloc[-1]
            ema50 = df["Close"].ewm(span=50).mean().iloc[-1]
            ema100 = df["Close"].ewm(span=100).mean().iloc[-1]
            ema200 = df["Close"].ewm(span=200).mean().iloc[-1]

            rsi_daily = calculate_rsi(df["Close"], 14).iloc[-1]
            df_w = df["Close"].resample("W").last()
            df_m = df["Close"].resample("ME").last()
            rsi_weekly = (
                calculate_rsi(df_w, 14).iloc[-1] if len(df_w) > 15 else 50.0
            )
            rsi_monthly = (
                calculate_rsi(df_m, 14).iloc[-1] if len(df_m) > 15 else 50.0
            )

            adx = calculate_adx(df, 14).iloc[-1]
            st_val = ema20 * 0.95
            is_bullish_st = cp > st_val

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
# 5. CONTROLS & HEADER
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

st.sidebar.markdown("### 📡 NSE Ticker Feed")
ticker_input = st.sidebar.text_area(
    "Tickers (Comma Separated)", value=", ".join(default_tickers), height=120
)
ticker_list = [t.strip() for t in ticker_input.split(",") if t.strip()]

if st.sidebar.button("🔄 Refresh Market Data", use_container_width=True):
    st.cache_data.clear()

st.markdown(
    '<div class="app-header">📈 Technical Stock Scanner</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="app-subtitle">Real-time indicators with direct TradingView'
    " daily chart linkage and multi-timeframe analysis.</div>",
    unsafe_allow_html=True,
)

with st.spinner("Loading Ultra HD Market Data..."):
    df_live = fetch_live_stock_data(ticker_list)

# -----------------------------------------------------------------------------
# 6. TABLE RENDER ENGINE
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
        "DAILY RSI",
        "WEEKLY RSI",
        "MONTHLY RSI",
        "> EMA 20",
        "> EMA 50",
        "> EMA 100",
        "> EMA 200",
    ]
    for h in headers:
        align_css = (
            'style="text-align: left; padding-left: 16px;"'
            if h == "STOCK NAME"
            else ""
        )
        html_table += f"<th {align_css}>{h}</th>"
    html_table += "</tr></thead><tbody>"

    for idx, row in df_live.iterrows():
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

        tv_url = f"https://in.tradingview.com/chart/?symbol=NSE%3A{row['symbol']}&interval=D"
        stock_cell = f'<td class="stock-title-cell"><a href="{tv_url}" target="_blank" class="stock-link">{row["symbol"]} ↗</a></td>'

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
            {stock_cell}
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
    st.error("No data fetched. Please check ticker list.")
