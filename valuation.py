import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os

# 1. 페이지 설정
st.set_page_config(page_title="기업가치분석", layout="wide")

# 2. 데이터 로드 (stock_settings.json 연동)
def load_my_stocks():
    if os.path.exists('stock_settings.json'):
        try:
            with open('stock_settings.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"nas_codes": [], "nas_names": [], "kos_codes": [], "kos_names": []}

# 3. 스타일 설정
st.markdown("""
    <style>
    /* 상단 여백 보정: 잘림 방지를 위해 대시보드와 유사한 3rem 확보 */
    .block-container { padding-top: 3rem !important; }
    
    /* 타이틀 스타일: 크기를 살짝 줄이고 여백 조정 */
    .main-title { 
        font-size: 1.6rem !important; 
        font-weight: bold; 
        color: #333; 
        text-align: center; 
        margin-bottom: 2rem; 
    }
    
    /* 버튼 및 라디오 버튼 높이 조절 */
    .stButton>button { height: 2.8rem; border-radius: 8px; font-weight: bold; }
    
    /* 테이블 가독성 */
    .stDataFrame { font-size: 0.95rem; }
    </style>
    """, unsafe_allow_html=True)

# 상단 타이틀
st.markdown('<div class="main-title">💎 기업가치분석</div>', unsafe_allow_html=True)

# 4. 데이터 준비
stocks = load_my_stocks()

# 상단 컨트롤바 (알림 박스 제거 및 구성 단순화)
col1, col2 = st.columns([3, 1])

with col1:
    market = st.radio("시장 선택", ["NASDAQ", "KOSPI"], horizontal=True, label_visibility="collapsed")

# 종목 데이터 필터링
codes = stocks['nas_codes'] if market == "NASDAQ" else stocks['kos_codes']
names = stocks['nas_names'] if market == "NASDAQ" else stocks['kos_names']
valid_stocks = [(c.strip(), n.strip()) for c, n in zip(codes, names) if c.strip()]

with col2:
    run_analysis = st.button("🚀 분석 시작", use_container_width=True)

st.divider()

# 5. 분석 로직
if run_analysis:
    if not valid_stocks:
        st.warning("등록된 종목이 없습니다.")
    else:
        results = []
        progress_bar = st.progress(0)
        
        for i, (code, name) in enumerate(valid_stocks):
            try:
                ticker = code.upper()
                if market == "KOSPI" and not (ticker.endswith(".KS") or ticker.endswith(".KQ")):
                    ticker += ".KS"
                
                stock_obj = yf.Ticker(ticker)
                info = stock_obj.info
                
                m_cap = info.get('marketCap', 0)
                if market == "NASDAQ":
                    m_cap_disp = f"${m_cap/1e9:.1f}B"
                else:
                    m_cap_disp = f"{m_cap/1e12:.1f}조" if m_cap >= 1e12 else f"{m_cap/1e8:.0f}억"
                
                results.append({
                    "종목명": name if name else code,
                    "티커": code,
                    "시가총액": m_cap_disp,
                    "현재가": f"{info.get('currentPrice', 0):,}",
                    "PER": round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else "-",
                    "PBR": round(info.get('priceToBook', 0), 2) if info.get('priceToBook') else "-",
                    "ROE(%)": round(info.get('returnOnEquity', 0) * 100, 1) if info.get('returnOnEquity') else "-",
                    "배당률": f"{info.get('dividendYield', 0)*100:.1f}%" if info.get('dividendYield') else "-"
                })
            except:
                pass
            progress_bar.progress((i + 1) / len(valid_stocks))
        
        if results:
            df = pd.DataFrame(results)
            # 결과 테이블 출력
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"최근 분석 시점: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.error("데이터 수집 실패")
