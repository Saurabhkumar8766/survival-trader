import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
from textblob import TextBlob
import time

# --- 1. ENGINE & CACHING ---
st.set_page_config(page_title="Survival Trader Pro", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=300)
def get_live_data(ticker):
    try:
        time.sleep(1) 
        return yf.Ticker(ticker).history(period="5d", interval="1h")
    except: return None

@st.cache_data(ttl=3600)
def get_usd_inr():
    try:
        return requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()["rates"]["INR"]
    except: return 91.52

rate = get_usd_inr()

# --- 2. SURVIVAL & 1g LOGIC ---
def analyze_survival(ticker, data):
    if data is None or data.empty: return "WAIT", "Neutral ↔️", "No Connection", 0
    intel_text = f"Global markets show stable interest in {ticker}."
    sentiment_score = TextBlob(intel_text).sentiment.polarity
    intel = "Bullish 📈" if sentiment_score > 0.1 else "Bearish 📉" if sentiment_score < -0.1 else "Neutral ↔️"
    cp = data['Close'].iloc[-1]
    low_5d = data['Low'].min()
    
    # 1g Conversion
    price_inr = (cp * rate) / 31.1035 if "=" in ticker else cp
    
    if cp <= (low_5d * 1.01) or intel == "Bearish 📉":
        signal, reason = "🔴 SELL", "DANGER: Exit to protect cash."
    elif cp > (low_5d * 1.04) and intel != "Bearish 📉":
        signal, reason = "🟢 BUY", "MOMENTUM: Recovery confirmed."
    else:
        signal, reason = "🟡 WAIT", "STABLE: Market sideways."
    return signal, intel, reason, price_inr

# --- 3. DASHBOARD ---
st.title("🛡️ Survival Trader Pro")
st.caption("Real-Time 1g Gold Pricing | Navi Mumbai")
asset = st.sidebar.text_input("Enter Ticker (GC=F)", "GC=F")

df = get_live_data(asset)
signal, intel, reason, price = analyze_survival(asset, df)

# Indicators
c_a, c_b = st.columns(2)
with c_a:
    if "BUY" in signal: st.success(f"### {signal}")
    elif "SELL" in signal: st.error(f"### {signal}")
    else: st.warning(f"### {signal}")
with c_b: st.info(f"### Intel: {intel}")

st.metric(label=f"Current {asset} Price (1g)", value=f"₹{price:,.2f}")
st.write(f"**Survival Alert:** {reason}")

# --- 4. CHART ---
if df is not None:
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,b=0,t=10))
    st.plotly_chart(fig, use_container_width=True)

# --- 5. TAX PREDICTOR ---
st.divider()
st.subheader("💰 1g Profit & Budget 2026 Tax")
invest = st.number_input("Investment (₹)", value=1000)
years = st.slider("Years", 1, 10, 3)
future_val = invest * (1.12)**years 
tax = (future_val - invest) * 0.125 if years >= 2 else (future_val - invest) * 0.20
st.success(f"**Net Profit after Tax:** ₹{(future_val - invest - tax):,.2f}")
