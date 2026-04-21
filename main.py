import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import json
import os

# 1. 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 세션 상태 초기화 (클릭한 종목을 기억하기 위함)
if 'selected_stock_code' not in st.session_state:
    st.session_state.selected_stock_code = None
if 'selected_stock_name' not in st.session_state:
    st.session_state.selected_stock_name = None

# 3. 데이터 로드/저장
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

# 4. 스타일 시트
st.markdown("""
    <style>
    .block-container { padding-top: 3.5rem !important; }
    .title-style { font-size: 1.5rem !important; font-weight: bold; margin-bottom: 1.5rem; color: #333; text-align: center; }
    .metric-container { text-align: center; margin-bottom: 10px; }
    .metric-label { font-size: 1rem; color: #666; }
    .metric-text { font-size: 1.5rem !important; font-weight: bold; white-space: nowrap; }
    .up { color: #ef5350; } .down { color: #1e88e5; }
    .list-row { display: flex; justify-content: space-around; align-items: center; padding: 5px 15px; border-bottom: 1px solid #eee; text-align: center; }
    .list-item { font-size: 1.1rem; font-weight: bold; flex: 1; }
    .list-header { font-size: 1rem; font-weight: bold; color: #555; flex: 1; }
    </style>
    """, unsafe_allow_html=True)

# 5. 유틸리티 함수
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
            return {"name": l_name, "c_name": c_name, "code": ticker_sym, "price": p_disp, "pct": pct, "change": c_disp, "status": "up" if diff >= 0 else "down", "curr": curr, "prev": prev}
    except: return None

# 6. 사이드바 설정 (20개 확장형)
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
    st.sidebar.success("설정이 저장되었습니다!")

# 7. 메인 레이아웃
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🏠 시장 지표", "📋 종목 리스트", "📊 개별 종목 차트"])

# --- Tab 1: 시장 지표 ---
with tab1:
    m_info = get_market_data()
    if m_info:
        cols = st.columns(4)
        for i in range(min(4, len(m_info))):
            with cols[i]:
                st.markdown(f'<div class="metric-container"><div class="metric-label">{m_info[i]["name"]}</div><div class="metric-text {m_info[i]["status"]}">{m_info[i]["val"]}</div></div>', unsafe_allow_html=True)
        st.divider()
        re_idx = [0, 2, 1, 3]
        c_cols = st.columns(2)
        for idx, t_idx in enumerate(re_idx):
            if t_idx < len(m_info):
                with c_cols[idx % 2]:
                    try:
                        data = yf.Ticker(m_info[t_idx]['ticker']).history(period="1y").tail(60)
                        fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(10, 6), returnfig=True)
                        ax[0].set_title(m_info[t_idx]['name'], fontsize=16, fontweight='bold'); st.pyplot(fig)
                    except: pass

# --- Tab 2: 종목 리스트 (클릭 연동) ---
with tab2:
    selected_market = st.radio("시장 선택", ["NASDAQ", "KOSPI"], horizontal=True)
    st.markdown(f"""<div class="list-row" style="background-color: #f8f9fa; border-top: 2px solid #333; margin-top: 10px;">
        <div class="list-header" style="flex: 1.5;">종목명 (클릭시 차트선택)</div>
        <div class="list-header">현재가</div>
        <div class="list-header">등락 (퍼센트)</div>
    </div>""", unsafe_allow_html=True)
    
    target_codes = new_nas_codes if selected_market == "NASDAQ" else new_kos_codes
    target_names = new_nas_names if selected_market == "NASDAQ" else new_kos_names
    
    for c, n in zip(target_codes, target_names):
        s = get_stock_info(c, n, selected_market)
        if s:
            col_btn, col_p, col_c = st.columns([1.5, 1, 1])
            with col_btn:
                # 종목명을 버튼으로 만들어 클릭 가능하게 구현
                if st.button(f"🔍 {s['name']}", key=f"btn_{s['code']}", use_container_width=True):
                    st.session_state.selected_stock_code = s['code']
                    st.session_state.selected_stock_name = s['c_name']
                    st.success(f"'{s['name']}' 차트가 선택되었습니다. 3번 탭으로 이동하세요!")
            with col_p:
                st.markdown(f"<div style='text-align:center; padding-top:10px; font-weight:bold;'>{s['price']}</div>", unsafe_allow_html=True)
            with col_c:
                color = "#ef5350" if s['status'] == "up" else "#1e88e5"
                st.markdown(f"<div style='text-align:center; padding-top:10px; font-weight:bold; color:{color};'>{s['change']}</div>", unsafe_allow_html=True)

# --- Tab 3: 개별 종목 차트 (선택된 단일 종목) ---
with tab3:
    if st.session_state.selected_stock_code:
        # 파란색 박스 제거 및 시간축 탭 유지
        c_tf = st.radio("시간축 변환", ["시봉", "일봉", "주봉"], index=1, horizontal=True)
        t_map = {"시봉": ("1h", "7d"), "일봉": ("1d", "1y"), "주봉": ("1wk", "2y")}
        
        code = st.session_state.selected_stock_code
        name = st.session_state.selected_stock_name
        
        try:
            ticker = yf.Ticker(code)
            data = ticker.history(period=t_map[c_tf][1], interval=t_map[c_tf][0]).tail(60)
            
            # 실시간 가격 정보 다시 가져오기
            curr = data['Close'].iloc[-1]
            prev = data['Close'].iloc[-2]
            pct = ((curr - prev) / prev) * 100
            
            fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(12, 7), returnfig=True)
            
            # 차트 제목에 가격 정보 표시
            p_disp = f"{curr:,.2f}$" if selected_market == "NASDAQ" else f"{int(curr):,}"
            ax[0].set_title(f"{name}  {p_disp} ({pct:+.2f}%)", fontsize=28, fontweight='bold', color="red" if curr >= prev else "blue", loc='center', pad=20)
            st.pyplot(fig)
            
        except Exception as e:
            st.error("차트 데이터를 불러오는 중 오류가 발생했습니다.")
    else:
        st.warning("📋 '종목 리스트' 탭에서 종목명을 클릭하면 이곳에 차트가 나타납니다.")
