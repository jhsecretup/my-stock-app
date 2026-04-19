import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 스타일 시트 (일관성 유지)
st.markdown("""
    <style>
    .block-container { padding-top: 3.5rem !important; }
    .title-style {
        font-size: 1.5rem !important;
        font-weight: bold;
        margin-bottom: 1.5rem;
        color: #333;
        text-align: center;
    }
    .metric-container { text-align: center; margin-bottom: 10px; }
    .metric-label { font-size: 1rem; color: #666; }
    .metric-text { font-size: 1.5rem !important; font-weight: bold; white-space: nowrap; }
    .up { color: #ef5350; }
    .down { color: #1e88e5; }
    
    .list-row {
        display: flex;
        justify-content: space-around;
        align-items: center;
        padding: 10px 15px;
        border-bottom: 1px solid #eee;
        text-align: center;
    }
    .list-item { font-size: 1.1rem; font-weight: bold; flex: 1; }
    .list-header { font-size: 1rem; font-weight: bold; color: #555; flex: 1; }
    </style>
    """, unsafe_allow_html=True)

# 3. 유틸리티 함수
def parse_display_names(raw_name, ticker):
    if not raw_name: return ticker, ticker
    if '/' in raw_name:
        parts = [p.strip() for p in raw_name.split('/')]
        l_name = parts[0] if parts[0] else ticker
        c_name = parts[1] if len(parts) > 1 and parts[1] else l_name
        return l_name, c_name
    return raw_name, raw_name

# 4. 데이터 로딩 함수
@st.cache_data(ttl=300)
def get_market_data():
    tickers = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "GOLD": "GC=F", "USD-KRW": "KRW=X"}
    info = []
    for name, ticker in tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="3d")
            if not hist.empty and len(hist) >= 2:
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                diff, pct = curr - prev, ((curr - prev) / prev) * 100
                status = "up" if diff >= 0 else "down"
                symbol = "▲" if diff >= 0 else "▼"
                val = f"{curr:,.1f} ({symbol}{abs(diff):,.1f} {abs(pct):.2f}%)"
                info.append({"name": name, "val": val, "status": status, "ticker": ticker})
        except: pass
    return info

@st.cache_data(ttl=300)
def get_all_stock_details(nas_c, nas_n, kos_c, kos_n):
    details = []
    combined = [(nas_c, nas_n, "NAS"), (kos_c, kos_n, "KOS")]
    for codes, names, m_type in combined:
        for c, n in zip(codes, names):
            if c:
                try:
                    ticker_sym = c.strip().upper()
                    hist = yf.Ticker(ticker_sym).history(period="2d")
                    if not hist.empty and len(hist) >= 2:
                        curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                        diff, pct = curr - prev, ((curr-prev)/prev)*100
                        l_name, _ = parse_display_names(n, ticker_sym)
                        p_disp = f"{curr:,.2f}$" if m_type == "NAS" else f"{int(curr):,}"
                        c_disp = f"{abs(diff):,.2f} ({abs(pct):.2f}%)" if m_type == "NAS" else f"{int(abs(diff)):,} ({abs(pct):.2f}%)"
                        details.append({"name": l_name, "price": p_disp, "change": c_disp, "status": "up" if diff >= 0 else "down"})
                except: pass
    return details

# 5. 사이드바 및 레이아웃
st.sidebar.title("🛠️ 종목 설정")
with st.sidebar.expander("🇺🇸 NASDAQ 종목", expanded=True):
    nas_codes = [st.text_input(f"NAS 코드 {i+1}", key=f"nc{i}") for i in range(10)]
    nas_names = [st.text_input(f"NAS 이름 {i+1}", key=f"nn{i}") for i in range(10)]
with st.sidebar.expander("🇰🇷 KOSPI 종목", expanded=False):
    kos_codes = [st.text_input(f"KOS 코드 {i+1}", key=f"kc{i}") for i in range(10)]
    kos_names = [st.text_input(f"KOS 이름 {i+1}", key=f"kn{i}") for i in range(10)]

st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🏠 시장 지표 (홈)", "📋 종목 리스트", "📊 개별 종목 차트"])

# --- Tab 1: 시장 지표 ---
with tab1:
    m_info = get_market_data()
    if len(m_info) >= 4:
        cols = st.columns(4); [cols[i].markdown(f'<div class="metric-container"><div class="metric-label">{m_info[i]["name"]}</div><div class="metric-text {m_info[i]["status"]}">{m_info[i]["val"]}</div></div>', unsafe_allow_html=True) for i in range(4)]
        st.divider(); re_idx = [0, 2, 1, 3]; c_cols = st.columns(2)
        for idx, t_idx in enumerate(re_idx):
            with c_cols[idx % 2]:
                try:
                    data = yf.Ticker(m_info[t_idx]['ticker']).history(period="1y").tail(60)
                    fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(10, 6), returnfig=True)
                    ax[0].set_title(m_info[t_idx]['name'], fontsize=16, fontweight='bold'); st.pyplot(fig)
                except: pass

# --- Tab 2: 종목 리스트 ---
with tab2:
    st.markdown("""<div class="list-row" style="background-color: #f8f9fa; border-top: 2px solid #333; margin-top: 10px;"><div class="list-header">종목명</div><div class="list-header">현재가</div><div class="list-header">등락 (퍼센트)</div></div>""", unsafe_allow_html=True)
    for s in get_all_stock_details(nas_codes, nas_names, kos_codes, kos_names):
        st.markdown(f"""<div class="list-row"><div class="list-item">{s['name']}</div><div class="list-item">{s['price']}</div><div class="list-item {s['status']}">{s['change']}</div></div>""", unsafe_allow_html=True)

# --- Tab 3: 개별 종목 차트 ---
with tab3:
    c_m = st.radio("시장", ["NASDAQ", "KOSPI"], horizontal=True); c_tf = st.radio("시간축", ["시봉", "일봉", "주봉"], index=1, horizontal=True)
    t_map = {"시봉": ("1h", "7d"), "일봉": ("1d", "1y"), "주봉": ("1wk", "2y")}
    codes, names = (nas_codes, nas_names) if c_m == "NASDAQ" else (kos_codes, kos_names)
    chart_cols = st.columns(2); v_idx = 0
    for c, n in zip(codes, names):
        if c:
            with chart_cols[v_idx % 2]:
                try:
                    ticker_sym = c.strip().upper()
                    data = yf.Ticker(ticker_sym).history(period=t_map[c_tf][1], interval=t_map[c_tf][0]).tail(60)
                    if not data.empty:
                        curr_price = data['Close'].iloc[-1]
                        hist_2d = yf.Ticker(ticker_sym).history(period="2d")
                        prev_price = hist_2d['Close'].iloc[-2]
                        
                        # 퍼센트 계산
                        pct_val = ((curr_price - prev_price) / prev_price) * 100
                        title_color = "red" if curr_price >= prev_price else "blue"
                        
                        _, c_name = parse_display_names(n, ticker_sym)
                        p_disp = f"{curr_price:,.2f}$" if c_m == "NASDAQ" else f"{int(curr_price):,}"
                        
                        fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(10, 6), returnfig=True)
                        if c_m == "NASDAQ": ax[0].set_ylabel('')
                        
                        # 차트 제목: 크기 30, 형식 [이름 현재가 (퍼센트%)]
                        ax[0].set_title(f"{c_name}  {p_disp} ({abs(pct_val):.2f}%)", fontsize=30, fontweight='bold', color=title_color, loc='center', pad=20)
                        st.pyplot(fig); v_idx += 1
                except: pass
