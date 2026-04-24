import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import json
import os

# 1. 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 데이터 로드/보정 함수 (IndexError 및 휘발성 저장 방어)
def load_settings():
    if 'current_settings' in st.session_state:
        data = st.session_state.current_settings
    elif os.path.exists('stock_settings.json'):
        try:
            with open('stock_settings.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: 
            data = {}
    else:
        data = {}

    # 모든 리스트를 무조건 20개로 맞춤
    for key in ['nas_codes', 'nas_names', 'kos_codes', 'kos_names']:
        if key not in data:
            data[key] = [""] * 20
        else:
            data[key] = (data[key] + [""] * 20)[:20]
    return data

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

# 4. 유틸리티 로직
def parse_display_names(raw_name, ticker):
    if not raw_name: return ticker, ticker
    if '/' in raw_name:
        parts = [p.strip() for p in raw_name.split('/')]
        l_name = parts[0] if parts[0] else ticker
        c_name = parts[1] if len(parts) > 1 and parts[1] else l_name
        return l_name, c_name
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
                status, symbol = ("up", "▲") if diff >= 0 else ("down", "▼")
                val = f"{curr:,.2f}   {symbol}{abs(diff):,.2f} ({abs(pct):.2f}%)"
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
            l_name, c_name = parse_display_names(n, c.strip().upper())
            p_disp = f"{curr:,.2f}$" if m_type == "NASDAQ" else f"{int(curr):,}"
            c_disp = f"{abs(diff):,.2f} ({abs(pct):.2f}%)" if m_type == "NASDAQ" else f"{int(abs(diff)):,} ({abs(pct):.2f}%)"
            return {"name": l_name, "c_name": c_name, "code": ticker_sym, "price": p_disp, "change": c_disp, "status": "up" if diff >= 0 else "down"}
    except: return None

# 5. 사이드바 - 설정 및 백업
saved_data = load_settings()
st.sidebar.title("🛠️ 설정 및 백업")

with st.sidebar.expander("📝 설정 백업 및 복구", expanded=False):
    st.write("설정 텍스트를 복사해서 따로 보관해 두세요.")
    json_str = json.dumps(saved_data, ensure_ascii=False)
    st.text_area("내 설정 데이터", value=json_str, height=100)
    new_json = st.text_input("복구할 데이터 붙여넣기")
    if st.button("🔄 데이터로 리스트 복구"):
        try:
            st.session_state.current_settings = json.loads(new_json)
            st.rerun()
        except: st.error("올바른 형식이 아닙니다.")

st.sidebar.divider()

new_nas_codes, new_nas_names = [], []
with st.sidebar.expander("🇺🇸 NASDAQ 종목 (20)", expanded=True):
    for i in range(20):
        new_nas_codes.append(st.text_input(f"NAS 코드 {i+1}", value=saved_data['nas_codes'][i], key=f"nc{i}"))
        new_nas_names.append(st.text_input(f"NAS 이름 {i+1}", value=saved_data['nas_names'][i], key=f"nn{i}"))

new_kos_codes, new_kos_names = [], []
with st.sidebar.expander("🇰🇷 KOSPI 종목 (20)", expanded=False):
    for i in range(20):
        new_kos_codes.append(st.text_input(f"KOS 코드 {i+1}", value=saved_data['kos_codes'][i], key=f"kc{i}"))
        new_kos_names.append(st.text_input(f"KOS 이름 {i+1}", value=saved_data['kos_names'][i], key=f"kn{i}"))

if st.sidebar.button("💾 리스트 임시 저장", use_container_width=True):
    updated_data = {"nas_codes": new_nas_codes, "nas_names": new_nas_names, "kos_codes": new_kos_codes, "kos_names": new_kos_names}
    st.session_state.current_settings = updated_data
    with open('stock_settings.json', 'w', encoding='utf-8') as f:
        json.dump(updated_data, f, ensure_ascii=False)
    st.sidebar.success("저장 완료!")

# 6. 메인 레이아웃
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🏠 시장 지표", "📋 종목 리스트", "📊 개별 종목 차트"])

# --- Tab 1: 시장 지표 ---
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

# --- Tab 2: 종목 리스트 ---
with tab2:
    selected_market = st.radio("시장 선택", ["NASDAQ", "KOSPI"], horizontal=True, label_visibility="collapsed")
    codes = new_nas_codes if selected_market == "NASDAQ" else new_kos_codes
    names = new_nas_names if selected_market == "NASDAQ" else new_kos_names
    st.markdown(f"""<div class="list-row" style="background-color: #f8f9fa; border-top: 2px solid #333; margin-top: 5px;">
        <div class="list-header">종목명</div><div class="list-header">현재가</div><div class="list-header">등락률</div>
    </div>""", unsafe_allow_html=True)
    for c, n in zip(codes, names):
        s = get_stock_info(c, n, selected_market)
        if s:
            # 현재가에도 status(up/down) 색상 적용
            st.markdown(f"""<div class="list-row">
                <div class="list-item">{s['name']}</div><div class="list-item {s['status']}">{s['price']}</div><div class="list-item {s['status']}">{s['change']}</div>
            </div>""", unsafe_allow_html=True)

# --- Tab 3: 개별 종목 차트 (요청 사항 반영) ---
with tab3:
    # 유효한 종목만 필터링 (이름과 코드를 묶어서 딕셔너리 생성)
    current_codes = new_nas_codes if selected_market == "NASDAQ" else new_kos_codes
    current_names = new_nas_names if selected_market == "NASDAQ" else new_kos_names
    
    stock_options = {}
    for c, n in zip(current_codes, current_names):
        if c.strip():
            # 화면에 표시될 이름 결정 (이름이 없으면 코드로)
            display_name = n.strip() if n.strip() else c.strip().upper()
            stock_options[display_name] = c.strip().upper()

    if stock_options:
        col1, col2 = st.columns([2, 1])
        with col1:
            # 선택은 이름으로, 결과는 코드로 받기
            selected_name = st.selectbox("📊 분석할 종목 선택", list(stock_options.keys()))
            target_code = stock_options[selected_name]
        with col2:
            c_tf = st.radio("⏰ 봉 종류", ["시봉", "일봉", "주봉"], index=1, horizontal=True)
            
        plot_code = target_code + ".KS" if selected_market == "KOSPI" and not (target_code.endswith(".KS") or target_code.endswith(".KQ")) else target_code
        t_map = {"시봉": ("1h", "7d"), "일봉": ("1d", "1y"), "주봉": ("1wk", "2y")}
        
        try:
            data = yf.Ticker(plot_code).history(period=t_map[c_tf][1], interval=t_map[c_tf][0]).tail(60)
            if not data.empty:
                curr, prev = data['Close'].iloc[-1], data['Close'].iloc[-2]
                diff, pct = curr - prev, ((curr - prev) / prev) * 100
                fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(12, 7), returnfig=True)
                p_disp = f"{curr:,.2f}$" if selected_market == "NASDAQ" else f"{int(curr):,}"
                d_disp = f"{diff:+.2f}" if selected_market == "NASDAQ" else f"{int(diff):+,}"
                # 차트 제목의 괄호 삭제
                ax[0].set_title(f"{selected_name} {c_tf}   {p_disp}   {d_disp} ({pct:+.2f}%)", fontsize=24, fontweight='bold', color="red" if diff >= 0 else "blue", loc='center', pad=20)
                st.pyplot(fig)
            else: st.warning("데이터가 없습니다.")
        except: st.error("데이터 로드 실패")
    else: st.info("사이드바에서 종목 코드를 먼저 입력해 주세요!")
