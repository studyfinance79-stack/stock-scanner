import base64
import json
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Pro Technical Stock Scanner 8K AI", page_icon="⚡", layout="wide"
)


# ==========================================
# 2. GITHUB API & STOCK LIST SYNC
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
# 3. DYNAMIC ULTRA-HD THEME ENGINE
# ==========================================
DIAMOND_SVG = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEwIDAgTDIwIDEwIEwxMCAyMCBMMCAxMCBaIiBmaWxsPSJub25lIiBzdHJva2U9InJnYmEoMjU1LDI1NSwyNTUsMC4wOCkiIHN0cm9rZS13aWR0aD0iMSIvPjwvc3ZnPg=="
HONEYCOMB_SVG = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iNDEuNTciIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEyIDBMMjQgNi45M1YyMC43OEwxMiAyNy43MUwwIDIwLjc4VjYuOTNMMTIgMFpNMTIgNDEuNTdMMjQgMzQuNjRWMjAuNzhMMTIgMjcuNzFMMCAyMC43OFYzNC42NEwxMiA0MS41N1oiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjA2KSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9zdmc+"
RHOMBUS_SVG = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAiIGhlaWdodD0iMzAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTAgMTUgTDE1IDAgTDMwIDE1IEwxNSAzMCBaIiBmaWxsPSJub25lIiBzdHJva2U9InJnYmEoMjU1LDI1NSwyNTUsMC4wNykiIHN0cm9rZS13aWR0aD0iMSIvPjwvc3ZnPg=="

THEMES = {
    "Dark Navy Blue (Diamond Pattern)": {
        "bg": "#0a1128",
        "card": "#101f42",
        "text": "#f8fafc",
        "accent": "#38bdf8",
        "grid": "#1e3a8a",
        "th_bg": "#1e293b",
        "texture": DIAMOND_SVG,
    },
    "Dark Bottle Green (Emerald Texture)": {
        "bg": "#031e16",
        "card": "#09382a",
        "text": "#f0fdf4",
        "accent": "#34d399",
        "grid": "#059669",
        "th_bg": "#064e3b",
        "texture": HONEYCOMB_SVG,
    },
    "Dark Grey Obsidian (Rhombus Grid)": {
        "bg": "#121316",
        "card": "#1c1e24",
        "text": "#ffffff",
        "accent": "#60a5fa",
        "grid": "#374151",
        "th_bg": "#282c34",
        "texture": RHOMBUS_SVG,
    },
    "24K Metallic Gold (Contrast Dark)": {
        "bg": "#d4af37",
        "card": "#fef3c7",
        "text": "#1e1b4b",
        "accent": "#854d0e",
        "grid": "#b45309",
        "th_bg": "#fde68a",
        "texture": DIAMOND_SVG,
    },
    "Metallic Silver (High Contrast)": {
        "bg": "#cbd5e1",
        "card": "#f1f5f9",
        "text": "#0f172a",
        "accent": "#1e293b",
        "grid": "#64748b",
        "th_bg": "#e2e8f0",
        "texture": RHOMBUS_SVG,
    },
    "Metallic Copper (Warm Texture)": {
        "bg": "#2a1810",
        "card": "#42281d",
        "text": "#ffedd5",
        "accent": "#fb923c",
        "grid": "#9a3412",
        "th_bg": "#573022",
        "texture": HONEYCOMB_SVG,
    },
}

col_theme, col_add = st.columns([1.2, 1])

with col_theme:
  theme_choice = st.selectbox(
      "🎨 Select Ultra-HD Theme Presentation:", list(THEMES.keys())
  )

with col_add:
  new_symbol = st.text_input(
      "➕ Add Stock Symbol:", placeholder="e.g. TATAMOTORS, RELIANCE"
  )
  if new_symbol:
    clean_symbol = new_symbol.strip().upper()
    if not clean_symbol.endswith(".NS") and not clean_symbol.endswith(".BO"):
      clean_symbol += ".NS"

    if clean_symbol not in current_stocks:
      updated_list = current_stocks + [clean_symbol]
      sync_stocks_to_github(updated_list)
      st.rerun()

active_theme = THEMES[theme_choice]

# Inject Ultra-HD CSS Stylesheet
st.markdown(
    f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}
    
    .stApp {{ 
        background-color: {active_theme['bg']};
        background-image: url('{active_theme['texture']}');
        background-repeat: repeat;
    }}
    
    .main-title {{ 
        text-align: center; 
        color: {active_theme['accent']}; 
        font-size: 2.3rem; 
        font-weight: 900; 
        letter-spacing: -0.5px;
        margin-bottom: 2px; 
        text-shadow: 0 0 15px {active_theme['accent']}55;
    }}
    .sub-title {{ 
        text-align: center; 
        color: {active_theme['text']}; 
        opacity: 0.85;
        font-size: 0.95rem; 
        font-weight: 700;
        margin-bottom: 20px; 
    }}
    
    /* ULTRA-HD STYLED TABLE WITH THICK CONTRAST LINES */
    .styled-table {{ 
        width: 100%; 
        border-collapse: collapse !important; 
        margin-top: 15px; 
        color: {active_theme['text']}; 
        background: {active_theme['card']};
        border-radius: 8px;
        overflow: hidden;
        border: 3px solid {active_theme['grid']} !important;
        box-shadow: 0 12px 35px rgba(0,0,0,0.65);
    }}
    .styled-table th {{ 
        background-color: {active_theme['th_bg']} !important; 
        color: {active_theme['accent']} !important; 
        text-align: center; 
        padding: 12px 6px; 
        font-weight: 800; 
        font-size: 0.80rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border: 2px solid {active_theme['grid']} !important; 
    }}
    .styled-table td {{ 
        padding: 10px 4px; 
        text-align: center; 
        vertical-align: middle;
        font-size: 0.85rem;
        font-weight: 600;
        border: 2px solid {active_theme['grid']} !important; 
    }}
    
    /* LEFT ALIGNMENT FOR STOCK NAME COLUMN */
    .styled-table td:nth-child(2) {{
        text-align: left !important;
        padding-left: 14px !important;
    }}
    
    .styled-table tr:hover {{
        background-color: rgba(255, 255, 255, 0.08);
    }}
    
    /* STACKED CELL FORMATTING */
    .cell-stack {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 4px;
        padding: 2px 0;
    }}
    .val-upper {{
        font-weight: 800;
        font-size: 0.88rem;
        letter-spacing: 0.2px;
        white-space: nowrap;
    }}
    
    /* GLOWING LED BADGES */
    .led-green {{
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
        border: 1.5px solid #10b981;
        box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
        border-radius: 14px;
        padding: 2px 8px;
        font-weight: 800;
        font-size: 0.72rem;
        display: inline-block;
        white-space: nowrap;
    }}
    .led-red {{
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1.5px solid #ef4444;
        box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
        border-radius: 14px;
        padding: 2px 8px;
        font-weight: 800;
        font-size: 0.72rem;
        display: inline-block;
        white-space: nowrap;
    }}
    .led-yellow {{
        background: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
        border: 1.5px solid #f59e0b;
        box-shadow: 0 0 8px rgba(245, 158, 11, 0.4);
        border-radius: 14px;
        padding: 2px 8px;
        font-weight: 800;
        font-size: 0.72rem;
        display: inline-block;
        white-space: nowrap;
    }}
    .led-purple {{
        background: rgba(168, 85, 247, 0.25);
        color: #c084fc;
        border: 1.5px solid #a855f7;
        box-shadow: 0 0 10px rgba(168, 85, 247, 0.5);
        border-radius: 14px;
        padding: 2px 8px;
        font-weight: 900;
        font-size: 0.72rem;
        display: inline-block;
        white-space: nowrap;
    }}
    
    .tv-link {{
        color: {active_theme['accent']};
        font-weight: 800;
        text-decoration: none;
    }}
    .tv-link:hover {{
        text-decoration: underline;
    }}
    .arrow-up {{ color: #10b981; font-weight: 900; font-size: 0.92rem; }}
    .arrow-down {{ color: #ef4444; font-weight: 900; font-size: 0.92rem; }}

    @media only screen and (max-width: 768px) {{
        .styled-table th, .styled-table td {{ padding: 6px 2px !important; font-size: 0.68rem !important; }}
        .main-title {{ font-size: 1.4rem !important; }}
    }}
</style>
""",
    unsafe_allow_html=True,
)

# Header
st.markdown(
    '<div class="main-title">⚡ PRO TECHNICAL STOCK SCANNER 8K AI</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-title">Multi-Timeframe RSI, Supertrend, ADX, TradingView'
    " Exact Volume & AI Signals</div>",
    unsafe_allow_html=True,
)

# Stock Manager
with st.expander("📌 Stock List & Removal Manager", expanded=False):
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
# 4. INDICATOR ENGINE
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
    return "N/A", False, '<span class="led-red">🔴 BEARISH</span>'

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
    return "N/A", False, '<span class="led-yellow">🟡 NEUTRAL</span>'

  val_str = f"₹{latest_st:,.1f}"
  status_html = (
      '<span class="led-green">🟢 BULLISH</span>'
      if is_bullish
      else '<span class="led-red">🔴 BEARISH</span>'
  )
  return val_str, is_bullish, status_html


def calculate_adx(df, period=14):
  if df is None or len(df) < period * 2:
    return "N/A", 0, '<span class="led-yellow">🟡 WEAK</span>'

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
    return "N/A", 0, '<span class="led-yellow">🟡 WEAK</span>'

  val_str = f"{adx:.1f}"
  if adx >= 25:
    status_html = '<span class="led-green">🟢 STRONG</span>'
  elif adx >= 20:
    status_html = '<span class="led-yellow">🟡 MODERATE</span>'
  else:
    status_html = '<span class="led-red">🔴 WEAK</span>'

  return val_str, adx, status_html


# FETCH UNADJUSTED DATA TO MATCH TRADINGVIEW VOLUME EXACTLY
@st.cache_data(ttl=300)
def fetch_batch_data(tickers):
  try:
    df = yf.download(
        tickers=tickers,
        period="2y",
        interval="1d",
        group_by="ticker",
        auto_adjust=False,  # Unadjusted Volume matching TradingView
        progress=False,
    )
    return df
  except Exception:
    return None


def extract_stock_df(ticker, batch_df):
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
    hist = stk.history(period="2y", interval="1d", auto_adjust=False)
    if not hist.empty and "Close" in hist.columns:
      return hist.dropna(subset=["Close"])
  except Exception:
    pass

  return None


# ==========================================
# 5. SCANNER EXECUTION
# ==========================================
progress_bar = st.progress(0, text="Executing AI Technical Analysis (0%)...")
table_data = []

batch_df = fetch_batch_data(current_stocks)
total_stocks = len(current_stocks)


# Helper function to generate Ultra-HD Stacked Cells
def make_stacked_cell(val_upper_text, arrow_html, led_badge_html):
  return f"""
    <div class="cell-stack">
        <div class="val-upper">{val_upper_text} {arrow_html}</div>
        <div>{led_badge_html}</div>
    </div>
    """


for i, ticker in enumerate(current_stocks):
  pct = int(((i + 1) / total_stocks) * 100)
  clean_name = ticker.replace(".NS", "").replace(".BO", "")
  progress_bar.progress(
      (i + 1) / total_stocks, text=f"Analyzing {clean_name}... ({pct}%)"
  )

  stock_df = extract_stock_df(ticker, batch_df)

  if stock_df is not None and len(stock_df) >= 20:
    close_s = stock_df["Close"]
    vol_s = stock_df["Volume"]
    latest_price = float(close_s.iloc[-1])
    prev_price = float(close_s.iloc[-2]) if len(close_s) > 1 else latest_price

    price_arrow = (
        '<span class="arrow-up">📈 ⬆</span>'
        if latest_price >= prev_price
        else '<span class="arrow-down">📉 ⬇</span>'
    )
    price_badge = (
        '<span class="led-green">🟢 UP</span>'
        if latest_price >= prev_price
        else '<span class="led-red">🔴 DOWN</span>'
    )
    price_cell_html = make_stacked_cell(
        f"₹{latest_price:,.2f}", price_arrow, price_badge
    )

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

    # RSIs (Daily, Weekly, Monthly) with Direction Arrows
    daily_rsi_s = calculate_rsi(close_s)
    daily_rsi = (
        float(daily_rsi_s.iloc[-1]) if not daily_rsi_s.empty else np.nan
    )
    daily_rsi_prev = (
        float(daily_rsi_s.iloc[-2]) if len(daily_rsi_s) > 1 else daily_rsi
    )
    d_arrow = (
        '<span class="arrow-up">📈 ⬆</span>'
        if daily_rsi >= daily_rsi_prev
        else '<span class="arrow-down">📉 ⬇</span>'
    )

    df_weekly = close_s.groupby(close_s.index.to_period("W")).last().dropna()
    weekly_rsi_s = calculate_rsi(df_weekly)
    weekly_rsi = (
        float(weekly_rsi_s.iloc[-1]) if not weekly_rsi_s.empty else np.nan
    )
    weekly_rsi_prev = (
        float(weekly_rsi_s.iloc[-2]) if len(weekly_rsi_s) > 1 else weekly_rsi
    )
    w_arrow = (
        '<span class="arrow-up">📈 ⬆</span>'
        if weekly_rsi >= weekly_rsi_prev
        else '<span class="arrow-down">📉 ⬇</span>'
    )

    df_monthly = close_s.groupby(close_s.index.to_period("M")).last().dropna()
    monthly_rsi_s = calculate_rsi(df_monthly)
    monthly_rsi = (
        float(monthly_rsi_s.iloc[-1]) if not monthly_rsi_s.empty else np.nan
    )
    monthly_rsi_prev = (
        float(monthly_rsi_s.iloc[-2])
        if len(monthly_rsi_s) > 1
        else monthly_rsi
    )
    m_arrow = (
        '<span class="arrow-up">📈 ⬆</span>'
        if monthly_rsi >= monthly_rsi_prev
        else '<span class="arrow-down">📉 ⬇</span>'
    )

    # Format RSI Stacked Cells with Threshold LED rules
    def fmt_rsi_stacked(val, threshold, arrow):
      if np.isnan(val):
        return make_stacked_cell("N/A", "", '<span class="led-yellow">N/A</span>')
      val_round = round(val, 2)
      if val >= threshold:
        badge = '<span class="led-green">🟢 BULLISH</span>'
      else:
        badge = '<span class="led-red">🔴 BEARISH</span>'
      return make_stacked_cell(f"{val_round}", arrow, badge)

    daily_rsi_cell = fmt_rsi_stacked(daily_rsi, 52, d_arrow)
    weekly_rsi_cell = fmt_rsi_stacked(weekly_rsi, 60, w_arrow)
    monthly_rsi_cell = fmt_rsi_stacked(monthly_rsi, 60, m_arrow)

    # Volume Analytics
    curr_vol = float(vol_s.iloc[-1])
    prev_vol = float(vol_s.iloc[-2]) if len(vol_s) > 1 else curr_vol
    avg_vol20 = (
        float(vol_s.rolling(20).mean().iloc[-1])
        if len(vol_s) >= 20
        else curr_vol
    )

    v_arrow = (
        '<span class="arrow-up">📈 ⬆</span>'
        if curr_vol >= prev_vol
        else '<span class="arrow-down">📉 ⬇</span>'
    )

    if curr_vol >= 1.5 * avg_vol20 and curr_vol > prev_vol:
      vol_status_html = '<span class="led-purple">🔥 SPIKE</span>'
      vol_is_strong = True
    elif curr_vol > avg_vol20:
      vol_status_html = '<span class="led-green">🟢 ABOVE AVG</span>'
      vol_is_strong = True
    else:
      vol_status_html = '<span class="led-red">🔴 LOW VOL</span>'
      vol_is_strong = False

    def human_format(num):
      if num >= 1e7:
        return f"{num/1e7:.2f}Cr"
      if num >= 1e5:
        return f"{num/1e5:.2f}L"
      if num >= 1e3:
        return f"{num/1e3:.1f}k"
      return str(int(num))

    vol_cell_html = make_stacked_cell(
        human_format(curr_vol), v_arrow, vol_status_html
    )

    # Supertrend & ADX (Daily)
    st_val_str, st_is_bullish, st_status_html = calculate_supertrend(stock_df)
    st_cell_html = make_stacked_cell(st_val_str, "", st_status_html)

    adx_val_str, adx_val, adx_status_html = calculate_adx(stock_df)
    adx_prev = (
        float(calculate_adx(stock_df.iloc[:-1])[1])
        if len(stock_df) > 30
        else adx_val
    )
    adx_arrow = (
        '<span class="arrow-up">📈 ⬆</span>'
        if adx_val >= adx_prev
        else '<span class="arrow-down">📉 ⬇</span>'
    )
    adx_cell_html = make_stacked_cell(adx_val_str, adx_arrow, adx_status_html)

    # ==========================================
    # COMBINED AI MULTI-FACTOR SIGNAL MATRIX
    # ==========================================
    ai_score = 0.0

    if not np.isnan(monthly_rsi) and monthly_rsi >= 60:
      ai_score += 2.0
    if not np.isnan(weekly_rsi) and weekly_rsi >= 60:
      ai_score += 1.5
    if not np.isnan(daily_rsi) and daily_rsi >= 52:
      ai_score += 1.0
    if st_is_bullish:
      ai_score += 2.0
    if adx_val >= 25:
      ai_score += 1.5
    elif adx_val >= 20:
      ai_score += 0.8
    if vol_is_strong:
      ai_score += 1.0

    if ai_score >= 7.5:
      ai_badge = '<span class="led-purple">🚀 STRONG BUY</span>'
    elif ai_score >= 5.5:
      ai_badge = '<span class="led-green">🟢 BUY</span>'
    elif ai_score >= 3.5:
      ai_badge = '<span class="led-yellow">🟡 HOLD</span>'
    else:
      ai_badge = '<span class="led-red">🔴 WEAK / AVOID</span>'

    ai_cell_html = make_stacked_cell(f"{ai_score:.1f} / 9.0", "", ai_badge)

    def fmt_ema_cell(val):
      if np.isnan(val):
        return make_stacked_cell(
            "N/A", "", '<span class="led-yellow">N/A</span>'
        )
      val_str = f"₹{val:,.1f}"
      if latest_price > val:
        return make_stacked_cell(
            val_str, "", '<span class="led-green">🟢 YES</span>'
        )
      else:
        return make_stacked_cell(
            val_str, "", '<span class="led-red">🔴 NO</span>'
        )

    # TradingView Link
    tv_url = f"https://in.tradingview.com/chart/?symbol=NSE:{clean_name}"
    tv_link_html = f'<a href="{tv_url}" target="_blank" class="tv-link" title="Open TradingView Chart">📈 {clean_name}</a>'

    table_data.append({
        "#": len(table_data) + 1,
        "Stock Name": tv_link_html,
        "Price": price_cell_html,
        "AI Signal": ai_cell_html,
        "Avg. Vol & Spike": vol_cell_html,
        "Supertrend (10,3)": st_cell_html,
        "ADX (14)": adx_cell_html,
        "Daily RSI (≥52)": daily_rsi_cell,
        "Weekly RSI (≥60)": weekly_rsi_cell,
        "Monthly RSI (≥60)": monthly_rsi_cell,
        "> EMA 20": fmt_ema_cell(ema20),
        "> EMA 50": fmt_ema_cell(ema50),
        "> EMA 100": fmt_ema_cell(ema100),
        "> EMA 200": fmt_ema_cell(ema200),
    })

progress_bar.empty()

# Render High-Contrast Table
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
