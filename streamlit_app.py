import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
import numpy as np
from sklearn.linear_model import LinearRegression

# --- 1. CORE ENGINE & STABILITY ---
st.set_page_config(page_title="Survival Trader Pro", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=600)
def get_live_data(ticker):
    try:
        # download is used for high-reliability mobile rendering
        data = yf.download(ticker, period="1mo", interval="1h", progress=False)
        return data if not data.empty else None
    except: return None

@st.cache_data(ttl=3600)
def get_usd_inr():
    try: return requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()["rates"]["INR"]
    except: return 91.52 

rate = get_usd_inr()

# --- 2. SIDEBAR: PROFESSIONAL CONTROLS ---
with st.sidebar:
    st.header("👤 Portfolio Settings")
    my_inv = st.number_input("Investment Amount (₹)", value=1162.0)
    my_buy = st.number_input("My Buy Price (1g)", value=15516.0)
    st.divider()
    st.subheader("⚠️ Stop-Loss Safety")
    stop_loss_pct = st.slider("Capital Protection (%)", 1.0, 10.0, 3.0)
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
    live_price_1g = ((cp * rate) / 31.1035) * 1.10
    
    # Portfolio Math
    current_total_value = (my_inv / my_buy) * live_price_1g
    current_pnl = current_total_value - my_inv
    pnl_pct = (current_pnl / my_inv) * 100

    # 7-Day Forecast (Machine Learning)
    df_p = df.copy(); df_p['Day'] = np.arange(len(df_p))
    model = LinearRegression().fit(df_p[['Day']], df_p['Close'])
    pred_usd = model.predict(np.array([[len(df_p) + 7]]))[0].item()
    pred_1g_price = ((pred_usd * rate) / 31.1035) * 1.10
    pred_portfolio_total = (my_inv / my_buy) * pred_1g_price

    # --- 4. MAIN DASHBOARD ---
    st.title("🛡️ Survival Trader Pro")
    
    # SAFETY ALERT: STOP-LOSS
    if live_price_1g <= stop_price_1g:
        st.error(f"## 🚨 SELL ALERT: STOP-LOSS TRIGGERED")
        st.write(f"Protecting your Capital. Exit Price: ₹{stop_price_1g:,.2f}")
    elif cp > (low_5d * 1.04):
        st.success("## 🟢 BUY SIGNAL")
        st.write("**Plan:** Recovery phase. Your money is in the 'Profit Zone'.")
    else:
        st.warning("## 🟡 WAIT / STABLE")

    # LIVE SCOREBOARD (Everything you wanted)
    st.divider()
    st.subheader("📊 My Real-Time Scoreboard")
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Live 1g Price", f"₹{live_price_1g:,.2f}")
    with m2: st.metric("Profit / Loss", f"₹{current_pnl:,.2f}", delta=f"{pnl_pct:.2f}%")
    with m3: st.metric("Total Portfolio Value", f"₹{current_total_value:,.2f}")

    # 7-DAY FORECAST
    st.divider()
    st.subheader("🔮 7-Day Growth Projection")
    f1, f2 = st.columns(2)
    with f1: st.metric("Predicted 1g Price", f"₹{pred_1g_price:,.2f}")
    with f2: st.metric("Predicted Portfolio", f"₹{pred_portfolio_total:,.2f}", 
                       delta=f"₹{(pred_portfolio_total - current_total_value):,.2f}")

    # --- 5. THE ORIGINAL CHART CODE (UNTOUCHED COLORS) ---
    st.divider()
    st.subheader("📉 Market Trend (Candlestick)")
    with st.container(): # Added container for mobile stabilization
        fig = go.Figure(data=[go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], 
            low=df['Low'], close=df['Close'],
            increasing_line_color='#26a69a', # ORIGINAL GREEN
            decreasing_line_color='#ef5350'  # ORIGINAL RED
        )])
        # Added a red safety line on the chart
        stop_usd = (stop_price_1g / 1.10 / rate * 31.1035)
        fig.add_hline(y=stop_usd, line_dash="dash", line_color="red", annotation_text="SAFETY")
        
        fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("💰 Budget 2026 Tax Predictor"):
        years = st.slider("Hold Duration (Years)", 1, 10, 3)
        tax = (current_total_value * (1.12)**years - current_total_value) * (0.125 if years >= 2 else 0.20)
        st.write(f"Estimated tax in {years} years: **₹{tax:,.2f}**")
else:
    st.error("Market data connection failed. Refreshing...")
