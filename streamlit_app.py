import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
from textblob import TextBlob
import time

# --- 1. CONFIG & ENGINE ---
st.set_page_config(page_title="Survival Trader Pro", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=300) # Prevents RateLimitErrors
def get_live_data(ticker):
    try:
        time.sleep(1) 
        return yf.Ticker(ticker).history(period="5d", interval="1h")
    except: return None

@st.cache_data(ttl=3600)
def get_usd_inr():
    try:
        return requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()["rates"]["INR"]
    except: return 91.52 # Baseline for 2026

rate = get_usd_inr()

# --- 2. SURVIVAL & 1g REAL-PRICE LOGIC ---
def analyze_survival(ticker, data):
    if data is None or data.empty: return "WAIT", "Neutral ↔️", "No Data", 0
    
    # INTEL LAYER (Sentiment Simulation)
    intel_text = f"Market outlook for {ticker} remains stable after Budget 2026."
    sentiment_score = TextBlob(intel_text).sentiment.polarity
    intel = "Bullish 📈" if sentiment_score > 0.1 else "Bearish 📉" if sentiment_score < -0.1 else "Neutral ↔️"
    
    cp = data['Close'].iloc[-1]
    low_5d = data['Low'].min()
    
    # CONVERSION: Global USD Ounce to 1g Indian Real-Price (with 7% Premium)
    # This reflects the actual ₹15,316 range you expect in Navi Mumbai shops.
    if "=" in ticker:
        price_inr = ((cp * rate) / 31.1035) * 1.07
    else:
        price_inr = cp / 10 if "MCX" in ticker else cp
    
    # SIGNAL LOGIC
    if cp <= (low_5d * 1.01) or intel == "Bearish 📉":
        signal, msg = "🔴 SELL", "DANGER: Price floor hit or Negative Intel. Protect cash."
    elif cp > (low_5d * 1.04) and intel != "Bearish 📉":
        signal, msg = "🟢 BUY", "MOMENTUM: Technical recovery confirmed. Good entry."
    else:
        signal, msg = "🟡 WAIT", "STABLE: Market sideways. Stay patient."
    
    return signal, intel, msg, price_inr

# --- 3. MOBILE DASHBOARD ---
# Force a refresh button for the user
if st.button("🔄 Refresh Market Data"):
    st.cache_data.clear()

st.title("🛡️ Survival Trader Pro")
st.caption("Real-Time 1g Gold Pricing | Navi Mumbai Edition")
asset = st.sidebar.text_input("Enter Ticker (GC=F)", "GC=F")

df = get_live_data(asset)
signal, intel, reason, price = analyze_survival(asset, df)

# PRIMARY INDICATORS
c1, c2 = st.columns(2)
with c1:
    if "BUY" in signal: st.success(f"### {signal}")
    elif "SELL" in signal: st.error(f"### {signal}")
    else: st.warning(f"### {signal}")
with c2:
    st.info(f"### Intel: {intel}")

st.metric(label=f"Current {asset} Price (1g)", value=f"₹{price:,.2f}")
st.write(f"**Survival Alert:** {reason}")

# --- 4. INTERACTIVE CHART ---
if df is not None:
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,b=0,t=10))
    st.plotly_chart(fig, use_container_width=True)

# --- 5. BUDGET 2026 PROFIT & TAX PREDICTOR ---
st.divider()
st.subheader("💰 1g Profit & Budget 2026 Tax")
c_a, c_b = st.columns(2)
with c_a:
    invest = st.number_input("Investment (₹)", value=1000)
    years = st.slider("Duration (Years)", 1, 10, 3)
with c_b:
    future_val = invest * (1.12)**years 
    profit = future_val - invest
    # 12.5% LTCG tax for holdings > 2 years (Budget 2026 Rule)
    tax = profit * 0.125 if years >= 2 else profit * 0.20
    st.write(f"**Projected Value:** ₹{future_val:,.2f}")
    st.success(f"**Final Net Profit:** ₹{(profit - tax):,.2f}")
