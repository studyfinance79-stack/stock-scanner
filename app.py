import base64
import json
import os
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

# Safe import for auto-refresh
try:
    from streamlit_autorefresh import st_autorefresh

    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

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
# 2. PERSISTENT TICKER STORAGE
# -----------------------------------------------------------------------------
TICKERS_FILE = "tickers.json"
DEFAULT_TICKERS = [
    "AEROFLEX",
    "BLSE",
    "DATAPATTNS",
    "IPCALAB",
    "KANORICHEM",
    "MODTHREAD",
    "NETWEB",
    "PREMIERPOL",
    "SONACOMS",
    "RELIANCE",
]


def load_saved_tickers():
    if os.path.exists(TICKERS_FILE):
        try:
            with open(TICKERS_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception:
            pass
    return DEFAULT_TICKERS.copy()


def save_tickers(ticker_list):
    try:
        with open(TICKERS_FILE, "w") as f:
            json.dump(ticker_list, f, indent=2)
    except Exception as e:
        st.error(f"Failed to save stock list: {e}")


if "ticker_list" not in st.session_state:
    st.session_state.ticker_list = load_saved_tickers()

# -----------------------------------------------------------------------------
# 3. BACKGROUND IMAGE SCANNER & ENGINE
# -----------------------------------------------------------------------------


def get_all_repo_images():
    """Scans repository folder for all background image files."""
    valid_exts = [".jpg", ".jpeg", ".png", ".webp"]
    images = []
    try:
        for file in os.listdir("."):
            if any(file.lower().endswith(ext) for ext in valid_exts):
                images.append(file)
    except Exception:
        pass
    return sorted(images)


def file_to_base64(filepath):
    """Converts a local file into a base64 string for CSS styling."""
    try:
        ext = os.path.splitext(filepath)[1].lower().replace(".", "")
        mime = "image/jpeg" if ext in ["jpg", "jpeg"] else f"image/{ext}"
        with open(filepath, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return encoded, mime
    except Exception:
        return None, None


# Session State for Custom Background
if "uploaded_bg_b64" not in st.session_state:
    st.session_state.uploaded_bg_b64 = None
if "uploaded_bg_mime" not in st.session_state:
    st.session_state.uploaded_bg_mime = None

# -----------------------------------------------------------------------------
# 4. SIDEBAR: REFRESH, TELEGRAM & THEMES
# -----------------------------------------------------------------------------
st.sidebar.markdown("### 🔄 Auto-Refresh Data")
refresh_option = st.sidebar.selectbox(
    "Select Refresh Rate",
    options=["Off", "30 Seconds", "1 Minute", "3 Minutes", "5 Minutes"],
    index=2,
)
refresh_map = {
    "30 Seconds": 30000,
    "1 Minute": 60000,
    "3 Minutes": 180000,
    "5 Minutes": 300000,
}

if refresh_option != "Off" and HAS_AUTOREFRESH:
    st_autorefresh(interval=refresh_map[refresh_option], key="data_autorefresh")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 Telegram Alerts (WEAK / SELL Only)")
enable_telegram = st.sidebar.checkbox(
    "Enable Telegram Notifications", value=True
)

default_token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
default_chat_id = st.secrets.get("TELEGRAM_CHAT_ID", "")

telegram_token = st.sidebar.text_input(
    "Bot Token", value=default_token, type="password"
)
telegram_chat_id = st.sidebar.text_input("Chat ID", value=default_chat_id)


def send_telegram_alert(bot_token, chat_id, text):
    """Sends HTML formatted Telegram messages and logs errors."""
    if not bot_token or not chat_id:
        return False, "Bot Token or Chat ID is missing!"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, json=payload, timeout=5)
        res_json = resp.json()
        if resp.status_code == 200 and res_json.get("ok"):
            return True, "Success"
        else:
            return (
                False,
                res_json.get("description", f"HTTP Error {resp.status_code}"),
            )
    except Exception as e:
        return False, str(e)


# TEST TELEGRAM BUTTON
if st.sidebar.button("🧪 Send Test Telegram Alert"):
    ok, err_msg = send_telegram_alert(
        telegram_token,
        telegram_chat_id,
        "<b>🧪 Test Alert from Technical Stock Scanner!</b>\nTelegram integration is working properly.",
    )
    if ok:
        st.sidebar.success("✅ Test Alert Sent Successfully!")
    else:
        st.sidebar.error(f"❌ Telegram Error: {err_msg}")

if st.sidebar.button("🔄 Reset Telegram Alert Logs"):
    for k in list(st.session_state.keys()):
        if k.startswith("alert_sent_"):
            del st.session_state[k]
    st.sidebar.success("Alert memory cleared!")

# SIDEBAR BACKGROUND SELECTOR
st.sidebar.markdown("---")
st.sidebar.markdown("### 🖼️ Background & Wallpaper")

repo_images = get_all_repo_images()
selected_repo_image = None

if repo_images:
    selected_repo_image = st.sidebar.selectbox(
        "Choose Uploaded Image from Repository",
        options=["(None / Custom Upload)"] + repo_images,
        index=1 if len(repo_images) > 0 else 0,
    )

sidebar_bg_file = st.sidebar.file_uploader(
    "Upload New Background Image",
    type=["jpg", "jpeg", "png", "webp"],
    key="sidebar_uploader",
)

# Determine Background Image to Apply
b64_str, mime_type = None, None

if sidebar_bg_file is not None:
    bytes_data = sidebar_bg_file.read()
    st.session_state.uploaded_bg_b64 = base64.b64encode(bytes_data).decode(
        "utf-8"
    )
    ext = sidebar_bg_file.name.split(".")[-1].lower()
    st.session_state.uploaded_bg_mime = (
        "image/jpeg" if ext in ["jpg", "jpeg"] else f"image/{ext}"
    )

if st.session_state.uploaded_bg_b64:
    b64_str = st.session_state.uploaded_bg_b64
    mime_type = st.session_state.uploaded_bg_mime
elif selected_repo_image and selected_repo_image != "(None / Custom Upload)":
    b64_str, mime_type = file_to_base64(selected_repo_image)

if b64_str and mime_type:
    bg_style = f"""
        background-image: linear-gradient(rgba(10, 14, 23, 0.55), rgba(10, 14, 23, 0.55)), url("data:{mime_type};base64,{b64_str}") !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
    """
else:
    bg_style = "background-color: #0b1426 !important;"

# ULTRA HD CSS STYLING
st.markdown(
    f"""
<style>
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main, .block-container {{
        {bg_style}
        background-color: transparent !important;
    }}
    .stSidebar {{
        background-color: rgba(11, 20, 38, 0.88) !important;
        border-right: 2px solid #0284c7 !important;
        backdrop-filter: blur(12px);
    }}
    .app-header {{
        font-size: 30px;
        font-weight: 800;
        color: #38bdf8;
        margin-bottom: 4px;
        text-shadow: 0 2px 10px rgba(0,0,0,0.8);
    }}
    .app-subtitle {{
        font-size: 13px;
        color: #cbd5e1;
        margin-bottom: 18px;
    }}
    .table-container {{
        width: 100%;
        overflow-x: auto;
        border: 2px solid #0284c7;
        border-radius: 10px;
        background-color: rgba(11, 20, 38, 0.85);
        backdrop-filter: blur(14px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.7);
    }}
    .scanner-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 12.5px;
        text-align: center;
    }}
    .scanner-table th {{
        background-color: rgba(17, 34, 64, 0.95);
        color: #38bdf8;
        font-weight: 800;
        padding: 12px 8px;
        border: 2px solid #0284c7 !important;
        text-transform: uppercase;
    }}
    .scanner-table td {{
        padding: 10px 8px;
        border: 2px solid #0284c7 !important;
        background-color: rgba(11, 20, 38, 0.60);
    }}
    .badge {{
        display: inline-block;
        padding: 3px 7px;
        border-radius: 8px;
        font-size: 9px;
        font-weight: 800;
    }}
    .badge-green {{ background-color: rgba(16, 185, 129, 0.25); color: #34d399; border: 1px solid #10b981; }}
    .badge-purple {{ background-color: rgba(168, 85, 247, 0.25); color: #c084fc; border: 1px solid #a855f7; }}
    .badge-red {{ background-color: rgba(239, 68, 68, 0.25); color: #fca5a5; border: 1px solid #ef4444; }}
    .badge-darkred {{ background-color: rgba(153, 27, 27, 0.7); color: #fecaca; border: 1px solid #dc2626; font-weight: 900; }}
    .cell-val {{ font-weight: 700; color: #f8fafc; }}
    .stock-link {{ color: #38bdf8 !important; font-weight: 800; text-decoration: none; }}
</style>
""",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# 5. TECHNICAL INDICATORS
# -----------------------------------------------------------------------------
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (
        delta.where(delta > 0, 0.0)
        .ewm(alpha=1 / period, adjust=False)
        .mean()
    )
    loss = (
        (-delta.where(delta < 0, 0.0))
        .ewm(alpha=1 / period, adjust=False)
        .mean()
    )
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))


def calculate_adx(df, period=14):
    high, low, close = df["High"], df["Low"], df["Close"]
    plus_dm = np.where(
        (high.diff() > low.diff().abs()) & (high.diff() > 0), high.diff(), 0.0
    )
    minus_dm = np.where(
        (low.diff().abs() > high.diff()) & (low.diff().abs() > 0),
        low.diff().abs(),
        0.0,
    )
    tr = pd.concat(
        [
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()

    plus_di = (
        100
        * (
            pd.Series(plus_dm, index=df.index)
            .ewm(alpha=1 / period, adjust=False)
            .mean()
            / (atr + 1e-9)
        )
    )
    minus_di = (
        100
        * (
            pd.Series(minus_dm, index=df.index)
            .ewm(alpha=1 / period, adjust=False)
            .mean()
            / (atr + 1e-9)
        )
    )

    dx = (
        abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)
    ) * 100
    return dx.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]


def calculate_supertrend(df, period=10, multiplier=2):
    high, low, close = df["High"], df["Low"], df["Close"]
    tr = pd.concat(
        [
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()

    hl2 = (high + low) / 2
    basic_ub = hl2 + (multiplier * atr)
    basic_lb = hl2 - (multiplier * atr)

    final_ub = basic_ub.copy()
    final_lb = basic_lb.copy()

    for i in range(1, len(df)):
        if (
            basic_ub.iloc[i] < final_ub.iloc[i - 1]
            or close.iloc[i - 1] > final_ub.iloc[i - 1]
        ):
            final_ub.iloc[i] = basic_ub.iloc[i]
        else:
            final_ub.iloc[i] = final_ub.iloc[i - 1]

        if (
            basic_lb.iloc[i] > final_lb.iloc[i - 1]
            or close.iloc[i - 1] < final_lb.iloc[i - 1]
        ):
            final_lb.iloc[i] = basic_lb.iloc[i]
        else:
            final_lb.iloc[i] = final_lb.iloc[i - 1]

    trend = "BULLISH"
    st_value = final_lb.iloc[-1]

    for i in range(1, len(df)):
        if close.iloc[i] > final_ub.iloc[i - 1]:
            trend = "BULLISH"
        elif close.iloc[i] < final_lb.iloc[i - 1]:
            trend = "BEARISH"

    if trend == "BEARISH":
        st_value = final_ub.iloc[-1]

    return st_value, (trend == "BULLISH")


@st.cache_data(ttl=60)
def fetch_live_stock_data(tickers):
    results = []
    for raw_symbol in tickers:
        try:
            symbol = (
                f"{raw_symbol.strip().upper()}.NS"
                if not raw_symbol.endswith(".NS")
                else raw_symbol.strip().upper()
            )
            df = yf.Ticker(symbol).history(period="2y")
            df = df.dropna(
                subset=["Open", "High", "Low", "Close", "Volume"]
            )

            if df.empty or len(df) < 50:
                continue

            clean_symbol = symbol.replace(".NS", "")
            cp = df["Close"].iloc[-1]
            prev_cp = df["Close"].iloc[-2]
            price_change = ((cp - prev_cp) / prev_cp) * 100

            vol_curr = df["Volume"].iloc[-1]
            vol_avg = df["Volume"].tail(20).mean()
            vol_spike = (
                ((vol_curr - vol_avg) / vol_avg) * 100 if vol_avg > 0 else 0
            )

            ema20 = (
                df["Close"].ewm(span=20, adjust=False).mean().iloc[-1]
            )
            ema50 = (
                df["Close"].ewm(span=50, adjust=False).mean().iloc[-1]
            )
            ema100 = (
                df["Close"].ewm(span=100, adjust=False).mean().iloc[-1]
            )
            ema200 = (
                df["Close"].ewm(span=200, adjust=False).mean().iloc[-1]
            )

            rsi_daily = calculate_rsi(df["Close"], 14).iloc[-1]
            df_w = df["Close"].resample("W-FRI").last().dropna()
            rsi_weekly = (
                calculate_rsi(df_w, 14).iloc[-1] if len(df_w) >= 15 else 50.0
            )
            df_m = df["Close"].resample("ME").last().dropna()
            rsi_monthly = (
                calculate_rsi(df_m, 14).iloc[-1] if len(df_m) >= 15 else 50.0
            )

            adx = calculate_adx(df, 14)
            st_val, is_bullish_st = calculate_supertrend(
                df, period=10, multiplier=2
            )

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
            })
        except Exception:
            continue
    return pd.DataFrame(results)


# -----------------------------------------------------------------------------
# 6. MAIN UI & TABS
# -----------------------------------------------------------------------------
st.markdown(
    '<div class="app-header">📈 Technical Stock Scanner</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="app-subtitle">Real-time indicators with 9-point Weakness'
    " scoring and instant Telegram alerts.</div>",
    unsafe_allow_html=True,
)

tab_scanner, tab_manage, tab_background = st.tabs(
    ["📊 Stock Scanner", "⚙️ Add / Remove Stocks", "🖼️ Background Settings"]
)

# TAB 1: SCANNER & TELEGRAM ALERTS
with tab_scanner:
    with st.spinner("Fetching Live Market Indicators..."):
        df_live = fetch_live_stock_data(st.session_state.ticker_list)

    if not df_live.empty:
        html_table = '<div class="table-container"><table class="scanner-table"><thead><tr>'
        headers = [
            "#",
            "STOCK NAME",
            "PRICE",
            "WEAKNESS SCORE",
            "AVG. VOL & SPIKE",
            "SUPERTREND (10,2)",
            "ADX (14)",
            "DAILY RSI (<52)",
            "WEEKLY RSI (<60)",
            "MONTHLY RSI (<60)",
            "< EMA 20",
            "< EMA 50",
            "< EMA 100",
            "< EMA 200",
        ]
        for h in headers:
            align_css = (
                'style="text-align: left; padding-left: 14px;"'
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

            # 9-POINT WEAKNESS SCORING MODEL
            weakness_score = 0.0
            reasons = []

            if row["rsi_m"] < 60:
                weakness_score += 1.5
                reasons.append(f"• Monthly RSI: {row['rsi_m']:.1f} (< 60)")
            if row["rsi_w"] < 60:
                weakness_score += 1.5
                reasons.append(f"• Weekly RSI: {row['rsi_w']:.1f} (< 60)")
            if row["rsi_d"] < 52:
                weakness_score += 1.0
                reasons.append(f"• Daily RSI: {row['rsi_d']:.1f} (< 52)")
            if row["price"] < row["ema20"]:
                weakness_score += 1.0
                reasons.append(f"• Price < Daily EMA 20 (₹{row['ema20']:.1f})")
            if not row["is_st_bullish"]:
                weakness_score += 1.5
                reasons.append("• Supertrend: BEARISH")
            if row["adx"] < 20:
                weakness_score += 0.5
                reasons.append(f"• ADX: {row['adx']:.1f} (< 20)")
            if row["price"] < row["ema50"]:
                weakness_score += 1.0
                reasons.append(f"• Price < Daily EMA 50 (₹{row['ema50']:.1f})")
            if row["price"] < row["ema100"]:
                weakness_score += 1.0
                reasons.append(f"• Price < Daily EMA 100 (₹{row['ema100']:.1f})")
            if row["price"] < row["ema200"]:
                weakness_score += 1.0
                reasons.append(f"• Price < Daily EMA 200 (₹{row['ema200']:.1f})")

            # Classification
            # Classification
            if weakness_score >= 7.5:
                score_badge = (
                    '<span class="badge badge-darkred">ULTRA BEARISH / STRONG'
                    " SELL</span>"
                )
                signal_title = "🔴 ULTRA BEARISH / STRONG SELL"
            elif weakness_score >= 5.0:
                score_badge = '<span class="badge badge-red">WEAK / SELL</span>'
                signal_title = "⚠️ WEAK / SELL"
            elif weakness_score >= 2.5:
                score_badge = (
                    '<span class="badge badge-purple">NEUTRAL</span>'
                )
                signal_title = "🟡 NEUTRAL"
            else:
                score_badge = (
                    '<span class="badge badge-green">BULLISH / STRONG'
                    " BULLISH</span>"
                )
                signal_title = "🟢 BULLISH / STRONG BULLISH"

            # TRIGGER TELEGRAM ALERT FOR NEUTRAL & WEAK/SELL ONLY (SKIP BULLISH)
            if (
                enable_telegram
                and telegram_token
                and telegram_chat_id
                and weakness_score >= 2.5  # Triggers for Neutral (2.5+), Weak (5.0+), and Ultra Bearish (7.5+)
            ):
                alert_key = f"alert_sent_{row['symbol']}_{weakness_score:.1f}"
                if alert_key not in st.session_state:
                    # Sanitize HTML tags (< and >) so Telegram parser accepts the message
                    clean_reasons = [
                        r.replace("<", "&lt;").replace(">", "&gt;")
                        for r in reasons
                    ]

                    alert_msg = (
                        f"<b>{signal_title}: {row['symbol']}</b>\n"
                        f"• <b>Price:</b> ₹{row['price']:,.2f}\n"
                        f"• <b>Weakness Score:</b> {weakness_score:.1f} / 10.0\n\n"
                        f"<b>Triggered Technical Criteria:</b>\n"
                        + (
                            "\n".join(clean_reasons)
                            if clean_reasons
                            else "• Overall Neutral conditions met."
                        )
                    )

                    ok, err = send_telegram_alert(
                        telegram_token, telegram_chat_id, alert_msg
                    )
                    if ok:
                        st.session_state[alert_key] = True
                        st.toast(
                            f"Telegram Alert sent for {row['symbol']}!",
                            icon="📱",
                        )
                    else:
                        st.sidebar.error(
                            f"Alert Failed for {row['symbol']}: {err}"
                        )

            # TRIGGER TELEGRAM ALERT FOR WEAK / SELL
            if (
                enable_telegram
                and telegram_token
                and telegram_chat_id
                and weakness_score >= 5.0
            ):
                alert_key = f"alert_sent_{row['symbol']}_{weakness_score:.1f}"
                if alert_key not in st.session_state:
                    alert_msg = (
                        f"<b>{signal_title}: {row['symbol']}</b>\n"
                        f"• <b>Price:</b> ₹{row['price']:,.2f}\n"
                        f"• <b>Weakness Score:</b> {weakness_score:.1f} / 10.0\n\n"
                        f"<b>Triggered Sell Criteria:</b>\n"
                        + "\n".join(reasons)
                    )
                    ok, err = send_telegram_alert(
                        telegram_token, telegram_chat_id, alert_msg
                    )
                    if ok:
                        st.session_state[alert_key] = True
                        st.toast(
                            f"Telegram Alert sent for {row['symbol']}!",
                            icon="📱",
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
            adx_badge = (
                '<span class="badge badge-green">STRONG</span>'
                if row["adx"] >= 25
                else '<span class="badge badge-red">WEAK</span>'
            )

            rsi_d_badge = (
                '<span class="badge badge-red">WEAK</span>'
                if row["rsi_d"] < 52
                else '<span class="badge badge-green">OK</span>'
            )
            rsi_w_badge = (
                '<span class="badge badge-red">WEAK</span>'
                if row["rsi_w"] < 60
                else '<span class="badge badge-green">OK</span>'
            )
            rsi_m_badge = (
                '<span class="badge badge-red">WEAK</span>'
                if row["rsi_m"] < 60
                else '<span class="badge badge-green">OK</span>'
            )

            tv_url = f"https://in.tradingview.com/chart/?symbol=NSE%3A{row['symbol']}&interval=D"
            stock_cell = f'<td style="text-align: left; padding-left: 14px;"><a href="{tv_url}" target="_blank" class="stock-link">{row["symbol"]} ↗</a></td>'

            def ema_td(ema_val):
                is_below = row["price"] < ema_val
                badge = (
                    '<span class="badge badge-red">YES</span>'
                    if is_below
                    else '<span class="badge badge-green">NO</span>'
                )
                return (
                    f'<td><div class="cell-val">₹{ema_val:,.1f}</div>{badge}</td>'
                )

            html_table += f"""<tr>
                <td style="color: #64748b; font-weight: bold;">{idx+1}</td>
                {stock_cell}
                <td><div class="cell-val">{cp_str}</div>{chg_badge}</td>
                <td><div class="cell-val">{weakness_score:.1f} / 10.0</div>{score_badge}</td>
                <td><div class="cell-val">{vol_lakhs}</div>{vol_badge}</td>
                <td><div class="cell-val">{st_str}</div>{st_badge}</td>
                <td><div class="cell-val">{row['adx']:.1f}</div>{adx_badge}</td>
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

# TAB 2: MANAGE STOCKS
with tab_manage:
    st.subheader("Manage Stock Tickers")
    col_add, col_remove = st.columns(2)
    with col_add:
        st.markdown("#### ➕ Add New Stocks")
        new_ticker = st.text_input("Enter Stock Ticker (e.g., SBIN, TCS)")
        if st.button("Add Ticker"):
            if new_ticker:
                clean_t = new_ticker.strip().upper().replace(".NS", "")
                if clean_t not in st.session_state.ticker_list:
                    st.session_state.ticker_list.append(clean_t)
                    save_tickers(st.session_state.ticker_list)
                    st.cache_data.clear()
                    st.success(f"Added {clean_t} permanently!")
                    st.rerun()

    with col_remove:
        st.markdown("#### ❌ Remove Stocks")
        to_remove = st.selectbox(
            "Select Stock to Remove", st.session_state.ticker_list
        )
        if st.button("Remove Selected Ticker"):
            if to_remove in st.session_state.ticker_list:
                st.session_state.ticker_list.remove(to_remove)
                save_tickers(st.session_state.ticker_list)
                st.cache_data.clear()
                st.success(f"Removed {to_remove}!")
                st.rerun()

# TAB 3: BACKGROUND SETTINGS
with tab_background:
    st.subheader("🖼️ Background Settings")

    if repo_images:
        st.markdown("#### Select background image detected in your repository:")
        tab_bg_choice = st.selectbox(
            "Choose Image",
            options=["(Keep Current)"] + repo_images,
            key="tab_bg_choice",
        )
        if (
            st.button("Apply Selected Image")
            and tab_bg_choice != "(Keep Current)"
        ):
            b64_str, mime_type = file_to_base64(tab_bg_choice)
            st.session_state.uploaded_bg_b64 = b64_str
            st.session_state.uploaded_bg_mime = mime_type
            st.success(f"Applied {tab_bg_choice} as background!")
            st.rerun()

    st.markdown("---")
    st.markdown("#### Upload a new custom wallpaper:")
    tab_uploader = st.file_uploader(
        "Upload Custom Background (.jpg / .png)",
        type=["jpg", "jpeg", "png", "webp"],
        key="tab_bg_file_uploader",
    )
    if tab_uploader:
        bytes_data = tab_uploader.read()
        st.session_state.uploaded_bg_b64 = base64.b64encode(bytes_data).decode(
            "utf-8"
        )
        ext = tab_uploader.name.split(".")[-1].lower()
        st.session_state.uploaded_bg_mime = (
            "image/jpeg" if ext in ["jpg", "jpeg"] else f"image/{ext}"
        )
        st.success("Uploaded and applied custom background!")
        st.rerun()
