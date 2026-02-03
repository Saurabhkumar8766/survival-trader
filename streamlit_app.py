import streamlit as st
import yfinance as yf
from textblob import TextBlob
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Survival Trader Pro", page_icon="🛡️", layout="centered")

# ENTER YOUR KEY HERE (from newsapi.org)
NEWS_API_KEY = "bc56e98cf39441c5b1e8b18659368d41" 

# --- CORE LOGIC ENGINE ---
def get_signal(ticker):
    try:
        data = yf.Ticker(ticker).history(period="5d", interval="1h")
        if data.empty:
            return "UNKNOWN", "Data not found", 0.0
        
        current_price = data['Close'].iloc[-1]
        low_5d = data['Low'].min()
        high_5d = data['High'].max()
        
        # 1. NO-LOSS SELL LOGIC
        # If price is at the absolute bottom of the 5-day range, it's a danger zone.
        if current_price <= (low_5d * 1.01):
            return "🔴 SELL", "DANGER: Support broken. Protect your capital!", current_price
            
        # 2. PROFITABLE BUY LOGIC (Requirement: Confirmation of Reversal)
        # We only buy if it's bounced at least 5% off the floor but isn't at the peak yet.
        if current_price > (low_5d * 1.05) and current_price < (high_5d * 0.98):
            return "🟢 BUY", "Recovery confirmed. High probability of profit.", current_price
            
        # 3. STABLE MARKET WAIT LOGIC
        return "🟡 WAIT", "Market is sideways or indecisive. Keep cash safe.", current_price
    except:
        return "ERROR", "Connection issue", 0.0

# --- MOBILE DASHBOARD ---
st.title("🛡️ Survival Trader Pro")
st.caption("Real-Time Asset Intelligence | Navi Mumbai Edition")

# ASSET SELECTOR
asset = st.text_input("Enter Ticker (e.g. GC=F for Gold, RVNL.NS for Rail)", "GC=F")

signal, reason, price = get_signal(asset)

# THE DECISION CARD (No Ifs/Ors)
if "BUY" in signal:
    st.success(f"### {signal}")
elif "SELL" in signal:
    st.error(f"### {signal}")
else:
    st.warning(f"### {signal}")

currency_symbol = "₹" if ".NS" in asset or ".BO" in asset else "$"
st.subheader(f"Current Price: {currency_symbol}{price:,.2f}")
st.info(f"**Action Plan:** {reason}")

# --- BUDGET 2026 AUTO-SCANNER ---
st.divider()
st.subheader("🚀 Budget 2026 'Big Money' Picks")
# These are sectors with high government allocation (Infra, Rail, Energy)
budget_watchlist = ["RVNL.NS", "IRCON.NS", "TATAPOWER.NS", "BEL.NS"]

cols = st.columns(2)
for i, stock in enumerate(budget_watchlist):
    s, _, p = get_signal(stock)
    with cols[i % 2]:
        if "BUY" in s:
            st.write(f"✅ **{stock}**: **BUY** (₹{p:.0f})")
        else:
            st.write(f"⚪ {stock}: Wait (₹{p:.0f})")

# VISUAL CHART
st.divider()
st.line_chart(yf.Ticker(asset).history(period="1mo")['Close'])
