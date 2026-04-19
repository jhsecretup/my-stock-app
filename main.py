import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 스타일 시트
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

# 3. 데이터 로딩 함수 (에러 방지 강화)
@st.cache_data(ttl=300)
def get_market_data():
    # 환율 이름 영문 고정 (글자 깨짐 방지)
    tickers = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "GOLD": "GC=F", "USD-KRW": "KRW=X"}
    info = []
    for name, ticker in tickers.items():
        try:
            t_obj = yf.Ticker(ticker)
            hist = t_obj.history(period="3d") # 데이터 안정성을 위해 3일치 로드
            if not hist.empty and len(hist) >= 2:
                curr = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                diff = curr - prev
                percent = (diff / prev) * 100
                status = "up" if diff >= 0 else "down"
                symbol = "▲" if diff >= 0 else "▼"
                # 등락 기호 제거 및 형식 최적화
                val = f"{curr:,.1f} ({symbol}{abs(diff):,.1f} {abs(percent):.2f}%)"
                info.append({"name": name, "val": val, "status": status, "ticker": ticker})
            else:
                info.append({"name": name, "val": "데이터 없음", "status": "up", "ticker": ticker})
        except:
            info.append({"name": name, "val": "접속 지연", "status": "up", "ticker": ticker})
    return info

@st.cache_data(ttl=300)
def get_all_stock_details(nas_c, nas_n, kos_c, kos_n):
    combined = []
    for c, n in zip(nas_c, nas_n):
        if c: combined.append((c.strip().upper(), n if n else c.upper()))
    for c, n in zip(kos_c, kos_n):
        if c: combined.append((c.strip().upper(), n if n else c.upper()))
    
    details = []
    for t_sym, d_name in combined:
        try:
            hist = yf.Ticker(t_sym).history(period="2d")
            if not hist.empty and len(hist) >= 2:
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                diff = curr - prev
                percent = (diff / prev) * 100
                details.append({
                    "name": d_name, "price": f"{curr:,.2f}",
                    "change": f"{abs(diff):,.2f} ({abs(percent):.2f}%)",
                    "status": "up" if diff >= 0 else "down"
                })
        except: pass
    return details

# 4. 사이드바
st.sidebar.title("🛠️ 종목 설정")
with st.sidebar.expander("🇺🇸 NASDAQ 종목", expanded=True):
    nas_codes = [st.text_input(f"NAS 코드 {i+1}", key=f"nc{i}") for i in range(10)]
    nas_names = [st.text_input(f"NAS 이름 {i+1}", key=f"nn{i}") for i in range(10)]
with st.sidebar.expander("🇰🇷 KOSPI 종목", expanded=False):
    kos_codes = [st.text_input(f"KOS 코드 {i+1}", key=f"kc{i}") for i in range(10)]
    kos_names = [st.text_input(f"KOS 이름 {i+1}", key=f"kn{i}") for i in range(10)]

# 5. 타이틀
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)

# 6. 탭 구성
tab1, tab2, tab3 = st.tabs(["🏠 시장 지표 (홈)", "📋 종목 리스트", "📊 개별 종목 차트"])

# --- Tab 1: 시장 지표 ---
with tab1:
    m_info = get_market_data()
    # 데이터가 정상적으로 4개 로드되었을 때만 차트 배치 실행
    if len(m_info) >= 4:
        cols = st.columns(4)
        for i, info in enumerate(m_info):
            with cols[i]:
                st.markdown(f'<div class="metric-container"><div class="metric-label">{info["name"]}</div><div class="metric-text {info["status"]}">{info["val"]}</div></div>', unsafe_allow_html=True)
        
        st.divider()
        st.markdown('<div style="text-align: center; font-size: 1.2rem; font-weight: bold; margin-bottom: 20px;">📊 주요 시장 지수 차트 (일봉)</div>', unsafe_allow_html=True)
        
        # 순서 재배치 (코스피-골드-나스닥-환율)
        re_idx = [0, 2, 1, 3]
        c_cols = st.columns(2)
        for idx, target_idx in enumerate(re_idx):
            info = m_info[target_idx]
            with c_cols[idx % 2]:
                try:
                    data = yf.Ticker(info['ticker']).history(period="1y", interval="1d").tail(60)
                    if not data.empty:
                        mc = mpf.make_marketcolors(up='red', down='blue', inherit=True)
                        s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=True)
                        fig, ax = mpf.plot(data, type='candle', style=s, figsize=(10, 6), returnfig=True)
                        ax[0].set_title(f"[{info['name']}]", fontsize=16, fontweight='bold', loc='center')
                        st.pyplot(fig)
                except: st.warning(f"{info['name']} 차트 로드 실패")
    else:
        st.error("시장 데이터를 불러오는 중입니다. 잠시만 기다려 주시거나 페이지를 새로고침 해주세요.")

# --- Tab 2: 통합 종목 리스트 ---
with tab2:
    st.markdown("""<div class="list-row" style="background-color: #f8f9fa; border-top: 2px solid #333; margin-top: 10px;"><div class="list-header">종목명</div><div class="list-header">현재가</div><div class="list-header">등락 (퍼센트)</div></div>""", unsafe_allow_html=True)
    s_list = get_all_stock_details(nas_codes, nas_names, kos_codes, kos_names)
    if s_list:
        for s in s_list:
            st.markdown(f"""<div class="list-row"><div class="list-item">{s['name']}</div><div class="list-item">{s['price']}</div><div class="list-item {s['status']}">{s['change']}</div></div>""", unsafe_allow_html=True)
    else: st.info("종목을 설정해주세요.")

# --- Tab 3: 개별 종목 차트 ---
with tab3:
    c_m = st.radio("시장", ["NASDAQ", "KOSPI"], horizontal=True)
    c_tf = st.radio("시간축", ["시봉", "일봉", "주봉"], index=1, horizontal=True)
    t_map = {"시봉": ("1h", "7d"), "일봉": ("1d", "1y"), "주봉": ("1wk", "2y")}
    
    codes = nas_codes if c_m == "NASDAQ" else kos_codes
    names = nas_names if c_m == "NASDAQ" else kos_names
    
    chart_cols = st.columns(2)
    valid_idx = 0
    for c, n in zip(codes, names):
        if c:
            with chart_cols[valid_idx % 2]:
                try:
                    data = yf.Ticker(c.strip().upper()).history(period=t_map[c_tf][1], interval=t_map[c_tf][0]).tail(60)
                    if not data.empty:
                        fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(10, 6), returnfig=True)
                        ax[0].set_title(f"[{c.upper()}] {n if n else ''} {c_tf}", fontsize=16, fontweight='bold', loc='center')
                        st.pyplot(fig)
                        valid_idx += 1
                except: pass
