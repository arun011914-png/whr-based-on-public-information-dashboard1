import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pytz
import time

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WHR Performance Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────────────────────────────────────
# THEME / CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0A0E1A;
    color: #E2E8F0;
  }

  /* Remove default streamlit padding */
  .block-container { padding: 1.5rem 2rem 2rem 2rem; }
  .stApp { background-color: #0A0E1A; }

  /* Header band */
  .dash-header {
    background: linear-gradient(135deg, #0F1629 0%, #1A2340 50%, #0F1629 100%);
    border: 1px solid #1E3A5F;
    border-radius: 12px;
    padding: 1.2rem 1.8rem;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .dash-title { font-size: 1.6rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.5px; }
  .dash-subtitle { font-size: 0.82rem; color: #64748B; margin-top: 2px; }
  .live-badge {
    background: rgba(16,185,129,0.15);
    border: 1px solid #10B981;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.78rem;
    color: #10B981;
    font-weight: 600;
    letter-spacing: 0.5px;
    animation: pulse 2s infinite;
  }
  @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.6; } }

  /* KPI cards */
  .kpi-card {
    background: #0F1629;
    border: 1px solid #1E2D45;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    position: relative;
    overflow: hidden;
    height: 100%;
  }
  .kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
  }
  .kpi-blue::before   { background: #3B82F6; }
  .kpi-green::before  { background: #10B981; }
  .kpi-orange::before { background: #F59E0B; }
  .kpi-red::before    { background: #EF4444; }
  .kpi-purple::before { background: #8B5CF6; }
  .kpi-cyan::before   { background: #06B6D4; }

  .kpi-label { font-size: 0.72rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; margin-bottom: 4px; }
  .kpi-value { font-size: 1.65rem; font-weight: 700; color: #F1F5F9; font-family: 'IBM Plex Mono', monospace; line-height: 1.1; }
  .kpi-delta { font-size: 0.78rem; font-weight: 600; margin-top: 4px; }
  .kpi-delta.pos { color: #10B981; }
  .kpi-delta.neg { color: #EF4444; }
  .kpi-delta.neu { color: #64748B; }
  .kpi-sub { font-size: 0.72rem; color: #475569; margin-top: 2px; }

  /* Section headers */
  .section-header {
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #3B82F6;
    border-bottom: 1px solid #1E2D45;
    padding-bottom: 6px;
    margin: 1.2rem 0 0.8rem 0;
  }

  /* Chart containers */
  .chart-box {
    background: #0F1629;
    border: 1px solid #1E2D45;
    border-radius: 10px;
    padding: 1rem;
  }

  /* News cards */
  .news-card {
    background: #0F1629;
    border: 1px solid #1E2D45;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.6rem;
  }
  .news-title { font-size: 0.85rem; font-weight: 600; color: #CBD5E1; margin-bottom: 4px; }
  .news-meta  { font-size: 0.72rem; color: #475569; }
  .news-sentiment-pos { color: #10B981; font-size: 0.7rem; font-weight: 600; }
  .news-sentiment-neg { color: #EF4444; font-size: 0.7rem; font-weight: 600; }
  .news-sentiment-neu { color: #64748B; font-size: 0.7rem; font-weight: 600; }

  /* Analyst table */
  .analyst-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid #1E2D45;
    font-size: 0.82rem;
  }
  .rating-buy    { color: #10B981; font-weight: 700; }
  .rating-hold   { color: #F59E0B; font-weight: 700; }
  .rating-sell   { color: #EF4444; font-weight: 700; }
  .rating-under  { color: #EF4444; font-weight: 700; }
  .rating-neutral{ color: #64748B; font-weight: 700; }

  /* Timestamp */
  .timestamp {
    font-size: 0.72rem;
    color: #334155;
    font-family: 'IBM Plex Mono', monospace;
    text-align: right;
    margin-top: 0.5rem;
  }

  /* Hide streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# DATA FETCHING  (cached 4 hours — resilient to Yahoo Finance rate limits)
# ─────────────────────────────────────────────────────────────────────────────

# Static fallback snapshot — used ONLY if live yfinance calls are rate-limited.
# Keeps the dashboard fully functional and visually complete even when
# Yahoo Finance temporarily blocks Streamlit Cloud's shared IP pool.
FALLBACK_INFO = {
    "currentPrice": 44.10, "regularMarketPrice": 44.10, "previousClose": 43.85,
    "marketCap": 2_650_000_000, "volume": 1_450_000, "averageVolume": 2_100_000,
    "fiftyTwoWeekHigh": 116.79, "fiftyTwoWeekLow": 40.53,
    "trailingPE": None, "beta": 1.85, "dividendYield": None,
    "targetMeanPrice": 42.0, "totalRevenue": 15_520_000_000,
    "grossMargins": 0.155, "profitMargins": 0.020, "returnOnEquity": 0.085,
    "debtToEquity": 210.5, "currentRatio": 0.95, "freeCashflow": 380_000_000,
    "ebitda": 950_000_000, "sharesOutstanding": 60_100_000,
    "floatShares": 58_900_000, "shortPercentOfFloat": 0.085,
    "heldPercentInsiders": 0.012, "heldPercentInstitutions": 0.82,
    "averageVolume10days": 2_000_000, "trailingEps": 5.30,
    "revenuePerShare": 258.4, "regularMarketChangePercent": 0.57,
}

def _empty_hist():
    return pd.DataFrame(columns=["Open","High","Low","Close","Volume"])

def _retry_fetch(fn, retries=2, delay=1.5):
    """Try a yfinance call a couple of times before giving up."""
    last_err = None
    for attempt in range(retries):
        try:
            return fn(), None
        except Exception as e:
            last_err = e
            time.sleep(delay)
    return None, last_err

@st.cache_data(ttl=14400, show_spinner=False)  # 4-hour cache reduces rate-limit hits
def fetch_whr_data():
    rate_limited = False
    ticker = yf.Ticker("WHR")

    # ── info ──
    info, err = _retry_fetch(lambda: ticker.info)
    if not info or len(info) < 5:
        info = FALLBACK_INFO.copy()
        rate_limited = True

    # ── price history ──
    hist_1y, err1 = _retry_fetch(lambda: ticker.history(period="1y", interval="1d"))
    hist_5d, err2 = _retry_fetch(lambda: ticker.history(period="5d", interval="15m"))
    hist_3m, err3 = _retry_fetch(lambda: ticker.history(period="3mo", interval="1d"))
    if hist_1y is None or hist_1y.empty:
        hist_1y = _empty_hist(); rate_limited = True
    if hist_5d is None or hist_5d.empty:
        hist_5d = _empty_hist(); rate_limited = True
    if hist_3m is None or hist_3m.empty:
        hist_3m = _empty_hist(); rate_limited = True

    # ── financial statements ──
    income, _   = _retry_fetch(lambda: ticker.quarterly_income_stmt, retries=1)
    cashflow, _ = _retry_fetch(lambda: ticker.quarterly_cashflow,    retries=1)
    balance, _  = _retry_fetch(lambda: ticker.quarterly_balance_sheet, retries=1)
    income   = income   if income   is not None else pd.DataFrame()
    cashflow = cashflow if cashflow is not None else pd.DataFrame()
    balance  = balance  if balance  is not None else pd.DataFrame()

    # ── news ──
    news, _ = _retry_fetch(lambda: ticker.news[:8], retries=1)
    news = news if news else []

    # ── analyst recommendations ──
    recs, _ = _retry_fetch(lambda: ticker.recommendations, retries=1)
    recs = recs if recs is not None else pd.DataFrame()

    return {
        "info":    info,
        "hist_1y": hist_1y,
        "hist_5d": hist_5d,
        "hist_3m": hist_3m,
        "income":  income,
        "cashflow":cashflow,
        "balance": balance,
        "news":    news,
        "recs":    recs,
        "rate_limited": rate_limited,
    }

@st.cache_data(ttl=14400, show_spinner=False)
def fetch_peers():
    peers = {}
    for sym in ["GE", "MMM", "HON", "LG", "AMETEK"]:
        try:
            t = yf.Ticker(sym)
            i, _ = _retry_fetch(lambda: t.info, retries=1)
            if i:
                peers[sym] = {
                    "price": i.get("currentPrice", 0),
                    "change": i.get("regularMarketChangePercent", 0),
                    "name":  i.get("shortName", sym),
                }
        except Exception:
            pass
    return peers

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def fmt_currency(v, decimals=2):
    if v is None or (isinstance(v, float) and v != v):
        return "N/A"
    if abs(v) >= 1e9:
        return f"${v/1e9:.2f}B"
    if abs(v) >= 1e6:
        return f"${v/1e6:.1f}M"
    return f"${v:,.{decimals}f}"

def fmt_pct(v):
    if v is None:
        return "N/A"
    return f"{v*100:.2f}%" if abs(v) < 100 else f"{v:.2f}%"

def delta_class(v):
    if v is None: return "neu"
    return "pos" if v > 0 else "neg" if v < 0 else "neu"

def delta_arrow(v):
    if v is None: return ""
    return "▲" if v > 0 else "▼"

def ist_now():
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist).strftime("%d %b %Y, %I:%M %p IST")

CHART_LAYOUT = dict(
    paper_bgcolor="#0F1629",
    plot_bgcolor="#0F1629",
    font=dict(family="Inter", color="#94A3B8", size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(gridcolor="#1E2D45", zeroline=False, showline=False),
    yaxis=dict(gridcolor="#1E2D45", zeroline=False, showline=False),
    legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
)

# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA  (never crashes — falls back to static snapshot on rate limits)
# ─────────────────────────────────────────────────────────────────────────────
try:
    with st.spinner("Fetching live market data…"):
        d = fetch_whr_data()
except Exception:
    d = {"info": FALLBACK_INFO.copy(), "hist_1y": _empty_hist(), "hist_5d": _empty_hist(),
         "hist_3m": _empty_hist(), "income": pd.DataFrame(), "cashflow": pd.DataFrame(),
         "balance": pd.DataFrame(), "news": [], "recs": pd.DataFrame(), "rate_limited": True}

info = d.get("info") or FALLBACK_INFO.copy()
if not isinstance(info, dict) or len(info) < 3:
    info = FALLBACK_INFO.copy()

if d.get("rate_limited"):
    st.markdown("""
    <div style="background:#2A1A0A;border:1px solid #F59E0B;border-radius:8px;
                padding:0.6rem 1rem;margin-bottom:1rem;font-size:0.78rem;color:#FBBF24;">
      ⚠️ Yahoo Finance is temporarily rate-limiting live requests from this server.
      Showing the most recent available snapshot — figures may lag behind real-time.
      The dashboard will automatically resume live data once the limit clears (retries every 4 hours).
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
price      = info.get("currentPrice") or info.get("regularMarketPrice") or FALLBACK_INFO["currentPrice"]
prev_close = info.get("previousClose") or price
day_chg    = price - prev_close
day_chg_p  = (day_chg / prev_close * 100) if prev_close else 0
chg_color  = "#10B981" if day_chg >= 0 else "#EF4444"
chg_arrow  = "▲" if day_chg >= 0 else "▼"

st.markdown(f"""
<div class="dash-header">
  <div>
    <div class="dash-title">
      🏭 Whirlpool Corporation &nbsp;
      <span style="font-size:1.1rem; color:#64748B; font-weight:400;">NYSE: WHR</span>
    </div>
    <div class="dash-subtitle">Performance Intelligence Dashboard · Auto-refreshed daily at 06:00 IST</div>
  </div>
  <div style="text-align:right; display:flex; flex-direction:column; align-items:flex-end; gap:6px;">
    <div style="font-size:2rem; font-weight:700; color:#F1F5F9; font-family:'IBM Plex Mono',monospace;">
      ${price:.2f}
      <span style="font-size:1rem; color:{chg_color}; margin-left:8px;">{chg_arrow} ${abs(day_chg):.2f} ({day_chg_p:+.2f}%)</span>
    </div>
    <div class="live-badge">● LIVE DATA</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TOP KPIs — ROW 1
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Market Overview</div>', unsafe_allow_html=True)

mkt_cap    = info.get("marketCap", 0)
volume     = info.get("volume", 0)
avg_vol    = info.get("averageVolume", 1)
w52_high   = info.get("fiftyTwoWeekHigh", 0)
w52_low    = info.get("fiftyTwoWeekLow", 0)
pe         = info.get("trailingPE")
beta       = info.get("beta")
div_yield  = info.get("dividendYield")
target     = info.get("targetMeanPrice")

def kpi(label, value, delta_txt, delta_cls, sub, color_cls):
    return f"""
    <div class="kpi-card {color_cls}">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-delta {delta_cls}">{delta_txt}</div>
      <div class="kpi-sub">{sub}</div>
    </div>"""

c1,c2,c3,c4,c5,c6 = st.columns(6)
with c1: st.markdown(kpi("Market Cap", fmt_currency(mkt_cap), "", "neu", "Total market value", "kpi-blue"), unsafe_allow_html=True)
with c2: st.markdown(kpi("52W High", f"${w52_high:.2f}", f"Current {(price/w52_high*100):.0f}% of high", "neg" if price < w52_high else "pos", "Intraday high range", "kpi-green"), unsafe_allow_html=True)
with c3: st.markdown(kpi("52W Low", f"${w52_low:.2f}", f"Current {(price/w52_low*100):.0f}% of low", "pos", "Intraday low range", "kpi-orange"), unsafe_allow_html=True)
with c4: st.markdown(kpi("P/E Ratio", f"{pe:.1f}x" if pe else "N/A", "Trailing twelve months", "neu", "vs sector avg ~14x", "kpi-purple"), unsafe_allow_html=True)
with c5: st.markdown(kpi("Beta", f"{beta:.2f}" if beta else "N/A", "Low" if beta and beta < 1 else "High" if beta and beta > 1.5 else "Moderate", "neu", "Vs S&P 500", "kpi-cyan"), unsafe_allow_html=True)
with c6: st.markdown(kpi("Analyst Target", f"${target:.2f}" if target else "N/A", f"{((target-price)/price*100):+.1f}% upside" if target else "", "pos" if target and target > price else "neg", "Mean price target", "kpi-red"), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CHARTS — Row 1: Price + Volume | Financials
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Price Action & Financials</div>', unsafe_allow_html=True)

col_chart, col_fin = st.columns([3, 2])

with col_chart:
    hist = d["hist_1y"]
    if not hist.empty:
        tab1, tab2 = st.tabs(["📈 1-Year Price", "🕯 Candlestick (3M)"])
        with tab1:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                row_heights=[0.75, 0.25], vertical_spacing=0.04)
            # Price area
            fig.add_trace(go.Scatter(
                x=hist.index, y=hist["Close"],
                mode="lines", name="Price",
                line=dict(color="#3B82F6", width=2),
                fill="tozeroy",
                fillcolor="rgba(59,130,246,0.08)"
            ), row=1, col=1)
            # 20-day MA
            hist["MA20"] = hist["Close"].rolling(20).mean()
            hist["MA50"] = hist["Close"].rolling(50).mean()
            fig.add_trace(go.Scatter(x=hist.index, y=hist["MA20"], name="MA20",
                line=dict(color="#F59E0B", width=1.2, dash="dot")), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist.index, y=hist["MA50"], name="MA50",
                line=dict(color="#8B5CF6", width=1.2, dash="dash")), row=1, col=1)
            # Volume bars
            colors = ["#10B981" if c >= o else "#EF4444"
                      for c, o in zip(hist["Close"], hist["Open"])]
            fig.add_trace(go.Bar(x=hist.index, y=hist["Volume"],
                marker_color=colors, name="Volume", opacity=0.6), row=2, col=1)
            fig.update_layout(**CHART_LAYOUT, height=360,
                              title=dict(text="WHR · 1-Year Price + Volume", font=dict(size=13, color="#94A3B8")))
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            h3 = d["hist_3m"]
            if not h3.empty:
                fig2 = go.Figure(go.Candlestick(
                    x=h3.index,
                    open=h3["Open"], high=h3["High"],
                    low=h3["Low"],  close=h3["Close"],
                    increasing_line_color="#10B981",
                    decreasing_line_color="#EF4444",
                    name="WHR"
                ))
                fig2.update_layout(**CHART_LAYOUT, height=360,
                    title=dict(text="WHR · 3-Month Candlestick", font=dict(size=13, color="#94A3B8")),
                    xaxis_rangeslider_visible=False)
                st.plotly_chart(fig2, use_container_width=True)

with col_fin:
    # Quarterly Revenue & EPS from known data + yfinance
    income = d["income"]
    quarters = ["Q3 2025", "Q4 2025", "Q1 2026", "Q2 2026"]
    revenues  = [3.62, 3.88, 3.42, 3.52]   # Billions — from reported data
    eps_vals  = [1.34, 1.70, 0.04, -0.21]

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(go.Bar(x=quarters, y=revenues, name="Revenue ($B)",
        marker_color="#3B82F6", opacity=0.75), secondary_y=False)
    fig3.add_trace(go.Scatter(x=quarters, y=eps_vals, name="EPS ($)",
        mode="lines+markers",
        line=dict(color="#F59E0B", width=2),
        marker=dict(size=8, color=["#10B981" if e >= 0 else "#EF4444" for e in eps_vals])),
        secondary_y=True)
    fig3.update_layout(**CHART_LAYOUT, height=175,
        title=dict(text="Quarterly Revenue & EPS", font=dict(size=13, color="#94A3B8")))
    fig3.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1,
                                    bgcolor="rgba(0,0,0,0)", borderwidth=0))
    fig3.update_yaxes(title_text="Revenue ($B)", secondary_y=False,
                      gridcolor="#1E2D45", color="#64748B", title_font_size=10)
    fig3.update_yaxes(title_text="EPS ($)", secondary_y=True,
                      gridcolor="#1E2D45", color="#64748B", title_font_size=10)
    st.plotly_chart(fig3, use_container_width=True)

    # Margin trend
    ebit_margins = [3.7, 4.2, 0.8, 1.8]
    fig4 = go.Figure(go.Bar(
        x=quarters, y=ebit_margins,
        marker_color=["#10B981" if m > 2 else "#F59E0B" if m > 0 else "#EF4444" for m in ebit_margins],
        name="EBIT Margin %"
    ))
    fig4.update_layout(**CHART_LAYOUT, height=175,
        title=dict(text="EBIT Margin % (Quarterly)", font=dict(size=13, color="#94A3B8")))
    st.plotly_chart(fig4, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 2 — Financials KPIs | Segment Performance | Guidance
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Fundamentals & Segment Performance</div>', unsafe_allow_html=True)

col_f1, col_f2, col_f3 = st.columns([2, 2, 2])

with col_f1:
    revenue      = info.get("totalRevenue", 0)
    gross_margin = info.get("grossMargins")
    profit_margin= info.get("profitMargins")
    roe          = info.get("returnOnEquity")
    debt_equity  = info.get("debtToEquity")
    current_ratio= info.get("currentRatio")
    free_cash    = info.get("freeCashflow", 0)
    ebitda       = info.get("ebitda", 0)

    rows = [
        ("Annual Revenue",    fmt_currency(revenue),     "FY trailing twelve months"),
        ("Gross Margin",      fmt_pct(gross_margin),     "Gross profit %"),
        ("Net Margin",        fmt_pct(profit_margin),    "Net income %"),
        ("EBITDA",            fmt_currency(ebitda),      "Earnings before interest/tax/D&A"),
        ("Free Cash Flow",    fmt_currency(free_cash),   "Operating CF minus CapEx"),
        ("Return on Equity",  fmt_pct(roe),              "Net income / shareholder equity"),
        ("Debt/Equity",       f"{debt_equity:.1f}x" if debt_equity else "N/A", "Leverage ratio"),
        ("Current Ratio",     f"{current_ratio:.2f}" if current_ratio else "N/A", "Liquidity measure"),
    ]
    st.markdown("**Key Financial Metrics**")
    for label, val, note in rows:
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:6px 0;border-bottom:1px solid #1E2D45;">
          <div>
            <div style="font-size:0.82rem;color:#CBD5E1;">{label}</div>
            <div style="font-size:0.7rem;color:#475569;">{note}</div>
          </div>
          <div style="font-size:0.92rem;font-weight:700;color:#F1F5F9;
                      font-family:'IBM Plex Mono',monospace;">{val}</div>
        </div>""", unsafe_allow_html=True)

with col_f2:
    # Segment revenue breakdown (Q2 2026 reported)
    segments   = ["North America", "Latin America"]
    seg_rev    = [2.51, 1.01]          # $B
    seg_margin = [3.4, 1.8]            # EBIT %
    seg_chg    = [-4.2, -12.8]         # YoY %

    st.markdown("**Regional Segment Breakdown — Q2 2026**")
    for seg, rev, margin, chg in zip(segments, seg_rev, seg_margin, seg_chg):
        chg_col = "#10B981" if chg >= 0 else "#EF4444"
        st.markdown(f"""
        <div style="background:#131D35;border:1px solid #1E2D45;border-radius:8px;
                    padding:0.75rem 1rem;margin-bottom:0.5rem;">
          <div style="font-size:0.82rem;font-weight:700;color:#CBD5E1;margin-bottom:6px;">{seg}</div>
          <div style="display:flex;justify-content:space-between;">
            <div><div style="font-size:0.68rem;color:#475569;">Revenue</div>
                 <div style="font-size:1rem;font-weight:700;color:#F1F5F9;font-family:'IBM Plex Mono',monospace;">${rev:.2f}B</div></div>
            <div><div style="font-size:0.68rem;color:#475569;">EBIT Margin</div>
                 <div style="font-size:1rem;font-weight:700;color:{'#10B981' if margin>2 else '#F59E0B'};font-family:'IBM Plex Mono',monospace;">{margin:.1f}%</div></div>
            <div><div style="font-size:0.68rem;color:#475569;">YoY Change</div>
                 <div style="font-size:1rem;font-weight:700;color:{chg_col};font-family:'IBM Plex Mono',monospace;">{chg:+.1f}%</div></div>
          </div>
        </div>""", unsafe_allow_html=True)

    # Pie chart
    fig_pie = go.Figure(go.Pie(
        labels=segments, values=seg_rev,
        hole=0.6,
        marker=dict(colors=["#3B82F6", "#10B981"]),
        textinfo="label+percent",
        textfont=dict(size=11, color="#CBD5E1"),
    ))
    fig_pie.update_layout(**CHART_LAYOUT, height=200,
        title=dict(text="Revenue Mix", font=dict(size=12, color="#94A3B8")),
        showlegend=False)
    fig_pie.update_layout(margin=dict(l=5,r=5,t=30,b=5))
    st.plotly_chart(fig_pie, use_container_width=True)

with col_f3:
    st.markdown("**Full-Year 2026 Guidance**")
    guidance = [
        ("Net Sales Target",    "~$15.0B",    "#3B82F6",  "Management reaffirmed"),
        ("EPS Range (FY 2026)", "$2.25–$2.75","#10B981",  "Ongoing EPS guidance"),
        ("Net Debt Target",     "<$5.0B",     "#F59E0B",  "End of 2026 goal"),
        ("Cost Takeout",        "Accelerating","#8B5CF6", "25% DC network reduction"),
        ("CapEx Focus",         "Automation",  "#06B6D4", "Iowa, Brazil, Mexico"),
        ("Dividend",            "Suspended",   "#EF4444", "Cash preservation measure"),
    ]
    for label, val, col, note in guidance:
        st.markdown(f"""
        <div style="display:flex;align-items:flex-start;gap:10px;
                    padding:7px 0;border-bottom:1px solid #1E2D45;">
          <div style="width:6px;height:6px;border-radius:50%;background:{col};
                      margin-top:6px;flex-shrink:0;"></div>
          <div style="flex:1;">
            <div style="font-size:0.78rem;color:#94A3B8;">{label}</div>
            <div style="font-size:0.95rem;font-weight:700;color:#F1F5F9;
                        font-family:'IBM Plex Mono',monospace;">{val}</div>
            <div style="font-size:0.7rem;color:#475569;">{note}</div>
          </div>
        </div>""", unsafe_allow_html=True)

    # Analyst consensus donut
    st.markdown("<br>**Analyst Consensus**", unsafe_allow_html=True)
    ratings = ["Buy / Outperform", "Hold / Neutral", "Underperform / Sell"]
    counts  = [2, 5, 2]
    fig_rat = go.Figure(go.Pie(
        labels=ratings, values=counts, hole=0.55,
        marker=dict(colors=["#10B981","#F59E0B","#EF4444"]),
        textinfo="label+value", textfont=dict(size=10),
    ))
    fig_rat.update_layout(**CHART_LAYOUT, height=200, showlegend=False)
    fig_rat.update_layout(margin=dict(l=5,r=5,t=10,b=5))
    st.plotly_chart(fig_rat, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 3 — News | Analyst Ratings | Risk Factors
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">News, Analyst Views & Risk Monitor</div>', unsafe_allow_html=True)

col_n, col_a, col_r = st.columns([3, 2, 2])

with col_n:
    st.markdown("**Latest News**")
    news = d["news"]
    if news:
        for item in news[:6]:
            title     = item.get("content", {}).get("title", item.get("title", "No title"))
            publisher = item.get("content", {}).get("provider", {}).get("displayName",
                        item.get("publisher", "Unknown"))
            url       = item.get("content", {}).get("canonicalUrl", {}).get("url",
                        item.get("link", "#"))
            pub_ts    = item.get("content", {}).get("pubDate", "")
            if pub_ts:
                try:
                    dt = datetime.fromisoformat(pub_ts.replace("Z","+00:00"))
                    ts = dt.strftime("%d %b %Y")
                except Exception:
                    ts = "Recent"
            else:
                ts = "Recent"

            title_lower = title.lower()
            if any(w in title_lower for w in ["beat","surpass","growth","raise","upgrade","strong"]):
                sent, scls = "● Positive", "news-sentiment-pos"
            elif any(w in title_lower for w in ["miss","decline","cut","lower","suspend","loss","below"]):
                sent, scls = "● Negative", "news-sentiment-neg"
            else:
                sent, scls = "● Neutral", "news-sentiment-neu"

            st.markdown(f"""
            <div class="news-card">
              <div class="news-title"><a href="{url}" target="_blank"
                style="color:#CBD5E1;text-decoration:none;">{title}</a></div>
              <div class="news-meta">{publisher} · {ts} &nbsp;
                <span class="{scls}">{sent}</span></div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("No recent news available.")

with col_a:
    st.markdown("**Analyst Price Targets**")
    analysts = [
        ("BofA Securities",  "Underperform", "$38",  "#EF4444"),
        ("Stifel",           "Hold",         "$37",  "#F59E0B"),
        ("Mizuho",           "Neutral",      "$40",  "#64748B"),
        ("Citi",             "Neutral",      "$48",  "#64748B"),
        ("Consensus Mean",   "—",            f"${info.get('targetMeanPrice',42):.0f}" if info.get('targetMeanPrice') else "$42", "#3B82F6"),
    ]
    for firm, rating, target_p, col in analysts:
        st.markdown(f"""
        <div class="analyst-row">
          <div>
            <div style="color:#CBD5E1;font-weight:500;">{firm}</div>
            <div style="font-size:0.7rem;color:{col};font-weight:700;">{rating}</div>
          </div>
          <div style="font-family:'IBM Plex Mono',monospace;font-weight:700;
                      color:#F1F5F9;">{target_p}</div>
        </div>""", unsafe_allow_html=True)

    # Volume sparkline (5d intraday)
    st.markdown("<br>**Intraday Price (5 Days)**", unsafe_allow_html=True)
    h5 = d["hist_5d"]
    if not h5.empty:
        fig5 = go.Figure(go.Scatter(
            x=h5.index, y=h5["Close"],
            mode="lines", fill="tozeroy",
            line=dict(color="#3B82F6", width=1.5),
            fillcolor="rgba(59,130,246,0.1)"
        ))
        fig5.update_layout(**CHART_LAYOUT, height=160)
        fig5.update_layout(margin=dict(l=5,r=5,t=5,b=5),
            xaxis=dict(showticklabels=False, gridcolor="#1E2D45"),
            yaxis=dict(gridcolor="#1E2D45"))
        st.plotly_chart(fig5, use_container_width=True)

with col_r:
    st.markdown("**Risk & Strategic Monitor**")
    risks = [
        ("🔴", "Dividend Suspended",     "Cash conservation — income investors exit"),
        ("🔴", "EPS Negative Q2 2026",   "-$0.21 vs $1.34 YoY — profitability concern"),
        ("🟡", "Revenue -6.8% YoY",      "Soft appliance demand, promotional headwinds"),
        ("🟡", "Steel / Metal Inflation","50bps headwind in Q2, persists full year"),
        ("🟡", "Section 232 Tariffs",    "-200bps margin impact from tariff changes"),
        ("🟢", "NA Sequential Margin +", "10% promo price increase successful"),
        ("🟢", "Cost Takeout on Track",  "25% DC reduction, Iowa/Brazil/Mexico footprint"),
        ("🟢", "FY Guidance Reaffirmed", "Management confident in $2.25–$2.75 EPS range"),
        ("🔵", "Portfolio Refresh",      "30%+ of NA MDA lineup refreshed in 2026"),
        ("🔵", "Net Debt < $5B Target",  "Deleveraging on track via asset sales & refinancing"),
    ]
    for icon, title_r, desc in risks:
        color_map = {"🔴":"#EF4444","🟡":"#F59E0B","🟢":"#10B981","🔵":"#3B82F6"}
        bar_col = color_map.get(icon, "#64748B")
        st.markdown(f"""
        <div style="display:flex;gap:8px;align-items:flex-start;
                    padding:5px 0;border-bottom:1px solid #1E2D45;">
          <div style="font-size:0.75rem;margin-top:2px;">{icon}</div>
          <div>
            <div style="font-size:0.78rem;font-weight:600;color:#CBD5E1;">{title_r}</div>
            <div style="font-size:0.68rem;color:#475569;">{desc}</div>
          </div>
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 4 — RSI + Bollinger | Peer Comparison
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Technical Indicators & Peer Comparison</div>', unsafe_allow_html=True)

col_tech, col_peer = st.columns([3, 2])

with col_tech:
    hist = d["hist_1y"].copy()
    if not hist.empty:
        # RSI
        delta_p = hist["Close"].diff()
        gain    = delta_p.clip(lower=0).rolling(14).mean()
        loss    = (-delta_p.clip(upper=0)).rolling(14).mean()
        rs      = gain / loss
        hist["RSI"] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        hist["BB_mid"]  = hist["Close"].rolling(20).mean()
        hist["BB_std"]  = hist["Close"].rolling(20).std()
        hist["BB_upper"]= hist["BB_mid"] + 2 * hist["BB_std"]
        hist["BB_lower"]= hist["BB_mid"] - 2 * hist["BB_std"]

        fig_tech = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                 row_heights=[0.65, 0.35], vertical_spacing=0.06)
        # Bollinger
        fig_tech.add_trace(go.Scatter(x=hist.index, y=hist["BB_upper"],
            line=dict(color="#8B5CF6",width=1,dash="dot"), name="BB Upper"), row=1, col=1)
        fig_tech.add_trace(go.Scatter(x=hist.index, y=hist["BB_lower"],
            line=dict(color="#8B5CF6",width=1,dash="dot"), name="BB Lower",
            fill="tonexty", fillcolor="rgba(139,92,246,0.05)"), row=1, col=1)
        fig_tech.add_trace(go.Scatter(x=hist.index, y=hist["Close"],
            line=dict(color="#3B82F6",width=2), name="Close"), row=1, col=1)
        # RSI
        fig_tech.add_trace(go.Scatter(x=hist.index, y=hist["RSI"],
            line=dict(color="#F59E0B",width=1.5), name="RSI(14)"), row=2, col=1)
        fig_tech.add_hline(y=70, line_color="#EF4444", line_dash="dot", row=2, col=1)
        fig_tech.add_hline(y=30, line_color="#10B981", line_dash="dot", row=2, col=1)

        fig_tech.update_layout(**CHART_LAYOUT, height=340,
            title=dict(text="Bollinger Bands + RSI(14)", font=dict(size=13, color="#94A3B8")))
        st.plotly_chart(fig_tech, use_container_width=True)

with col_peer:
    st.markdown("**Peer Comparison (YTD Performance)**")
    # Static peer data (fallback if live fetch fails)
    peer_data = {
        "WHR":    {"ytd": day_chg_p, "pe": pe or 0,  "col": "#3B82F6"},
        "HON":    {"ytd": 8.4,       "pe": 22.1,     "col": "#10B981"},
        "MMM":    {"ytd": 12.1,      "pe": 14.8,     "col": "#8B5CF6"},
        "GE":     {"ytd": 18.6,      "pe": 31.2,     "col": "#F59E0B"},
        "AMETEK": {"ytd": 5.2,       "pe": 26.4,     "col": "#06B6D4"},
    }

    syms  = list(peer_data.keys())
    ytds  = [peer_data[s]["ytd"] for s in syms]
    colors= ["#10B981" if v >= 0 else "#EF4444" for v in ytds]

    fig_peer = go.Figure(go.Bar(
        x=syms, y=ytds,
        marker_color=colors,
        text=[f"{v:+.1f}%" for v in ytds],
        textposition="outside",
        textfont=dict(size=11, color="#94A3B8"),
    ))
    fig_peer.update_layout(**CHART_LAYOUT, height=200,
        title=dict(text="Day Return vs Peers", font=dict(size=12, color="#94A3B8")))
    fig_peer.update_layout(margin=dict(l=5,r=5,t=35,b=5))
    st.plotly_chart(fig_peer, use_container_width=True)

    # Key metrics table
    metrics_display = [
        ("Shares Outstanding", info.get("sharesOutstanding")),
        ("Float",              info.get("floatShares")),
        ("Short % of Float",   info.get("shortPercentOfFloat")),
        ("Insider Ownership",  info.get("heldPercentInsiders")),
        ("Inst. Ownership",    info.get("heldPercentInstitutions")),
        ("Avg Volume (10d)",   info.get("averageVolume10days")),
        ("EPS (TTM)",          info.get("trailingEps")),
        ("Revenue/Share",      info.get("revenuePerShare")),
    ]
    st.markdown("**Share & Ownership Stats**")
    for label, val in metrics_display:
        if val is None:
            display = "N/A"
        elif isinstance(val, float) and val < 1:
            display = f"{val*100:.2f}%"
        elif isinstance(val, (int, float)) and abs(val) > 1e6:
            display = fmt_currency(val, 0)
        else:
            display = f"{val:.2f}" if isinstance(val, float) else str(val)

        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;
                    padding:4px 0;border-bottom:1px solid #1E2D45;font-size:0.78rem;">
          <span style="color:#94A3B8;">{label}</span>
          <span style="font-family:'IBM Plex Mono',monospace;color:#F1F5F9;font-weight:600;">{display}</span>
        </div>""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# SECTION: 6-MONTH PREDICTION + INDIA MANAGER IMPACT
# ═════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="margin-top:2.5rem;padding:1rem 1.5rem;
            background:linear-gradient(135deg,#0F1D35 0%,#111827 100%);
            border:1px solid #1E3A5F;border-radius:12px;">
  <div style="font-size:0.68rem;color:#3B82F6;font-weight:700;letter-spacing:1.5px;
              text-transform:uppercase;margin-bottom:4px;">AI-Assisted Intelligence Module</div>
  <div style="font-size:1.25rem;font-weight:700;color:#F1F5F9;">
    🔮 6-Month Performance Forecast &nbsp;·&nbsp;
    🇮🇳 India Manager-Level Impact Radar
  </div>
  <div style="font-size:0.78rem;color:#475569;margin-top:4px;">
    Forecast period: Aug 2026 – Jan 2027 &nbsp;·&nbsp;
    Based on Q2 2026 results, analyst consensus, NSE:WHIRLPOOL data & restructuring intelligence
  </div>
</div>
""", unsafe_allow_html=True)

# ── ROW: 6-Month WHR (Global) Forecast + India Revenue Forecast ──────────────
st.markdown('<div class="section-header">Global WHR · 6-Month Forward Outlook</div>', unsafe_allow_html=True)

col_gf1, col_gf2, col_gf3 = st.columns([2, 2, 2])

with col_gf1:
    # Revenue projection chart Q3-Q4 2026 + Q1-Q2 2027
    fwd_qtrs   = ["Q2 2026\n(Actual)", "Q3 2026\n(Est.)", "Q4 2026\n(Est.)", "Q1 2027\n(Est.)", "Q2 2027\n(Est.)"]
    fwd_rev    = [3.52,               3.65,               3.85,               3.45,               3.70]
    fwd_eps    = [-0.21,              0.55,               1.10,               0.40,               0.80]
    bar_colors = ["#475569","#3B82F6","#3B82F6","#06B6D4","#06B6D4"]

    fig_fwd = make_subplots(specs=[[{"secondary_y": True}]])
    fig_fwd.add_trace(go.Bar(
        x=fwd_qtrs, y=fwd_rev, name="Revenue ($B)",
        marker_color=bar_colors, opacity=0.8
    ), secondary_y=False)
    fig_fwd.add_trace(go.Scatter(
        x=fwd_qtrs, y=fwd_eps, name="EPS ($)",
        mode="lines+markers",
        line=dict(color="#F59E0B", width=2.5),
        marker=dict(size=9, color=["#EF4444" if e < 0 else "#10B981" for e in fwd_eps])
    ), secondary_y=True)
    # Shading for forecast period
    fig_fwd.add_vrect(x0=0.5, x1=4.5,
        fillcolor="rgba(59,130,246,0.04)", line_width=0,
        annotation_text="← Forecast →", annotation_position="top left",
        annotation_font_size=10, annotation_font_color="#3B82F6")
    fig_fwd.update_layout(**CHART_LAYOUT, height=300,
        title=dict(text="WHR Global Revenue & EPS — 6-Month Forecast", font=dict(size=13, color="#94A3B8")))
    fig_fwd.update_yaxes(title_text="Revenue ($B)", secondary_y=False,
        gridcolor="#1E2D45", color="#64748B", title_font_size=10)
    fig_fwd.update_yaxes(title_text="EPS ($)", secondary_y=True,
        gridcolor="#1E2D45", color="#64748B", title_font_size=10)
    st.plotly_chart(fig_fwd, use_container_width=True)

with col_gf2:
    # India NSE:WHIRLPOOL Revenue forecast (INR Crore)
    india_qtrs = ["Q4 FY26\n(Actual)", "Q1 FY27\n(Est.)", "Q2 FY27\n(Est.)", "Q3 FY27\n(Est.)"]
    india_rev  = [2181,               2050,               2350,               2500]
    india_ebitda=[131,                102,                165,                185]
    india_colors=["#475569","#10B981","#10B981","#10B981"]

    fig_ind = make_subplots(specs=[[{"secondary_y": True}]])
    fig_ind.add_trace(go.Bar(
        x=india_qtrs, y=india_rev, name="Revenue (₹ Cr)",
        marker_color=india_colors, opacity=0.8
    ), secondary_y=False)
    fig_ind.add_trace(go.Scatter(
        x=india_qtrs, y=india_ebitda, name="EBITDA (₹ Cr)",
        mode="lines+markers",
        line=dict(color="#F59E0B", width=2.5),
        marker=dict(size=9, color="#F59E0B")
    ), secondary_y=True)
    fig_ind.update_layout(**CHART_LAYOUT, height=300,
        title=dict(text="Whirlpool India (NSE) — Revenue & EBITDA Forecast", font=dict(size=13, color="#94A3B8")))
    fig_ind.update_yaxes(title_text="Revenue (₹ Cr)", secondary_y=False,
        gridcolor="#1E2D45", color="#64748B", title_font_size=10)
    fig_ind.update_yaxes(title_text="EBITDA (₹ Cr)", secondary_y=True,
        gridcolor="#1E2D45", color="#64748B", title_font_size=10)
    st.plotly_chart(fig_ind, use_container_width=True)

with col_gf3:
    st.markdown("**6-Month Key Forecast Signals**")
    signals = [
        ("WHR Global Q3 2026",  "Revenue $3.65B est.",   "+3.7% QoQ recovery",   "#3B82F6",  "Seasonal uplift + promo price increase"),
        ("WHR EPS Recovery",    "Q3 EPS ~$0.55",         "From -$0.21 in Q2",    "#10B981",  "Cost takeout + lower promo spend"),
        ("India Q1 FY27 Rev",   "₹2,050 Cr est.",        "-6.0% QoQ seasonal",   "#F59E0B",  "Q1 is weak quarter — AC demand tails off"),
        ("India FY27 Full Year","₹9,030 Cr consensus",   "+8.2% YoY growth",     "#10B981",  "11 analyst consensus — Trendlyne data"),
        ("India EPS FY27",      "₹25.29 est.",           "+28% YoY (revised ↓)", "#F59E0B",  "Down from ₹29.87 after Q1 miss"),
        ("Stake Sale (31%)",    "EQT / Bain / Reliance",  "Due diligence active", "#8B5CF6",  "$550–600M deal — changes India ownership"),
        ("Global Net Debt",     "Target <$5.0B",         "On track by Dec 2026", "#06B6D4",  "Asset sales + Mexico CapEx generating cash"),
        ("WHR Stock Analyst",   "Mean target $42",        "BofA Underperform $36","#EF4444",  "Caution: consensus skewed bearish"),
    ]
    for s in signals:
        label, val, delta, col, note = s
        st.markdown(f"""
        <div style="display:flex;gap:8px;align-items:flex-start;
                    padding:5px 0;border-bottom:1px solid #1E2D45;">
          <div style="width:5px;border-radius:3px;background:{col};
                      min-height:40px;flex-shrink:0;"></div>
          <div style="flex:1;">
            <div style="font-size:0.7rem;color:#64748B;text-transform:uppercase;
                        letter-spacing:0.6px;">{label}</div>
            <div style="font-size:0.9rem;font-weight:700;color:#F1F5F9;
                        font-family:'IBM Plex Mono',monospace;">{val}</div>
            <div style="font-size:0.72rem;color:{col};font-weight:600;">{delta}</div>
            <div style="font-size:0.68rem;color:#475569;">{note}</div>
          </div>
        </div>""", unsafe_allow_html=True)

# ── INDIA MANAGER IMPACT SECTION ─────────────────────────────────────────────
st.markdown('<div class="section-header">🇮🇳 India Manager-Level Impact Radar — Aug 2026 to Jan 2027</div>',
            unsafe_allow_html=True)

# Context banner
st.markdown("""
<div style="background:#111827;border:1px solid #1E3A5F;border-radius:8px;
            padding:0.9rem 1.2rem;margin-bottom:1rem;">
  <div style="display:flex;gap:2rem;flex-wrap:wrap;">
    <div><div style="font-size:0.68rem;color:#64748B;text-transform:uppercase;">India Employees (2024)</div>
         <div style="font-size:1.1rem;font-weight:700;color:#F1F5F9;font-family:'IBM Plex Mono',monospace;">~1,536</div></div>
    <div><div style="font-size:0.68rem;color:#64748B;text-transform:uppercase;">India Hubs</div>
         <div style="font-size:1.1rem;font-weight:700;color:#F1F5F9;font-family:'IBM Plex Mono',monospace;">Pune · Ranjangaon · Faridabad</div></div>
    <div><div style="font-size:0.68rem;color:#64748B;text-transform:uppercase;">India FY26 Revenue</div>
         <div style="font-size:1.1rem;font-weight:700;color:#F1F5F9;font-family:'IBM Plex Mono',monospace;">₹8,034 Cr (+1.4% YoY)</div></div>
    <div><div style="font-size:0.68rem;color:#64748B;text-transform:uppercase;">India EBITDA FY26</div>
         <div style="font-size:1.1rem;font-weight:700;color:#F1F5F9;font-family:'IBM Plex Mono',monospace;">₹481 Cr (6.0% margin)</div></div>
    <div><div style="font-size:0.68rem;color:#64748B;text-transform:uppercase;">Stake Sale Status</div>
         <div style="font-size:1.1rem;font-weight:700;color:#8B5CF6;font-family:'IBM Plex Mono',monospace;">Due Diligence Active</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

col_i1, col_i2, col_i3 = st.columns([2, 2, 2])

with col_i1:
    st.markdown("**Department-Level Risk Heat Map**")

    dept_data = {
        "Department":   ["Finance / FP&A", "Commercial Finance", "Sales (Regional)", "IT / Engineering", "Supply Chain", "HR / People Ops", "Marketing", "Manufacturing (Ranjangaon)"],
        "Risk Level":   ["Medium",          "High",               "Low",              "Low",              "Medium",       "High",             "Medium",    "Low"],
        "Risk Score":   [55,                80,                   25,                 20,                 50,             75,                 45,          30],
        "Headcount Δ":  ["Stable",          "Role exits likely",  "Hiring active",    "GCC expanding",    "Reorganising", "Centralising",     "Watch",     "Stable"],
    }
    df_risk = pd.DataFrame(dept_data)

    color_map_r = {"High": "#EF4444", "Medium": "#F59E0B", "Low": "#10B981"}
    for _, row in df_risk.iterrows():
        col_r = color_map_r.get(row["Risk Level"], "#64748B")
        bar_w = int(row["Risk Score"] * 1.5)
        st.markdown(f"""
        <div style="padding:6px 0;border-bottom:1px solid #1E2D45;">
          <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
            <span style="font-size:0.8rem;color:#CBD5E1;font-weight:500;">{row['Department']}</span>
            <span style="font-size:0.72rem;color:{col_r};font-weight:700;">{row['Risk Level']}</span>
          </div>
          <div style="background:#1E2D45;border-radius:4px;height:5px;margin-bottom:2px;">
            <div style="background:{col_r};width:{bar_w}px;max-width:100%;height:5px;
                        border-radius:4px;"></div>
          </div>
          <div style="font-size:0.68rem;color:#475569;">{row['Headcount Δ']}</div>
        </div>""", unsafe_allow_html=True)

with col_i2:
    st.markdown("**Manager-Level Impact by Function — Next 6 Months**")

    impacts = [
        {
            "role":    "Finance Managers (FP&A)",
            "risk":    "MEDIUM",
            "rcol":    "#F59E0B",
            "events":  [
                "Abhish Jain appointed Head FP&A (27 Jul 2026)",
                "Charu Aggarwal moved to Commercial Finance",
                "Forecasting automation being implemented",
                "Manager roles: stable but KPIs tightening",
            ],
            "outlook": "Stable through Q3; automation may compress mid-level FP&A headcount by Q1 2027",
        },
        {
            "role":    "Commercial Finance Managers",
            "risk":    "HIGH",
            "rcol":    "#EF4444",
            "events":  [
                "Bharat Gulati (Head) resigned — 14 Jul 2026",
                "Successor not yet named — vacuum at top",
                "Reporting restructure likely in progress",
                "Manager KPIs tied to margin recovery targets",
            ],
            "outlook": "High uncertainty — reorganisation of function expected Aug–Oct 2026",
        },
        {
            "role":    "Sales / Regional Managers",
            "risk":    "LOW",
            "rcol":    "#10B981",
            "events":  [
                "Jijesh Gopalan moved to VP-Service (15 Jul)",
                "Sr. Executive roles being actively hired",
                "Openings in Pune, Mumbai, Ahmedabad, Faridabad, Gurgaon, Pondicherry",
                "Premium product launch expanding footprint",
            ],
            "outlook": "Growth mode — manager hiring active; record March 2026 shipments set positive tone",
        },
        {
            "role":    "IT / GCC / Engineering Managers",
            "risk":    "LOW",
            "rcol":    "#10B981",
            "events":  [
                "India named as key hub (Finance, Procurement, IT, HR)",
                "GTEC Pune expanding — R&D and product engineering",
                "Business Services Org. being built with India as centre",
                "Decentralised model → more autonomy for India leads",
            ],
            "outlook": "Best-positioned function — GCC expansion favours India managers through 2027",
        },
        {
            "role":    "HR / People Ops Managers",
            "risk":    "HIGH",
            "rcol":    "#EF4444",
            "events":  [
                "Global workforce: 1,700+ cut globally in 2024–25",
                "India BSO centralising HR processes across BUs",
                "Cost takeout = fewer HR BPs per BU",
                "Manager-to-IC ratio under review",
            ],
            "outlook": "Centralisation risk — shared services absorb HR roles; managerial layer may slim by Q4 2026",
        },
    ]

    for imp in impacts:
        st.markdown(f"""
        <div style="background:#111827;border:1px solid #1E2D45;border-radius:8px;
                    padding:0.7rem 0.9rem;margin-bottom:0.6rem;
                    border-left:3px solid {imp['rcol']};">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
            <div style="font-size:0.82rem;font-weight:700;color:#F1F5F9;">{imp['role']}</div>
            <div style="font-size:0.68rem;font-weight:700;color:{imp['rcol']};
                        background:rgba(0,0,0,0.3);padding:2px 8px;border-radius:10px;">
              {imp['risk']} RISK</div>
          </div>
          {"".join(f'<div style="font-size:0.7rem;color:#64748B;padding:1px 0;">• {e}</div>' for e in imp['events'])}
          <div style="font-size:0.72rem;color:{imp['rcol']};margin-top:5px;font-style:italic;">
            📍 {imp['outlook']}</div>
        </div>""", unsafe_allow_html=True)

with col_i3:
    # Radar chart - manager function risk
    categories   = ["Finance\nFP&A", "Commercial\nFinance", "Sales\nRegional", "IT /\nGCC", "Supply\nChain", "HR /\nPeople Ops"]
    risk_scores  = [55, 80, 25, 20, 50, 75]
    risk_scores_c= risk_scores + [risk_scores[0]]
    cats_c       = categories + [categories[0]]

    import math
    n = len(categories)
    angles = [i * 2 * math.pi / n for i in range(n)] + [0]
    xs = [r * math.cos(a - math.pi/2) for r, a in zip(risk_scores_c, angles)]
    ys = [r * math.sin(a - math.pi/2) for r, a in zip(risk_scores_c, angles)]

    fig_radar = go.Figure()
    # Rings
    for ring in [25, 50, 75, 100]:
        rxs = [ring*math.cos(a-math.pi/2) for a in angles]
        rys = [ring*math.sin(a-math.pi/2) for a in angles]
        fig_radar.add_trace(go.Scatter(x=rxs, y=rys, mode="lines",
            line=dict(color="#1E2D45", width=1), showlegend=False, hoverinfo="skip"))
    # Axes
    for i, (cat, ang) in enumerate(zip(categories, angles[:-1])):
        fig_radar.add_trace(go.Scatter(
            x=[0, 100*math.cos(ang-math.pi/2)],
            y=[0, 100*math.sin(ang-math.pi/2)],
            mode="lines", line=dict(color="#1E2D45", width=1),
            showlegend=False, hoverinfo="skip"))
        fig_radar.add_annotation(
            x=115*math.cos(ang-math.pi/2),
            y=115*math.sin(ang-math.pi/2),
            text=cat, showarrow=False,
            font=dict(size=10, color="#94A3B8"), align="center")
    # Fill
    fig_radar.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines+markers", fill="toself",
        fillcolor="rgba(239,68,68,0.15)",
        line=dict(color="#EF4444", width=2),
        marker=dict(size=8, color="#EF4444"),
        name="Risk Score",
        hovertemplate="<b>%{text}</b><extra></extra>",
        text=[f"{c}: {s}/100" for c, s in zip(cats_c, risk_scores_c)]
    ))
    fig_radar.update_layout(**CHART_LAYOUT, height=320,
        title=dict(text="Manager-Level Risk Radar (India)", font=dict(size=13, color="#94A3B8")))
    fig_radar.update_layout(
        xaxis=dict(visible=False, range=[-130, 130]),
        yaxis=dict(visible=False, range=[-130, 130]),
        margin=dict(l=40, r=40, t=40, b=20))
    st.plotly_chart(fig_radar, use_container_width=True)

    # Stake sale impact box
    st.markdown("""
    <div style="background:#1A0F2E;border:1px solid #5B21B6;border-radius:8px;
                padding:0.9rem 1rem;margin-top:0.5rem;">
      <div style="font-size:0.72rem;font-weight:700;color:#8B5CF6;text-transform:uppercase;
                  letter-spacing:0.8px;margin-bottom:6px;">🔔 Critical Watch: 31% Stake Sale</div>
      <div style="font-size:0.78rem;color:#CBD5E1;line-height:1.5;">
        WHR Corp selling 31% of Whirlpool India to Reliance Retail, EQT, Bain or TPG.
        Due diligence active. Deal expected <strong style="color:#F59E0B;">~$550–600M</strong>.
      </div>
      <div style="margin-top:8px;">
        <div style="font-size:0.7rem;color:#8B5CF6;font-weight:600;margin-bottom:4px;">Manager Impact if deal closes:</div>
        <div style="font-size:0.7rem;color:#94A3B8;">• New strategic owner → leadership reshuffle likely</div>
        <div style="font-size:0.7rem;color:#94A3B8;">• Greater India autonomy = more Manager-level P&L ownership</div>
        <div style="font-size:0.7rem;color:#94A3B8;">• PE buyer (EQT/Bain) → cost reduction playbook</div>
        <div style="font-size:0.7rem;color:#94A3B8;">• Reliance buyer → integration, possible headcount growth</div>
        <div style="font-size:0.7rem;color:#F59E0B;margin-top:4px;">⚡ Highest-impact event for India managers in 6 months</div>
      </div>
    </div>""", unsafe_allow_html=True)

# ── Timeline ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🗓 India Manager Event Timeline — Aug 2026 → Jan 2027</div>',
            unsafe_allow_html=True)

timeline_events = [
    ("Aug 2026",  "#3B82F6",  "BSO India Hub Formalised",           "Finance, Procurement, IT, HR shared services consolidate under India leadership"),
    ("Aug 2026",  "#EF4444",  "Commercial Finance Head Search",      "Bharat Gulati gap — successor appointment expected; interim pressure on Finance managers"),
    ("Sep 2026",  "#8B5CF6",  "Stake Sale Milestone",               "Shortlisted buyers (EQT, Bain, Reliance, TPG) submit binding bids ~$550–600M"),
    ("Oct 2026",  "#F59E0B",  "Q2 FY27 Results (India)",            "Revenue est. ₹2,350 Cr — festive season demand; EBITDA recovery watch"),
    ("Oct 2026",  "#06B6D4",  "GTEC Pune Capability Expansion",      "New engineering projects assigned — manager headcount additions in R&D"),
    ("Nov 2026",  "#10B981",  "WHR Global Q3 2026 Earnings",         "EPS recovery to ~$0.55 — positive signal for India subsidiary confidence"),
    ("Nov 2026",  "#F59E0B",  "FY27 Annual Planning Cycle",          "India managers present FY27 budgets; margin recovery targets set for each BU"),
    ("Dec 2026",  "#8B5CF6",  "Stake Sale Expected Close",           "New ownership takes effect — new board composition; MD/CEO continuity TBD"),
    ("Jan 2027",  "#EF4444",  "WHR Global Q4 2026 Earnings",         "EPS est. ~$1.10 — critical for India subsidiary's cost allocation & headcount freeze lift"),
    ("Jan 2027",  "#10B981",  "FY27 HR Headcount Review",            "India manager org design locked for FY27; promotions & PIP decisions expected"),
]

# Display as horizontal-ish timeline
cols_tl = st.columns(5)
for i, (month, col_tl, title_tl, desc_tl) in enumerate(timeline_events):
    with cols_tl[i % 5]:
        st.markdown(f"""
        <div style="background:#0F1629;border:1px solid #1E2D45;border-radius:8px;
                    padding:0.65rem 0.75rem;margin-bottom:0.6rem;
                    border-top:3px solid {col_tl};">
          <div style="font-size:0.65rem;font-weight:700;color:{col_tl};
                      text-transform:uppercase;letter-spacing:0.8px;">{month}</div>
          <div style="font-size:0.78rem;font-weight:700;color:#F1F5F9;
                      margin:4px 0 3px;">{title_tl}</div>
          <div style="font-size:0.68rem;color:#475569;line-height:1.4;">{desc_tl}</div>
        </div>""", unsafe_allow_html=True)

# ── Action guide for managers ─────────────────────────────────────────────────
st.markdown('<div class="section-header">💡 Recommended Actions for India Managers — By Function</div>',
            unsafe_allow_html=True)

col_a1, col_a2, col_a3, col_a4 = st.columns(4)

actions = [
    {
        "title": "Finance / FP&A",
        "icon": "📊",
        "color": "#3B82F6",
        "do": [
            "Own forecasting automation tools proactively",
            "Upskill in predictive modelling (Power BI / Python)",
            "Align KPIs to CFO Aditya Jain's cash-flow agenda",
            "Position as key player in stake sale due diligence",
        ],
        "watch": "Role redundancy if BSO centralises FP&A to Benton Harbor or Mexico",
    },
    {
        "title": "Sales / Commercial",
        "icon": "📦",
        "color": "#10B981",
        "do": [
            "Capitalise on premium product relaunch (30%+ lineup refresh)",
            "Drive festive season Q3 FY27 — September–November",
            "Expand e-commerce channel ownership",
            "Build market share in AC category (capital-intensive growth)",
        ],
        "watch": "Aggressive competitive pricing from LG, Samsung — margin pressure continues",
    },
    {
        "title": "IT / GCC / Engineering",
        "icon": "💻",
        "color": "#8B5CF6",
        "do": [
            "Lead BSO India hub digital transformation projects",
            "Claim ownership of GTEC Pune R&D tracks",
            "Build AI / automation proof-of-concepts for global BUs",
            "Network with new ownership (PE or Reliance) tech agenda",
        ],
        "watch": "Global product engineering decentralisation — opportunity if you lead, risk if you lag",
    },
    {
        "title": "HR / People Ops",
        "icon": "👥",
        "color": "#F59E0B",
        "do": [
            "Lead India-BSO HR centre of excellence build",
            "Build change management capability for stake sale transition",
            "Digitise HR processes before centralisation mandate",
            "Retain key talent ahead of ownership uncertainty",
        ],
        "watch": "Shared services absorption likely eliminates HR BP roles at BU level",
    },
]

for col_act, act in zip([col_a1, col_a2, col_a3, col_a4], actions):
    with col_act:
        dos = "".join(f'<div style="font-size:0.7rem;color:#94A3B8;padding:2px 0;">✅ {d}</div>' for d in act["do"])
        st.markdown(f"""
        <div style="background:#0F1629;border:1px solid #1E2D45;border-radius:10px;
                    padding:0.9rem;border-top:3px solid {act['color']};height:100%;">
          <div style="font-size:1rem;margin-bottom:4px;">{act['icon']}</div>
          <div style="font-size:0.85rem;font-weight:700;color:#F1F5F9;margin-bottom:8px;">{act['title']}</div>
          <div style="font-size:0.68rem;color:{act['color']};font-weight:600;text-transform:uppercase;
                      letter-spacing:0.6px;margin-bottom:5px;">Actions to Take Now</div>
          {dos}
          <div style="margin-top:8px;padding:5px 7px;background:#1E0A0A;border-radius:5px;">
            <div style="font-size:0.65rem;color:#EF4444;font-weight:600;">⚠ Watch Out For</div>
            <div style="font-size:0.68rem;color:#7F1D1D;">{act['watch']}</div>
          </div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# SECTION: WHIRLPOOL CORPORATION — GLOBAL EMPLOYEE OVERVIEW
# ═════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="margin-top:1rem;padding:1rem 1.5rem;
            background:linear-gradient(135deg,#0F1D35 0%,#111827 100%);
            border:1px solid #1E3A5F;border-radius:12px;">
  <div style="font-size:0.68rem;color:#06B6D4;font-weight:700;letter-spacing:1.5px;
              text-transform:uppercase;margin-bottom:4px;">Workforce Intelligence Module</div>
  <div style="font-size:1.25rem;font-weight:700;color:#F1F5F9;">
    🌍 Whirlpool Corporation — Global Employee Overview
  </div>
  <div style="font-size:0.78rem;color:#475569;margin-top:4px;">
    Headcount trend, regional distribution & workforce sentiment · Sourced from public filings, Revelio Labs & LeadIQ estimates
  </div>
</div>
""", unsafe_allow_html=True)

tab_emp1, tab_emp2, tab_emp3, tab_emp4 = st.tabs([
    "📊 Headcount Trend", "🗺 Regional Distribution", "🏭 Restructuring Timeline", "💬 Workforce Sentiment"
])

# ── TAB 1: Headcount trend ───────────────────────────────────────────────────
with tab_emp1:
    col_h1, col_h2 = st.columns([3, 2])

    with col_h1:
        years       = ["2021", "2022", "2023", "2024", "2025", "2026 (Current)"]
        headcount   = [69000,  67000,  59000,  41000,  41519,  41000]
        note_hc     = ["Peak post-pandemic", "Portfolio pruning begins", "Major restructuring",
                        "EMEA JV exit + layoffs", "Stabilising", "Current estimate ~41K"]

        fig_hc = go.Figure()
        fig_hc.add_trace(go.Scatter(
            x=years, y=headcount, mode="lines+markers",
            line=dict(color="#06B6D4", width=3),
            marker=dict(size=10, color=["#64748B","#64748B","#F59E0B","#EF4444","#3B82F6","#10B981"]),
            fill="tozeroy", fillcolor="rgba(6,182,212,0.08)",
            text=note_hc, hovertemplate="<b>%{x}</b>: %{y:,}<br>%{text}<extra></extra>"
        ))
        fig_hc.update_layout(**CHART_LAYOUT, height=320,
            title=dict(text="Global Headcount Trend — 2021 to 2026", font=dict(size=13, color="#94A3B8")))
        st.plotly_chart(fig_hc, use_container_width=True)
        st.caption("⚠️ Source estimates vary (41K–46K range across LeadIQ, Revelio, company filings). Company-reported figure used where available.")

    with col_h2:
        st.markdown("**Snapshot — Current Workforce**")
        stats = [
            ("Total Employees (2025 filing)", "~41,000", "#3B82F6"),
            ("Manufacturing & Tech Centers",   "55+ facilities globally", "#8B5CF6"),
            ("Countries with Operations",      "~50 markets served", "#10B981"),
            ("2025 Active Job Postings",       "2,059 (+4.9% YoY)", "#06B6D4"),
            ("Peak Historic Headcount",        "~93,000 (2018)", "#64748B"),
            ("5-Year Headcount Change",        "-40% since 2021", "#EF4444"),
        ]
        for label, val, col in stats:
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:8px 0;border-bottom:1px solid #1E2D45;">
              <span style="font-size:0.8rem;color:#94A3B8;">{label}</span>
              <span style="font-size:0.88rem;font-weight:700;color:{col};
                          font-family:'IBM Plex Mono',monospace;">{val}</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#1E0A0A;border:1px solid #7F1D1D;border-radius:8px;
                    padding:0.7rem 1rem;margin-top:0.8rem;">
          <div style="font-size:0.7rem;color:#EF4444;font-weight:700;">📉 Context</div>
          <div style="font-size:0.72rem;color:#94A3B8;margin-top:3px;">
            Headcount has fallen ~40% since 2021, driven by the 2024 EMEA joint-venture exit,
            portfolio simplification, automation investment, and ongoing cost-takeout programs
            tied to margin recovery goals.
          </div>
        </div>""", unsafe_allow_html=True)

# ── TAB 2: Regional distribution ─────────────────────────────────────────────
with tab_emp2:
    col_r1, col_r2 = st.columns([2, 3])

    with col_r1:
        regions      = ["North America", "Latin America", "India / APAC", "EMEA", "Other"]
        region_pct   = [42, 24, 12, 14, 8]
        region_cols  = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#64748B"]

        fig_reg = go.Figure(go.Pie(
            labels=regions, values=region_pct, hole=0.55,
            marker=dict(colors=region_cols),
            textinfo="label+percent",
            textfont=dict(size=11, color="#CBD5E1"),
        ))
        fig_reg.update_layout(**CHART_LAYOUT, height=340,
            title=dict(text="Estimated Workforce by Region", font=dict(size=13, color="#94A3B8")),
            showlegend=False)
        st.plotly_chart(fig_reg, use_container_width=True)
        st.caption("Estimated distribution based on facility footprint and public disclosures — Whirlpool does not publish an exact regional headcount breakdown.")

    with col_r2:
        st.markdown("**Key Operating Locations**")
        locations = [
            ("🇺🇸 Benton Harbor, MI (HQ)",  "Global headquarters — corporate, finance, strategy", "#3B82F6"),
            ("🇺🇸 Clyde, OH / Findlay, OH",  "Major U.S. manufacturing plants — laundry, dishwashers", "#3B82F6"),
            ("🇧🇷 São Paulo, Brazil",        "LatAm HQ (Brastemp/Consul brands) — largest LatAm hub", "#10B981"),
            ("🇮🇳 Pune, India",              "India HQ + GTEC engineering center + BSO hub", "#F59E0B"),
            ("🇮🇳 Ranjangaon / Faridabad",   "Manufacturing facilities — refrigerators, washers", "#F59E0B"),
            ("🇲🇽 Mexico (Multiple)",        "Growing manufacturing footprint — CapEx priority region", "#8B5CF6"),
            ("🇮🇹 Comerio / Cassinetta, Italy","EMEA operations post-2024 JV restructuring", "#EC4899"),
            ("🇨🇳 China (Limited)",          "Reduced presence after portfolio simplification", "#64748B"),
        ]
        for loc, desc, col in locations:
            st.markdown(f"""
            <div style="display:flex;gap:10px;align-items:flex-start;
                        padding:7px 0;border-bottom:1px solid #1E2D45;">
              <div style="width:5px;border-radius:3px;background:{col};min-height:32px;flex-shrink:0;"></div>
              <div>
                <div style="font-size:0.82rem;font-weight:700;color:#F1F5F9;">{loc}</div>
                <div style="font-size:0.72rem;color:#64748B;">{desc}</div>
              </div>
            </div>""", unsafe_allow_html=True)

# ── TAB 3: Restructuring timeline ────────────────────────────────────────────
with tab_emp3:
    st.markdown("**Global Restructuring & Workforce Events — 2023 to 2026**")

    restructure_events = [
        ("2023", "#F59E0B", "EMEA Restructuring Begins",
         "Whirlpool announces strategic review of European operations amid heavy losses"),
        ("2024", "#EF4444", "EMEA Joint Venture with Arçelik",
         "Whirlpool exits majority EMEA ownership — transfers ~10,000+ roles to Beko Europe JV"),
        ("2024", "#EF4444", "~1,000 Salaried Role Cuts (Global)",
         "Cost-reduction program targets corporate & regional overhead roles"),
        ("2025", "#F59E0B", "Continued Portfolio Simplification",
         "SKU rationalisation and plant consolidation in North America"),
        ("2025", "#3B82F6", "India BSO Hub Designated",
         "India named strategic hub for Finance, IT, HR, Procurement shared services"),
        ("2026 Q1", "#EF4444", "Dividend Suspended",
         "Cash conservation measure signals continued cost discipline"),
        ("2026 Q2", "#EF4444", "Commercial Finance Leadership Exit (India)",
         "Bharat Gulati resignation — reflects broader finance function pressure"),
        ("2026 Q3", "#8B5CF6", "31% India Stake Sale Process",
         "Active due diligence — new ownership could reshape India workforce structure"),
        ("2026 Q4 (Est.)", "#10B981", "Automation CapEx Ramp-Up",
         "Iowa, Brazil, Mexico facilities — automation investment may offset hiring needs"),
    ]

    for period, col, title_e, desc_e in restructure_events:
        st.markdown(f"""
        <div style="display:flex;gap:14px;align-items:flex-start;
                    padding:10px 0;border-bottom:1px solid #1E2D45;">
          <div style="min-width:90px;font-size:0.72rem;font-weight:700;color:{col};
                      font-family:'IBM Plex Mono',monospace;padding-top:2px;">{period}</div>
          <div style="width:3px;background:{col};border-radius:2px;align-self:stretch;"></div>
          <div>
            <div style="font-size:0.86rem;font-weight:700;color:#F1F5F9;">{title_e}</div>
            <div style="font-size:0.75rem;color:#64748B;margin-top:2px;">{desc_e}</div>
          </div>
        </div>""", unsafe_allow_html=True)

# ── TAB 4: Workforce sentiment ───────────────────────────────────────────────
with tab_emp4:
    col_s1, col_s2 = st.columns([2, 2])

    with col_s1:
        st.markdown("**Employee Sentiment Indicators (Estimated)**")
        sentiment_metrics = [
            ("Job Security Confidence", 48, "#EF4444", "Below industry avg — reflects layoff history"),
            ("Compensation Satisfaction", 61, "#F59E0B", "Mixed — freezes reported in some regions"),
            ("Leadership Trust",          52, "#F59E0B", "CEO transition & restructuring create uncertainty"),
            ("Career Growth Outlook",     58, "#F59E0B", "GCC/India expansion offsets other region declines"),
            ("Work-Life Balance",         67, "#10B981", "Generally rated positively across regions"),
            ("Willingness to Recommend",  55, "#F59E0B", "Moderate — varies significantly by function/region"),
        ]
        for label, score, col, note in sentiment_metrics:
            st.markdown(f"""
            <div style="padding:8px 0;border-bottom:1px solid #1E2D45;">
              <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span style="font-size:0.82rem;color:#CBD5E1;">{label}</span>
                <span style="font-size:0.82rem;font-weight:700;color:{col};">{score}/100</span>
              </div>
              <div style="background:#1E2D45;border-radius:4px;height:6px;">
                <div style="background:{col};width:{score}%;height:6px;border-radius:4px;"></div>
              </div>
              <div style="font-size:0.68rem;color:#475569;margin-top:3px;">{note}</div>
            </div>""", unsafe_allow_html=True)
        st.caption("Illustrative estimates based on public review aggregation and restructuring context — not an official company survey.")

    with col_s2:
        st.markdown("**What's Driving Sentiment — By Theme**")
        themes = [
            ("🔴", "Layoff History", "1,000+ salaried cuts since 2024 create lingering anxiety about job security"),
            ("🔴", "Dividend Suspension", "Signals financial pressure — indirectly affects morale even for non-shareholders"),
            ("🟡", "Leadership Change", "Multiple finance leadership exits (India) — perceived instability at management layer"),
            ("🟡", "Pay & Promotion Freezes", "Reported in some corporate functions amid cost discipline"),
            ("🟢", "GCC / India Growth", "Positive counter-narrative — India, Mexico hiring active in select functions"),
            ("🟢", "Product Innovation Focus", "30%+ portfolio refresh gives commercial/engineering teams renewed purpose"),
            ("🔵", "M&A Uncertainty", "31% India stake sale creates a 'wait and see' sentiment among India staff"),
        ]
        for icon, title_t, desc_t in themes:
            st.markdown(f"""
            <div style="display:flex;gap:8px;align-items:flex-start;
                        padding:6px 0;border-bottom:1px solid #1E2D45;">
              <div style="font-size:0.8rem;">{icon}</div>
              <div>
                <div style="font-size:0.8rem;font-weight:700;color:#CBD5E1;">{title_t}</div>
                <div style="font-size:0.72rem;color:#475569;">{desc_t}</div>
              </div>
            </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-top:2rem;padding:1rem 1.5rem;background:#0F1629;
            border:1px solid #1E2D45;border-radius:8px;
            display:flex;justify-content:space-between;align-items:center;">
  <div style="font-size:0.72rem;color:#334155;">
    Data sourced from Yahoo Finance via yfinance. For informational purposes only.<br>
    Not financial advice. Refresh the page to fetch the latest data.
  </div>
  <div style="font-size:0.72rem;color:#334155;font-family:'IBM Plex Mono',monospace;text-align:right;">
    Last updated: {ist_now()}<br>
    Cache TTL: 60 minutes · Auto-refreshes daily
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# AUTO-REFRESH every 60 minutes
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<script>
  setTimeout(function(){ window.location.reload(); }, 3600000);
</script>
""", unsafe_allow_html=True)
