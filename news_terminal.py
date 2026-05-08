import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import json
import os

# 1. 페이지 설정
st.set_page_config(page_title="비서표 뉴스 터미널", layout="wide")

# 2. 스타일 시트
st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; }
    .news-card {
        padding: 15px; border-radius: 10px; border-left: 5px solid #1e88e5;
        background-color: #f8f9fa; margin-bottom: 12px;
    }
    .news-title { font-size: 1.1rem; font-weight: bold; color: #1565c0; text-decoration: none; display: block; }
    .news-meta { font-size: 0.85rem; color: #757575; margin-top: 8px; }
    .source-tag { background-color: #e0e0e0; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] { width: 60% !important; flex-wrap: nowrap !important; gap: 5px !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드
def load_stock_settings():
    try:
        if os.path.exists('stock_settings.json'):
            with open('stock_settings.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except: pass
    return {"nas_codes": [], "nas_names": [], "kos_codes": [], "kos_names": []}

# 4. 사이드바
st.sidebar.title("📰 뉴스 터미널")
settings = load_stock_settings()
market = st.sidebar.radio("시장 선택", ["NASDAQ", "KOSPI"], horizontal=True)
codes = settings.get('nas_codes', []) if market == "NASDAQ" else settings.get('kos_codes', [])
names = settings.get('nas_names', []) if market == "NASDAQ" else settings.get('kos_names', [])

stock_dict = {}
for c, n in zip(codes, names):
    if c and str(c).strip():
        ticker = str(c).strip().upper()
        display = str(n).strip() if n and str(n).strip() else ticker
        stock_dict[display] = ticker

selected_stock_name = st.sidebar.selectbox("🎯 뉴스 분석 종목", list(stock_dict.keys()) if stock_dict else ["등록 종목 없음"])

# 5. 메인 레이아웃
col_list, col_content = st.columns([1, 1.2])

if stock_dict and selected_stock_name != "등록 종목 없음":
    target_code = stock_dict[selected_stock_name]
    full_code = target_code + (".KS" if market == "KOSPI" and not (target_code.endswith(".KS") or target_code.endswith(".KQ")) else "")

    with col_list:
        st.subheader(f"🔍 {selected_stock_name} 헤드라인")
        try:
            news_items = yf.Ticker(full_code).news
            if news_items:
                for item in news_items[:10]:
                    # [V1.2 핵심] 모든 필드를 .get()으로 가져와서 KeyError 원천 봉쇄
                    content = item.get('content', item)
                    title = content.get('title') or content.get('headline') or "제목 없음"
                    link = content.get('clickThroughUrl', {}).get('url') or content.get('url') or content.get('link') or "#"
                    publisher = content.get('publisher') or "출처 미상"
                    
                    # 시간 변환 안전 장치
                    pub_time = "시간 미상"
                    raw_time = content.get('pubDate') or content.get('providerPublishTime')
                    if raw_time and isinstance(raw_time, (int, float)):
                        try: pub_time = datetime.fromtimestamp(raw_time).strftime('%m/%d %H:%M')
                        except: pass
                    
                    st.markdown(f"""
                    <div class="news-card">
                        <a href="{link}" target="_blank" class="news-title">{title}</a>
                        <div class="news-meta"><span class="source-tag">{publisher}</span> | {pub_time}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.info("최신 뉴스가 없습니다.")
        except: st.error("뉴스 로딩 중 오류가 발생했습니다.")

    with col_content:
        st.subheader("📊 실시간 시황")
        try:
            t_obj = yf.Ticker(full_code)
            hist = t_obj.history(period="5d", interval="30m")
            if not hist.empty:
                st.line_chart(hist['Close'], height=300)
                info = t_obj.fast_info
                st.metric("현재가", f"{info['last_price']:.2f}", f"{((info['last_price']-info['previous_close'])/info['previous_close']*100):.2f}%")
        except: st.write("시황 정보를 불러올 수 없습니다.")
else:
    st.warning("종목을 선택해 주세요.")
