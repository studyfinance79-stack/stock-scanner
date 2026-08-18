import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Stock Technical Scanner", layout="wide")
st.title("📈 Daily Technical Stock Scanner")

DEFAULT_STOCKS = "RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS, ICICIBANK.NS, TATAMOTORS.NS, SBIN.NS, BHARTIARTL.NS, ITC.NS, LTIM.NS"

user_input = st.text_area("Enter Stock Tickers (comma-separated, up to 50):", value=DEFAULT_STOCKS, height=100)
stock_list = [s.strip().upper() for s in user_input.split(",") if s.strip()]

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def fetch_stock_data(ticker):
    try:
        df_daily = yf.download(ticker, period="2y", interval="1d", progress=False)
        if df_daily.empty or len(df_daily) < 200:
            return None

        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily = df_daily.xs(ticker, axis=1, level=1)

        close = df_daily['Close']
        ema20 = close.ewm(span=20, adjust=False).mean()
        ema50 = close.ewm(span=50, adjust=False).mean()
        ema100 = close.ewm(span=100, adjust=False).mean()
        ema200 = close.ewm(span=200, adjust=False).mean()

        rsi_daily = calculate_rsi(close, 14)

        df_weekly = close.resample('W').last().to_frame()
        rsi_weekly = calculate_rsi(df_weekly['Close'], 14)

        df_monthly = close.resample('ME').last().to_frame()
        rsi_monthly = calculate_rsi(df_monthly['Close'], 14)

        curr_price = float(close.iloc[-1])
        e20, e50, e100, e200 = float(ema20.iloc[-1]), float(ema50.iloc[-1]), float(ema100.iloc[-1]), float(ema200.iloc[-1])
        r_d, r_w, r_m = float(rsi_daily.iloc[-1]), float(rsi_weekly.iloc[-1]), float(rsi_monthly.iloc[-1])

        ema_aligned = (curr_price > e20) and (e20 > e50) and (e50 > e100) and (e100 > e200)

        # Signals Logic
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
            "EMA Aligned (P>20>50>100>200)": "YES" if ema_aligned else "NO",
            "Current Price": round(curr_price, 2)
        }
    except Exception:
        return None

if st.button("🔍 Scan Stocks Now"):
    st.info("Scanning technical indicators...")
    results = []
    for symbol in stock_list[:50]:
        data = fetch_stock_data(symbol)
        if data:
            results.append(data)
    
    if results:
        df = pd.DataFrame(results)
        st.dataframe(df[["Stock Name", "Signal", "Monthly RSI", "Weekly RSI", "Daily RSI", "EMA Aligned (P>20>50>100>200)", "Current Price"]], use_container_width=True)
