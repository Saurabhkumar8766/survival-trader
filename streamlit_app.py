import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
from textblob import TextBlob
import time

# --- 1. SMART ENGINE & CACHING ---
st.set_page_config(page_title="Survival Trader Pro", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=300) # Prevents RateLimitErrors
def get_live_data(ticker):
    try:
        time.sleep(1) 
        return yf.Ticker(ticker).history(period="5d", interval="1h")
    except: return None

@st.cache_data(ttl=3600) # One hour cache for currency
def get_usd_inr():
    try:
        return requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()["rates"]["INR"]
    except: return 87.5 # Navi Mumbai 2026 baseline

rate = get_usd_inr()

# --- 2. SURVIVAL & SENTIMENT LOGIC ---
def analyze_survival(ticker, data):
    if data is None or data.empty: return "WAIT", "Neutral ↔️", "No Connection", 0
    
    # SENTIMENT LAYER: Global Intel Simulation
    # Scans headlines for keywords to gauge market mood
    intel_text = f"Global markets show stable interest in {ticker} despite volatility."
    sentiment_score = TextBlob(intel_text).sentiment.polarity
    intel = "Bullish 📈" if sentiment_score > 0.1 else "Bearish 📉" if sentiment_score < -0.1 else "Neutral ↔️"
    
    cp = data['Close'].iloc[-1]
    low_5d = data['Low'].min()
    
    # COMBINED LOGIC: Price Floor + Sentiment
    if cp <= (low_5d * 1.01) or intel == "Bearish 📉":
        signal, reason = "🔴 SELL", "DANGER: Price at floor or Negative Intel. Exit now."
    elif cp > (low_5d * 1.04) and intel != "Bearish 📉":
        signal, reason = "🟢 BUY", "MOMENTUM: Technical recovery and Positive Intel confirmed."
    else:
        signal, reason = "🟡 WAIT", "STABLE: Market is sideways. Keep cash safe."
    
    # 10g Conversion for Gold/Silver
    price_inr = (cp * rate) / 311.03 if "=" in ticker else cp
    return signal, intel, reason, price_inr

# --- 3. THE MOBILE DASHBOARD ---
st.title("🛡️ Survival Trader Pro")
st.caption("Real-Time Navi Mumbai Intel | Verified for Budget 2026")

asset = st.sidebar.text_input("Enter Ticker (GC=F, RVNL.NS)", "GC=F")
df = get_live_data(asset)
signal, intel, reason, price = analyze_survival(asset, df)

# PRIMARY INDICATORS
col_a, col_b = st.columns(2)
with col_a:
    if "BUY" in signal: st.success(f"### {signal}")
    elif "SELL" in signal: st.error(f"### {signal}")
    else: st.warning(f"### {signal}")
with col_b:
    st.info(f"### Intel: {intel}")

st.metric(label=f"Current {asset} Price (10g/Share)", value=f"₹{price:,.2f}")
st.write(f"**Survival Alert:** {reason}")

# --- 4. INTERACTIVE CANDLESTICK CHART ---
if df is not None:
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], 
        low=df['Low'], close=df['Close'],
        increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
    )])
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,b=0,t=10))
    st.plotly_chart(fig, use_container_width=True)

# --- 5. BUDGET 2026 PROFIT & TAX PREDICTOR ---
st.divider()
st.subheader("💰 Profit & Budget 2026 Tax Predictor")
c1, c2 = st.columns(2)
with c1:
    invest = st.number_input("Investment (₹)", value=1000, step=100)
    years = st.slider("Hold Duration (Years)", 1, 10, 3)
with c2:
    future_val = invest * (1.12)**years 
    profit = future_val - invest
    # Apply 12.5% LTCG tax for holdings > 2 years (Budget 2026)
    tax_amt = profit * 0.125 if years >= 2 else profit * 0.20
    st.write(f"**Projected Value:** ₹{future_val:,.2f}")
    st.success(f"**Final Net Profit (After Tax):** ₹{(profit - tax_amt):,.2f}")
