import pandas as pd
import numpy as np
import yfinance as yf

def calculate_tv_rsi(series, period=14):
    """
    Pine Script ta.rma / ta.rsi implementation with extended warm-up support.
    """
    if len(series) < period + 1:
        return pd.Series(50.0, index=series.index)

    delta = series.diff()
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)

    rma_gain = np.zeros(len(series))
    rma_loss = np.zeros(len(series))

    # Seed initial value with Simple Moving Average (SMA) matching TradingView
    rma_gain[period] = np.mean(gain[1:period + 1])
    rma_loss[period] = np.mean(loss[1:period + 1])

    alpha = 1.0 / period
    for i in range(period + 1, len(series)):
        rma_gain[i] = alpha * gain[i] + (1.0 - alpha) * rma_gain[i - 1]
        rma_loss[i] = alpha * loss[i] + (1.0 - alpha) * rma_loss[i - 1]

    with np.errstate(divide='ignore', invalid='ignore'):
        rs = np.divide(rma_gain, rma_loss, out=np.zeros_like(rma_gain), where=rma_loss != 0)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        rsi[rma_loss == 0] = 100.0
        rsi[rma_gain == 0] = 0.0

    return pd.Series(rsi, index=series.index)


def fetch_stock_data(ticker_symbol):
    ticker = ticker_symbol if ("." in ticker_symbol) else f"{ticker_symbol}.NS"
    try:
        # Fetch 15 years of data to ensure Monthly & Weekly RMA fully converges
        df_daily = yf.download(ticker, period="15y", interval="1d", auto_adjust=False, progress=False)
        if df_daily.empty or len(df_daily) < 50:
            return None

        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily = df_daily.xs(ticker, axis=1, level=1)

        close_daily = df_daily['Close'].dropna()

        # 1. Daily RSI
        rsi_daily_s = calculate_tv_rsi(close_daily, 14)

        # 2. Weekly RSI (Resampled to Friday close, including active current week)
        close_weekly = close_daily.resample('W-FRI').last().dropna()
        rsi_weekly_s = calculate_tv_rsi(close_weekly, 14)

        # 3. Monthly RSI (Resampled to Month-End, including active current month)
        close_monthly = close_daily.resample('ME').last().dropna()
        rsi_monthly_s = calculate_tv_rsi(close_monthly, 14)

        curr_price = float(close_daily.iloc[-1])
        
        # Moving averages calculated on daily close
        e20 = float(close_daily.ewm(span=20, adjust=False).mean().iloc[-1])
        e50 = float(close_daily.ewm(span=50, adjust=False).mean().iloc[-1])
        e100 = float(close_daily.ewm(span=100, adjust=False).mean().iloc[-1])
        e200 = float(close_daily.ewm(span=200, adjust=False).mean().iloc[-1])

        r_d = float(rsi_daily_s.iloc[-1])
        r_w = float(rsi_weekly_s.iloc[-1])
        r_m = float(rsi_monthly_s.iloc[-1])

        sell_condition = (curr_price < e20) and (r_d < 50)
        signal = "🔴 SELL" if sell_condition else "🟢 HOLD"

        return {
            "Stock Name": ticker_symbol.replace(".NS", "").replace(".BO", ""),
            "Current Price": f"₹{curr_price:,.2f}",
            "Daily RSI": round(r_d, 2),
            "Weekly RSI": round(r_w, 2),
            "Monthly RSI": round(r_m, 2),
            "EMA20_Check": curr_price > e20,
            "EMA50_Check": curr_price > e50,
            "EMA100_Check": curr_price > e100,
            "EMA200_Check": curr_price > e200,
            "Signal": signal
        }
    except Exception:
        return None
