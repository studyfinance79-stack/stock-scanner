import numpy as np
import pandas as pd
import yfinance as yf

def calculate_tv_rsi(series, period=14):
    """
    Exact replica of TradingView Pine Script ta.rma / RSI calculation.
    """
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0).to_numpy()
    loss = (-delta.where(delta < 0, 0.0)).to_numpy()

    # Wilder's Smoothing (ta.rma) implementation with SMA initialization
    def ta_rma(x, n):
        out = np.full_like(x, np.nan)
        # Seed initial value with Simple Moving Average (SMA) of first n gains/losses
        out[n] = np.mean(x[1:n+1])
        alpha = 1.0 / n
        for i in range(n + 1, len(x)):
            out[i] = alpha * x[i] + (1.0 - alpha) * out[i - 1]
        return out

    avg_gain = ta_rma(gain, period)
    avg_loss = ta_rma(loss, period)

    # Calculate RS and RSI
    with np.errstate(divide='ignore', invalid='ignore'):
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        
        # Handle zero-loss edge cases matching Pine Script logic
        rsi[avg_loss == 0] = 100.0
        rsi[avg_gain == 0] = 0.0

    return pd.Series(rsi, index=series.index)


def fetch_stock_data(ticker_symbol):
    ticker = ticker_symbol if ("." in ticker_symbol) else f"{ticker_symbol}.NS"
    try:
        # Fetch 5 years to ensure zero warm-up drift against TradingView
        df_daily = yf.download(ticker, period="5y", interval="1d", progress=False)
        if df_daily.empty or len(df_daily) < 50:
            return None

        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily = df_daily.xs(ticker, axis=1, level=1)

        close_daily = df_daily['Close']

        # 1. Daily RSI
        rsi_daily_s = calculate_tv_rsi(close_daily, 14)

        # 2. Weekly RSI (Resampled to Friday week-ending for NSE)
        close_weekly = close_daily.resample('W-FRI').last().dropna()
        rsi_weekly_s = calculate_tv_rsi(close_weekly, 14)

        # 3. Monthly RSI
        close_monthly = close_daily.resample('ME').last().dropna()
        rsi_monthly_s = calculate_tv_rsi(close_monthly, 14)

        curr_price = float(close_daily.iloc[-1])
        
        # Exponential Moving Averages
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
