import os
import requests
import yfinance as yf
import pandas as pd

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Stock watchlist to monitor
STOCKS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "TATAMOTORS.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LTIM.NS"
]

# ---------------------------------------------------------
# TradingView-Compliant Indicator Functions
# ---------------------------------------------------------
def calculate_tv_rsi(series, period=14):
    """TradingView ta.rsi() implementation using Wilder's Smoothing (alpha = 1/14)."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_tv_ema(series, period):
    """TradingView ta.ema() implementation."""
    return series.ewm(span=period, adjust=False).mean()

def send_telegram(msg):
    """Sends notification to Telegram Bot."""
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=data)

# ---------------------------------------------------------
# Execution & Scan Logic
# ---------------------------------------------------------
sell_alerts = []

for ticker in STOCKS:
    try:
        # Fetch 2 years of daily data for indicator warmup depth
        df = yf.download(ticker, period="2y", interval="1d", progress=False)
        if df.empty or len(df) < 50:
            continue

        if isinstance(df.columns, pd.MultiIndex):
            df = df.xs(ticker, axis=1, level=1)
        
        close = df['Close']
        
        ema20_s = calculate_tv_ema(close, 20)
        rsi_daily_s = calculate_tv_rsi(close, 14)

        curr_price = float(close.iloc[-1])
        e20 = float(ema20_s.iloc[-1])
        r_d = float(rsi_daily_s.iloc[-1])

        # Check SELL criteria
        reasons = []
        if r_d < 50:
            reasons.append(f"Daily RSI < 50 ({round(r_d, 2)})")
        if curr_price < e20:
            reasons.append(f"Price ({round(curr_price, 2)}) below EMA20 ({round(e20, 2)})")

        if reasons:
            sell_alerts.append(f"• {ticker}: " + " & ".join(reasons))
    except Exception:
        continue

if sell_alerts:
    alert_msg = "⚠️ DAILY SELL SIGNALS DETECTED (TradingView Engine):\n\n" + "\n".join(sell_alerts)
    send_telegram(alert_msg)
