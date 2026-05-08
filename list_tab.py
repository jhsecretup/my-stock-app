import streamlit as st
import yfinance as yf

def run(n_codes, n_names, k_codes, k_names):
    market = st.radio("시장 선택", ["NASDAQ", "KOSPI"], horizontal=True, key="list_market")
    codes = n_codes if market == "NASDAQ" else k_codes
    names = n_names if market == "NASDAQ" else k_names
    
    st.markdown("""<div style="display:flex; justify-content:space-around; background:#f8f9fa; padding:10px; font-weight:bold; border-top:2px solid #333;">
        <div style="flex:1; text-align:center;">종목명</div>
        <div style="flex:1; text-align:center;">현재가</div>
        <div style="flex:1; text-align:center;">등락률</div>
    </div>""", unsafe_allow_html=True)
    
    for c, n in zip(codes, names):
        if c.strip():
            try:
                sym = c.strip().upper() + (".KS" if market == "KOSPI" and not (c.endswith(".KS") or c.endswith(".KQ")) else "")
                hist = yf.Ticker(sym).history(period="2d")
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                diff, pct = curr - prev, ((curr-prev)/prev)*100
                color = "#ef5350" if diff >= 0 else "#1e88e5"
                p_disp = f"{curr:,.2f}$" if market == "NASDAQ" else f"{int(curr):,}"
                
                st.markdown(f"""<div style="display:flex; justify-content:space-around; padding:8px; border-bottom:1px solid #eee;">
                    <div style="flex:1; text-align:center; font-weight:bold;">{n if n.strip() else c}</div>
                    <div style="flex:1; text-align:center; color:{color};">{p_disp}</div>
                    <div style="flex:1; text-align:center; color:{color};">{pct:.2f}%</div>
                </div>""", unsafe_allow_html=True)
            except: pass