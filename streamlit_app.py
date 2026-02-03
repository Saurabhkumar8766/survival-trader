import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
from textblob import TextBlob
import numpy as np
from sklearn.linear_model import LinearRegression

# --- 1. CONFIG & MOBILE OPTIMIZATION ---
st.set_page_config(page_title="Survival Trader Pro", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=600)
def get_live_data(ticker):
    try:
        # download is safer for mobile browsers
        data = yf.download(ticker, period="1mo", interval="1h", progress=False)
        return data if not data.empty else None
    except: return None

@st.cache_data(ttl=3600)
def get_usd_inr():
    try: return requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()["rates"]["INR"]
    except: return 91.52 

rate = get_usd_inr()

# --- 2. SIDEBAR (CONTROLS) ---
with st.sidebar:
    st.header("⚙️ Settings")
    my_inv = st.number_input("Invested (₹)", value=1162.0)
    my_buy = st.number_input("Buy Price (1g)", value=15516.0)
    st.divider()
    # SAFETY: Stop-loss protection slider
    stop_loss_pct = st.slider("Capital Protection (%)", 1.0, 10.0, 3.0)
    stop_price = my_buy * (1 - (stop_loss_pct / 100))
    st.warning(f"Safety Floor: ₹{stop_price:,.2f}")
    
    if st.button("🔄 Refresh Market"):
        st.cache_data.clear()
        st.rerun()

# --- 3. SURVIVAL LOGIC ---
df = get_live_data("GC=F")
if df is not None:
    cp = float(df['Close'].iloc[-1].item())
    live_price = ((cp * rate) / 31.1035) * 1.10
    
    # Portfolio Status
    total_val = (my_inv / my_buy) * live_price
    pnl = total_val - my_inv
    pnl_pct = (pnl / my_inv) * 100

    # --- 4. MAIN DASHBOARD ---
    st.title("🛡️ Survival Trader Pro")
    
    # SAFETY ALERTS
    if live_price <= stop_price:
        st.error(f"## 🚨 SELL ALERT: STOP-LOSS TRIGGERED")
        st.write(f"Price is below safety floor. Sell now to protect your ₹{total_val:,.2f}!")
    else:
        st.success("## 🟢 BUY / HOLD")
        st.write("Momentum is up. Your capital is currently protected.")

    # LIVE METRICS
    st.divider()
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Live 1g Price", f"₹{live_price:,.2f}")
    with m2: st.metric("Current P&L", f"₹{pnl:,.2f}", delta=f"{pnl_pct:.2f}%")
    with m3: st.metric("Total Portfolio Value", f"₹{total_val:,.2f}")

    # 7-DAY FORECAST
    st.divider()
    st.subheader("🔮 7-Day Forecast")
    df_p = df.copy(); df_p['Day'] = np.arange(len(df_p))
    model = LinearRegression().fit(df_p[['Day']], df_p['Close'])
    p_usd = model.predict(np.array([[len(df_p) + 7]]))[0].item()
    p_1g = ((p_usd * rate) / 31.1035) * 1.10
    p_total = (my_inv / my_buy) * p_1g
    
    f1, f2 = st.columns(2)
    with f1: st.metric("Expected 1g Price", f"₹{p_1g:,.2f}")
    with f2: st.metric("Expected Portfolio", f"₹{p_total:,.2f}", delta=f"₹{(p_total - total_val):,.2f}")

    # MOBILE-FRIENDLY CHART
    st.divider()
    st.subheader("📉 Live Market Trend")
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    # Dotted red line for your Stop-Loss Safety
    stop_usd = (stop_price / 1.10 / rate * 31.1035)
    fig.add_hline(y=stop_usd, line_dash="dash", line_color="red", annotation_text="SAFETY FLOOR")
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,b=0,t=0))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Connecting to global servers... Tap Refresh in 5 seconds.")
