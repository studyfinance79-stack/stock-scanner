import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# Page Configuration (Full-Width, Hidden Sidebar)
# ---------------------------------------------------------
st.set_page_config(
    page_title="HD Technical Stock Scanner",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit default UI elements
st.markdown("""
<style>
    [data-testid="collapsedControl"] { display: none; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Session State Setup
# ---------------------------------------------------------
if "stocks" not in st.session_state:
    st.session_state.stocks = [
        "AEROFLEX", "BLSE", "DATAPATTNS", "IPCALAB",
        "KANORICHEM", "MODTHREAD", "NETWEB", "PREMIERPOL", "SONACOMS"
    ]

if "selected_theme" not in st.session_state:
    st.session_state.selected_theme = "Golden Honeycomb"

# Callback for adding stocks
def add_stock_callback():
    val = st.session_state.new_stock_input.strip().upper()
    if val:
        clean_val = val.replace(".NS", "").replace(".BO", "")
        if clean_val not in st.session_state.stocks:
            st.session_state.stocks.append(clean_val)
        st.session_state.new_stock_input = ""

# ---------------------------------------------------------
# CSS Theme Engines with Background Patterns
# ---------------------------------------------------------
THEME_CSS = {
    "Golden Honeycomb": """
    <style>
        .stApp {
            background-color: #2D2103;
            background-image: radial-gradient(#F59E0B 0.8px, transparent 0.8px), radial-gradient(#F59E0B 0.8px, #2D2103 0.8px);
            background-size: 26px 26px;
            background-position: 0 0, 13px 13px;
            color: #FEF3C7;
        }
        .styled-table {
            background-color: #3D2D05 !important;
            border: 2px solid #F59E0B !important;
            color: #FEF3C7 !important;
        }
        .styled-table th {
            background-color: #523E07 !important;
            color: #FDE047 !important;
            border-bottom: 2px solid #F59E0B !important;
        }
        .styled-table td { border-bottom: 1px solid #523E07 !important; }
        .styled-table tr:hover { background-color: #664E09 !important; }
        .text-primary-header { color: #FDE047 !important; }
        .stock-link { color: #FDE047 !important; }
        .stock-link:hover { color: #38BDF8 !important; text-decoration: underline !important; }
    </style>
    """,
    "Navy Blue Honeycomb": """
    <style>
        .stApp {
            background-color: #080D1A;
            background-image: radial-gradient(#1E3A8A 0.75px, transparent 0.75px), radial-gradient(#1E3A8A 0.75px, #080D1A 0.75px);
            background-size: 30px 30px;
            background-position: 0 0, 15px 15px;
            color: #F0F9FF;
        }
        .styled-table {
            background-color: #0F172A !important;
            border: 2px solid #1E3A8A !important;
            color: #F0F9FF !important;
        }
        .styled-table th {
            background-color: #1E293B !important;
            color: #38BDF8 !important;
            border-bottom: 2px solid #1E3A8A !important;
        }
        .styled-table td { border-bottom: 1px solid #1E293B !important; }
        .styled-table tr:hover { background-color: #1E293B !important; }
        .text-primary-header { color: #38BDF8 !important; }
        .stock-link { color: #38BDF8 !important; }
        .stock-link:hover { color: #FACC15 !important; text-decoration: underline !important; }
    </style>
    """,
    "Dark Bottle Green (Ficus Motif)": """
    <style>
        .stApp {
            background-color: #041E15;
            background-image: radial-gradient(#D4AF37 0.8px, transparent 0.8px), radial-gradient(#D4AF37 0.8px, #041E15 0.8px);
            background-size: 28px 28px;
            background-position: 0 0, 14px 14px;
            color: #DCFCE7;
        }
        .styled-table {
            background-color: #0B2E21 !important;
            border: 2px solid #D4AF37 !important;
            color: #DCFCE7 !important;
        }
        .styled-table th {
            background-color: #113E2E !important;
            color: #FACC15 !important;
            border-bottom: 2px solid #D4AF37 !important;
        }
        .styled-table td { border-bottom: 1px solid #113E2E !important; }
        .styled-table tr:hover { background-color: #164E3A !important; }
        .text-primary-header { color: #FACC15 !important; }
        .stock-link { color: #FACC15 !important; }
        .stock-link:hover { color: #38BDF8 !important; text-decoration: underline !important; }
    </style>
    """,
    "Metallic Silver Rhombus": """
    <style>
        .stApp {
            background-color: #E5E7EB;
            background-image: linear-gradient(135deg, #CBD5E1 25%, transparent 25%), linear-gradient(225deg, #CBD5E1 25%, transparent 25%), linear-gradient(45deg, #CBD5E1 25%, transparent 25%), linear-gradient(315deg, #CBD5E1 25%, #E5E7EB 25%);
            background-position: 18px 0, 18px 0, 0 0, 0 0;
            background-size: 36px 36px;
            color: #0F172A;
        }
        .styled-table {
            background-color: #FFFFFF !important;
            border: 2px solid #64748B !important;
            color: #0F172A !important;
        }
        .styled-table th {
            background-color: #334155 !important;
            color: #38BDF8 !important;
            border-bottom: 2px solid #64748B !important;
        }
        .styled-table td { border-bottom: 1px solid #E2E8F0 !important; color: #0F172A !important; }
        .styled-table tr:hover { background-color: #F1F5F9 !important; }
        .text-primary-header { color: #1E3A8A !important; }
        .stock-link { color: #0284C7 !important; }
        .stock-link:hover { color: #0369A1 !important; text-decoration: underline !important; }
    </style>
    """
}

# Inject Global Core Layout Styling
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    .main-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: 1px;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        text-align: center;
        font-size: 1.05rem;
        font-weight: 500;
        margin-bottom: 1.5rem;
        opacity: 0.85;
    }
    .custom-table-container {
        width: 100%;
        overflow-x: auto;
        margin-top: 1rem;
        border-radius: 10px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Inter', -apple-system, sans-serif;
        font-size: 0.92rem;
    }
    .styled-table th {
        padding: 14px 12px;
        text-align: center !important;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .styled-table td {
        padding: 12px 10px;
        text-align: center !important;
        vertical-align: middle;
    }
    .stock-link {
        text-decoration: none;
        font-weight: 700;
        transition: all 0.2s ease-in-out;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    .led-yes {
        background-color: rgba(34, 197, 94, 0.2);
        color: #22C55E;
        border: 1px solid #22C55E;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 700;
        display: inline-block;
        font-size: 0.85rem;
    }
    .led-no {
        background-color: rgba(239, 68, 68, 0.2);
        color: #EF4444;
        border: 1px solid #EF4444;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 700;
        display: inline-block;
        font-size: 0.85rem;
    }
    .badge-hold {
        background-color: rgba(34, 197, 94, 0.25);
        color: #22C55E;
        border: 1px solid #22C55E;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 800;
        display: inline-block;
    }
    .badge-sell {
        background-color: rgba(239, 68, 68, 0.25);
        color: #EF4444;
        border: 1px solid #EF4444;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 800;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Top Header Control Bar
# ---------------------------------------------------------
st.markdown("<div class='main-title text-primary-header'>⚡ PRO TECHNICAL STOCK SCANNER</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>HD Multi-Timeframe RSI & Moving Average LED Analytics</div>", unsafe_allow_html=True)

top_col1, top_col2 = st.columns([2, 1])

with top_col1:
    st.session_state.selected_theme = st.selectbox(
        "🎨 Select UI Theme Presentation:",
        options=list(THEME_CSS.keys()),
        index=list(THEME_CSS.keys()).index(st.session_state.selected_theme)
    )

# Inject Selected Theme CSS
st.markdown(THEME_CSS[st.session_state.selected_theme], unsafe_allow_html=True)

with top_col2:
    st.text_input(
        "➕ Add Stock Symbol (Press Enter):",
        key="new_stock_input",
        placeholder="e.g. TATAMOTORS, RELIANCE, INFY",
        on_change=add_stock_callback
    )

st.markdown("---")

# ---------------------------------------------------------
# Stock Deletion & Management Bar
# ---------------------------------------------------------
if st.session_state.stocks:
    with st.expander("📌 Stock List & Removal Manager (Check to remove stocks)", expanded=False):
        to_delete = []
        cols = st.columns(6)
        for idx, symbol in enumerate(st.session_state.stocks):
            col_idx = idx % 6
            if cols[col_idx].checkbox(f"❌ {symbol}", key=f"del_{symbol}"):
                to_delete.append(symbol)
        
        if to_delete:
            if st.button("🗑️ Delete Selected Stocks", type="secondary"):
                st.session_state.stocks = [s for s in st.session_state.stocks if s not in to_delete]
                st.rerun()

# ---------------------------------------------------------
# Pine Script Compliant Technical Indicators Engine
# ---------------------------------------------------------
def calculate_tv_rsi(series, period=14):
    """
    Exact replica of TradingView Pine Script ta.rma / RSI calculation.
    """
    if len(series) <= period:
        return pd.Series(50.0, index=series.index)

    delta = series.diff()
    gain = delta.where(delta > 0, 0.0).to_numpy()
    loss = (-delta.where(delta < 0, 0.0)).to_numpy()

    rma_gain = np.zeros_like(gain)
    rma_loss = np.zeros_like(loss)

    # Seed initial values using SMA of the first 14 periods (matching TV ta.rma)
    rma_gain[period] = np.mean(gain[1:period+1])
    rma_loss[period] = np.mean(loss[1:period+1])

    alpha = 1.0 / period
    for i in range(period + 1, len(gain)):
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
        df_daily = yf.download(ticker, period="3y", interval="1d", progress=False)
        if df_daily.empty or len(df_daily) < 30:
            return None

        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily = df_daily.xs(ticker, axis=1, level=1)

        close_daily = df_daily['Close']

        # Exponential Moving Averages
        e20 = float(close_daily.ewm(span=20, adjust=False).mean().iloc[-1])
        e50 = float(close_daily.ewm(span=50, adjust=False).mean().iloc[-1])
        e100 = float(close_daily.ewm(span=100, adjust=False).mean().iloc[-1])
        e200 = float(close_daily.ewm(span=200, adjust=False).mean().iloc[-1])

        # Exact TradingView RSIs across timeframes
        rsi_daily_s = calculate_tv_rsi(close_daily, 14)

        close_weekly = close_daily.resample('W-FRI').last().dropna()
        rsi_weekly_s = calculate_tv_rsi(close_weekly, 14)

        close_monthly = close_daily.resample('ME').last().dropna()
        rsi_monthly_s = calculate_tv_rsi(close_monthly, 14)

        curr_price = float(close_daily.iloc[-1])

        r_d = float(rsi_daily_s.iloc[-1])
        r_w = float(rsi_weekly_s.iloc[-1]) if len(rsi_weekly_s) > 0 else 0.0
        r_m = float(rsi_monthly_s.iloc[-1]) if len(rsi_monthly_s) > 0 else 0.0

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

# ---------------------------------------------------------
# Scan Trigger & Table Render
# ---------------------------------------------------------
if st.button("🚀 Run Technical Scan", type="primary", use_container_width=True):
    if not st.session_state.stocks:
        st.warning("⚠️ Tracked stock list is empty. Add stock symbols above.")
    else:
        with st.spinner("Fetching live market technicals..."):
            results = []
            for symbol in st.session_state.stocks:
                data = fetch_stock_data(symbol)
                if data:
                    results.append(data)

        if results:
            table_rows = []
            for idx, row in enumerate(results, start=1):
                badge_cls = "badge-sell" if "SELL" in row["Signal"] else "badge-hold"
                
                # TradingView Chart Link
                stock_name = row['Stock Name']
                tv_chart_url = f"https://www.tradingview.com/chart/?symbol=NSE:{stock_name}&interval=D"
                stock_link_html = f"<a href='{tv_chart_url}' target='_blank' class='stock-link' title='Click to open {stock_name} Daily Chart on TradingView'>📈 {stock_name} ↗</a>"

                led_20 = '<span class="led-yes">🟢 YES</span>' if row["EMA20_Check"] else '<span class="led-no">🔴 NO</span>'
                led_50 = '<span class="led-yes">🟢 YES</span>' if row["EMA50_Check"] else '<span class="led-no">🔴 NO</span>'
                led_100 = '<span class="led-yes">🟢 YES</span>' if row["EMA100_Check"] else '<span class="led-no">🔴 NO</span>'
                led_200 = '<span class="led-yes">🟢 YES</span>' if row["EMA200_Check"] else '<span class="led-no">🔴 NO</span>'

                table_rows.append(
                    f"<tr>"
                    f"<td><strong>{idx}</strong></td>"
                    f"<td>{stock_link_html}</td>"
                    f"<td><strong>{row['Current Price']}</strong></td>"
                    f"<td>{row['Daily RSI']}</td>"
                    f"<td>{row['Weekly RSI']}</td>"
                    f"<td>{row['Monthly RSI']}</td>"
                    f"<td>{led_20}</td>"
                    f"<td>{led_50}</td>"
                    f"<td>{led_100}</td>"
                    f"<td>{led_200}</td>"
                    f"<td><span class='{badge_cls}'>{row['Signal']}</span></td>"
                    f"</tr>"
                )

            rows_str = "".join(table_rows)
            
            table_html = (
                '<div class="custom-table-container">'
                '<table class="styled-table">'
                '<thead>'
                '<tr>'
                '<th>Serial No.</th>'
                '<th>Stock Name (TradingView)</th>'
                '<th>Current Price</th>'
                '<th>Daily RSI</th>'
                '<th>Weekly RSI</th>'
                '<th>Monthly RSI</th>'
                '<th>Price > EMA 20</th>'
                '<th>Price > EMA 50</th>'
                '<th>Price > EMA 100</th>'
                '<th>Price > EMA 200</th>'
                '<th>Signal</th>'
                '</tr>'
                '</thead>'
                f'<tbody>{rows_str}</tbody>'
                '</table>'
                '</div>'
            )

            st.markdown(table_html, unsafe_allow_html=True)
            st.write("")
            st.success(f"✅ Successfully scanned {len(results)} stock(s). RSI values match TradingView `ta.rma` formulas.")
        else:
            st.error("No stock data could be retrieved. Check ticker symbols.")
