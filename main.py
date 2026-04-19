import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 스타일 시트 (V7.2의 완벽한 타이틀 & 지수 스타일 계승)
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
    
    /* 탭 메뉴 글자 크기 조절 */
    .stTabs [data-baseweb="tab"] { font-size: 1.2rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로딩 함수 (지수용)
@st.cache_data(ttl=300)
def get_market_data():
    tickers = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "GOLD": "GC=F", "USD-KRW": "KRW=X"}
    info = []
    for name, ticker in tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            if not hist.empty and len(hist) >= 2:
                if isinstance(hist.columns, pd.MultiIndex):
                    hist.columns = hist.columns.get_level_values(0)
                curr = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                diff = curr - prev
                percent = (diff / prev) * 100
                status = "up" if diff >= 0 else "down"
                symbol = "▲" if diff >= 0 else "▼"
                pct_sign = "+" if diff > 0 else "" 
                combined_val = f"{curr:,.1f} ({symbol}{abs(diff):,.1f} {pct_sign}{percent:.2f}%)"
                info.append({"name": name, "val": combined_val, "status": status, "ticker": ticker})
            else:
                info.append({"name": name, "val": "N/A", "status": "up", "ticker": ticker})
        except:
            info.append({"name": name, "val": "Error", "status": "up", "ticker": ticker})
    return info

# 4. 사이드바 설정 (종목 입력 유지)
st.sidebar.title("🛠️ 종목 설정")
with st.sidebar.expander("🇺🇸 NASDAQ 종목", expanded=True):
    nas_codes = [st.text_input(f"NAS 코드 {i+1}", key=f"nc{i}") for i in range(10)]
    nas_names = [st.text_input(f"NAS 이름 {i+1}", key=f"nn{i}") for i in range(10)]
with st.sidebar.expander("🇰🇷 KOSPI 종목", expanded=False):
    kos_codes = [st.text_input(f"KOS 코드 {i+1}", key=f"kc{i}") for i in range(10)]
    kos_names = [st.text_input(f"KOS 이름 {i+1}", key=f"kn{i}") for i in range(10)]

# 5. 최상단 공통 타이틀
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)

# 6. 메인 탭 구성 (표제부 / 개별 종목부)
tab1, tab2 = st.tabs(["🏠 시장 지표 (홈)", "🔍 개별 종목 분석"])

# --- [Tab 1: 표제부 (시장 지표)] ---
with tab1:
    m_info = get_market_data()
    cols = st.columns(4)
    for i, info in enumerate(m_info):
        with cols[i]:
            st.markdown(f'''
                <div class="metric-container">
                    <div class="metric-label">{info['name']}</div>
                    <div class="metric-text {info['status']}">{info['val']}</div>
                </div>
            ''', unsafe_allow_html=True)
    
    st.divider()
    st.markdown('<div style="text-align: center; font-size: 1.2rem; font-weight: bold; margin-bottom: 20px;">📊 주요 시장 지수 차트 (일봉)</div>', unsafe_allow_html=True)
    
    # V7.2 순서 재배치 (모바일 대응: 코스피-골드-나스닥-환율)
    re_idx = [0, 2, 1, 3]
    re_info = [m_info[i] for i in re_idx]
    
    c_cols = st.columns(2)
    for idx, info in enumerate(re_info):
        with c_cols[idx % 2]:
            try:
                data = yf.Ticker(info['ticker']).history(period="1y", interval="1d").tail(60)
                if not data.empty:
                    mc = mpf.make_marketcolors(up='red', down='blue', inherit=True)
                    s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=True)
                    fig, ax = mpf.plot(data, type='candle', style=s, figsize=(10, 6), returnfig=True)
                    ax[0].set_title(f"[{info['name']}]", fontsize=16, fontweight='bold', loc='center')
                    st.pyplot(fig)
            except: pass

# --- [Tab 2: 개별 종목부] ---
with tab2:
    # 상단 제어 칸 (시장 선택 & 시간축 선택)
    ctrl_col1, ctrl_col2 = st.columns([1, 1])
    
    with ctrl_col1:
        selected_market = st.radio("시장 선택", ["NASDAQ", "KOSPI"], horizontal=True)
    with ctrl_col2:
        selected_tf = st.radio("시간축 선택", ["시봉", "일봉", "주봉"], index=1, horizontal=True)
    
    st.divider()
    
    # 시간축 설정 맵
    tf_map = {
        "시봉": ("1h", "7d", "%H:%M"),
        "일봉": ("1d", "1y", "%m/%d"),
        "주봉": ("1wk", "2y", "%y/%m")
    }
    interval, period, d_fmt = tf_map[selected_tf]
    
    # 분석 리스트 구성
    analysis_list = []
    if selected_market == "NASDAQ":
        for c, n in zip(nas_codes, nas_names):
            if c: analysis_list.append((c.upper(), n if n else c.upper()))
    else:
        for c, n in zip(kos_codes, kos_names):
            if c: analysis_list.append((c.upper(), n if n else c.upper()))
    
    if not analysis_list:
        st.info("왼쪽 사이드바에서 분석할 종목 코드를 입력해 주세요!")
    else:
        chart_cols = st.columns(2)
        for idx, (ticker, name) in enumerate(analysis_list):
            with chart_cols[idx % 2]:
                try:
                    data = yf.Ticker(ticker).history(period=period, interval=interval).tail(60)
                    if not data.empty:
                        mc = mpf.make_marketcolors(up='red', down='blue', inherit=True)
                        s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=True)
                        fig, ax = mpf.plot(data, type='candle', style=s, figsize=(10, 6), returnfig=True)
                        ax[0].set_title(f"[{name}] {selected_tf}", fontsize=16, fontweight='bold', loc='center')
                        
                        # X축 날짜 포맷 최적화
                        total = len(data)
                        xticks = list(range(total - 1, -1, -12))
                        ax[0].set_xticks(xticks)
                        ax[0].set_xticklabels([data.index[j].strftime(d_fmt) for j in xticks], fontsize=9)
                        
                        st.pyplot(fig)
                except:
                    st.error(f"{name} ({ticker}) 데이터를 가져올 수 없습니다.")
