import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import json
import os
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 데이터 로드/보정
def load_settings():
    if 'current_settings' in st.session_state:
        data = st.session_state.current_settings
    elif os.path.exists('stock_settings.json'):
        try:
            with open('stock_settings.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: data = {}
    else: data = {}
    for key in ['nas_codes', 'nas_names', 'kos_codes', 'kos_names']:
        if key not in data: data[key] = [""] * 50
        else: data[key] = (data[key] + [""] * 50)[:50]
    return data

# 3. 스타일 시트 (V11.3 디자인 유지 + 테이블 스타일 추가)
st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; }
    .title-style { font-size: 1.6rem !important; font-weight: bold; margin-bottom: 1.5rem; color: #333; text-align: center; }
    
    /* 사이드바 가로 폭 제한 (사용자님 선호 스타일) */
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] { width: 55% !important; flex-wrap: nowrap !important; gap: 5px !important; }
    
    /* 리스트 디자인 */
    .list-row { display: flex; justify-content: space-around; align-items: center; padding: 10px 15px; border-bottom: 1px solid #eee; text-align: center; }
    .list-item { font-size: 1rem; font-weight: bold; flex: 1; }
    .metric-label { font-size: 0.8rem; color: #666; }
    .up { color: #ef5350; } .down { color: #1e88e5; }
    
    /* 분석 탭 전용 테이블 스타일 */
    .analysis-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    .analysis-table th { background-color: #f8f9fa; padding: 10px; font-size: 0.85rem; border-bottom: 2px solid #dee2e6; }
    .analysis-table td { padding: 12px 10px; border-bottom: 1px solid #eee; text-align: center; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

# 4. 데이터 추출 로직
@st.cache_data(ttl=3600) # 상세 정보는 로딩이 길어 1시간 동안 캐시 유지
def get_company_valuation(ticker_code, market_type):
    try:
        full_code = ticker_code
        if market_type == "KOSPI" and not (full_code.endswith(".KS") or full_code.endswith(".KQ")):
            full_code += ".KS"
        
        t = yf.Ticker(full_code)
        info = t.info
        
        # 단위 변환 (시가총액 조 단위 또는 억 단위)
        m_cap = info.get('marketCap', 0)
        if market_type == "NASDAQ":
            m_cap_disp = f"${m_cap/1e9:.1f}B" # 빌리언 달러
        else:
            m_cap_disp = f"{m_cap/1e12:.1f}조" if m_cap >= 1e12 else f"{m_cap/1e8:.0f}억"
            
        return {
            "name": info.get('shortName', ticker_code),
            "price": info.get('currentPrice', 0),
            "m_cap": m_cap_disp,
            "per": info.get('trailingPE', "-"),
            "pbr": info.get('priceToBook', "-"),
            "div": f"{info.get('dividendYield', 0)*100:.1f}%" if info.get('dividendYield') else "-"
        }
    except: return None

# ... (중략: get_market_data, get_stock_info 등 기존 함수들 유지)

# 5. 사이드바 및 메인 탭 구성
saved_data = load_settings()
# (기존 사이드바 입력 로직 동일)
# [생략된 부분은 기존 V11.3의 사이드바 렌더링 코드와 같습니다]
# ... (생략된 사이드바 입력창 코드)

# [여기가 핵심: 메인 레이아웃]
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(["🏠 시장 지표", "📋 종목 리스트", "📊 차트 분석", "💎 기업 가치 분석"])

# Tab 1, 2, 3는 기존과 동일 (생략)

with tab4:
    st.subheader("💎 주요 종목 기업 가치 분석")
    market_sel = st.radio("시장 선택", ["NASDAQ", "KOSPI"], horizontal=True, key="val_market")
    
    current_codes = [c for c in (saved_data['nas_codes'] if market_sel == "NASDAQ" else saved_data['kos_codes']) if c.strip()]
    current_names = [n for n in (saved_data['nas_names'] if market_sel == "NASDAQ" else saved_data['kos_names']) if n.strip()]
    
    if not current_codes:
        st.info("사이드바에 종목을 먼저 등록해 주세요.")
    else:
        if st.button("🚀 데이터 분석 시작 (실시간)", use_container_width=True):
            valuation_list = []
            progress_bar = st.progress(0)
            
            for i, code in enumerate(current_codes):
                val_data = get_company_valuation(code, market_sel)
                if val_data:
                    valuation_list.append(val_data)
                progress_bar.progress((i + 1) / len(current_codes))
            
            if valuation_list:
                # 테이블 헤더 생성
                cols = st.columns([2, 1.5, 1.2, 1, 1, 1])
                headers = ["종목명", "시가총액", "현재가", "PER", "PBR", "배당"]
                for col, header in zip(cols, headers):
                    col.markdown(f"**{header}**")
                st.divider()
                
                # 데이터 행 생성
                for v in valuation_list:
                    c = st.columns([2, 1.5, 1.2, 1, 1, 1])
                    c[0].write(v['name'])
                    c[1].write(v['m_cap'])
                    c[2].write(f"{v['price']:,}")
                    c[3].write(f"{v['per']}" if v['per'] == "-" else f"{v['per']:.1f}")
                    c[4].write(f"{v['pbr']}" if v['pbr'] == "-" else f"{v['pbr']:.1f}")
                    c[5].write(v['div'])
            else:
                st.error("데이터를 불러오지 못했습니다.")

# [나머지 탭 로직은 기존 V11.3 유지]
