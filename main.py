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

# 3. 스타일 시트 (제목 복원 및 지표 크기 원복)
st.markdown("""
    <style>
    /* 상단 여백을 살짝 늘려 제목이 잘리지 않게 조정 */
    .block-container { padding-top: 3rem !important; }
    .title-style { font-size: 1.6rem !important; font-weight: bold; margin-bottom: 1.5rem; color: #333; text-align: center; }
    
    /* 시장 지표 글자 크기를 이전처럼 시원하게 복원 */
    .metric-container { text-align: center; margin-bottom: 15px; }
    .metric-label { font-size: 1rem; color: #666; margin-bottom: 5px; }
    .metric-text { font-size: 1.5rem !important; font-weight: bold; white-space: nowrap; }
    
    .up { color: #ef5350; } .down { color: #1e88e5; }
    
    /* 리스트 가독성 유지 */
    .list-row { display: flex; justify-content: space-around; align-items: center; padding: 10px 15px; border-bottom: 1px solid #eee; text-align: center; }
    .list-item { font-size: 1.1rem; font-weight: bold; flex: 1; }
    .list-header { font-size: 1rem; font-weight: bold; color: #555; flex: 1; }
    
    /* 입력 도구 간격 최적화 */
    div[data-testid="stRadio"] > div { margin-top: -5px; }
    div[data-testid="stSelectbox"] { margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 4. 유틸리티 및 데이터 로직
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
                val = f"{int(curr):,} ({symbol}{int(abs(diff)):,} {abs(pct):.2f}%)"
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
            c_disp = f"{abs(diff):,.2f} ({abs(pct):.2f}%)" if m_type == "NASDAQ" else f"{int(abs(diff)):,} ({abs(pct):.2f}%)"
            return {"name": l_name, "c_name": c_name, "code": ticker_sym, "price": p_disp, "change": c_disp, "status": "up" if diff >= 0 else "down", "curr": curr, "prev": prev}
    except: return None

# 5. 사이드바 (20개 확장)
st.sidebar.title("🛠️ 종목 설정")
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

if st.sidebar.button("💾 리스트 영구 저장"):
    save_settings({"nas_codes": new_nas_codes, "nas_names": new_nas_names, "kos_codes": new_kos_codes, "kos_names": new_kos_names})
    st.sidebar.success("저장 완료!")

# 6. 메인 레이아웃
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🏠 시장 지표", "📋 종목 리스트", "📊 개별 종목 차트"])

# --- Tab 1: 시장 지표 (폰트 크기 복원) ---
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

# --- Tab 2: 종목 리스트 (초압축 유지 & 제목 라벨 숨김) ---
with tab2:
    selected_market = st.radio("", ["NASDAQ", "KOSPI"], horizontal=True, label_visibility="collapsed")
    codes = new_nas_codes if selected_market == "NASDAQ" else new_kos_codes
    names = new_nas_names if selected_market == "NASDAQ" else new_kos_names
    
    valid_data = [{"code": c.strip().upper(), "l_name": parse_display_names(n, c.strip().upper())[0], "c_name": parse_display_names(n, c.strip().upper())[1]} for c, n in zip(codes, names) if c.strip()]

    if valid_data:
        options = [d['l_name'] for d in valid_data]
        selected_l_name = st.selectbox("", options, label_visibility="collapsed")
        target_idx = options.index(selected_l_name)
        st.session_state.selected_stock_code = valid_data[target_idx]['code']
        st.session_state.selected_stock_name = valid_data[target_idx]['c_name']

    st.markdown(f"""<div class="list-row" style="background-color: #f8f9fa; border-top: 2px solid #333; margin-top: 5px;">
        <div class="list-header">종목명</div><div class="list-header">현재가</div><div class="list-header">등락률</div>
    </div>""", unsafe_allow_html=True)
    
    for d in valid_data:
        s = get_stock_info(d['code'], d['l_name'], selected_market)
        if s:
            st.markdown(f"""<div class="list-row">
                <div class="list-item">{s['name']}</div><div class="list-item">{s['price']}</div><div class="list-item {s['status']}">{s['change']}</div>
            </div>""", unsafe_allow_html=True)

# --- Tab 3: 개별 종목 차트 (정제된 텍스트 적용) ---
with tab3:
    if 'selected_stock_code' in st.session_state and st.session_state.selected_stock_code:
        c_tf = st.radio("", ["시봉", "일봉", "주봉"], index=1, horizontal=True)
        t_map = {"시봉": ("1h", "7d"), "일봉": ("1d", "1y"), "주봉": ("1wk", "2y")}
        code, name = st.session_state.selected_stock_code, st.session_state.selected_stock_name
        
        try:
            data = yf.Ticker(code).history(period=t_map[c_tf][1], interval=t_map[c_tf][0]).tail(60)
            curr, prev = data['Close'].iloc[-1], data['Close'].iloc[-2]
            pct = ((curr - prev) / prev) * 100
            fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(12, 7), returnfig=True)
            p_disp = f"{curr:,.2f}$" if selected_market == "NASDAQ" else f"{int(curr):,}"
            ax[0].set_title(f"{name}  {p_disp} ({pct:+.2f}%)", fontsize=28, fontweight='bold', color="red" if curr >= prev else "blue", loc='center', pad=20)
            st.pyplot(fig)
        except: st.error("데이터 로드 실패")
