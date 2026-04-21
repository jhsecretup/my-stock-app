import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import json
import os
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 데이터 복구 및 로드 (image_2.png 기반 데이터 복원)
def load_and_restore_settings():
    # 캡처 화면(image_2.png)에서 확인된 데이터로 복구 데이터 구성
    restored_nas_codes = ["INTC", "AMD", "AMZN", "META"] + [""] * 16
    restored_nas_names = ["인텔/Intel", "AMD/AMD", "아마존/Amazon", "메타/Meta"] + [""] * 16
    
    # 기본 구조 (20개씩)
    default_data = {
        "nas_codes": restored_nas_codes,
        "nas_names": restored_nas_names,
        "kos_codes": [""] * 20,
        "kos_names": [""] * 20
    }

    # 만약 저장된 파일이 있다면 읽어오되, 위 복구 데이터를 우선 적용하는 안전장치
    if os.path.exists('stock_settings.json'):
        try:
            with open('stock_settings.json', 'r', encoding='utf-8') as f:
                saved = json.load(f)
                
                # 저장된 데이터가 V10.0 구조(20개)와 맞는지 확인 및 병합
                def sync_data(saved_list, restored_list):
                    result = restored_list.copy() # 복구 데이터 기반
                    if saved_list:
                        # 저장된 데이터가 비어있지 않은 칸만 덮어쓰기 (복구 데이터 보존)
                        for i in range(min(20, len(saved_list))):
                            if saved_list[i].strip(): # 저장된 내용이 있으면
                                result[i] = saved_list[i]
                    return result

                default_data["nas_codes"] = sync_data(saved.get("nas_codes"), restored_nas_codes)
                default_data["nas_names"] = sync_data(saved.get("nas_names"), restored_nas_names)
                default_data["kos_codes"] = sync_data(saved.get("kos_codes"), [""] * 20)
                default_data["kos_names"] = sync_data(saved.get("kos_names"), [""] * 20)
        except: pass

    return default_data

def save_settings(data):
    with open('stock_settings.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 복구된 데이터 로드
saved_data = load_and_restore_settings()

# 3. 스타일 시트 (모바일 가독성 및 디자인 통일)
st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
    .title-style { font-size: 1.3rem !important; font-weight: bold; margin-bottom: 1rem; color: #333; text-align: center; }
    
    /* 모바일에서 입력칸 레이벨 숨기기 (공간 확보 핵심) */
    div[data-testid="stWidgetLabel"] p { font-size: 0.8rem !important; color: #888 !important; }
    
    /* 입력창 간격 줄이기 */
    div[data-testid="stVerticalBlock"] > div { margin-bottom: -15px !important; }
    
    /* 지표 텍스트 크기 모바일 최적화 */
    .metric-text { font-size: 1.1rem !important; font-weight: bold; white-space: nowrap; }
    .metric-label { font-size: 0.8rem !important; }
    .up { color: #ef5350; } .down { color: #1e88e5; }
    
    /* 종목 리스트 행 디자인 */
    .list-row { display: flex; justify-content: space-around; align-items: center; padding: 10px 15px; border-bottom: 1px solid #eee; text-align: center; }
    .list-item { font-size: 1rem; font-weight: bold; flex: 1; }
    .list-header { font-size: 0.9rem; font-weight: bold; color: #555; flex: 1; }
    </style>
    """, unsafe_allow_html=True)

# 4. 유틸리티 함수
def parse_display_names(raw_name, ticker):
    if not raw_name: return ticker, ticker
    if '/' in raw_name:
        parts = [p.strip() for p in raw_name.split('/')]
        l_name = parts[0] if parts[0] else ticker
        c_name = parts[1] if len(parts) > 1 and parts[1] else l_name
        return l_name, c_name
    return raw_name, raw_name

@st.cache_data(ttl=60)
def get_market_data():
    tickers = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "GOLD": "GC=F", "USD-KRW": "KRW=X"}
    info = []
    for name, ticker in tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="3d")
            if not hist.empty and len(hist) >= 2:
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                diff, pct = curr - prev, ((curr - prev) / prev) * 100
                status, symbol = ("up", "▲") if diff >= 0 else ("down", "▼")
                # 가독성을 위해 현재가만 int로
                val = f"{int(curr):,} ({symbol}{int(abs(diff)):,})"
                info.append({"name": name, "val": val, "status": status, "ticker": ticker})
        except: pass
    return info

def get_stock_info(c, n, m_type):
    if not c: return None
    try:
        ticker_sym = c.strip().upper()
        hist = yf.Ticker(ticker_sym).history(period="2d")
        if not hist.empty and len(hist) >= 2:
            curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
            diff, pct = curr - prev, ((curr-prev)/prev)*100
            l_name, c_name = parse_display_names(n, ticker_sym)
            p_disp = f"{curr:,.2f}$" if m_type == "NASDAQ" else f"{int(curr):,}"
            c_disp = f"{abs(pct):.2f}%"
            return {"name": c_name, "price": p_disp, "change": c_disp, "status": "up" if diff >= 0 else "down", "curr": curr, "prev": prev}
    except: return None

# 5. 사이드바 설정 (모바일 강제 2열 배치 핵심 로직)
st.sidebar.title("🛠️ 모바일 종목 설정")

def render_mobile_sidebar(title, codes, names, prefix):
    new_codes, new_names = [], []
    with st.sidebar.expander(title, expanded=(prefix == "nc")):
        # 헤더 표시 (공간 절약)
        h1, h2 = st.columns([1, 1.5]) # 모바일에서 코드창은 좁게, 이름창은 넓게
        h1.caption("티커(코드)")
        h2.caption("표시 이름")
        
        for i in range(20):
            c1, c2 = st.columns([1, 1.5]) # 2열 강제 배치
            with c1:
                # label_visibility="collapsed"로 라벨을 숨겨 공간 확보
                c = st.text_input(f"C{i}", value=codes[i], key=f"{prefix}_c{i}", label_visibility="collapsed", placeholder=f"코드 {i+1}")
            with c2:
                n = st.text_input(f"N{i}", value=names[i], key=f"{prefix}_n{i}", label_visibility="collapsed", placeholder=f"이름 {i+1}")
            new_codes.append(c)
            new_names.append(n)
    return new_codes, new_names

new_nas_codes, new_nas_names = render_mobile_sidebar("🇺🇸 NASDAQ (20)", saved_data['nas_codes'], saved_data['nas_names'], "nc")
new_kos_codes, new_kos_names = render_mobile_sidebar("🇰🇷 KOSPI (20)", saved_data['kos_codes'], saved_data['kos_names'], "kc")

# 영구 저장 버튼 (사이드바 하단 고정)
if st.sidebar.button("💾 리스트 영구 저장"):
    save_settings({"nas_codes": new_nas_codes, "nas_names": new_nas_names, "kos_codes": new_kos_codes, "kos_names": new_kos_names})
    st.sidebar.success("데이터가 안전하게 저장되었습니다!")

# 6. 메인 레이아웃 (모바일 대응)
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🏠 지표", "📋 리스트", "📊 차트"])

with tab1:
    m_info = get_market_data()
    if m_info:
        # 지표 텍스트 크기 모바일 대응 (st.metric 사용)
        cols = st.columns(len(m_info))
        for i, m in enumerate(m_info):
            with cols[i]: st.metric(label=m['name'], value=m['val'], delta=m['status'])
        
        st.divider()
        # 차트는 모바일에서 한 줄에 하나씩 크게
        for m in m_info:
            try:
                data = yf.Ticker(m['ticker']).history(period="1y").tail(40)
                fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(8, 5), returnfig=True)
                ax[0].set_title(m['name'], fontsize=12); st.pyplot(fig)
            except: pass

with tab2:
    st.markdown("""<div class="list-row" style="background-color: #f8f9fa; border-top: 2px solid #333;"><div class="list-header">종목명</div><div class="list-header">현재가</div><div class="list-header">등락</div></div>""", unsafe_allow_html=True)
    for c, n in zip(new_nas_codes + new_kos_codes, new_nas_names + new_kos_names):
        m_type = "NASDAQ" if c in new_nas_codes else "KOSPI"
        s = get_stock_info(c, n, m_type)
        if s:
            st.markdown(f"""<div class="list-row"><div class="list-item" style="text-align:left;">{s['name']}</div><div class="list-item">{s['price']}</div><div class="list-item {s['status']}">{s['change']}</div></div>""", unsafe_allow_html=True)

with tab3:
    c_m = st.radio("시장", ["NASDAQ", "KOSPI"], horizontal=True)
    sel_codes, sel_names = (new_nas_codes, new_nas_names) if c_m == "NASDAQ" else (new_kos_codes, new_kos_names)
    for c, n in zip(sel_codes, sel_names):
        s = get_stock_info(c, n, c_m)
        if s:
            try:
                data = yf.Ticker(c.strip().upper()).history(period="1y").tail(40)
                fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(8, 5), returnfig=True)
                title_color = "red" if s['curr'] >= s['prev'] else "blue"
                ax[0].set_title(f"{s['name']} {s['price']}", fontsize=14, color=title_color); st.pyplot(fig)
            except: pass
