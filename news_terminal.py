import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import json
import os

# 1. 페이지 설정 (뉴스 가독성을 위해 와이드 모드 유지)
st.set_page_config(page_title="비서표 뉴스 터미널", layout="wide")

# 2. 스타일 시트 (뉴스 터미널 전용 UI)
st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; }
    .news-card {
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #1e88e5;
        background-color: #f8f9fa;
        margin-bottom: 10px;
        transition: 0.3s;
    }
    .news-card:hover { background-color: #e3f2fd; }
    .news-title { font-size: 1.1rem; font-weight: bold; color: #1565c0; text-decoration: none; }
    .news-meta { font-size: 0.85rem; color: #757575; margin-top: 5px; }
    .source-tag { background-color: #e0e0e0; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
    
    /* 사용자님이 좋아하시는 사이드바 입력창 가로 50% 제한 */
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] {
        width: 60% !important;
        flex-wrap: nowrap !important;
        gap: 5px !important;
    }
    div[data-testid="stTextInput"] div[data-baseweb="base-input"] {
        min-height: 30px !important;
        height: 30px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드 (기존 대시보드와 설정파일 공유)
def load_stock_settings():
    if os.path.exists('stock_settings.json'):
        with open('stock_settings.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"nas_codes": [], "nas_names": [], "kos_codes": [], "kos_names": []}

# 4. 뉴스 가져오기 로직 (속도 최적화)
def get_stock_news(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        news_list = ticker.news
        return news_list
    except:
        return []

# 5. 사이드바 - 종목 선택 중심
st.sidebar.title("📰 뉴스 터미널")
settings = load_stock_settings()

market = st.sidebar.radio("시장 선택", ["NASDAQ", "KOSPI"], horizontal=True)
codes = settings['nas_codes'] if market == "NASDAQ" else settings['kos_codes']
names = settings['nas_names'] if market == "NASDAQ" else settings['kos_names']

# 실제 등록된 종목만 필터링
stock_dict = {}
for c, n in zip(codes, names):
    if c.strip():
        display = n.strip() if n.strip() else c.strip().upper()
        stock_dict[display] = c.strip().upper()

st.sidebar.divider()
selected_stock_name = st.sidebar.selectbox("🎯 뉴스 분석 종목", list(stock_dict.keys()) if stock_dict else ["등록된 종목 없음"])

# 6. 메인 화면 레이아웃 (2단 구성)
col_list, col_content = st.columns([1, 1.5])

if stock_dict and selected_stock_name != "등록된 종목 없음":
    target_code = stock_dict[selected_stock_name]
    
    # KOSPI 접미사 처리
    full_code = target_code
    if market == "KOSPI" and not (full_code.endswith(".KS") or full_code.endswith(".KQ")):
        full_code += ".KS"

    with col_list:
        st.subheader(f"🔍 {selected_stock_name} 헤드라인")
        with st.spinner('최신 뉴스를 불러오는 중...'):
            news_items = get_stock_news(full_code)
        
        if news_items:
            for i, item in enumerate(news_items[:8]): # 최신 8개
                # 발행 시간 변환
                pub_time = datetime.fromtimestamp(item['providerPublishTime']).strftime('%m/%d %H:%M')
                
                # 뉴스 카드 UI
                with st.container():
                    st.markdown(f"""
                    <div class="news-card">
                        <a href="{item['link']}" target="_blank" class="news-title">{item['title']}</a>
                        <div class="news-meta">
                            <span class="source-tag">{item['publisher']}</span> | {pub_time}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("검색된 최신 뉴스가 없습니다.")

    with col_content:
        st.subheader("📊 실시간 시황 요약")
        # 뉴스 옆에 작은 미니 차트 배치 (흐름 확인용)
        try:
            data = yf.Ticker(full_code).history(period="5d", interval="15m")
            if not data.empty:
                st.line_chart(data['Close'], height=250)
                
                # 간단한 종목 정보
                info = yf.Ticker(full_code).fast_info
                c1, c2, c3 = st.columns(3)
                c1.metric("현재가", f"{info['last_price']:.2f}")
                c2.metric("거래량", f"{int(info['last_volume']):,}")
                c3.metric("시가총액", f"{info['market_cap']/1e9:.1f}B")
        except:
            st.write("시황 정보를 불러올 수 없습니다.")
        
        st.divider()
        st.write("💡 **팁:** 뉴스 제목을 클릭하면 원문 기사로 연결됩니다. 미국 주식 뉴스는 주로 영어로 제공됩니다.")

else:
    st.warning("사이드바에서 종목을 선택해 주세요.")