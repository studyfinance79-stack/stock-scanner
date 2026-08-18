import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(page_title="Pro Stock Technical Scanner", layout="wide", page_icon="📈")

st.markdown("<h1 style='text-align: center;'>📊 Pro Stock Technical Scanner</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8B949E;'>Real-time TradingView RSI & EMA Trend Signals</p>", unsafe_allow_html=True)
st.markdown("---")

# ---------------------------------------------------------
# Sidebar Setup
# ---------------------------------------------------------
st.sidebar.header("⚙️ Scanner Settings & Alerts")
st.sidebar.markdown("---")
st.sidebar.subheader("📱 Telegram Notification")
telegram_token = st.sidebar.text_input("Bot Token", type="password", help="Bot Token from @BotFather")
telegram_chat_id = st.sidebar.text_input("Chat ID", help="Your personal or group Chat ID")

# ---------------------------------------------------------
# Session State for Dynamic Stock List
# ---------------------------------------------------------
if "stocks" not in st.session_state:
    st.session_state.stocks = [
        "AEROFLEX", "BLSE", "DATAPATTNS", "IPCALAB",
        "KANORICHEM", "MODTHREAD", "NETWEB", "PREMIERPOL", "SONACOMS"
    ]

def add_stock_callback():
    val = st.session_state.new_stock_input.strip().upper()
    if val:
        clean_val = val.replace(".NS", "").replace(".BO", "")
        if clean_val not in st.session_state.stocks:
            st.session_state.stocks.append(clean_val)
        st.session_state.new_stock_input = ""

# ---------------------------------------------------------
# Stock Addition Bar
# ---------------------------------------------------------
col1, col2 = st.columns([3, 1])

with col1:
    st.text_input(
        "➕ Add Stock Name (Type ticker & press Enter):",
        key="new_stock_input",
        placeholder="e.g. RELIANCE, TATAMOTORS, INFY",
        on_change=add_stock_callback
    )

with col2:
    st.write(" ")
    st.write(" ")
    if st.button("🗑️ Clear Stock List"):
        st.session_state.stocks = []
        st.rerun()

if st.session_state.stocks:
    st.write("**Tracked Stocks:** " + " • ".join([f"`{s}`" for s in st.session_state.stocks]))

st.markdown("---")

# ---------------------------------------------------------
# Calculation Helpers
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

def calculate_tv_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_tv_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def fetch_stock_data(ticker_symbol):
    ticker = ticker_symbol if ("." in ticker_symbol) else f"{ticker_symbol}.NS"
    try:
        df_daily = yf.download(ticker, period="3y", interval="1d", progress=False)
        if df_daily.empty or len(df_daily) < 20:
            return None

        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily = df_daily.xs(ticker, axis=1, level=1)

        close_daily = df_daily['Close']

        ema20_s = calculate_tv_ema(close_daily, 20)
        rsi_daily_s = calculate_tv_rsi(close_daily, 14)

        close_weekly = close_daily.resample('W').last().dropna()
        rsi_weekly_s = calculate_tv_rsi(close_weekly, 14)

        close_monthly = close_daily.resample('ME').last().dropna()
        rsi_monthly_s = calculate_tv_rsi(close_monthly, 14)

        curr_price = float(close_daily.iloc[-1])
        e20 = float(ema20_s.iloc[-1])
        r_d = float(rsi_daily_s.iloc[-1])
        r_w = float(rsi_weekly_s.iloc[-1]) if len(rsi_weekly_s) > 0 else 0.0
        r_m = float(rsi_monthly_s.iloc[-1]) if len(rsi_monthly_s) > 0 else 0.0

        sell_condition = (r_d < 50) or (curr_price < e20)
        signal = "🔴 SELL" if sell_condition else "🟢 HOLD"

        return {
            "Stock Name": ticker_symbol.replace(".NS", ""),
            "Current Price": f"₹{curr_price:,.2f}",
            "Daily RSI": round(r_d, 2),
            "Weekly RSI": round(r_w, 2),
            "Monthly RSI": round(r_m, 2),
            "Signal": signal,
            "EMA20": e20
        }
    except Exception:
        return None

# ---------------------------------------------------------
# Execution & Display
# ---------------------------------------------------------
if st.button("🚀 Run Technical Scan", type="primary", use_container_width=True):
    if not st.session_state.stocks:
        st.warning("⚠️ Stock list is empty. Add stock names above.")
    else:
        with st.spinner("Scanning market data..."):
            results = []
            sell_alerts = []
            for symbol in st.session_state.stocks:
                data = fetch_stock_data(symbol)
                if data:
                    results.append(data)
                    if data["Signal"] == "🔴 SELL":
                        sell_alerts.append(data)

        if results:
            df = pd.DataFrame(results)
            
            # Start Index at 1 for Serial No.
            df.index = range(1, len(df) + 1)
            df.index.name = "Serial No."

            display_cols = ["Stock Name", "Current Price", "Daily RSI", "Weekly RSI", "Monthly RSI", "Signal"]
            
            # Render Clean Native Table
            st.dataframe(
                df[display_cols],
                use_container_width=True,
                column_config={
                    "Signal": st.column_config.TextColumn("Signal", help="🟢 HOLD or 🔴 SELL"),
                }
            )

            # Telegram Dispatch
            if sell_alerts:
                if telegram_token and telegram_chat_id:
                    alert_msg = "🚨 *STOCK SCANNER SELL ALERT* 🚨\n\n"
                    for item in sell_alerts:
                        alert_msg += f"• *{item['Stock Name']}* | Price: {item['Current Price']} | Daily RSI: {item['Daily RSI']}\n"
                    
                    if send_telegram_alert(telegram_token, telegram_chat_id, alert_msg):
                        st.success(f"📲 Telegram alert sent for {len(sell_alerts)} stock(s)!")
                    else:
                        st.error("❌ Telegram alert failed. Check Bot Token and Chat ID.")
                else:
                    st.info("ℹ️ SELL signals present. Enter Telegram Token/Chat ID in sidebar to get alerts.")
            else:
                st.success("✅ All scanned stocks are in 🟢 HOLD state.")
