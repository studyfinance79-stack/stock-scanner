import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(page_title="Stock Technical Scanner", layout="wide")
st.title("📈 Multi-Timeframe Stock Technical Scanner & Alerts")

# Sidebar Configuration for Telegram Alerts
st.sidebar.header("📱 Telegram Notification Setup")
telegram_token = st.sidebar.text_input("Bot Token", type="password", help="Get this from @BotFather on Telegram")
telegram_chat_id = st.sidebar.text_input("Chat ID", help="Your personal or channel Chat ID")

DEFAULT_STOCKS = "RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS, ICICIBANK.NS, TATAMOTORS.NS, SBIN.NS, BHARTIARTL.NS, ITC.NS, LTIM.NS"

user_input = st.text_area("Enter Stock Tickers (separated by commas, up to 50):", value=DEFAULT_STOCKS, height=100)
stock_list = [s.strip().upper() for s in user_input.split(",") if s.strip()]

# ---------------------------------------------------------
# Telegram Messaging Function
# ---------------------------------------------------------
def send_telegram_alert(token, chat_id, message):
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

# ---------------------------------------------------------
# TradingView Technical Indicators
# ---------------------------------------------------------
def calculate_tv_rsi(series, period=14):
    """TradingView ta.rsi() calculation using Wilder's Smoothing (alpha = 1/14)."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_tv_ema(series, period):
    """TradingView ta.ema() calculation."""
    return series.ewm(span=period, adjust=False).mean()

def fetch_stock_data(ticker):
    try:
        df_daily = yf.download(ticker, period="3y", interval="1d", progress=False)
        if df_daily.empty or len(df_daily) < 200:
            return None

        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily = df_daily.xs(ticker, axis=1, level=1)

        close_daily = df_daily['Close']

        # Indicator Calculations
        ema20_s = calculate_tv_ema(close_daily, 20)
        ema50_s = calculate_tv_ema(close_daily, 50)
        ema100_s = calculate_tv_ema(close_daily, 100)
        ema200_s = calculate_tv_ema(close_daily, 200)
        rsi_daily_s = calculate_tv_rsi(close_daily, 14)

        close_weekly = close_daily.resample('W').last().dropna()
        rsi_weekly_s = calculate_tv_rsi(close_weekly, 14)

        close_monthly = close_daily.resample('ME').last().dropna()
        rsi_monthly_s = calculate_tv_rsi(close_monthly, 14)

        curr_price = float(close_daily.iloc[-1])
        e20 = float(ema20_s.iloc[-1])
        e50 = float(ema50_s.iloc[-1])
        e100 = float(ema100_s.iloc[-1])
        e200 = float(ema200_s.iloc[-1])

        r_d = float(rsi_daily_s.iloc[-1])
        r_w = float(rsi_weekly_s.iloc[-1])
        r_m = float(rsi_monthly_s.iloc[-1])

        ema_aligned = (curr_price > e20) and (e20 > e50) and (e50 > e100) and (e100 > e200)

        # Signal Logic:
        # SELL if Daily RSI < 50 OR Price < EMA 20; otherwise HOLD
        sell_condition = (r_d < 50) or (curr_price < e20)
        signal = "🔴 SELL" if sell_condition else "🟢 HOLD"

        return {
            "Stock Name": ticker,
            "Monthly RSI": round(r_m, 2),
            "Weekly RSI": round(r_w, 2),
            "Daily RSI": round(r_d, 2),
            "Price > EMA 20 > 50 > 100 > 200": "YES" if ema_aligned else "NO",
            "Signal": signal,
            "Price": round(curr_price, 2),
            "EMA20": round(e20, 2)
        }
    except Exception:
        return None

# ---------------------------------------------------------
# Execution & Telegram Alert Dispatch
# ---------------------------------------------------------
if st.button("🔍 Scan Technical Indicators"):
    st.info("Fetching market data and scanning signals...")
    results = []
    sell_alerts = []
    
    for symbol in stock_list[:50]:
        data = fetch_stock_data(symbol)
        if data:
            results.append(data)
            if data["Signal"] == "🔴 SELL":
                sell_alerts.append(data)

    if results:
        df = pd.DataFrame(results)
        
        # Display 6-column Table
        df_display = df[[
            "Stock Name",
            "Monthly RSI",
            "Weekly RSI",
            "Daily RSI",
            "Price > EMA 20 > 50 > 100 > 200",
            "Signal"
        ]]
        
        st.dataframe(df_display, use_container_width=True)

        # Send Telegram Alert if SELL signals exist
        if sell_alerts:
            if telegram_token and telegram_chat_id:
                alert_msg = "🚨 *STOCK SCANNER SELL ALERT* 🚨\n\n"
                for item in sell_alerts:
                    alert_msg += (
                        f"• *{item['Stock Name']}*\n"
                        f"  Price: ₹{item['Price']} (EMA20: ₹{item['EMA20']})\n"
                        f"  Daily RSI: {item['Daily RSI']} | Signal: SELL\n\n"
                    )
                
                if send_telegram_alert(telegram_token, telegram_chat_id, alert_msg):
                    st.success(f"📲 Sent Telegram SELL notification for {len(sell_alerts)} stock(s)!")
                else:
                    st.error("❌ Failed to send Telegram alert. Check your Bot Token and Chat ID.")
            else:
                st.warning("⚠️ SELL signals detected, but Telegram Bot Token/Chat ID were not provided in the sidebar.")
        else:
            st.success("✅ No SELL signals detected across scanned stocks.")
    else:
        st.error("No valid stock data could be fetched.")
