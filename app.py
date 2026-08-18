import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Stock Technical Scanner", layout="wide")
st.title("📈 Multi-Timeframe Stock Technical Scanner")
st.caption("Calculates TradingView-accurate Monthly/Weekly/Daily RSI and EMA 20, 50, 100, 200 alignments.")

# Default list of popular stocks
DEFAULT_STOCKS = "RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS, ICICIBANK.NS, TATAMOTORS.NS, SBIN.NS, BHARTIARTL.NS, ITC.NS, LTIM.NS"

user_input = st.text_area("Enter Stock Tickers (separated by commas, up to 50):", value=DEFAULT_STOCKS, height=100)
stock_list = [s.strip().upper() for s in user_input.split(",") if s.strip()]

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

def fetch_stock_data(ticker):
    try:
        # Fetch 3 years of daily OHLC data to give EMAs and Monthly RSI proper warm-up depth
        df_daily = yf.download(ticker, period="3y", interval="1d", progress=False)
        if df_daily.empty or len(df_daily) < 200:
            return None

        # Clean multi-index headers if present
        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily = df_daily.xs(ticker, axis=1, level=1)

        close_daily = df_daily['Close']

        # --- Daily Calculations ---
        ema20_s = calculate_tv_ema(close_daily, 20)
        ema50_s = calculate_tv_ema(close_daily, 50)
        ema100_s = calculate_tv_ema(close_daily, 100)
        ema200_s = calculate_tv_ema(close_daily, 200)
        rsi_daily_s = calculate_tv_rsi(close_daily, 14)

        # --- Weekly Calculations ---
        close_weekly = close_daily.resample('W').last().dropna()
        rsi_weekly_s = calculate_tv_rsi(close_weekly, 14)

        # --- Monthly Calculations ---
        close_monthly = close_daily.resample('ME').last().dropna()
        rsi_monthly_s = calculate_tv_rsi(close_monthly, 14)

        # Latest Values
        curr_price = float(close_daily.iloc[-1])
        e20 = float(ema20_s.iloc[-1])
        e50 = float(ema50_s.iloc[-1])
        e100 = float(ema100_s.iloc[-1])
        e200 = float(ema200_s.iloc[-1])

        r_d = float(rsi_daily_s.iloc[-1])
        r_w = float(rsi_weekly_s.iloc[-1])
        r_m = float(rsi_monthly_s.iloc[-1])

        # EMA Trend Alignment Criteria
        ema_aligned = (curr_price > e20) and (e20 > e50) and (e50 > e100) and (e100 > e200)

        # Signal Logic
        buy_condition = (r_m > 60) and (r_w > 60) and (r_d > 50) and ema_aligned
        sell_condition = (r_d < 50) or (curr_price < e20)

        if buy_condition:
            signal = "🟢 BUY / HOLD"
        elif sell_condition:
            signal = "🔴 SELL"
        else:
            signal = "🟡 NEUTRAL"

        return {
            "Stock Name": ticker,
            "Signal": signal,
            "Monthly RSI": round(r_m, 2),
            "Weekly RSI": round(r_w, 2),
            "Daily RSI": round(r_d, 2),
            "EMA Alignment (Price > 20 > 50 > 100 > 200)": "YES" if ema_aligned else "NO",
            "Current Price": round(curr_price, 2)
        }
    except Exception:
        return None

# ---------------------------------------------------------
# Web UI Trigger
# ---------------------------------------------------------
if st.button("🔍 Scan Technical Indicators"):
    st.info("Fetching market data and calculating indicators...")
    results = []
    
    for symbol in stock_list[:50]:
        data = fetch_stock_data(symbol)
        if data:
            results.append(data)

    if results:
        df = pd.DataFrame(results)
        
        # Display formatted table
        st.dataframe(
            df[["Stock Name", "Signal", "Monthly RSI", "Weekly RSI", "Daily RSI", "EMA Alignment (Price > 20 > 50 > 100 > 200)", "Current Price"]],
            use_container_width=True
        )
    else:
        st.error("No valid stock data could be fetched. Please check the ticker symbols.")
