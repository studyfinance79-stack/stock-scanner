import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# ---------------------------------------------------------
# Page Configuration & Custom CSS Injection
# ---------------------------------------------------------
st.set_page_config(page_title="Pro Stock Technical Scanner", layout="wide", page_icon="📈")

# Inject Custom High-Contrast CSS
st.markdown("""
<style>
    /* Dark Theme Core Styles */
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    
    /* Header Styling */
    .main-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 0.2rem;
        letter-spacing: 0.5px;
    }
    .sub-title {
        text-align: center;
        font-size: 1rem;
        color: #8B949E;
        margin-bottom: 2rem;
    }

    /* Custom Input & Card Containers */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    
    /* Custom Table Styling */
    .custom-table-container {
        width: 100%;
        overflow-x: auto;
        margin-top: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 0.95rem;
        background-color: #161B22;
        color: #F0F6FC;
        border: 1px solid #30363D;
    }
    .styled-table th {
        background-color: #21262D;
        color: #58A6FF;
        padding: 14px 16px;
        text-align: center !important;
        font-weight: 600;
        border-bottom: 2px solid #30363D;
        letter-spacing: 0.5px;
    }
    .styled-table td {
        padding: 12px 16px;
        text-align: center !important;
        vertical-align: middle;
        border-bottom: 1px solid #21262D;
    }
    .styled-table tr:hover {
        background-color: #1C2128;
    }
    
    /* Signal Badges */
    .badge-hold {
        background-color: rgba(38, 166, 154, 0.15);
        color: #26A69A;
        border: 1px solid #26A69A;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-sell {
        background-color: rgba(239, 83, 80, 0.15);
        color: #EF5350;
        border: 1px solid #EF5350;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar Setup
# ---------------------------------------------------------
st.sidebar.header("⚙️ Scanner Settings & Alerts")
st.sidebar.markdown("---")
st.sidebar.subheader("📱 Telegram Notification")
telegram_token = st.sidebar.text_input("Bot Token", type="password", help="Bot Token from @BotFather")
telegram_chat_id = st.sidebar.text_input("Chat ID", help="Your personal or group Chat ID")

# ---------------------------------------------------------
# Session State for Dynamic Stock Management
# ---------------------------------------------------------
if "stocks" not in st.session_state:
    st.session_state.stocks = [
        "AEROFLEX", "BLSE", "DATAPATTNS", "IPCALAB",
        "KANORICHEM", "MODTHREAD", "NETWEB", "PREMIERPOL", "SONACOMS"
    ]

def add_stock_callback():
    val = st.session_state.new_stock_input.strip().upper()
    if val:
        # Clean ticker symbol
        clean_val = val.replace(".NS", "").replace(".BO", "")
        if clean_val not in st.session_state.stocks:
            st.session_state.stocks.append(clean_val)
        st.session_state.new_stock_input = ""

# ---------------------------------------------------------
# Page Header
# ---------------------------------------------------------
st.markdown("<div class='main-title'>📊 Pro Stock Technical Scanner</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Real-time TradingView RSI & EMA Trend Signals</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Stock Addition & Management Bar
# ---------------------------------------------------------
col1, col2 = st.columns([3, 1])

with col1:
    st.text_input(
        "➕ Add Stock Name (Press Enter to add):",
        key="new_stock_input",
        placeholder="e.g. RELIANCE, TATAMOTORS, INFY",
        on_change=add_stock_callback
    )

with col2:
    st.write(" ") # Spacing align
    st.write(" ")
    if st.button("🗑️ Clear Stock List"):
        st.session_state.stocks = []
        st.rerun()

# Display current stock tags
if st.session_state.stocks:
    st.write("**Tracked Stocks:** " + " • ".join([f"`{s}`" for s in st.session_state.stocks]))

st.markdown("---")

# ---------------------------------------------------------
# Indicator Calculation Functions
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

        # Signal Logic
        sell_condition = (r_d < 50) or (curr_price < e20)
        signal = "🔴 SELL" if sell_condition else "🟢 HOLD"

        return {
            "Stock Name": ticker_symbol.replace(".NS", ""),
            "Current Price": f"₹{curr_price:,.2f}",
            "Monthly RSI": round(r_m, 2),
            "Weekly RSI": round(r_w, 2),
            "Daily RSI": round(r_d, 2),
            "Signal": signal,
            "RawPrice": curr_price,
            "EMA20": e20
        }
    except Exception:
        return None

# ---------------------------------------------------------
# Scan Execution & Render
# ---------------------------------------------------------
scan_btn = st.button("🚀 Run Technical Scan", type="primary", use_container_width=True)

if scan_btn or "initial_scan" not in st.session_state:
    st.session_state.initial_scan = True
    
    if not st.session_state.stocks:
        st.warning("⚠️ Stock list is empty. Please add at least one stock name above.")
    else:
        with st.spinner("Scanning market technicals..."):
            results = []
            sell_alerts = []
            
            for symbol in st.session_state.stocks:
                data = fetch_stock_data(symbol)
                if data:
                    results.append(data)
                    if data["Signal"] == "🔴 SELL":
                        sell_alerts.append(data)

        if results:
            # Build Custom Centered HTML Table
            table_html = """
            <div class="custom-table-container">
                <table class="styled-table">
                    <thead>
                        <tr>
                            <th>Serial No.</th>
                            <th>Stock Name</th>
                            <th>Current Price</th>
                            <th>Daily RSI</th>
                            <th>Weekly RSI</th>
                            <th>Monthly RSI</th>
                            <th>Signal</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for idx, row in enumerate(results, start=1):
                badge_class = "badge-sell" if "SELL" in row["Signal"] else "badge-hold"
                table_html += f"""
                    <tr>
                        <td><strong>{idx}</strong></td>
                        <td style="font-weight: 600; color: #58A6FF;">{row['Stock Name']}</td>
                        <td><strong>{row['Current Price']}</strong></td>
                        <td>{row['Daily RSI']}</td>
                        <td>{row['Weekly RSI']}</td>
                        <td>{row['Monthly RSI']}</td>
                        <td><span class="{badge_class}">{row['Signal']}</span></td>
                    </tr>
                """
            
            table_html += """
                    </tbody>
                </table>
            </div>
            """
            
            st.markdown(table_html, unsafe_allow_html=True)
            st.write("")

            # Handle Telegram Dispatch
            if sell_alerts:
                if telegram_token and telegram_chat_id:
                    alert_msg = "🚨 *STOCK SCANNER SELL ALERT* 🚨\n\n"
                    for item in sell_alerts:
                        alert_msg += (
                            f"• *{item['Stock Name']}*\n"
                            f"  Price: {item['Current Price']} (EMA20: ₹{item['EMA20']:.2f})\n"
                            f"  Daily RSI: {item['Daily RSI']} | Signal: SELL\n\n"
                        )
                    if send_telegram_alert(telegram_token, telegram_chat_id, alert_msg):
                        st.success(f"📲 Telegram alert sent for {len(sell_alerts)} SELL signal(s)!")
                    else:
                        st.error("❌ Telegram dispatch failed. Check Token and Chat ID.")
                else:
                    st.info("ℹ️ SELL signals present. Enter Telegram Token/Chat ID in sidebar to receive alerts.")
            else:
                st.success("✅ All scanned stocks are in 🟢 HOLD state.")
