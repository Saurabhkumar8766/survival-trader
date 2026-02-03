import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
from textblob import TextBlob
import numpy as np
from sklearn.linear_model import LinearRegression
import time

# --- 1. CONFIG & STABLE ENGINE ---
st.set_page_config(page_title="Survival Trader Pro", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=600)
def get_live_data(ticker):
    try:
        # download is more stable for Streamlit Cloud
        data = yf.download(ticker, period="1mo", interval="1h", progress=False)
        return data if not data.empty else None
    except: return None

@st.cache_data(ttl=3600)
def get_usd_inr():
    try:
        return requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()["rates"]["INR"]
    except: return 91.52 

rate = get_usd_inr()

# --- 2. SURVIVAL LOGIC (Future-Proofed) ---
def analyze_survival(ticker, data):
    if data is None or data.empty: return "WAIT", "Neutral", "Connecting...", 0
    
    # Fix for FutureWarning: using .item() to get clean float values
    cp = float(data['Close'].iloc[-1].item())
    low_5d = float(data['Low'].tail(120).min().item())
    
    price_inr = ((cp * rate) / 31.1035) * 1.07 if "=" in ticker else cp
    intel = "Bullish 📈" if TextBlob(f"Market {ticker}").sentiment.polarity >= 0 else "Bearish 📉"
    
    if cp <= (low_5d * 1.01): signal, msg = "🔴 SELL", "Support broken."
    elif cp > (low_5d * 1.04): signal, msg = "🟢 BUY", "Recovery confirmed."
    else: signal, msg = "🟡 WAIT", "Market sideways."
    
    return signal, intel, msg, price_inr

# --- 3. DASHBOARD UI ---
st.title("🛡️ Survival Trader Pro")
if st.button("🔄 Refresh Market Data"): 
    st.cache_data.clear()
    st.rerun()

asset = st.sidebar.text_input("Ticker (GC=F)", "GC=F")
df = get_live_data(asset)
signal, intel, reason, live_price = analyze_survival(asset, df)

# Metrics
c1, c2, c3 = st.columns(3)
with c1: 
    if "BUY" in signal: st.success(f"### {signal}")
    elif "SELL" in signal: st.error(f"### {signal}")
    else: st.warning(f"### {signal}")
with c2: st.info(f"### Intel: {intel}")
with c3: st.metric("Live 1g Price", f"₹{live_price:,.2f}")

# --- 4. PORTFOLIO & FIXED PREDICTION ---
st.divider()
p1, p2 = st.columns(2)
with p1:
    st.subheader("📊 My Live Investment")
    my_inv = st.number_input("Amount (₹)", value=700)
    my_buy = st.number_input("My Buy Price (1g)", value=15516.0)
    current_val = (my_inv / my_buy) * live_price
    pnl = current_val - my_inv
    st.metric("Live P&L", f"₹{pnl:,.2f}", delta=f"{(pnl/my_inv)*100:.2f}%")
    if pnl > 0: st.balloons()

with p2:
    st.subheader("🔮 7-Day Forecast")
    if df is not None:
        df_p = df.copy()
        df_p['Day'] = np.arange(len(df_p))
        model = LinearRegression().fit(df_p[['Day']], df_p['Close'])
        
        # FIX: Added .item() to resolve TypeError
        pred_usd = model.predict(np.array([[len(df_p) + 7]]))[0].item()
        p_price = ((pred_usd * rate) / 31.1035) * 1.07
        p_ret = ((p_price - live_price) / live_price) * 100
        
        st.metric("Predicted 1g (7D)", f"₹{p_price:,.2f}", delta=f"{p_ret:.2f}%")
    else:
        st.write("Fetching data for prediction...")

# --- 5. CHART ---
if df is not None:
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)
