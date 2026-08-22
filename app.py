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
    page_title="Pro Technical Stock Scanner 8K", page_icon="⚡", layout="wide"
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
          "RELIANCE.NS",
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
# CONTROLS & DYNAMIC UI THEME ENGINE (HD 8K)
# ==========================================
col_theme, col_add = st.columns([1, 1])

with col_theme:
  theme_choice = st.selectbox(
      "🎨 Select UI Theme Presentation:",
      [
          "Dark Cyber Neon",
          "Obsidian Glass",
          "Golden Honeycomb",
          "Emerald Forest",
      ],
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
    "Dark Cyber Neon": {
        "bg": "#07090e",
        "card": "#0f172a",
        "accent": "#38bdf8",
        "border": "rgba(56, 189, 248, 0.3)",
        "text": "#f8fafc",
    },
    "Obsidian Glass": {
        "bg": "#121212",
        "card": "#1e1e1e",
        "accent": "#90caf9",
        "border": "#333333",
        "text": "#ffffff",
    },
    "Golden Honeycomb": {
        "bg": "#0c0d0e",
        "card": "#181a1d",
        "accent": "#fbbf24",
        "border": "rgba(251, 191, 36, 0.3)",
        "text": "#f3f4f6",
    },
    "Emerald Forest": {
        "bg": "#04130e",
        "card": "#0a261d",
        "accent": "#34d399",
        "border": "rgba(52, 211, 153, 0.3)",
        "text": "#f0fdf4",
    },
}

active_theme = THEMES.get(theme_choice, THEMES["Dark Cyber Neon"])

st.markdown(
    f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}
    
    .stApp {{ background-color: {active_theme['bg']}; }}
    
    .main-title {{ 
        text-align: center; 
        color: {active_theme['accent']}; 
        font-size: 2.3rem; 
        font-weight: 800; 
        letter-spacing: -0.5px;
        margin-bottom: 2px; 
        text-shadow: 0 0 20px {active_theme['accent']}44;
    }}
    .sub-title {{ 
        text-align: center; 
        color: #94a3b8; 
        font-size: 0.92rem; 
        font-weight: 600;
        margin-bottom: 25px; 
    }}
    
    /* GLASSMORPHISM TABLE STYLING */
    .styled-table {{ 
        width: 100%; 
        border-collapse: separate; 
        border-spacing: 0; 
        margin-top: 15px; 
        color: {active_theme['text']}; 
        background: {active_theme['card']};
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid {active_theme['border']};
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .styled-table th {{ 
        background-color: rgba(255, 255, 255, 0.03); 
        color: {active_theme['accent']}; 
        text-align: center; 
        padding: 14px 10px; 
        font-weight: 700; 
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 2px solid {active_theme['border']}; 
    }}
    .styled-table td {{ 
        padding: 12px 10px; 
        text-align: center; 
        font-size: 0.88rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05); 
    }}
    .styled-table tr:hover {{
        background-color: rgba(255, 255, 255, 0.03);
    }}
    
    /* GLOWING LED BADGES */
    .led-green {{
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid #10b981;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
        border-radius: 20px;
        padding: 3px 10px;
        font-weight: 700;
        font-size: 0.78rem;
        display: inline-block;
    }}
    .led-red {{
        background: rgba(239, 68, 68, 0.15);
        color: #fca5a5;
        border: 1px solid #ef4444;
        box-shadow: 0 0 10px rgba(239, 68, 68, 0.3);
        border-radius: 20px;
        padding: 3px 10px;
        font-weight: 700;
        font-size: 0.78rem;
        display: inline-block;
    }}
    .led-yellow {{
        background: rgba(245, 158, 11, 0.15);
        color: #fde047;
        border: 1px solid #f59e0b;
        box-shadow: 0 0 10px rgba(245, 158, 11, 0.3);
        border-radius: 20px;
        padding: 3px 10px;
        font-weight: 700;
        font-size: 0.78rem;
        display: inline-block;
    }}
    
    .tv-link {{
        color: {active_theme['accent']};
        font-weight: 700;
        text-decoration: none;
        transition: all 0.2s ease;
    }}
    .tv-link:hover {{
        text-decoration: underline;
        filter: brightness(1.2);
    }}

    @media only screen and (max-width: 768px) {{
        .styled-table th, .styled-table td {{ padding: 8px 4px !important; font-size: 0.72rem !important; }}
        .main-title {{ font-size: 1.6rem !important; }}
    }}
</style>
""",
    unsafe_allow_html=True,
)

# Header
st.markdown(
    '<div class="main-title">⚡ PRO TECHNICAL STOCK SCANNER HD</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-title">Multi-Timeframe RSI, Moving Averages, Daily'
    " Supertrend & ADX LED Analytics</div>",
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
# INDICATOR CALCULATION ENGINE
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


def calculate_supertrend(df, period=10, multiplier=3):
  if df is None or len(df) < period + 1:
    return "N/A", '<span class="led-red">🔴 BEARISH</span>'

  high = df["High"].copy()
  low = df["Low"].copy()
  close = df["Close"].copy()

  tr1 = high - low
  tr2 = (high - close.shift(1)).abs()
  tr3 = (low - close.shift(1)).abs()
  tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
  atr = tr.ewm(alpha=1 / period, adjust=False).mean()

  hl2 = (high + low) / 2
  basic_ub = hl2 + (multiplier * atr)
  basic_lb = hl2 - (multiplier * atr)

  final_ub = basic_ub.copy()
  final_lb = basic_lb.copy()

  for i in range(1, len(df)):
    if (
        basic_ub.iloc[i] < final_ub.iloc[i - 1]
        or close.iloc[i - 1] > final_ub.iloc[i - 1]
    ):
      final_ub.iloc[i] = basic_ub.iloc[i]
    else:
      final_ub.iloc[i] = final_ub.iloc[i - 1]

    if (
        basic_lb.iloc[i] > final_lb.iloc[i - 1]
        or close.iloc[i - 1] < final_lb.iloc[i - 1]
    ):
      final_lb.iloc[i] = basic_lb.iloc[i]
    else:
      final_lb.iloc[i] = final_lb.iloc[i - 1]

  st_val = pd.Series(index=df.index, dtype=float)
  st_dir = pd.Series(index=df.index, dtype=bool)

  for i in range(1, len(df)):
    if close.iloc[i] > final_ub.iloc[i - 1]:
      st_dir.iloc[i] = True
    elif close.iloc[i] < final_lb.iloc[i - 1]:
      st_dir.iloc[i] = False
    else:
      st_dir.iloc[i] = st_dir.iloc[i - 1] if i > 1 else True

    st_val.iloc[i] = (
        final_lb.iloc[i] if st_dir.iloc[i] else final_ub.iloc[i]
    )

  is_bullish = st_dir.iloc[-1]
  latest_st = st_val.iloc[-1]

  if np.isnan(latest_st):
    return "N/A", '<span class="led-yellow">🟡 NEUTRAL</span>'

  val_str = f"₹{latest_st:,.1f}"
  status_html = (
      '<span class="led-green">🟢 BULLISH</span>'
      if is_bullish
      else '<span class="led-red">🔴 BEARISH</span>'
  )
  return val_str, status_html


def calculate_adx(df, period=14):
  if df is None or len(df) < period * 2:
    return "N/A", '<span class="led-yellow">🟡 WEAK</span>'

  high = df["High"]
  low = df["Low"]
  close = df["Close"]

  up_move = high.diff()
  down_move = -low.diff()

  plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
  minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

  tr1 = high - low
  tr2 = (high - close.shift(1)).abs()
  tr3 = (low - close.shift(1)).abs()
  tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

  tr_smoothed = tr.ewm(alpha=1 / period, adjust=False).mean()
  plus_di = (
      100
      * (
          pd.Series(plus_dm, index=df.index)
          .ewm(alpha=1 / period, adjust=False)
          .mean()
          / tr_smoothed
      )
  )
  minus_di = (
      100
      * (
          pd.Series(minus_dm, index=df.index)
          .ewm(alpha=1 / period, adjust=False)
          .mean()
          / tr_smoothed
      )
  )

  dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
  adx = dx.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]

  if np.isnan(adx):
    return "N/A", '<span class="led-yellow">🟡 WEAK</span>'

  val_str = f"{adx:.1f}"
  if adx >= 25:
    status_html = '<span class="led-green">🟢 STRONG</span>'
  elif adx >= 20:
    status_html = '<span class="led-yellow">🟡 MODERATE</span>'
  else:
    status_html = '<span class="led-red">🔴 WEAK</span>'

  return val_str, status_html


@st.cache_data(ttl=300)
def fetch_batch_data(tickers):
  """Downloads 2 years of complete stock OHLC data in one batch."""
  try:
    df = yf.download(
        tickers=tickers,
        period="2y",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        progress=False,
    )
    return df
  except Exception:
    return None


def extract_stock_df(ticker, batch_df):
  """Extracts full OHLC DataFrame for a ticker."""
  if batch_df is not None and not batch_df.empty:
    try:
      if isinstance(batch_df.columns, pd.MultiIndex):
        if ticker in batch_df.columns.levels[0]:
          sub = batch_df[ticker].dropna(subset=["Close"])
          if not sub.empty:
            return sub
      else:
        if "Close" in batch_df.columns:
          sub = batch_df.dropna(subset=["Close"])
          if not sub.empty:
            return sub
    except Exception:
      pass

  try:
    stk = yf.Ticker(ticker)
    hist = stk.history(period="2y", interval="1d")
    if not hist.empty and "Close" in hist.columns:
      return hist.dropna(subset=["Close"])
  except Exception:
    pass

  return None


# ==========================================
# SCANNER EXECUTION
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

  stock_df = extract_stock_df(ticker, batch_df)

  if stock_df is not None and len(stock_df) >= 20:
    close_s = stock_df["Close"]
    latest_price = float(close_s.iloc[-1])

    # Moving Averages
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

    # RSIs
    daily_rsi_s = calculate_rsi(close_s)
    daily_rsi = (
        float(daily_rsi_s.iloc[-1]) if not daily_rsi_s.empty else np.nan
    )

    df_weekly = close_s.groupby(close_s.index.to_period("W")).last().dropna()
    weekly_rsi_s = calculate_rsi(df_weekly)
    weekly_rsi = (
        float(weekly_rsi_s.iloc[-1]) if not weekly_rsi_s.empty else np.nan
    )

    df_monthly = close_s.groupby(close_s.index.to_period("M")).last().dropna()
    monthly_rsi_s = calculate_rsi(df_monthly)
    monthly_rsi = (
        float(monthly_rsi_s.iloc[-1]) if not monthly_rsi_s.empty else np.nan
    )

    # Supertrend & ADX (Daily)
    st_val_str, st_status_html = calculate_supertrend(stock_df)
    adx_val_str, adx_status_html = calculate_adx(stock_df)

    # Overall Signal Logic
    if (
        not np.isnan(daily_rsi)
        and not np.isnan(ema20)
        and daily_rsi < 50
        and latest_price < ema20
    ):
      signal_html = '<span class="led-red">🔴 SELL</span>'
    elif (
        not np.isnan(daily_rsi)
        and not np.isnan(ema20)
        and daily_rsi > 50
        and latest_price > ema20
    ):
      signal_html = '<span class="led-green">🟢 HOLD</span>'
    else:
      signal_html = '<span class="led-yellow">🟡 NEUTRAL</span>'

    def fmt_ema(val):
      if np.isnan(val):
        return '<span class="led-yellow">N/A</span>'
      return (
          '<span class="led-green">🟢 YES</span>'
          if latest_price > val
          else '<span class="led-red">🔴 NO</span>'
      )

    # TradingView Direct Link
    tv_url = f"https://in.tradingview.com/chart/?symbol=NSE:{clean_name}"
    tv_link_html = f'<a href="{tv_url}" target="_blank" class="tv-link" title="Open TradingView Chart">📈 {clean_name}</a>'

    table_data.append({
        "#": len(table_data) + 1,
        "Stock Name": tv_link_html,
        "Price": f"₹{latest_price:,.2f}",
        "Supertrend (10,3)": f"{st_val_str} {st_status_html}",
        "ADX (14)": f"{adx_val_str} {adx_status_html}",
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
        "Signal": signal_html,
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
