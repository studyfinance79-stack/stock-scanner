import base64
import json
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Pro Technical Stock Scanner", page_icon="⚡", layout="wide"
)


# ==========================================
# GITHUB API & STOCK LIST SYNC
# ==========================================
def load_stocks():
  if "stocks" not in st.session_state:
    try:
      with open("stocks.json", "r") as f:
        st.session_state.stocks = json.load(f)
    except Exception:
      st.session_state.stocks = [
          "APARINDS.NS",
          "AEROFLEX.NS",
          "BLSE.NS",
          "DATAPATTNS.NS",
          "IPCALAB.NS",
          "KANORICHEM.NS",
          "MODTHREAD.NS",
          "NETWEB.NS",
          "PREMIERPOL.NS",
          "SONACOMS.NS",
      ]
  return st.session_state.stocks


def sync_stocks_to_github(updated_stock_list):
  st.session_state.stocks = updated_stock_list

  try:
    with open("stocks.json", "w") as f:
      json.dump(updated_stock_list, f, indent=2)
  except Exception:
    pass

  token = st.secrets.get("GITHUB_TOKEN")
  repo = st.secrets.get("REPO_NAME", "studyfinance79-stack/stock-scanner")

  if not token:
    st.toast("Updated locally for this session.", icon="ℹ️")
    return

  url = f"https://api.github.com/repos/{repo}/contents/stocks.json"
  headers = {
      "Authorization": f"token {token}",
      "Accept": "application/vnd.github.v3+json",
  }

  try:
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None

    content_bytes = json.dumps(updated_stock_list, indent=2).encode("utf-8")
    content_b64 = base64.b64encode(content_bytes).decode("utf-8")

    payload = {
        "message": "Update stocks.json via Streamlit Web UI",
        "content": content_b64,
    }
    if sha:
      payload["sha"] = sha

    put_res = requests.put(url, headers=headers, json=payload)
    if put_res.status_code in [200, 201]:
      st.toast("Synced with GitHub! Telegram alerts updated.", icon="✅")
  except Exception:
    pass


current_stocks = load_stocks()

# ==========================================
# CONTROLS & DYNAMIC UI THEME ENGINE
# ==========================================
col_theme, col_add = st.columns([1, 1])

with col_theme:
  theme_choice = st.selectbox(
      "🎨 Select UI Theme Presentation:",
      ["Dark Slate", "Golden Honeycomb", "Cyberpunk Neon", "Emerald Forest"],
  )

with col_add:
  new_symbol = st.text_input(
      "➕ Add Stock Symbol (Auto-Refreshes):",
      placeholder="e.g. TATAMOTORS, RELIANCE",
  )
  if new_symbol:
    clean_symbol = new_symbol.strip().upper()
    if not clean_symbol.endswith(".NS") and not clean_symbol.endswith(".BO"):
      clean_symbol += ".NS"

    if clean_symbol not in current_stocks:
      updated_list = current_stocks + [clean_symbol]
      sync_stocks_to_github(updated_list)
      st.rerun()
    else:
      st.info(f"{clean_symbol.replace('.NS', '')} is already in your list.")

THEMES = {
    "Dark Slate": {
        "bg": "#121212",
        "card": "#1e1e1e",
        "accent": "#90caf9",
        "border": "#424242",
        "text": "#ffffff",
    },
    "Golden Honeycomb": {
        "bg": "#0d0f12",
        "card": "#181b20",
        "accent": "#ffb703",
        "border": "#ffb703",
        "text": "#e0e0e0",
    },
    "Cyberpunk Neon": {
        "bg": "#0a0a12",
        "card": "#121225",
        "accent": "#00f5d4",
        "border": "#f72585",
        "text": "#f8f9fa",
    },
    "Emerald Forest": {
        "bg": "#061a14",
        "card": "#0c2d23",
        "accent": "#2ec4b6",
        "border": "#10b981",
        "text": "#e8f5e9",
    },
}

active_theme = THEMES.get(theme_choice, THEMES["Dark Slate"])

st.markdown(
    f"""
<style>
    .stApp {{ background-color: {active_theme['bg']}; }}
    .main-title {{ text-align: center; color: {active_theme['accent']}; font-size: 2.2rem; font-weight: 800; margin-bottom: 0px; }}
    .sub-title {{ text-align: center; color: #a0a0a0; font-size: 0.95rem; margin-bottom: 25px; }}
    .styled-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; color: {active_theme['text']}; font-family: sans-serif; }}
    .styled-table th {{ background-color: {active_theme['card']}; color: {active_theme['accent']}; text-align: center; padding: 12px; font-weight: bold; border-bottom: 2px solid {active_theme['border']}; }}
    .styled-table td {{ padding: 10px; text-align: center; border-bottom: 1px solid #22272e; }}
    @media only screen and (max-width: 600px) {{
        .styled-table th, .styled-table td {{ padding: 6px 3px !important; font-size: 0.75rem !important; }}
        .main-title {{ font-size: 1.5rem !important; }}
    }}
</style>
""",
    unsafe_allow_html=True,
)

# Header
st.markdown(
    '<div class="main-title">⚡ PRO TECHNICAL STOCK SCANNER</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-title">HD Multi-Timeframe RSI & Moving Average LED'
    " Analytics</div>",
    unsafe_allow_html=True,
)

# Stock Manager
with st.expander("📌 Stock List & Removal Manager", expanded=True):
  cols = st.columns(6)
  stocks_to_remove = []

  for idx, symbol in enumerate(current_stocks):
    col_idx = idx % 6
    display_name = symbol.replace(".NS", "").replace(".BO", "")
    with cols[col_idx]:
      if st.button(f"❌ {display_name}", key=f"del_{symbol}"):
        stocks_to_remove.append(symbol)

  if stocks_to_remove:
    updated_list = [s for s in current_stocks if s not in stocks_to_remove]
    sync_stocks_to_github(updated_list)
    st.rerun()


# ==========================================
# TECHNICAL CALCULATIONS & BATCH SCANNER
# ==========================================
def calculate_rsi(series, period=14):
  if len(series) < period + 1:
    return pd.Series([np.nan] * len(series), index=series.index)
  delta = series.diff()
  gain = delta.where(delta > 0, 0.0)
  loss = -delta.where(delta < 0, 0.0)
  avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
  avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
  rs = avg_gain / avg_loss
  return 100 - (100 / (1 + rs))


@st.cache_data(ttl=300)
def fetch_batch_data(tickers):
  """Downloads all stock data in one fast batch to prevent server rate blocks."""
  try:
    df = yf.download(
        tickers=tickers,
        period="1y",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        progress=False,
    )
    return df
  except Exception:
    return None


def extract_stock_series(ticker, batch_df):
  """Extracts price series from batch or falls back to individual fetch."""
  if batch_df is not None and not batch_df.empty:
    try:
      if isinstance(batch_df.columns, pd.MultiIndex):
        if ticker in batch_df.columns.levels[0]:
          sub = batch_df[ticker]["Close"].dropna()
          if not sub.empty:
            return sub
      else:
        if "Close" in batch_df.columns:
          sub = batch_df["Close"].dropna()
          if not sub.empty:
            return sub
    except Exception:
      pass

  try:
    stk = yf.Ticker(ticker)
    hist = stk.history(period="1y", interval="1d")
    if not hist.empty and "Close" in hist.columns:
      return hist["Close"].dropna()
  except Exception:
    pass

  return None


# ==========================================
# SCANNER EXECUTION & PERCENTAGE COUNTER
# ==========================================
progress_bar = st.progress(0, text="Initializing Market Scanner (0%)...")
table_data = []

batch_df = fetch_batch_data(current_stocks)
total_stocks = len(current_stocks)

for i, ticker in enumerate(current_stocks):
  pct = int(((i + 1) / total_stocks) * 100)
  clean_name = ticker.replace(".NS", "").replace(".BO", "")
  progress_bar.progress(
      (i + 1) / total_stocks, text=f"Scanning {clean_name}... ({pct}%)"
  )

  close_s = extract_stock_series(ticker, batch_df)

  if close_s is not None and len(close_s) >= 20:
    latest_price = float(close_s.iloc[-1])

    ema20 = float(
        close_s.ewm(span=20, adjust=False).mean().iloc[-1]
        if len(close_s) >= 20
        else np.nan
    )
    ema50 = float(
        close_s.ewm(span=50, adjust=False).mean().iloc[-1]
        if len(close_s) >= 50
        else np.nan
    )
    ema100 = float(
        close_s.ewm(span=100, adjust=False).mean().iloc[-1]
        if len(close_s) >= 100
        else np.nan
    )
    ema200 = float(
        close_s.ewm(span=200, adjust=False).mean().iloc[-1]
        if len(close_s) >= 200
        else np.nan
    )

    # Daily RSI
    daily_rsi_s = calculate_rsi(close_s)
    daily_rsi = (
        float(daily_rsi_s.iloc[-1]) if not daily_rsi_s.empty else np.nan
    )

    # Weekly RSI (grouped by week period)
    df_weekly = close_s.groupby(close_s.index.to_period("W")).last().dropna()
    weekly_rsi_s = calculate_rsi(df_weekly)
    weekly_rsi = (
        float(weekly_rsi_s.iloc[-1]) if not weekly_rsi_s.empty else np.nan
    )

    # Monthly RSI (grouped by month period)
    df_monthly = close_s.groupby(close_s.index.to_period("M")).last().dropna()
    monthly_rsi_s = calculate_rsi(df_monthly)
    monthly_rsi = (
        float(monthly_rsi_s.iloc[-1]) if not monthly_rsi_s.empty else np.nan
    )

    if (
        not np.isnan(daily_rsi)
        and not np.isnan(ema20)
        and daily_rsi < 50
        and latest_price < ema20
    ):
      signal = "🔴 SELL"
    elif (
        not np.isnan(daily_rsi)
        and not np.isnan(ema20)
        and daily_rsi > 50
        and latest_price > ema20
    ):
      signal = "🟢 HOLD"
    else:
      signal = "🟡 NEUTRAL"

    def fmt_ema(val):
      if np.isnan(val):
        return "N/A"
      return "🟢 YES" if latest_price > val else "🔴 NO"

    table_data.append({
        "#": len(table_data) + 1,
        "Stock Name": clean_name,
        "Price": f"₹{latest_price:,.2f}",
        "Daily RSI": (
            round(daily_rsi, 2) if not np.isnan(daily_rsi) else "N/A"
        ),
        "Weekly RSI": (
            round(weekly_rsi, 2) if not np.isnan(weekly_rsi) else "N/A"
        ),
        "Monthly RSI": (
            round(monthly_rsi, 2) if not np.isnan(monthly_rsi) else "N/A"
        ),
        "> EMA 20": fmt_ema(ema20),
        "> EMA 50": fmt_ema(ema50),
        "> EMA 100": fmt_ema(ema100),
        "> EMA 200": fmt_ema(ema200),
        "Signal": signal,
    })

progress_bar.empty()

# Render Table
if table_data:
  df_display = pd.DataFrame(table_data)
  st.markdown(
      '<div style="overflow-x:auto;">'
      + df_display.to_html(index=False, classes="styled-table", escape=False)
      + "</div>",
      unsafe_allow_html=True,
  )
else:
  st.warning("No stock data available. Add symbols above to begin scanning.")
