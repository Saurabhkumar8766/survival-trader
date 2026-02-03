import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
import time

# --- CONFIG ---
st.set_page_config(page_title="Survival Trader Pro", page_icon="🛡️", layout="wide")

# --- SMART DATA ENGINE (Fixes Rate Limit) ---
@st.cache_data(ttl=300) # Only asks Yahoo every 5 minutes to stay safe
def get_data(ticker):
    try:
        time.sleep(1) # Tiny pause to avoid spamming the server
        stock = yf.Ticker(ticker)
        return stock.history(period="5d", interval="1h")
    except:
        return None

@st.cache_data(ttl=3600) # Updates exchange rate once per hour
def get_usd_inr():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        return requests.get(url).json()["rates"]["INR"]
    except:
        return 87.5 # Fallback for Navi Mumbai precision

rate = get_usd_inr()

# --- HEADER ---
st.title("🛡️ Survival Trader Pro: Navi Mumbai Edition")
asset = st.sidebar.text_input("Enter Ticker (GC=F, RVNL.NS)", "GC=F")

data = get_data(asset)

# --- REAL-TIME DISPLAY ---
if data is not None and not data.empty:
    cp_usd = data['Close'].iloc[-1]
    price_inr = cp_usd * rate if "=" in asset else cp_usd
    
    st.metric(label=f"Current {asset} Price", value=f"₹{price_inr:,.2f}", 
              delta=f"{rate:.2f} USD/INR Rate")

    # --- INTERACTIVE CANDLESTICK CHART ---
    fig = go.Figure(data=[go.Candlestick(
        x=data.index, open=data['Open'], high=data['High'], 
        low=data['Low'], close=data['Close'],
        increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
    )])
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,b=0,t=30))
    st.plotly_chart(fig, use_container_width=True)

    # --- PROFIT & BUDGET 2026 TAX PREDICTOR ---
    st.divider()
    st.subheader("💰 Survival Profit & Tax Predictor")
    col1, col2 = st.columns(2)
    with col1:
        buy_p = st.number_input("Your Buy Price (₹)", value=int(price_inr))
        qty = st.number_input("Quantity/Grams", value=1.0)
        years = st.slider("Hold Duration (Years)", 1, 10, 3)
    
    future_val = (buy_p * qty) * (1.12)**years # 12% avg CAGR
    raw_profit = future_val - (buy_p * qty)
    tax_rate = 0.125 if years >= 2 else 0.20 # Budget 2026 LTCG/STCG logic
    tax_amt = raw_profit * tax_rate if raw_profit > 0 else 0

    with col2:
        st.write(f"**Projected Value:** ₹{future_val:,.2f}")
        st.error(f"**Est. Tax (Budget 2026):** ₹{tax_amt:,.2f}")
        st.success(f"**Final Net Profit:** ₹{(raw_profit - tax_amt):,.2f}")
else:
    st.warning("⚠️ Waiting for Yahoo Finance to reset (Rate Limit). Try again in 5 minutes or check your Ticker.")

