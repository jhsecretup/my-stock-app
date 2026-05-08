import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import json
import os

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

# 3. 스타일 시트 (가로 너비 절반 제한 및 디자인 조정)
st.markdown("""
    <style>
    .block-container { padding-top: 3rem !important; }
    .title-style { font-size: 1.6rem !important; font-weight: bold; margin-bottom: 1.5rem; color: #333; text-align: center; }
    
    /* [핵심] 사이드바 입력칸 전체 가로 폭을 50%로 제한 */
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] {
        width: 55% !important; /* 약간의 여유를 둔 절반 */
        flex-wrap: nowrap !important;
        gap: 5px !important;
    }
    
    /* 입력창 높이는 V11.2의 콤팩트함 유지 */
    div[data-testid="stTextInput"] div[data-baseweb="base-input"] {
        min-height: 28px !important;
        height: 28px !important;
    }
    
    /* 메인 리스트 가독성 */
    .metric-container { text-align: center; margin-bottom: 15px; }
    .metric-text { font-size: 1.5rem !important; font-weight: bold; white-space: nowrap; }
    .up { color: #ef5350; } .down { color: #1e88e5; }
    .list-row { display: flex; justify-content: space-around; align-items: center; padding: 10px 15px; border-bottom: 1px solid #eee; text-align: center; }
    .list-item { font-size: 1.1rem; font-weight: bold; flex: 1; }
    </style>
    """, unsafe_allow_html=True)

# 4. 유틸리티 로직
def parse_display_names(raw_name, ticker):
    if not raw_name: return ticker, ticker
    if '/' in raw_name:
        parts = [p.strip() for p in raw_name.split('/')]
        l_n = parts[0] if parts[0] else ticker
        c_n = parts[1] if len(parts) > 1 and parts[1] else l_n
        return l_n, c_n
    return raw_name, raw_name

@st.cache_data(ttl=10)
def get_market_data():
    tickers = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "GOLD": "GC=F", "USD-KRW": "KRW=X"}
    info = []
    for name, ticker in tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            if not hist.empty and len(hist) >= 2:
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                diff, pct = curr - prev, ((curr - prev) / prev) * 100
                status, sym = ("up", "▲") if diff >= 0 else ("down", "▼")
                val = f"{curr:,.2f}   {sym}{abs(diff):,.2f} ({abs(pct):.2f}%)"
                info.append({"name": name, "val": val, "status": status, "ticker": ticker})
        except: pass
    return info

def get_stock_info(c, n, m_type):
    if not c: return None
    try:
        ticker_sym = c.strip().upper()
        if m_type == "KOSPI" and not (ticker_sym.endswith(".KS") or ticker_sym.endswith(".KQ")):
            ticker_sym += ".KS"
        hist = yf.Ticker(ticker_sym).history(period="2d")
        if not hist.empty and len(hist) >= 2:
            curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
            diff, pct = curr - prev, ((curr-prev)/prev)*100
            l_n, c_n = parse_display_names(n, c.strip().upper())
            p_disp = f"{curr:,.2f}$" if m_type == "NASDAQ" else f"{int(curr):,}"
            c_disp = f"{abs(diff):,.2f} ({abs(pct):.2f}%)" if m_type == "NASDAQ" else f"{int(abs(diff)):,} ({abs(pct):.2f}%)"
            return {"name": l_n, "c_name": c_n, "code": ticker_sym, "price": p_disp, "change": c_disp, "status": "up" if diff >= 0 else "down"}
    except: return None

# 5. 사이드바 편집 영역
saved_data = load_settings()
st.sidebar.title("🛠️ 종목 설정 센터")

st.sidebar.subheader("📌 종목 리스트 편집 (50개씩)")
input_tab_nas, input_tab_kos = st.sidebar.tabs(["🇺🇸 NASDAQ", "🇰🇷 KOSPI"])

def render_inputs(tab, codes, names, prefix):
    new_c, new_n = [], []
    with tab:
        for i in range(50):
            c1, c2 = st.columns([1.5, 2]) # 가로 폭 안에서의 비율
            with c1:
                code = st.text_input(f"{prefix}C{i}", value=codes[i], key=f"{prefix}c{i}", label_visibility="collapsed", placeholder="코드")
            with c2:
                name = st.text_input(f"{prefix}N{i}", value=names[i], key=f"{prefix}n{i}", label_visibility="collapsed", placeholder="종목명")
            new_c.append(code); new_n.append(name)
    return new_c, new_n

new_nas_codes, new_nas_names = render_inputs(input_tab_nas, saved_data['nas_codes'], saved_data['nas_names'], "nc")
new_kos_codes, new_kos_names = render_inputs(input_tab_kos, saved_data['kos_codes'], saved_data['kos_names'], "kc")

if st.sidebar.button("💾 모든 설정 영구 저장", use_container_width=True, type="primary"):
    updated_data = {"nas_codes": new_nas_codes, "nas_names": new_nas_names, "kos_codes": new_kos_codes, "kos_names": new_kos_names}
    st.session_state.current_settings = updated_data
    with open('stock_settings.json', 'w', encoding='utf-8') as f:
        json.dump(updated_data, f, ensure_ascii=False, indent=4)
    st.rerun()

# 6. 메인 레이아웃 (Tab 1, 2, 3 로직 유지)
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🏠 시장 지표", "📋 종목 리스트", "📊 개별 종목 차트"])

with tab1:
    m_info = get_market_data()
    if m_info:
        cols = st.columns(4)
        for i, m in enumerate(m_info):
            with cols[i]:
                st.markdown(f'<div class="metric-container"><div class="metric-label">{m["name"]}</div><div class="metric-text {m["status"]}">{m["val"]}</div></div>', unsafe_allow_html=True)
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
    selected_market = st.radio("표시 시장", ["NASDAQ", "KOSPI"], horizontal=True, label_visibility="collapsed")
    codes = new_nas_codes if selected_market == "NASDAQ" else new_kos_codes
    names = new_nas_names if selected_market == "NASDAQ" else new_kos_names
    
    st.markdown(f"""<div class="list-row" style="background-color: #f8f9fa; border-top: 2px solid #333; margin-top: 5px;">
        <div class="list-header">종목명</div><div class="list-header">현재가</div><div class="list-header">등락률</div>
    </div>""", unsafe_allow_html=True)
    
    for c, n in zip(codes, names):
        if c.strip():
            s = get_stock_info(c, n, selected_market)
            if s:
                st.markdown(f"""<div class="list-row">
                    <div class="list-item">{s['name']}</div><div class="list-item {s['status']}">{s['price']}</div><div class="list-item {s['status']}">{s['change']}</div>
                </div>""", unsafe_allow_html=True)

with tab3:
    current_codes = new_nas_codes if selected_market == "NASDAQ" else new_kos_codes
    current_names = new_nas_names if selected_market == "NASDAQ" else new_kos_names
    stock_options = { (n.strip() if n.strip() else c.strip().upper()): c.strip().upper() for c, n in zip(current_codes, current_names) if c.strip() }

    if stock_options:
        col_s1, col_s2 = st.columns([2, 1])
        with col_s1:
            selected_name = st.selectbox("📊 분석할 종목 선택", list(stock_options.keys()), key="chart_select")
            target_code = stock_options[selected_name]
        with col_s2:
            c_tf = st.radio("⏰ 봉 종류", ["시봉", "일봉", "주봉"], index=1, horizontal=True, key="time_frame")
            
        plot_code = target_code + ".KS" if selected_market == "KOSPI" and not (target_code.endswith(".KS") or target_code.endswith(".KQ")) else target_code
        t_map = {"시봉": ("1h", "7d"), "일봉": ("1d", "1y"), "주봉": ("1wk", "2y")}
        
        try:
            data = yf.Ticker(plot_code).history(period=t_map[c_tf][1], interval=t_map[c_tf][0]).tail(60)
            if not data.empty:
                curr, prev = data['Close'].iloc[-1], data['Close'].iloc[-2]
                fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(12, 7), returnfig=True)
                p_disp = f"{curr:,.2f}$" if selected_market == "NASDAQ" else f"{int(curr):,}"
                ax[0].set_title(f"{selected_name} {c_tf}   {p_disp}", fontsize=24, fontweight='bold', color="red" if curr >= prev else "blue", loc='center', pad=20)
                st.pyplot(fig)
        except: st.error("데이터 로드 실패")