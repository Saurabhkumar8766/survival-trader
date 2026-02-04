import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
from textblob import TextBlob
import numpy as np
from sklearn.linear_model import LinearRegression

# --- 1. CORE CONFIG & MOBILE FIX ---
st.set_page_config(page_title="Survival Trader Pro", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=600)
def get_live_data(ticker):
    try:
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
    st.header("👤 Portfolio Settings")
    my_inv = st.number_input("Investment Amount (₹)", value=1162.33)
    my_buy = st.number_input("My Buy Price (1g)", value=15516.0)
    st.divider()
    st.subheader("⚠️ Stop-Loss Risk")
    stop_loss_pct = st.slider("Protect My Capital (% Drop)", 1.0, 10.0, 3.0)
    stop_price_1g = my_buy * (1 - (stop_loss_pct / 100))
    st.divider()
    asset = st.text_input("Ticker Symbol", "GC=F")
    if st.button("🔄 Full Market Refresh"):
        st.cache_data.clear()
        st.rerun()

# --- 3. SURVIVAL & PREDICTION LOGIC ---
df = get_live_data(asset)
if df is not None:
    cp = float(df['Close'].iloc[-1].item())
    low_5d = float(df['Low'].tail(120).min().item())
    
    # ADJUSTED PREMIUM: Increased to 12% to match your ₹16,280 Paytm Live Price
    live_price_1g = ((cp * rate) / 31.1035) * 1.12
    
    # Portfolio Real-Time Math
    current_total_value = (my_inv / my_buy) * live_price_1g
    current_pnl = current_total_value - my_inv
    pnl_pct = (current_pnl / my_inv) * 100

    # 7-Day Forecast (Machine Learning)
    df_p = df.copy(); df_p['Day'] = np.arange(len(df_p))
    model = LinearRegression().fit(df_p[['Day']], df_p['Close'])
    pred_usd = model.predict(np.array([[len(df_p) + 7]]))[0].item()
    pred_1g_price = ((pred_usd * rate) / 31.1035) * 1.12
    pred_portfolio_total = (my_inv / my_buy) * pred_1g_price

    # --- 4. MAIN DASHBOARD ---
    st.title("🛡️ Survival Trader Pro")
    
    if live_price_1g <= stop_price_1g:
        st.error(f"## 🚨 SELL ALERT: STOP-LOSS TRIGGERED")
        st.write(f"Price is below safety floor. Save your capital now!")
    elif cp > (low_5d * 1.04):
        st.success("## 🟢 BUY SIGNAL")
        st.write("**Survival Action:** Momentum is up. Recovery phase active.")
    else:
        st.warning("## 🟡 WAIT / STABLE")

    st.divider()
    st.subheader("📊 My Real-Time Scoreboard")
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Live 1g Price", f"₹{live_price_1g:,.2f}")
    with m2: st.metric("Profit / Loss", f"₹{current_pnl:,.2f}", delta=f"{pnl_pct:.2f}%")
    with m3: st.metric("Total Portfolio Value", f"₹{current_total_value:,.2f}")

    st.divider()
    st.subheader("🔮 7-Day Growth Projection")
    f1, f2 = st.columns(2)
    with f1: st.metric("Predicted 1g Price", f"₹{pred_1g_price:,.2f}")
    with f2: st.metric("Predicted Portfolio", f"₹{pred_portfolio_total:,.2f}", 
                       delta=f"₹{(pred_portfolio_total - current_total_value):,.2f}")

    # --- 5. THE LIVE CHART (MOBILE FIX) ---
    st.divider()
    st.subheader("📉 Market Trend (Candlestick)")
    # MOBILE FIX: Forcing height and explicit container width
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], 
        low=df['Low'], close=df['Close'],
        increasing_line_color='#26a69a', 
        decreasing_line_color='#ef5350'
    )])
    # Forced mobile responsiveness
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=10,r=10,b=10,t=10))
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("💰 Budget 2026 Tax Predictor"):
        years = st.slider("Hold Duration (Years)", 1, 10, 3)
        tax = (current_total_value * (1.12)**years - current_total_value) * (0.125 if years >= 2 else 0.20)
        st.write(f"Estimated tax on 12% growth in {years} years: **₹{tax:,.2f}**")
else:
    st.error("Market data connection failed. Refreshing...")
