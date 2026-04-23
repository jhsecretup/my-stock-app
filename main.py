import streamlit as st
import pandas as pd
import json
import os
import requests
from bs4 import BeautifulSoup
import mplfinance as mpf
import yfinance as yf # 차트 데이터는 안정성을 위해 유지하되, 현재가는 구글에서 가져옵니다.

# 1. 페이지 설정
st.set_page_config(page_title="비서표 실시간 대시보드", layout="wide")

# 2. 데이터 로드/저장
def load_settings():
    if os.path.exists('stock_settings.json'):
        try:
            with open('stock_settings.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key in ['nas_codes', 'nas_names', 'kos_codes', 'kos_names']:
                    if len(data.get(key, [])) < 20:
                        data[key] = data.get(key, []) + [""] * (20 - len(data.get(key, [])))
                return data
        except: pass
    return {"nas_codes": [""]*20, "nas_names": [""]*20, "kos_codes": [""]*20, "kos_names": [""]*20}

def save_settings(data):
    with open('stock_settings.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

saved_data = load_settings()

# 3. 스타일 시트
st.markdown("""
    <style>
    .block-container { padding-top: 3rem !important; }
    .title-style { font-size: 1.6rem !important; font-weight: bold; margin-bottom: 1.5rem; color: #333; text-align: center; }
    .metric-container { text-align: center; margin-bottom: 15px; }
    .metric-label { font-size: 1rem; color: #666; margin-bottom: 5px; }
    .metric-text { font-size: 1.5rem !important; font-weight: bold; white-space: nowrap; }
    .up { color: #ef5350; } .down { color: #1e88e5; }
    .list-row { display: flex; justify-content: space-around; align-items: center; padding: 10px 15px; border-bottom: 1px solid #eee; text-align: center; }
    .list-item { font-size: 1.1rem; font-weight: bold; flex: 1; }
    .list-header { font-size: 1rem; font-weight: bold; color: #555; flex: 1; }
    </style>
    """, unsafe_allow_html=True)

# 4. 실시간 데이터 크롤링 함수 (Google Finance 기반)
def get_realtime_price(ticker, market_type):
    try:
        # 구글 파이낸스 주소 설정
        if market_type == "KOSPI":
            search_ticker = f"KRX:{ticker.replace('.KS', '')}"
        else:
            search_ticker = ticker
            
        url = f"https://www.google.com/search?q=google+finance+{search_ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 구글 검색 결과에서 가격 및 등락 추출
        price = soup.find('div', {'class': 'YMlS1d'}).text # 현재가
        change_info = soup.find('span', {'class': 'W7S99'}).text # 등락폭 및 퍼센트
        
        # 수치 정리
        is_up = "+" in change_info or "▲" in change_info
        status = "up" if is_up else "down"
        
        return price, change_info, status
    except:
        return None, None, "black"

@st.cache_data(ttl=10) # 갱신 버튼 대신 10초마다 자동 만료되도록 설정
def get_market_indices():
    indices = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "GOLD": "GC=F", "USD-KRW": "KRW=X"}
    info = []
    for name, ticker in indices.items():
        try:
            # 지수는 yfinance를 쓰되, 기간을 아주 짧게 잡아 로딩 속도 최적화
            hist = yf.Ticker(ticker).history(period="2d")
            curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
            diff, pct = curr - prev, (curr - prev) / prev * 100
            status, sym = ("up", "▲") if diff >= 0 else ("down", "▼")
            val = f"{curr:,.2f}   {sym}{abs(diff):,.2f} ({abs(pct):.2f}%)"
            info.append({"name": name, "val": val, "status": status, "ticker": ticker})
        except: pass
    return info

# 5. 사이드바
st.sidebar.title("🛠️ 종목 설정")
new_nas_codes, new_nas_names = [], []
with st.sidebar.expander("🇺🇸 NASDAQ 종목", expanded=True):
    for i in range(20):
        new_nas_codes.append(st.text_input(f"NAS 코드 {i+1}", value=saved_data['nas_codes'][i], key=f"nc{i}"))
        new_nas_names.append(st.text_input(f"NAS 이름 {i+1}", value=saved_data['nas_names'][i], key=f"nn{i}"))

new_kos_codes, new_kos_names = [], []
with st.sidebar.expander("🇰🇷 KOSPI 종목", expanded=False):
    for i in range(20):
        new_kos_codes.append(st.text_input(f"KOS 코드 {i+1}", value=saved_data['kos_codes'][i], key=f"kc{i}"))
        new_kos_names.append(st.text_input(f"KOS 이름 {i+1}", value=saved_data['kos_names'][i], key=f"kn{i}"))

if st.sidebar.button("💾 리스트 영구 저장", use_container_width=True):
    save_settings({"nas_codes": new_nas_codes, "nas_names": new_nas_names, "kos_codes": new_kos_codes, "kos_names": new_kos_names})
    st.sidebar.success("저장 완료!")

# 6. 메인 레이아웃
st.markdown('<div class="title-style">📈 비서표 실시간 투자 대시보드</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🏠 시장 지표", "📋 종목 리스트", "📊 개별 종목 차트"])

# --- Tab 1: 시장 지표 ---
with tab1:
    m_info = get_market_indices()
    if m_info:
        cols = st.columns(4)
        for i, m in enumerate(m_info):
            with cols[i]:
                st.markdown(f'<div class="metric-container"><div class="metric-label">{m["name"]}</div><div class="metric-text {m["status"]}">{m["val"]}</div></div>', unsafe_allow_html=True)
        st.divider()
        # 하단 캔들 차트는 yfinance 데이터 활용 (기존 로직)
        c_cols = st.columns(2)
        for idx, m in enumerate(m_info[:4]):
            with c_cols[idx % 2]:
                try:
                    data = yf.Ticker(m['ticker']).history(period="60d")
                    fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(10, 6), returnfig=True)
                    ax[0].set_title(m['name'], fontsize=16, fontweight='bold'); st.pyplot(fig)
                except: pass

# --- Tab 2: 종목 리스트 (실시간 크롤링 적용) ---
with tab2:
    selected_market = st.radio("", ["NASDAQ", "KOSPI"], horizontal=True, label_visibility="collapsed")
    codes = new_nas_codes if selected_market == "NASDAQ" else new_kos_codes
    names = new_nas_names if selected_market == "NASDAQ" else new_kos_names
    
    st.markdown(f"""<div class="list-row" style="background-color: #f8f9fa; border-top: 2px solid #333; margin-top: 5px;">
        <div class="list-header">종목명</div><div class="list-header">현재가</div><div class="list-header">등락폭 (율)</div>
    </div>""", unsafe_allow_html=True)
    
    for c, n in zip(codes, names):
        if c.strip():
            price, change, status = get_realtime_price(c.strip().upper(), selected_market)
            if price:
                st.markdown(f"""<div class="list-row">
                    <div class="list-item">{n if n else c}</div><div class="list-item">{price}</div><div class="list-item {status}">{change}</div>
                </div>""", unsafe_allow_html=True)

# --- Tab 3: 개별 종목 차트 ---
with tab3:
    # 종목 선택 셀렉트박스
    valid_codes = [c.strip().upper() for c in codes if c.strip()]
    if valid_codes:
        selected_code = st.selectbox("차트를 볼 종목 선택", valid_codes)
        c_tf = st.radio("", ["시봉", "일봉", "주봉"], index=1, horizontal=True)
        t_map = {"시봉": ("1h", "7d"), "일봉": ("1d", "1y"), "주봉": ("1wk", "2y")}
        
        try:
            data = yf.Ticker(selected_code).history(period=t_map[c_tf][1], interval=t_map[c_tf][0]).tail(60)
            # 실시간 가격은 구글에서 다시 가져와서 제목에 표시
            price, change, status = get_realtime_price(selected_code, selected_market)
            
            fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(12, 7), returnfig=True)
            ax[0].set_title(f"{selected_code}   {price}   {change}", 
                           fontsize=24, fontweight='bold', 
                           color="red" if status == "up" else "blue", loc='center', pad=20)
            st.pyplot(fig)
        except: st.error("차트 데이터를 불러올 수 없습니다.")
