import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os

# 1. 페이지 설정 (단독 앱처럼 구성)
st.set_page_config(page_title="비서표 기업가치 분석기", layout="wide")

# 2. 기존 설정 파일(stock_settings.json)에서 종목 불러오기
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
    .title-text { font-size: 2rem !important; font-weight: bold; color: #1E88E5; text-align: center; margin-bottom: 2rem; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; height: 3rem; background-color: #1E88E5; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="title-text">💎 실시간 기업 가치 분석 터미널</div>', unsafe_allow_html=True)

# 4. 데이터 로드 및 시장 선택
stocks = load_my_stocks()
market = st.radio("분석할 시장을 선택하세요", ["🇺🇸 NASDAQ", "🇰🇷 KOSPI"], horizontal=True)

codes = stocks['nas_codes'] if "NASDAQ" in market else stocks['kos_codes']
names = stocks['nas_names'] if "NASDAQ" in market else stocks['kos_names']

# 실제 코드가 있는 종목만 필터링
valid_stocks = [(c, n) for c, n in zip(codes, names) if c.strip()]

if not valid_stocks:
    st.warning("등록된 종목이 없습니다. stock_settings.json 파일을 확인해주세요.")
else:
    st.info(f"현재 등록된 {len(valid_stocks)}개 종목의 데이터를 수집합니다.")
    
    if st.button("🚀 분석 시작 (실시간 데이터 호출)"):
        results = []
        progress_bar = st.progress(0)
        
        for i, (code, name) in enumerate(valid_stocks):
            try:
                # 티커 심볼 보정
                ticker = code.strip().upper()
                if "KOSPI" in market and not (ticker.endswith(".KS") or ticker.endswith(".KQ")):
                    ticker += ".KS"
                
                # 데이터 호출
                stock_obj = yf.Ticker(ticker)
                info = stock_obj.info
                
                # 시가총액 변환
                m_cap = info.get('marketCap', 0)
                if "NASDAQ" in market:
                    m_cap_disp = f"${m_cap/1e9:.1f}B"
                else:
                    m_cap_disp = f"{m_cap/1e12:.1f}조" if m_cap >= 1e12 else f"{m_cap/1e8:.0f}억"
                
                results.append({
                    "순번": i + 1,
                    "종목명": name if name.strip() else code,
                    "티커": code,
                    "시가총액": m_cap_disp,
                    "현재가": f"{info.get('currentPrice', 0):,}",
                    "PER": round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else "-",
                    "PBR": round(info.get('priceToBook', 0), 2) if info.get('priceToBook') else "-",
                    "배당수익률": f"{info.get('dividendYield', 0)*100:.1f}%" if info.get('dividendYield') else "-"
                })
            except Exception as e:
                pass # 에러 난 종목은 건너뜀
            
            progress_bar.progress((i + 1) / len(valid_stocks))
        
        if results:
            df = pd.DataFrame(results)
            st.success("데이터 수집 완료!")
            
            # 테이블 출력
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # 간단한 요약
            st.caption("※ PER/PBR 데이터는 Yahoo Finance 실시간 제공 수치를 기준으로 합니다.")
        else:
            st.error("데이터를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.")