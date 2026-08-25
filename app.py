import numpy as np
import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yfinance as yf

# Page Setup
st.set_page_config(
    page_title="Technical Stock Scanner Ultra", page_icon="📈", layout="wide"
)

# Auto-refresh app every 60 seconds
st_autorefresh(interval=60000, key="stock_scanner_autorefresh")

# Original HD Styling & Glassmorphism CSS
st.markdown(
    """
<style>
    .stApp {
        background: linear-gradient(rgba(11, 19, 43, 0.85), rgba(11, 19, 43, 0.85)), 
                    url("https://images.unsplash.com/photo-1518837695005-2083093ee35b?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        color: #ffffff;
    }
    .table-container {
        max-height: 78vh;
        overflow-y: auto;
        border: 2px solid #0284c7;
        border-radius: 10px;
        margin-top: 10px;
        box-shadow: 0 0 20px rgba(2, 132, 199, 0.35);
        background: rgba(11, 19, 43, 0.75);
        backdrop-filter: blur(8px);
    }
    .scanner-table {
        width: 100%;
        border-collapse: collapse;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 13px;
    }
    .scanner-table th {
        background-color: rgba(17, 34, 64, 0.98) !important;
        color: #38bdf8;
        font-weight: 800;
        padding: 12px 8px;
        border: 2px solid #0284c7 !important;
        text-transform: uppercase;
        position: sticky;
        top: 0;
        z-index: 10;
        text-align: center;
    }
    .scanner-table tfoot th {
        background-color: rgba(17, 34, 64, 0.98) !important;
        color: #38bdf8;
        font-weight: 800;
        padding: 12px 8px;
        border: 2px solid #0284c7 !important;
        text-transform: uppercase;
        text-align: center;
    }
    .scanner-table td {
        padding: 8px 6px;
        border: 1px solid rgba(2, 132, 199, 0.25);
        text-align: center;
        vertical-align: middle;
    }
    .badge {
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 10px;
        display: inline-block;
        border: 1px solid transparent;
        line-height: 1.3;
    }
    .badge-darkred { background-color: rgba(127, 29, 29, 0.8); color: #fca5a5; border-color: #ef4444; }
    .badge-red { background-color: rgba(153, 27, 27, 0.8); color: #fecaca; border-color: #f87171; }
    .badge-purple { background-color: rgba(88, 28, 135, 0.8); color: #e9d5ff; border-color: #c084fc; }
    .badge-green { background-color: rgba(6, 95, 70, 0.8); color: #a7f3d0; border-color: #34d399; }
    .badge-vol-high { background-color: rgba(6, 95, 70, 0.8); color: #a7f3d0; border-color: #34d399; }
    .badge-vol-low { background-color: rgba(153, 27, 27, 0.8); color: #fecaca; border-color: #f87171; }
    .badge-vol-spike { background-color: rgba(88, 28, 135, 0.8); color: #e9d5ff; border-color: #c084fc; }
</style>
""",
    unsafe_allow_html=True,
)


def send_telegram_alert(token, chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        res = requests.post(url, json=payload, timeout=5)
        res_json = res.json()
        if res_json.get("ok"):
            return True, None
        return False, res_json.get("description", "Unknown Telegram API Error")
    except Exception as e:
        return False, str(e)


def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_adx(df, period=14):
    df = df.copy()
    df["tr1"] = df["High"] - df["Low"]
    df["tr2"] = abs(df["High"] - df["Close"].shift(1))
    df["tr3"] = abs(df["Low"] - df["Close"].shift(1))
    df["tr"] = df[["tr1", "tr2", "tr3"]].max(axis=1)

    df["up_move"] = df["High"] - df["High"].shift(1)
    df["down_move"] = df["Low"].shift(1) - df["Low"]

    df["plus_dm"] = np.where(
        (df["up_move"] > df["down_move"]) & (df["up_move"] > 0),
        df["up_move"],
        0,
    )
    df["minus_dm"] = np.where(
        (df["down_move"] > df["up_move"]) & (df["down_move"] > 0),
        df["down_move"],
        0,
    )

    tr_smooth = df["tr"].rolling(window=period).sum()
    plus_di = 100 * (df["plus_dm"].rolling(window=period).sum() / tr_smooth)
    minus_di = 100 * (df["minus_dm"].rolling(window=period).sum() / tr_smooth)

    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.rolling(window=period).mean()
    return adx.iloc[-1]


def calculate_supertrend(df, period=10, multiplier=2):
    high, low, close = df["High"], df["Low"], df["Close"]
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    atr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).rolling(period).mean()

    hl2 = (high + low) / 2
    basic_ub = hl2 + (multiplier * atr)
    basic_lb = hl2 - (multiplier * atr)

    final_ub = pd.Series(0.0, index=df.index)
    final_lb = pd.Series(0.0, index=df.index)
    st_val = pd.Series(0.0, index=df.index)

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

    for i in range(1, len(df)):
        if close.iloc[i] <= final_ub.iloc[i]:
            st_val.iloc[i] = final_ub.iloc[i]
        else:
            st_val.iloc[i] = final_lb.iloc[i]

    current_st = st_val.iloc[-1]
    is_bullish = close.iloc[-1] > current_st
    return current_st, is_bullish


# Sidebar Configuration
st.sidebar.title("⚙️ Scanner Settings")

default_stocks = [
    "DATAPATTNS.NS",
    "IPCALAB.NS",
    "KANORICHEM.NS",
    "MODTHREAD.NS",
    "NETWEB.NS",
    "PREMIERPOL.NS",
    "SONACOMS.NS",
    "RELIANCE.NS",
]
stock_list_input = st.sidebar.text_area(
    "Stock Watchlist (NSE tickers separated by comma):",
    value=", ".join(default_stocks),
    height=120,
)
stocks = [s.strip().upper() for s in stock_list_input.split(",") if s.strip()]

st.sidebar.markdown("---")
st.sidebar.subheader("📱 Telegram Alerts")
enable_telegram = st.sidebar.checkbox(
    "Enable Telegram Notifications", value=True
)

telegram_token = st.sidebar.text_input(
    "Telegram Bot Token",
    value=st.secrets.get("TELEGRAM_BOT_TOKEN", ""),
    type="password",
)
telegram_chat_id = st.sidebar.text_input(
    "Telegram Chat ID", value=st.secrets.get("TELEGRAM_CHAT_ID", "")
)

if st.sidebar.button("🧪 Send Test Telegram Alert"):
    if telegram_token and telegram_chat_id:
        ok, err = send_telegram_alert(
            telegram_token,
            telegram_chat_id,
            "<b>Test Alert from Technical Stock Scanner!</b>\nTelegram integration is working properly.",
        )
        if ok:
            st.sidebar.success("Test alert sent successfully!")
        else:
            st.sidebar.error(f"Failed to send: {err}")
    else:
        st.sidebar.warning("Please enter Bot Token and Chat ID.")

if st.sidebar.button("🔄 Reset Telegram Alert Logs"):
    keys_to_remove = [
        key for key in st.session_state if key.startswith("alert_sent_")
    ]
    for key in keys_to_remove:
        del st.session_state[key]
    st.sidebar.success("Alert memory cleared! Re-evaluating scanner...")

# Data Processing Loop
scanner_data = []

for symbol in stocks:
    try:
        ticker = yf.Ticker(symbol)
        df_daily = ticker.history(period="1y", interval="1d")
        if df_daily.empty or len(df_daily) < 100:
            continue

        df_weekly = ticker.history(period="2y", interval="1wk")
        df_monthly = ticker.history(period="5y", interval="1mo")

        latest_price = df_daily["Close"].iloc[-1]
        prev_price = df_daily["Close"].iloc[-2]
        price_change_up = latest_price >= prev_price

        ema20 = df_daily["Close"].ewm(span=20, adjust=False).mean().iloc[-1]
        ema50 = df_daily["Close"].ewm(span=50, adjust=False).mean().iloc[-1]
        ema100 = df_daily["Close"].ewm(span=100, adjust=False).mean().iloc[-1]
        ema200 = df_daily["Close"].ewm(span=200, adjust=False).mean().iloc[-1]

        daily_rsi = calculate_rsi(df_daily["Close"]).iloc[-1]
        weekly_rsi = calculate_rsi(df_weekly["Close"]).iloc[-1]
        monthly_rsi = calculate_rsi(df_monthly["Close"]).iloc[-1]

        adx_val = calculate_adx(df_daily)
        st_val, st_bullish = calculate_supertrend(df_daily)

        avg_vol_20 = df_daily["Volume"].tail(20).mean()
        latest_vol = df_daily["Volume"].iloc[-1]
        has_vol_spike = latest_vol > (1.8 * avg_vol_20)
        is_high_vol = latest_vol > (1.2 * avg_vol_20)
        vol_lakhs = latest_vol / 100000

        weakness_score = 0.0
        reasons = []

        if monthly_rsi < 60:
            weakness_score += 1.0
            reasons.append(f"• Monthly RSI: {monthly_rsi:.1f} (&lt; 60)")
        if weekly_rsi < 60:
            weakness_score += 1.0
            reasons.append(f"• Weekly RSI: {weekly_rsi:.1f} (&lt; 60)")
        if daily_rsi < 52:
            weakness_score += 1.0
            reasons.append(f"• Daily RSI: {daily_rsi:.1f} (&lt; 52)")

        if latest_price < ema20:
            weakness_score += 1.0
            reasons.append(f"• Price &lt; Daily EMA 20 (₹{ema20:.1f})")
        if latest_price < ema50:
            weakness_score += 1.0
            reasons.append(f"• Price &lt; Daily EMA 50 (₹{ema50:.1f})")
        if latest_price < ema100:
            weakness_score += 1.0
            reasons.append(f"• Price &lt; Daily EMA 100 (₹{ema100:.1f})")
        if latest_price < ema200:
            weakness_score += 1.0
            reasons.append(f"• Price &lt; Daily EMA 200 (₹{ema200:.1f})")

        if not st_bullish:
            weakness_score += 1.5
            reasons.append(f"• Bearish Supertrend (₹{st_val:.1f})")
        if adx_val < 20:
            weakness_score += 1.5
            reasons.append(f"• Weak Trend ADX: {adx_val:.1f} (&lt; 20)")

        clean_symbol = symbol.replace(".NS", "")

        scanner_data.append({
            "symbol": clean_symbol,
            "price": latest_price,
            "price_up": price_change_up,
            "weakness_score": weakness_score,
            "vol_lakhs": vol_lakhs,
            "vol_spike": has_vol_spike,
            "vol_high": is_high_vol,
            "supertrend_val": st_val,
            "supertrend_bullish": st_bullish,
            "adx": adx_val,
            "daily_rsi": daily_rsi,
            "weekly_rsi": weekly_rsi,
            "monthly_rsi": monthly_rsi,
            "ema20": ema20,
            "ema50": ema50,
            "ema100": ema100,
            "ema200": ema200,
            "reasons": reasons,
        })
    except Exception as e:
        continue

df_live = pd.DataFrame(scanner_data)

st.title("⚡ Technical Stock Scanner")

headers = [
    "#",
    "STOCK NAME",
    "PRICE",
    "WEAKNESS SCORE",
    "AVG. VOL & SPIKE",
    "SUPERTREND (10,2)",
    "ADX (14)",
    "DAILY RSI (&lt;52)",
    "WEEKLY RSI (&lt;60)",
    "MONTHLY RSI (&lt;60)",
    "&lt; EMA 20",
    "&lt; EMA 50",
    "&lt; EMA 100",
    "&lt; EMA 200",
]

if not df_live.empty:
    html_table = (
        '<div class="table-container"><table class="scanner-table"><thead><tr>'
    )
    for h in headers:
        align_css = (
            'style="text-align: left; padding-left: 14px;"'
            if "STOCK NAME" in h
            else ""
        )
        html_table += f"<th {align_css}>{h}</th>"
    html_table += "</tr></thead><tbody>"

    for idx, row in df_live.iterrows():
        w_score = row["weakness_score"]
        if w_score >= 7.5:
            score_badge = '<span class="badge badge-darkred">7.5 / 10.0<br>ULTRA BEARISH</span>'
            signal_title = "🔴 ULTRA BEARISH / STRONG SELL"
        elif w_score >= 5.0:
            score_badge = (
                f'<span class="badge badge-red">{w_score:.1f} /'
                ' 10.0<br>WEAK / SELL</span>'
            )
            signal_title = "⚠️ WEAK / SELL"
        elif w_score >= 2.5:
            score_badge = (
                f'<span class="badge badge-purple">{w_score:.1f} /'
                ' 10.0<br>NEUTRAL</span>'
            )
            signal_title = "🟡 NEUTRAL"
        else:
            score_badge = (
                f'<span class="badge badge-green">{w_score:.1f} /'
                ' 10.0<br>BULLISH / STRONG BULLISH</span>'
            )
            signal_title = "🟢 BULLISH"

        price_dir = (
            '<span class="badge badge-green">UP</span>'
            if row["price_up"]
            else '<span class="badge badge-red">DOWN</span>'
        )

        if row["vol_spike"]:
            vol_badge = '<span class="badge badge-vol-spike">SPIKE</span>'
        elif row["vol_high"]:
            vol_badge = '<span class="badge badge-vol-high">HIGH VOL</span>'
        else:
            vol_badge = '<span class="badge badge-vol-low">LOW VOL</span>'

        st_badge = (
            '<span class="badge badge-green">BULLISH</span>'
            if row["supertrend_bullish"]
            else '<span class="badge badge-red">BEARISH</span>'
        )
        adx_badge = (
            '<span class="badge badge-green">STRONG</span>'
            if row["adx"] >= 25
            else '<span class="badge badge-red">WEAK</span>'
        )

        daily_rsi_badge = (
            '<span class="badge badge-red">WEAK</span>'
            if row["daily_rsi"] < 52
            else '<span class="badge badge-green">OK</span>'
        )
        weekly_rsi_badge = (
            '<span class="badge badge-red">WEAK</span>'
            if row["weekly_rsi"] < 60
            else '<span class="badge badge-green">OK</span>'
        )
        monthly_rsi_badge = (
            '<span class="badge badge-red">WEAK</span>'
            if row["monthly_rsi"] < 60
            else '<span class="badge badge-green">OK</span>'
        )

        below_ema20 = (
            '<span class="badge badge-red">YES</span>'
            if row["price"] < row["ema20"]
            else '<span class="badge badge-green">NO</span>'
        )
        below_ema50 = (
            '<span class="badge badge-red">YES</span>'
            if row["price"] < row["ema50"]
            else '<span class="badge badge-green">NO</span>'
        )
        below_ema100 = (
            '<span class="badge badge-red">YES</span>'
            if row["price"] < row["ema100"]
            else '<span class="badge badge-green">NO</span>'
        )
        below_ema200 = (
            '<span class="badge badge-red">YES</span>'
            if row["price"] < row["ema200"]
            else '<span class="badge badge-green">NO</span>'
        )

        html_table += (
            f"<tr>"
            f"<td>{idx + 1}</td>"
            f'<td style="text-align: left; padding-left: 14px; font-weight:'
            f' bold; color: #38bdf8;">{row["symbol"]} ↗</td>'
            f"<td><b>₹{row['price']:,.2f}</b><br>{price_dir}</td>"
            f"<td>{score_badge}</td>"
            f"<td><b>{row['vol_lakhs']:.2f}L</b><br>{vol_badge}</td>"
            f"<td><b>₹{row['supertrend_val']:,.1f}</b><br>{st_badge}</td>"
            f"<td><b>{row['adx']:.1f}</b><br>{adx_badge}</td>"
            f"<td><b>{row['daily_rsi']:.2f}</b><br>{daily_rsi_badge}</td>"
            f"<td><b>{row['weekly_rsi']:.2f}</b><br>{weekly_rsi_badge}</td>"
            f"<td><b>{row['monthly_rsi']:.2f}</b><br>{monthly_rsi_badge}</td>"
            f"<td><b>₹{row['ema20']:,.1f}</b><br>{below_ema20}</td>"
            f"<td><b>₹{row['ema50']:,.1f}</b><br>{below_ema50}</td>"
            f"<td><b>₹{row['ema100']:,.1f}</b><br>{below_ema100}</td>"
            f"<td><b>₹{row['ema200']:,.1f}</b><br>{below_ema200}</td>"
            f"</tr>"
        )

        if (
            enable_telegram
            and telegram_token
            and telegram_chat_id
            and w_score >= 2.5
        ):
            alert_key = f"alert_sent_{row['symbol']}_{w_score:.1f}"
            if alert_key not in st.session_state:
                clean_reasons = [
                    r.replace("<", "&lt;").replace(">", "&gt;")
                    for r in row["reasons"]
                ]
                alert_msg = (
                    f"<b>{signal_title}: {row['symbol']}</b>\n"
                    f"• <b>Price:</b> ₹{row['price']:,.2f}\n"
                    f"• <b>Weakness Score:</b> {w_score:.1f} / 10.0\n\n"
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
                        f"Telegram Alert sent for {row['symbol']}!", icon="📱"
                    )
                else:
                    st.sidebar.error(f"Alert Failed for {row['symbol']}: {err}")

    html_table += "</tbody>"

    # FOOTER ROW WITH COLUMN HEADERS
    html_table += "<tfoot><tr>"
    for h in headers:
        align_css = (
            'style="text-align: left; padding-left: 14px;"'
            if "STOCK NAME" in h
            else ""
        )
        html_table += f"<th {align_css}>{h}</th>"
    html_table += "</tr></tfoot>"

    html_table += "</table></div>"
    st.markdown(html_table, unsafe_allow_html=True)
else:
    st.info("No stock data fetched. Please check your stock list tickers.")
