import streamlit as st
import yfinance as yf
import mplfinance as mpf

def run():
    tickers = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "GOLD": "GC=F", "USD-KRW": "KRW=X"}
    cols = st.columns(len(tickers))
    
    for i, (name, sym) in enumerate(tickers.items()):
        try:
            hist = yf.Ticker(sym).history(period="2d")
            curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
            diff, pct = curr - prev, ((curr - prev) / prev) * 100
            color = "#ef5350" if diff >= 0 else "#1e88e5"
            arrow = "▲" if diff >= 0 else "▼"
            
            with cols[i]:
                st.markdown(f"""
                <div style="text-align:center; border:1px solid #eee; padding:10px; border-radius:10px;">
                    <div style="color:#666; font-size:0.9rem;">{name}</div>
                    <div style="color:{color}; font-size:1.2rem; font-weight:bold;">{curr:,.2f}</div>
                    <div style="color:{color}; font-size:0.8rem;">{arrow}{abs(diff):,.2f} ({pct:.2f}%)</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 미니 차트
                data = yf.Ticker(sym).history(period="1mo")
                st.line_chart(data['Close'], height=150)
        except: pass