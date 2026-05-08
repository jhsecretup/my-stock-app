import streamlit as st
import yfinance as yf
import mplfinance as mpf

def run(n_codes, n_names, k_codes, k_names):
    market = st.radio("시장", ["NASDAQ", "KOSPI"], horizontal=True, key="chart_market")
    codes = n_codes if market == "NASDAQ" else k_codes
    names = n_names if market == "NASDAQ" else k_names
    
    stock_options = { (n.strip() if n.strip() else c.strip().upper()): c.strip().upper() for c, n in zip(codes, names) if c.strip() }
    
    if stock_options:
        sel_name = st.selectbox("종목 선택", list(stock_options.keys()))
        target = stock_options[sel_name]
        if market == "KOSPI" and not (target.endswith(".KS") or target.endswith(".KQ")): target += ".KS"
        
        tf = st.radio("주기", ["시봉", "일봉", "주봉"], index=1, horizontal=True)
        t_map = {"시봉": ("1h", "7d"), "일봉": ("1d", "1y"), "주봉": ("1wk", "2y")}
        
        data = yf.Ticker(target).history(period=t_map[tf][1], interval=t_map[tf][0]).tail(60)
        if not data.empty:
            fig, ax = mpf.plot(data, type='candle', style='charles', figsize=(12, 7), returnfig=True, y_on_right=True)
            st.pyplot(fig)