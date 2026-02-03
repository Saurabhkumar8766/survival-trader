import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests

# --- CONFIG ---
st.set_page_config(page_title="Survival Trader Pro", page_icon="🛡️", layout="wide")

# --- LIVE DATA ENGINE ---
@st.cache_data(ttl=3600) # Updates exchange rate every hour
def get_usd_inr():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        return requests.get(url).json()["rates"]["INR"]
    except:
        return 83.5 # Solid fallback

rate = get_usd_inr()

def get_data(ticker):
    data = yf.Ticker(ticker).history(period="5d", interval="1h")
    return data

# --- HEADER ---
st.title("🛡️ Survival Trader Pro: Navi Mumbai Edition")
asset = st.sidebar.text_input("Enter Ticker (GC=F, RVNL.NS)", "GC=F")
data = get_data(asset)

# --- REAL-TIME DISPLAY ---
if not data.empty:
    curr_price_usd = data['Close'].iloc[-1]
    # Auto-convert if it's a USD asset (like Gold/Silver)
    price_inr = curr_price_usd * rate if "=" in asset else curr_price_usd
    
    st.metric(label=f"Current {asset} Price", value=f"₹{price_inr:,.2f}", 
              delta=f"{rate:.2f} USD/INR Rate")

    # --- INTERACTIVE CANDLESTICK CHART ---
    fig = go.Figure(data=[go.Candlestick(
        x=data.index, open=data['Open'], high=data['High'], 
        low=data['Low'], close=data['Close']
    )])
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,b=0,t=30))
    st.plotly_chart(fig, use_container_width=True)

    # --- BUDGET 2026 PROFIT & TAX CALCULATOR ---
    st.divider()
    st.subheader("💰 Survival Profit & Tax Predictor")
    
    col1, col2 = st.columns(2)
    with col1:
        buy_price = st.number_input("Your Buy Price (₹)", value=int(price_inr))
        qty = st.number_input("Quantity/Grams", value=1.0)
    
    # Logic: 12.5% LTCG tax for holdings > 24 months (Budget 2026 Rule)
    # 3% GST on physical gold purchases
    total_cost = (buy_price * qty) * 1.03 
    projected_growth = st.slider("Expected Annual Growth (%)", 5, 25, 12)
    years = st.slider("Hold Duration (Years)", 1, 10, 3)
    
    future_val = (buy_price * qty) * (1 + (projected_growth/100))**years
    raw_profit = future_val - total_cost
    
    # Taxing: 12.5% on profits if held > 24 months
    tax_rate = 0.125 if years >= 2 else 0.20 # Simple estimate: LTCG vs Slab
    tax_amt = raw_profit * tax_rate if raw_profit > 0 else 0
    final_takehome = raw_profit - tax_amt

    with col2:
        st.write(f"**Total Cost (with 3% GST):** ₹{total_cost:,.2f}")
        st.write(f"**Projected Value:** ₹{future_val:,.2f}")
        st.error(f"**Estimated Tax (Budget 2026):** ₹{tax_amt:,.2f}")
        st.success(f"**Final Survival Profit:** ₹{final_takehome:,.2f}")

else:
    st.error("Invalid Ticker. Please use GC=F for Gold or append .NS for Indian Stocks.")
