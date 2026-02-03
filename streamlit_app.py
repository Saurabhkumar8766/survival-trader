import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
from textblob import TextBlob
import numpy as np
from sklearn.linear_model import LinearRegression
import time

# --- 1. CONFIG & STABILITY ---
st.set_page_config(page_title="Survival Trader Pro", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=600)
def get_live_data(ticker):
    try:
        # download is used for better reliability on Streamlit Cloud
        data = yf.download(ticker, period="1mo", interval="1h", progress=False)
        return data if not data.empty else None
    except: return None

@st.cache_data(ttl=3600)
def get_usd_inr():
    try:
        # Live Rate for Navi Mumbai precision
        return requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()["rates"]["INR"]
    except: return 91.52 

rate = get_usd_inr()

# --- 2. SIDEBAR CONTROLS (Keeps Main Screen Clean) ---
with st.sidebar:
    st.header("👤 Portfolio Settings")
    my_inv = st.number_input("Investment Amount (₹)", value=1162.0)
    my_buy = st.number_input("My Buy Price (1g)", value=15516.0)
    st.divider()
    asset = st.text_input("Ticker Symbol", "GC=F")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Adjusting these values updates the Real-Time Scoreboard.")

# --- 3. THE SURVIVAL ENGINE ---
df = get_live_data(asset)
if df is not None:
    # Get clean float values
    cp = float(df['Close'].iloc[-1].item())
    low_5d = float(df['Low'].tail(120).min().item())
    
    # Live 1g Gold Price (10% premium for Paytm/GST/Storage parity)
    live_price = ((cp * rate) / 31.1035) * 1.10
    
    # Portfolio Math
    current_total_value = (my_inv / my_buy) * live_price
    current_pnl = current_total_value - my_inv
    pnl_pct = (current_pnl / my_inv) * 100

    # 7-Day Forecast (Linear Regression)
    df_p = df.copy()
    df_p['Day'] = np.arange(len(df_p))
    model = LinearRegression().fit(df_p[['Day']], df_p['Close'])
    pred_usd = model.predict(np.array([[len(df_p) + 7]]))[0].item()
    pred_1g_price = ((pred_usd * rate) / 31.1035) * 1.10
    
    # Predicted Total Portfolio Value
    pred_portfolio_total = (my_inv / my_buy) * pred_1g_price

    # --- 4. MAIN DASHBOARD ---
    st.title("🛡️ Survival Trader Pro")
    
    # ROW 1: SIGNAL & LIVE PRICE
    c1, c2 = st.columns([2, 1])
    with c1:
        if cp > (low_5d * 1.04):
            st.success("## 🟢 BUY SIGNAL")
            st.write("**Plan:** Recovery confirmed. Momentum is positive.")
        else:
            st.warning("## 🟡 WAIT / STABLE")
            st.write("**Plan:** Market moving sideways. Hold position.")
    with c2:
        st.metric("Live 1g Price", f"₹{live_price:,.2f}")

    # ROW 2: LIVE SCOREBOARD (Current Status)
    st.divider()
    st.subheader("📊 My Real-Time Portfolio Status")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Invested Amount", f"₹{my_inv:,.2f}")
    with m2:
        st.metric("Current Profit/Loss", f"₹{current_pnl:,.2f}", delta=f"{pnl_pct:.2f}%")
    with m3:
        st.metric("Total Portfolio Value", f"₹{current_total_value:,.2f}")

    # ROW 3: 7-DAY FORECAST (Expected Status)
    st.divider()
    st.subheader("🔮 7-Day Growth Projection")
    f1, f2 = st.columns(2)
    with f1:
        st.metric("Expected 1g Price", f"₹{pred_1g_price:,.2f}")
    with f2:
        st.metric("Expected Portfolio Value", f"₹{pred_portfolio_total:,.2f}", 
                  delta=f"₹{(pred_portfolio_total - current_total_value):,.2f}")

    # ROW 4: THE LIVE CHART
    st.divider()
    st.subheader("📉 Market Trend (Candlestick)")
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], 
        low=df['Low'], close=df['Close'],
        increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
    )])
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,b=0,t=0))
    st.plotly_chart(fig, use_container_width=True)

    # ROW 5: TAX TOOL
    with st.expander("💰 Budget 2026 Tax Predictor"):
        years = st.slider("Hold Duration (Years)", 1, 10, 3)
        tax = (current_total_value * (1.12)**years - current_total_value) * (0.125 if years >= 2 else 0.20)
        st.write(f"Estimated tax on 12% growth in {years} years: **₹{tax:,.2f}**")
else:
    st.error("Connecting to global market servers... Please refresh.")
