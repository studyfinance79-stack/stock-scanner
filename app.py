import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

# ==========================================
# 1. PAGE SETUP & CONFIGURATION
# ==========================================
st.set_page_config(page_title="Technical Stock Scanner", layout="wide")

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

# ==========================================
# 2. TELEGRAM ALERT FUNCTION
# ==========================================


def send_telegram_alert(message):
    """Sends HTML formatted Telegram messages using secrets."""
    bot_token = st.secrets.get("TELEGRAM_BOT_TOKEN")
    chat_id = st.secrets.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}

    try:
        res = requests.post(url, data=payload, timeout=5)
        return res.status_code == 200
    except Exception:
        return False


# ==========================================
# 3. TECHNICAL INDICATORS CALCULATION
# ==========================================


def calc_rsi(series, period=14):
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
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calc_adx(df, period=14):
    high, low, close = df["High"], df["Low"], df["Close"]
    plus_dm = high.diff()
    minus_dm = low.diff().abs()

    plus_dm = np.where(
        (plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0.0
    )
    minus_dm = np.where(
        (minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0.0
    )

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()

    plus_di = (
        100
        * (
            pd.Series(plus_dm, index=df.index)
            .ewm(alpha=1 / period, adjust=False)
            .mean()
            / atr
        )
    )
    minus_di = (
        100
        * (
            pd.Series(minus_dm, index=df.index)
            .ewm(alpha=1 / period, adjust=False)
            .mean()
            / atr
        )
    )

    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.ewm(alpha=1 / period, adjust=False).mean()
    return adx.iloc[-1]


def calc_supertrend(df, period=10, multiplier=2):
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

    return st_value, trend


# ==========================================
# 4. DATA FETCHING (CACHED)
# ==========================================
@st.cache_data(ttl=300)
def fetch_stock_data(tickers):
    data_list = []
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

            if len(df) < 100:
                continue

            current_price = df["Close"].iloc[-1]

            # EMAs
            ema_20 = (
                df["Close"].ewm(span=20, adjust=False).mean().iloc[-1]
            )
            ema_50 = (
                df["Close"].ewm(span=50, adjust=False).mean().iloc[-1]
            )
            ema_100 = (
                df["Close"].ewm(span=100, adjust=False).mean().iloc[-1]
            )
            ema_200 = (
                df["Close"].ewm(span=200, adjust=False).mean().iloc[-1]
            )

            # Daily RSI & ADX
            daily_rsi = calc_rsi(df["Close"]).iloc[-1]
            adx_val = calc_adx(df)
            st_val, st_status = calc_supertrend(df)

            # Weekly RSI
            df_weekly = (
                df["Close"].resample("W-FRI").last().dropna()
            )
            weekly_rsi = calc_rsi(df_weekly).iloc[-1]

            # Monthly RSI
            df_monthly = df["Close"].resample("ME").last().dropna()
            monthly_rsi = calc_rsi(df_monthly).iloc[-1]

            clean_name = raw_symbol.replace(".NS", "").upper()

            data_list.append(
                {
                    "symbol": clean_name,
                    "price": current_price,
                    "monthly_rsi": monthly_rsi,
                    "weekly_rsi": weekly_rsi,
                    "daily_rsi": daily_rsi,
                    "ema_20": ema_20,
                    "ema_50": ema_50,
                    "ema_100": ema_100,
                    "ema_200": ema_200,
                    "supertrend_status": st_status,
                    "supertrend_val": st_val,
                    "adx": adx_val,
                }
            )
        except Exception:
            continue
    return data_list


# ==========================================
# 5. WEAKNESS EVALUATOR & TELEGRAM TRIGGER
# ==========================================


def evaluate_weakness_and_alert(row):
    score = 0.0
    triggers = []

    # 1st Priority: Monthly RSI < 60 (1.5 pts)
    if row["monthly_rsi"] < 60:
        score += 1.5
        triggers.append(f"• Monthly RSI: {row['monthly_rsi']:.1f} (< 60)")

    # 2nd Priority: Weekly RSI < 60 (1.5 pts)
    if row["weekly_rsi"] < 60:
        score += 1.5
        triggers.append(f"• Weekly RSI: {row['weekly_rsi']:.1f} (< 60)")

    # 3rd Priority: Daily RSI < 52 (1.0 pt)
    if row["daily_rsi"] < 52:
        score += 1.0
        triggers.append(f"• Daily RSI: {row['daily_rsi']:.1f} (< 52)")

    # 4th Priority: Price < EMA 20 (1.0 pt)
    if row["price"] < row["ema_20"]:
        score += 1.0
        triggers.append(f"• Below EMA 20 (₹{row['ema_20']:.1f})")

    # 5th Priority: Supertrend Bearish (1.5 pts)
    if row["supertrend_status"] == "BEARISH":
        score += 1.5
        triggers.append("• Supertrend: BEARISH")

    # 6th Priority: ADX < 20 (0.5 pt)
    if row["adx"] < 20:
        score += 0.5
        triggers.append(f"• ADX: {row['adx']:.1f} (< 20)")

    # 7th Priority: Price < EMA 50 (1.0 pt)
    if row["price"] < row["ema_50"]:
        score += 1.0
        triggers.append(f"• Below EMA 50 (₹{row['ema_50']:.1f})")

    # 8th Priority: Price < EMA 100 (1.0 pt)
    if row["price"] < row["ema_100"]:
        score += 1.0
        triggers.append(f"• Below EMA 100 (₹{row['ema_100']:.1f})")

    # 9th Priority: Price < EMA 200 (1.0 pt)
    if row["price"] < row["ema_200"]:
        score += 1.0
        triggers.append(f"• Below EMA 200 (₹{row['ema_200']:.1f})")

    # Classification
    if score >= 7.5:
        signal_type = "🔴 STRONG SELL"
    elif score >= 5.0:
        signal_type = "⚠️ WEAK / SELL"
    else:
        signal_type = "🟢 BULLISH / NEUTRAL"

    # SEND TELEGRAM ALERT ONLY IF WEAK/SELL OR STRONG SELL
    if score >= 5.0:
        message = (
            f"<b>{signal_type}: {row['symbol']}</b>\n"
            f"<b>Price:</b> ₹{row['price']:.2f}\n"
            f"<b>Weakness Score:</b> {score:.1f} / 10.0\n\n"
            f"<b>Triggered Sell Criteria:</b>\n" + "\n".join(triggers)
        )

        alert_key = f"telegram_sent_{row['symbol']}_{score}"
        if alert_key not in st.session_state:
            sent = send_telegram_alert(message)
            if sent:
                st.session_state[alert_key] = True

    return score, signal_type


# ==========================================
# 6. MAIN APP RENDER
# ==========================================
st.title("📈 Technical Stock Scanner")

raw_stocks = fetch_stock_data(DEFAULT_TICKERS)
table_rows = []

for stock in raw_stocks:
    score, signal = evaluate_weakness_and_alert(stock)

    table_rows.append(
        {
            "STOCK NAME": stock["symbol"],
            "PRICE": f"₹{stock['price']:.2f}",
            "WEAKNESS SCORE": f"{score:.1f} / 10.0",
            "SIGNAL": signal,
            "SUPERTREND": stock["supertrend_status"],
            "ADX (14)": f"{stock['adx']:.1f}",
            "DAILY RSI": f"{stock['daily_rsi']:.1f}",
            "WEEKLY RSI": f"{stock['weekly_rsi']:.1f}",
            "MONTHLY RSI": f"{stock['monthly_rsi']:.1f}",
            "BELOW EMA 20": "YES"
            if stock["price"] < stock["ema_20"]
            else "NO",
            "BELOW EMA 50": "YES"
            if stock["price"] < stock["ema_50"]
            else "NO",
            "BELOW EMA 100": "YES"
            if stock["price"] < stock["ema_100"]
            else "NO",
            "BELOW EMA 200": "YES"
            if stock["price"] < stock["ema_200"]
            else "NO",
        }
    )

df_display = pd.DataFrame(table_rows)
st.dataframe(df_display, use_container_width=True)
