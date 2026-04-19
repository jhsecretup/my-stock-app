import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 스타일 시트 (일관된 1.5rem 및 중앙 정렬)
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
    
    /* 종목 리스트 탭 전용 스타일 */
    .list-row {
        display: flex;
        justify-content: space-around;
        align-items: center;
        padding: 15px;
        border-bottom: 1px solid #eee;
        text-align: center;
    }
    .list-item { font-size: 1.2rem; font-weight: bold; flex: 1; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로딩 함수 (개별 종목용 상세 데이터 포함)
@st.cache_data(ttl=300)
def get_stock_details(codes, names):
    details = []
    for c, n in zip(codes, names):
        if c:
            try:
                ticker = yf.Ticker(c.strip().upper())
                hist = ticker.history(period="2d")
                if not hist.empty and len(hist) >= 2:
                    curr = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    diff = curr - prev
                    percent = (diff / prev) * 100
                    details.append({
                        "name": n if n else c.upper(),
                        "ticker": c.upper(),
                        "price": f"{curr:,.2f}",
                        "change": f"{'+' if diff > 0 else ''}{diff:,.2f} ({'+' if diff > 0 else ''}{percent:.2f}%)",
                        "status": "up" if diff >= 0 else "down"
                    })
            except: pass
    return details

# (기존 시장 지수 함수 계승)
@st.cache_data(ttl=300)
def get_market_data():
    tickers = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "GOLD": "GC=F", "USD-KRW": "KRW=X"}
    info = []
    for name, ticker in tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            curr = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            diff = curr - prev
            percent = (diff / prev) * 100
            status = "up" if diff >= 0 else "down"
            symbol = "▲" if diff >= 0 else "▼"
            combined_val = f"{curr:,.1f} ({symbol}{abs(diff):,.1f} {'+' if diff>0 else ''}{percent:.2f}%)"
            info.append({"name": name, "val": combined_val, "status": status, "ticker": ticker})
        except: pass
    return info

# 4. 사이드바 설정
st.sidebar.title("🛠️ 종목 설정")
with st.sidebar.expander("🇺🇸 NASDAQ 종목", expanded=True):
    nas_codes = [st.text_input(f"NAS 코드 {i+1}", key=f"nc{i}") for i in range(10)]
    nas_names = [st.text_input(f"NAS 이름 {i+1}", key=f"nn{i}") for i in range(10)]
with st.sidebar.expander("🇰🇷 KOSPI 종목", expanded=False):
    kos_codes = [st.text_input(f"KOS 코드 {i+1}", key=f"kc{i}") for i in range(10)]
    kos_names = [st.text_input(f"KOS 이름 {i+1}", key=f"kn{i}") for i in range(10)]

# 5. 메인 타이틀
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)

# 6. 3분할 탭 구성
tab1, tab2, tab3 = st.tabs(["🏠 시장 지표 (홈)", "📋 종목 리스트", "📊 개별 종목 차트"])

# --- [Tab 1: 시장 지표] ---
with tab1:
    m_info = get_market_data()
    cols = st.columns(4)
    for i, info in enumerate(m_info):
        with cols[i]:
            st.markdown(f'<div class="metric-container"><div class="metric-label">{info["name"]}</div><div class="metric-text {info["status"]}">{info["val"]}</div></div>', unsafe_allow_html=True)
    st.divider()
    re_idx = [0, 2, 1, 3] # 모바일 최적화 순서
    re_info = [m_info[i] for i in re_idx]
    c_cols = st.columns(2)
    for idx, info in enumerate(re_info):
        with c_cols[idx % 2]:
            data = yf.Ticker(info['ticker']).history(period="1y", interval="1d").tail(60)
            fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(10, 6), returnfig=True)
            ax[0].set_title(f"[{info['name']}]", fontsize=16, fontweight='bold', loc='center')
            st.pyplot(fig)

# --- [Tab 2: 종목 리스트 (새로 추가)] ---
with tab2:
    st.markdown('<div style="text-align: center; font-size: 1.2rem; font-weight: bold; margin-bottom: 20px;">🕒 실시간 종목 현황</div>', unsafe_allow_html=True)
    
    market_sel = st.radio("시장 선택", ["NASDAQ", "KOSPI"], horizontal=True, key="list_market")
    
    # 헤더 (3분할 영역)
    st.markdown("""
        <div class="list-row" style="background-color: #f8f9fa; border-top: 2px solid #333;">
            <div class="list-item">종목명</div>
            <div class="list-item">현재가</div>
            <div class="list-item">등락 (퍼센트)</div>
        </div>
    """, unsafe_allow_html=True)
    
    codes = nas_codes if market_sel == "NASDAQ" else kos_codes
    names = nas_names if market_sel == "NASDAQ" else kos_names
    stock_list = get_stock_details(codes, names)
    
    if not stock_list:
        st.info("사이드바에 종목을 입력하면 리스트가 나타납니다.")
    else:
        for s in stock_list:
            st.markdown(f"""
                <div class="list-row">
                    <div class="list-item">{s['name']}</div>
                    <div class="list-item">{s['price']}</div>
                    <div class="list-item {s['status']}">{s['change']}</div>
                </div>
            """, unsafe_allow_html=True)

# --- [Tab 3: 개별 종목 차트] ---
with tab3:
    col_m, col_t = st.columns(2)
    with col_m: chart_market = st.radio("시장", ["NASDAQ", "KOSPI"], horizontal=True, key="chart_market")
    with col_t: chart_tf = st.radio("시간축", ["시봉", "일봉", "주봉"], index=1, horizontal=True)
    
    tf_map = {"시봉": ("1h", "7d", "%H:%M"), "일봉": ("1d", "1y", "%m/%d"), "주봉": ("1wk", "2y", "%y/%m")}
    interval, period, d_fmt = tf_map[chart_tf]
    
    codes = nas_codes if chart_market == "NASDAQ" else kos_codes
    names = nas_names if chart_market == "NASDAQ" else kos_names
    
    chart_cols = st.columns(2)
    c_idx = 0
    for c, n in zip(codes, names):
        if c:
            with chart_cols[c_idx % 2]:
                try:
                    data = yf.Ticker(c.strip().upper()).history(period=period, interval=interval).tail(60)
                    if not data.empty:
                        fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(10, 6), returnfig=True)
                        # 티커와 한글 이름을 병기하여 가독성 확보
                        ax[0].set_title(f"[{c.upper()}] {n if n else ''} {chart_tf}", fontsize=16, fontweight='bold', loc='center')
                        st.pyplot(fig)
                        c_idx += 1
                except: pass
