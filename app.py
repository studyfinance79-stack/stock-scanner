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
# GITHUB API & PERSISTENCE
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
# TECHNICAL ANALYSIS ENGINE
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
def fetch_stock_metrics(ticker):
  try:
    stk = yf.Ticker(ticker)
    df_daily = stk.history(period="1y", interval="1d")

    if df_daily.empty:
      df_daily = yf.download(
          ticker, period="1y", interval="1d", progress=False
      )

    if df_daily.empty:
      return None

    if isinstance(df_daily.columns, pd.MultiIndex):
      df_daily.columns = df_daily.columns.get_level_values(0)

    close_d = df_daily["Close"]
    if isinstance(close_d, pd.DataFrame):
      close_d = close_d.iloc[:, 0]
    close_d = close_d.dropna()

    if len(close_d) < 20:
      return None

    latest_price = float(close_d.iloc[-1])

    # EMAs
    ema20 = float(
        close_d.ewm(span=20, adjust=False).mean().iloc[-1]
        if len(close_d) >= 20
        else np.nan
    )
    ema50 = float(
        close_d.ewm(span=50, adjust=False).mean().iloc[-1]
        if len(close_d) >= 50
        else np.nan
    )
    ema100 = float(
        close_d.ewm(span=100, adjust=False).mean().iloc[-1]
        if len(close_d) >= 100
        else np.nan
    )
    ema200 = float(
        close_d.ewm(span=200, adjust=False).mean().iloc[-1]
        if len(close_d) >= 200
        else np.nan
    )

    # RSIs
    daily_rsi_s = calculate_rsi(close_d)
    daily_rsi = (
        float(daily_rsi_s.iloc[-1]) if not daily_rsi_s.empty else np.nan
    )

    df_weekly = close_d.resample("W").last().dropna()
    weekly_rsi_s = calculate_rsi(df_weekly)
    weekly_rsi = (
        float(weekly_rsi_s.iloc[-1]) if not weekly_rsi_s.empty else np.nan
    )

    df_monthly = close_d.resample("ME").last().dropna()
    if len(df_monthly) < 14:
      df_monthly = close_d.resample("M").last().dropna()
    monthly_rsi_s = calculate_rsi(df_monthly)
    monthly_rsi = (
        float(monthly_rsi_s.iloc[-1]) if not monthly_rsi_s.empty else np.nan
    )

    # Signal logic
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

    def fmt_ema(ema_val):
      if np.isnan(ema_val):
        return "N/A"
      return "🟢 YES" if latest_price > ema_val else "🔴 NO"

    return {
        "Stock Name": ticker.replace(".NS", "").replace(".BO", ""),
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
    }
  except Exception:
    return None


# ==========================================
# CONTROLS & DYNAMIC THEMES
# ==========================================
col_theme, col_add = st.columns([1, 1])

with col_theme:
  theme_choice = st.selectbox(
      "🎨 Select UI Theme Presentation:",
      ["Golden Honeycomb", "Dark Slate", "Cyberpunk Neon", "Emerald Forest"],
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

# Theme Palette Map
THEMES = {
    "Golden Honeycomb": {
        "bg": "#0d0f12",
        "card": "#181b20",
        "accent": "#ffb703",
        "border": "#ffb703",
        "text": "#e0e0e0",
    },
    "Dark Slate": {
        "bg": "#121212",
        "card": "#1e1e1e",
        "accent": "#90caf9",
        "border": "#424242",
        "text": "#ffffff",
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

active_theme = THEMES.get(theme_choice, THEMES["Golden Honeycomb"])

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

# Stock Manager Expander
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
# SCAN EXECUTION & TABLE DISPLAY
# ==========================================
progress_bar = st.progress(0)

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

  st.markdown(
      '<div style="overflow-x:auto;">'
      + df_display.to_html(index=False, classes="styled-table", escape=False)
      + "</div>",
      unsafe_allow_html=True,
  )
else:
  st.warning("No stock data available. Add symbols above to begin scanning.")
