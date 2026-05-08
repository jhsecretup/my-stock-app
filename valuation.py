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
    # 파일이 없거나 에러 시 빈 리스트 반환
    return {"nas_codes": [], "nas_names": [], "kos_codes": [], "kos_names": []}

# 3. 스타일 설정 (타이틀 크기 및 디자인)
st.markdown("""
    <style>
    .main-title { 
        font-size: 1.8rem !important; 
        font-weight: bold; 
        color: #333; 
        text-align: center; 
        margin-top: -1rem;
        margin-bottom: 2rem; 
    }
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        font-weight: bold; 
        height: 3rem; 
        background-color: #1E88E5; 
        color: white; 
    }
    /* 테이블 가독성 향상 */
    .stDataFrame { border: 1px solid #eee; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 수정된 간결한 타이틀
st.markdown('<div class="main-title">💎 기업가치분석</div>', unsafe_allow_html=True)

# 4. 데이터 로드 및 시장 선택
stocks = load_my_stocks()
col1, col2 = st.columns([1, 1])
with col1:
    market = st.radio("분석 시장 선택", ["🇺🇸 NASDAQ", "🇰🇷 KOSPI"], horizontal=True)

# 종목 데이터 매핑
codes = stocks['nas_codes'] if "NASDAQ" in market else stocks['kos_codes']
names = stocks['nas_names'] if "NASDAQ" in market else stocks['kos_names']

# 실제 데이터가 있는 종목만 추출
valid_stocks = [(c.strip(), n.strip()) for c, n in zip(codes, names) if c.strip()]

if not valid_stocks:
    st.warning("등록된 종목이 없습니다. 메인 대시보드에서 종목을 먼저 등록해주세요.")
else:
    st.info(f"선택하신 {market} 시장의 {len(valid_stocks)}개 종목을 분석할 준비가 되었습니다.")
    
    if st.button("🚀 실시간 데이터 분석 시작"):
        results = []
        progress_bar = st.progress(0)
        
        for i, (code, name) in enumerate(valid_stocks):
            try:
                ticker = code.upper()
                if "KOSPI" in market and not (ticker.endswith(".KS") or ticker.endswith(".KQ")):
                    ticker += ".KS"
                
                stock_obj = yf.Ticker(ticker)
                info = stock_obj.info
                
                # 시가총액 변환 로직
                m_cap = info.get('marketCap', 0)
                if "NASDAQ" in market:
                    m_cap_disp = f"${m_cap/1e9:.1f}B" # 빌리언 달러 단위
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
            st.success("✅ 실시간 가치 분석이 완료되었습니다.")
            
            # 테이블 출력 (인덱스 제외)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.caption("※ PER, PBR, ROE 데이터는 Yahoo Finance에서 제공하는 최근 12개월(TTM) 기준 수치입니다.")
        else:
            st.error("데이터를 수집하는 중에 문제가 발생했습니다. 종목 코드를 확인해주세요.")
