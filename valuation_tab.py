import streamlit as st
import yfinance as yf
import pandas as pd

def run(n_codes, n_names, k_codes, k_names):
    market = st.radio("시장", ["NASDAQ", "KOSPI"], horizontal=True, key="val_market")
    codes = [c for c in (n_codes if market == "NASDAQ" else k_codes) if c.strip()]
    
    if st.button("🚀 가치 데이터 분석 시작"):
        res = []
        pb = st.progress(0)
        for i, c in enumerate(codes):
            try:
                sym = c.strip().upper() + (".KS" if market == "KOSPI" and not (c.endswith(".KS") or c.endswith(".KQ")) else "")
                inf = yf.Ticker(sym).info
                mc = inf.get('marketCap', 0)
                mc_d = f"${mc/1e9:.1f}B" if market == "NASDAQ" else (f"{mc/1e12:.1f}조" if mc >= 1e12 else f"{mc/1e8:.0f}억")
                res.append({
                    "종목명": inf.get('shortName', c),
                    "시가총액": mc_d,
                    "현재가": f"{inf.get('currentPrice', 0):,}",
                    "PER": round(inf.get('trailingPE', 0), 2) if inf.get('trailingPE') else "-",
                    "PBR": round(inf.get('priceToBook', 0), 2) if inf.get('priceToBook') else "-",
                    "배당률": f"{inf.get('dividendYield', 0)*100:.1f}%" if inf.get('dividendYield') else "-"
                })
            except: pass
            pb.progress((i+1)/len(codes))
        
        if res:
            st.dataframe(pd.DataFrame(res), use_container_width=True)