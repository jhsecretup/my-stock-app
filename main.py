import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import json
import os

# 1. 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 데이터 로드/저장
def load_settings():
    if os.path.exists('stock_settings.json'):
        try:
            with open('stock_settings.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"nas_codes": [""]*20, "nas_names": [""]*20, "kos_codes": [""]*20, "kos_names": [""]*20}

# 세션에 최신 데이터 유지 (rerun 시에도 일관성 유지)
if 'main_data' not in st.session_state:
    st.session_state.main_data = load_settings()

# 3. 스타일 시트 (V10.5 가독성 유지)
st.markdown("""
    <style>
    .block-container { padding-top: 3rem !important; }
    .title-style { font-size: 1.6rem !important; font-weight: bold; margin-bottom: 1.5rem; color: #333; text-align: center; }
    .metric-container { text-align: center; margin-bottom: 15px; }
    .metric-text { font-size: 1.5rem !important; font-weight: bold; white-space: nowrap; }
    .up { color: #ef5350; } .down { color: #1e88e5; }
    .list-row { display: flex; justify-content: space-around; align-items: center; padding: 10px 15px; border-bottom: 1px solid #eee; text-align: center; }
    .list-item { font-size: 1.1rem; font-weight: bold; flex: 1; }
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
                diff, pct = curr - prev, ((curr-prev)/prev)*100
                status, sym = ("up", "▲") if diff >= 0 else ("down", "▼")
                info.append({"name": name, "val": f"{int(curr):,} ({sym}{int(abs(diff)):,} {abs(pct):.2f}%)", "status": status, "ticker": ticker})
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
            l_n, c_n = parse_display_names(n, ticker_sym)
            p_disp = f"{curr:,.2f}$" if m_type == "NASDAQ" else f"{int(curr):,}"
            c_disp = f"{abs(diff):,.2f} ({abs(pct):.2f}%)" if m_type == "NASDAQ" else f"{int(abs(diff)):,} ({abs(pct):.2f}%)"
            return {"name": l_n, "c_name": c_n, "code": ticker_sym, "price": p_disp, "change": c_disp, "status": "up" if diff >= 0 else "down"}
    except: return None

# 5. 사이드바 (완전 정렬 기능 보강)
st.sidebar.title("🛠️ 종목 설정 & 순서")

def render_sidebar_section(title, codes, names, prefix):
    current_items = [{"c": c, "n": n} for c, n in zip(codes, names) if c.strip()]
    item_labels = [f"{i['n'] if i['n'] else i['c']}" for i in current_items]
    
    with st.sidebar.expander(title):
        st.write("↕️ 순서 재배치")
        reordered = st.multiselect("선택 순서대로 정렬", options=item_labels, default=item_labels, key=f"ms_{prefix}")
        
        label_to_item = {l: i for l, i in zip(item_labels, current_items)}
        sorted_items = [label_to_item[l] for l in reordered]
        
        # 🌟 핵심: 위젯의 'value'를 직접 수정하여 화면 강제 동기화
        res_c, res_n = [], []
        for i in range(20):
            c_init = sorted_items[i]['c'] if i < len(sorted_items) else ""
            n_init = sorted_items[i]['n'] if i < len(sorted_items) else ""
            c_input = st.text_input(f"{prefix} 코드 {i+1}", value=c_init, key=f"{prefix}c_{i}")
            n_input = st.text_input(f"{prefix} 이름 {i+1}", value=n_init, key=f"{prefix}n_{i}")
            res_c.append(c_input); res_n.append(n_input)
    return res_c, res_n

new_nas_c, new_nas_n = render_sidebar_section("🇺🇸 NASDAQ 종목", st.session_state.main_data['nas_codes'], st.session_state.main_data['nas_names'], "nas")
new_kos_c, new_kos_n = render_sidebar_section("🇰🇷 KOSPI 종목", st.session_state.main_data['kos_codes'], st.session_state.main_data['kos_names'], "kos")

if st.sidebar.button("💾 리스트 영구 저장 및 적용"):
    final_data = {"nas_codes": new_nas_c, "nas_names": new_nas_n, "kos_codes": new_kos_c, "kos_names": new_kos_n}
    with open('stock_settings.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    st.session_state.main_data = final_data # 세션 데이터 즉시 교체
    st.sidebar.success("정렬이 반영되었습니다!")
    st.rerun()

# 6. 메인 레이아웃 (정렬된 new_nas_c, new_nas_n 사용)
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🏠 시장 지표", "📋 종목 리스트", "📊 개별 종목 차트"])

with tab1:
    m_info = get_market_data()
    if m_info:
        cols = st.columns(4)
        for i, m in enumerate(m_info):
            with cols[i]:
                st.markdown(f'<div class="metric-container"><div class="metric-label" style="font-size:1rem;">{m["name"]}</div><div class="metric-text {m["status"]}">{m["val"]}</div></div>', unsafe_allow_html=True)
        st.divider()
        c_cols = st.columns(2)
        for idx, m in enumerate(m_info[:4]):
            with c_cols[idx % 2]:
                try:
                    data = yf.Ticker(m['ticker']).history(period="1y").tail(40)
                    fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(10, 6), returnfig=True)
                    ax[0].set_title(m['name'], fontsize=16, fontweight='bold'); st.pyplot(fig)
                except: pass

with tab2:
    selected_market = st.radio("", ["NASDAQ", "KOSPI"], horizontal=True, label_visibility="collapsed")
    m_codes = new_nas_c if selected_market == "NASDAQ" else new_kos_c
    m_names = new_nas_n if selected_market == "NASDAQ" else new_kos_n
    
    # 🌟 현재 정렬된 순서대로 리스트 생성
    valid_data = []
    for c, n in zip(m_codes, m_names):
        if c.strip():
            l_n, c_n = parse_display_names(n, c.strip().upper())
            valid_data.append({"code": c.strip().upper(), "l_name": l_n, "c_name": c_n})

    if valid_data:
        options = [d['l_name'] for d in valid_data]
        sel_l_name = st.selectbox("", options, label_visibility="collapsed")
        t_idx = options.index(sel_l_name)
        st.session_state.selected_stock_code = valid_data[t_idx]['code']
        st.session_state.selected_stock_name = valid_data[t_idx]['c_name']

    st.markdown(f"""<div class="list-row" style="background-color: #f8f9fa; border-top: 2px solid #333; margin-top: 5px;">
        <div class="list-header">종목명</div><div class="list-header">현재가</div><div class="list-header">등락률</div>
    </div>""", unsafe_allow_html=True)
    
    for d in valid_data:
        s = get_stock_info(d['code'], d['l_name'], selected_market)
        if s:
            st.markdown(f"""<div class="list-row">
                <div class="list-item">{s['name']}</div><div class="list-item">{s['price']}</div><div class="list-item {s['status']}">{s['change']}</div>
            </div>""", unsafe_allow_html=True)

with tab3:
    if 'selected_stock_code' in st.session_state and st.session_state.selected_stock_code:
        c_tf = st.radio("", ["시봉", "일봉", "주봉"], index=1, horizontal=True)
        t_map = {"시봉": ("1h", "7d"), "일봉": ("1d", "1y"), "주봉": ("1wk", "2y")}
        code, name = st.session_state.selected_stock_code, st.session_state.selected_stock_name
        try:
            data = yf.Ticker(code).history(period=t_map[c_tf][1], interval=t_map[c_tf][0]).tail(60)
            curr, prev = data['Close'].iloc[-1], data['Close'].iloc[-2]
            fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(12, 7), returnfig=True)
            p_disp = f"{curr:,.2f}$" if selected_market == "NASDAQ" else f"{int(curr):,}"
            ax[0].set_title(f"{name}  {p_disp}", fontsize=28, fontweight='bold', color="red" if curr >= prev else "blue", loc='center', pad=20)
            st.pyplot(fig)
        except: st.error("데이터 로드 실패")
