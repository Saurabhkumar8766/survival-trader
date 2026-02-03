import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
from textblob import TextBlob
import numpy as np
from sklearn.linear_model import LinearRegression
import time

# --- 1. CORE CONFIG ---
st.set_page_config(page_title="Survival Trader Pro", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=600)
def get_live_data(ticker):
    try:
        # Using yf.download for high-speed mobile stability
        data = yf.download(ticker, period="1mo", interval="1h", progress=False)
        return data if not data.empty else None
    except: return None

@st.cache_data(ttl=3600)
def get_usd_inr():
    try:
        # Fetches live USD/INR exchange rate (~91.50 range for Feb 2026)
        return requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()["rates"]["INR"]
    except: return 91.52 

rate = get_usd_inr()

# --- 2. SIDEBAR (CONTROLS) ---
with st.sidebar:
    st.header("👤 Portfolio Settings")
    # Investment inputs are now safely tucked away here
    my_inv = st.number_input("Investment Amount (₹)", value=700.0)
    my_buy = st.number_input("My Buy Price (1g)", value=15516.0)
    st.divider()
    asset = st.text_input("Ticker Symbol", "GC=F")
    if st.button("🔄 Refresh Market Data"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Side-toggle controls keep your main dashboard clean.")

# --- 3. SURVIVAL ENGINE ---
df = get_live_data(asset)
if df is not None:
    # Clean float conversion to prevent TypeErrors
    cp = float(df['Close'].iloc[-1].item())
    low_5d = float(df['Low'].tail(120).min().item())
    
    # 1g Price: USD Price * Exchange Rate / Troy Oz Grams * 10% Premium (GST+Storage)
    live_price = ((cp * rate) / 31.1035) * 1.10
    
    # Dynamic Signal Logic
    if cp <= (low_5d * 1.01): signal, msg, col = "🔴 SELL", "DANGER: Support floor broken. Exit now!", "error"
    elif cp > (low_5d * 1.04): signal, msg, col = "🟢 BUY", "MOMENTUM: Technical recovery is confirmed.", "success"
    else: signal, msg, col = "🟡 WAIT", "STABLE: Market is sideways. Stay patient.", "warning"

    # Portfolio Real-Time Math
    current_value = (my_inv / my_buy) * live_price
    pnl = current_value - my_inv
    pnl_pct = (pnl / my_inv) * 100

    # --- 4. MAIN DASHBOARD ---
    st.title("🛡️ Survival Trader Pro")
    
    # Row 1: Signals
    c1, c2 = st.columns([2, 1])
    with c1:
        if col == "success": st.success(f"## {signal}")
        elif col == "error": st.error(f"## {signal}")
        else: st.warning(f"## {signal}")
        st.write(f"**Survival Plan:** {msg}")
    with c2:
        st.metric("Live 1g Gold Price", f"₹{live_price:,.2f}")

    # Row 2: Results Only
    st.divider()
    m1, m2 = st.columns(2)
    with m1:
        st.metric("My Live Profit/Loss", f"₹{pnl:,.2f}", delta=f"{pnl_pct:.2f}%")
    with m2:
        st.metric("Total Portfolio Value", f"₹{current_value:,.2f}")
    if pnl > 0: st.balloons()

    # SECTION 5: ADVANCED FEATURES (COLLAPSIBLE)
    st.divider()
    with st.expander("🔮 7-Day Prediction & Market Intel"):
        # Machine Learning: Linear Regression
        df_p = df.copy()
        df_p['Day'] = np.arange(len(df_p))
        model = LinearRegression().fit(df_p[['Day']], df_p['Close'])
        pred_usd = model.predict(np.array([[len(df_p) + 7]]))[0].item()
        p_price = ((pred_usd * rate) / 31.1035) * 1.10
        expected_total = (current_value / live_price) * p_price
        
        st.metric("Expected Total (7 Days)", f"₹{expected_total:,.2f}", delta=f"₹{(expected_total-current_value):,.2f}")
        st.write(f"**Global Sentiment:** {'Bullish 📈' if p_price > live_price else 'Bearish 📉'}")

    with st.expander("📉 Full Candlestick Market Trend"):
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("💰 Budget 2026 Net Profit (After Tax)"):
        years = st.slider("Hold Duration (Years)", 1, 10, 3)
        # Budget 2026: 12.5% LTCG for Gold
        tax = (current_value * (1.12)**years - current_value) * (0.125 if years >= 2 else 0.20)
        st.write(f"Calculated tax in {years} years: **₹{tax:,.2f}**")
else:
    st.error("Connecting to global bullion servers... Please wait.")
