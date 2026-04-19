import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 타이틀 및 지수 한 줄 배치를 위한 핵심 스타일
st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; }
    
    /* 타이틀 크기 살짝 키움 */
    .title-style {
        font-size: 1.4rem !important;
        font-weight: bold;
        margin-bottom: 1.2rem;
    }

    /* 지수와 등락을 한 줄로 붙이는 설정 */
    [data-testid="stMetricValue"] {
        display: inline-block !important;
        font-size: 1.1rem !important;
    }
    [data-testid="stMetricDelta"] {
        display: inline-block !important;
        margin-left: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로딩 함수 (에러 방지 강화)
@st.cache_data(ttl=300)
def get_market_data():
    tickers = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "GOLD": "GC=F", "환율": "KRW=X"}
    info = []
    for name, ticker in tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            if not hist.empty and len(hist) >= 2:
                if isinstance(hist.columns, pd.MultiIndex):
                    hist.columns = hist.columns.get_level_values(0)
                curr = hist['Close'].iloc[-1]
                diff = curr - hist['Close'].iloc[-2]
                info.append({"name": name, "val": f"{curr:,.1f}", "diff": f"{diff:,.1f}"})
            else:
                info.append({"name": name, "val": "N/A", "diff": "0.0"})
        except:
            info.append({"name": name, "val": "Error", "diff": "0.0"})
    return info

# 4. 사이드바 - 종목 설정
st.sidebar.title("🛠️ 설정")
with st.sidebar.expander("🇺🇸 NASDAQ 종목", expanded=False):
    nas_codes = [st.text_input(f"NAS 코드 {i+1}", key=f"nc{i}") for i in range(10)]
    nas_names = [st.text_input(f"NAS 이름 {i+1}", key=f"nn{i}") for i in range(10)]
with st.sidebar.expander("🇰🇷 KOSPI 종목", expanded=False):
    kos_codes = [st.text_input(f"KOS 코드 {i+1}", key=f"kc{i}") for i in range(10)]
    kos_names = [st.text_input(f"KOS 이름 {i+1}", key=f"kn{i}") for i in range(10)]

# 5. 메인 화면 상단
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)

m_info = get_market_data()
cols = st.columns(4)
for i, info in enumerate(m_info):
    with cols[i]:
        # 지수 옆에 등락이 바로 붙도록 출력
        st.metric(label=info['name'], value=info['val'], delta=info['diff'])

st.divider()

# 6. 제어부 - 토글 버튼
if 'tf' not in st.session_state: st.session_state.tf = "DAY"
if 'mk' not in st.session_state: st.session_state.mk = "NASDAQ"

col_tf1, col_tf2, col_tf3, col_sp, col_mk1, col_mk2 = st.columns([1, 1, 1, 0.5, 1, 1])

with col_tf1:
    if st.button("HOUR", type="primary" if st.session_state.tf=="HOUR" else "secondary"): st.session_state.tf="HOUR"
with col_tf2:
    if st.button("DAY", type="primary" if st.session_state.tf=="DAY" else "secondary"): st.session_state.tf="DAY"
with col_tf3:
    if st.button("WEEK", type="primary" if st.session_state.tf=="WEEK" else "secondary"): st.session_state.tf="WEEK"

with col_mk1:
    if st.button("NASDAQ", type="primary" if st.session_state.mk=="NASDAQ" else "secondary"): st.session_state.mk="NASDAQ"
with col_mk2:
    if st.button("KOSPI", type="primary" if st.session_state.mk=="KOSPI" else "secondary"): st.session_state.mk="KOSPI"

# 7. 차트 렌더링
analysis_list = []
if st.session_state.mk == "NASDAQ":
    for c, n in zip(nas_codes, nas_names):
        if c: analysis_list.append((c.upper(), n if n else c.upper()))
else:
    for c, n in zip(kos_codes, kos_names):
        if c: analysis_list.append((c.upper(), n if
