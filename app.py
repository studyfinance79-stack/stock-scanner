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
# GITHUB API & STOCK LIST SYNC FUNCTIONS
# ==========================================
def load_stocks():
  """Loads stock list from session state, stocks.json, or defaults."""
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
  """Pushes the updated stock list directly to stocks.json on GitHub."""
  st.session_state.stocks = updated_stock_list

  # Update local file if accessible
  try:
    with open("stocks.json", "w") as f:
      json.dump(updated_stock_list, f, indent=2)
  except Exception:
    pass

  # Fetch GitHub credentials from Streamlit Secrets
  token = st.secrets.get("GITHUB_TOKEN")
  repo = st.secrets.get("REPO_NAME", "studyfinance79-stack/stock-scanner")

  if not token:
    st.warning(
        "⚠️ GITHUB_TOKEN not found in Streamlit Secrets. Stock list updated"
        " locally for this session only."
    )
    return

  url = f"https://api.github.com/repos/{repo}/contents/stocks.json"
  headers = {
      "Authorization": f"token {token}",
      "Accept": "application/vnd.github.v3+json",
  }

  try:
    # 1. Fetch current file SHA (required by GitHub API for updates)
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None

    # 2. Encode JSON content
    content_bytes = json.dumps(updated_stock_list, indent=2).encode("utf-8")
    content_b64 = base64.b64encode(content_bytes).decode("utf-8")

    # 3. Commit updated stocks.json to GitHub
    payload = {
        "message": "Update stocks.json via Streamlit Web UI",
        "content": content_b64,
    }
    if sha:
      payload["sha"] = sha

    put_res = requests.put(url, headers=headers, json=payload)
    if put_res.status_code in [200, 201]:
      st.toast("Synced with GitHub! Telegram alerts updated.", icon="✅")
    else:
      st.error(
          f"GitHub Sync Failed ({put_res.status_code}): {put_res.json().get('message')}"
      )
  except Exception as e:
    st.error(f"Error syncing with GitHub: {e}")


# Initialize current stocks
current_stocks = load_stocks()


# ==========================================
# TECHNICAL ANALYSIS CALCULATIONS
# ==========================================
def calculate_rsi(series, period=14):
  """Calculates Relative Strength Index (RSI)."""
  delta = series.diff()
  gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
  loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
  rs = gain / loss
  return 100 - (100 / (1 + rs))


@st.cache_data(ttl=300)
def fetch_stock_metrics(ticker):
  """Fetches price history and computes Multi-Timeframe RSI & EMAs."""
  try:
    df_daily = yf.download(
        ticker, period="1y", interval="1d", progress=False, auto_adjust=True
    )
    if df_daily.empty or len(df_daily) < 50:
      return None

    # Clean multi-index columns if present
    if isinstance(df_daily.columns, pd.MultiIndex):
      df_daily.columns = df_daily.columns.get_level_values(0)

    close_d = df_daily["Close"]
    latest_price = float(close_d.iloc[-1])

    # Daily EMAs
    ema20 = float(close_d.ewm(span=20, adjust=False).mean().iloc[-1])
    ema50 = float(close_d.ewm(span=50, adjust=False).mean().iloc[-1])
    ema100 = float(close_d.ewm(span=100, adjust=False).mean().iloc[-1])
    ema200 = float(close_d.ewm(span=200, adjust=False).mean().iloc[-1])

    # Daily RSI
    daily_rsi = float(calculate_rsi(close_d).iloc[-1])

    # Weekly RSI
    df_weekly = close_d.resample("W").last()
    weekly_rsi = float(calculate_rsi(df_weekly).iloc[-1])

    # Monthly RSI
    df_monthly = close_d.resample("M").last()
    monthly_rsi = float(calculate_rsi(df_monthly).iloc[-1])

    # Signal Logic
    if daily_rsi < 50 and latest_price < ema20:
      signal = "🔴 SELL"
    elif daily_rsi > 50 and latest_price > ema20:
      signal = "🟢 HOLD"
    else:
      signal = "🟡 NEUTRAL"

    return {
        "Stock Name": ticker.replace(".NS", ""),
        "Price": f"₹{latest_price:,.2f}",
        "Daily RSI": round(daily_rsi, 2),
        "Weekly RSI": round(weekly_rsi, 2),
        "Monthly RSI": round(monthly_rsi, 2),
        "> EMA 20": "🟢 YES" if latest_price > ema20 else "🔴 NO",
        "> EMA 50": "🟢 YES" if latest_price > ema50 else "🔴 NO",
        "> EMA 100": "🟢 YES" if latest_price > ema100 else "🔴 NO",
        "> EMA 200": "🟢 YES" if latest_price > ema200 else "🔴 NO",
        "Signal": signal,
    }
  except Exception:
    return None


# ==========================================
# CUSTOM STYLING (GOLDEN HONEYCOMB THEME)
# ==========================================
st.markdown(
    """
<style>
    .main { background-color: #0d0f12; }
    .main-title { text-align: center; color: #ffb703; font-size: 2.2rem; font-weight: 800; margin-bottom: 0px; }
    .sub-title { text-align: center; color: #a0a0a0; font-size: 0.95rem; margin-bottom: 25px; }
    .styled-table { width: 100%; border-collapse: collapse; margin-top: 15px; color: #e0e0e0; font-family: sans-serif; }
    .styled-table th { background-color: #1a1e24; color: #ffb703; text-align: center; padding: 10px; font-weight: bold; border-bottom: 2px solid #ffb703; }
    .styled-table td { padding: 10px; text-align: center; border-bottom: 1px solid #22272e; }
    @media only screen and (max-width: 600px) {
        .styled-table th, .styled-table td { padding: 6px 3px !important; font-size: 0.75rem !important; }
        .main-title { font-size: 1.5rem !important; }
    }
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

# ==========================================
# CONTROLS & STOCK MANAGER
# ==========================================
col_theme, col_add = st.columns([1, 1])

with col_theme:
  theme = st.selectbox(
      "🎨 Select UI Theme Presentation:", ["Golden Honeycomb", "Dark Slate"]
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

# Stock Removal Expander
with st.expander("📌 Stock List & Removal Manager", expanded=True):
  cols = st.columns(6)
  stocks_to_remove = []

  for idx, symbol in enumerate(current_stocks):
    col_idx = idx % 6
    display_name = symbol.replace(".NS", "")
    with cols[col_idx]:
      if st.button(f"❌ {display_name}", key=f"del_{symbol}"):
        stocks_to_remove.append(symbol)

  if stocks_to_remove:
    updated_list = [s for s in current_stocks if s not in stocks_to_remove]
    sync_stocks_to_github(updated_list)
    st.rerun()

# ==========================================
# SCAN EXECUTION & TABLE DISPLAY
# ==========================================
progress_bar = st.progress(0)
st.info("Technical scan completed 100%!")

table_data = []
for i, ticker in enumerate(current_stocks):
  data = fetch_stock_metrics(ticker)
  if data:
    data["#"] = len(table_data) + 1
    table_data.append(data)
  progress_bar.progress((i + 1) / len(current_stocks))

progress_bar.empty()

if table_data:
  df_display = pd.DataFrame(table_data)
  # Reorder columns
  cols_order = [
      "#",
      "Stock Name",
      "Price",
      "Daily RSI",
      "Weekly RSI",
      "Monthly RSI",
      "> EMA 20",
      "> EMA 50",
      "> EMA 100",
      "> EMA 200",
      "Signal",
  ]
  df_display = df_display[cols_order]

  # Render HTML table with responsive mobile container
  st.markdown(
      '<div style="overflow-x:auto;">'
      + df_display.to_html(index=False, classes="styled-table", escape=False)
      + "</div>",
      unsafe_allow_html=True,
  )
else:
  st.warning("No stock data available. Add symbols above to begin scanning.")
