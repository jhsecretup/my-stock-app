import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="나만의 투자 대시보드", layout="wide")

# 2. 모바일 한 줄 정렬을 위한 핵심 CSS
st.markdown("""
    <style>
    /* 전체 배경 및 여백 최적화 */
    .main { background-color: #ffffff; }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }

    /* 지수 카드(Metric) 한 줄 강제 정렬 */
    [data-testid="stHorizontalBlock"] > div {
        min-width: 0px !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.1rem !important; /* 글자 크기 살짝 축소 */
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
    }

    /* 버튼 한 줄 정렬 및 크기 최적화 */
    .stButton>button {
        width: 100%;
        padding: 0px;
        height: 2.5rem;
        font-size: 0.7rem !important; /* 버튼 글자를 작게 해서 한 줄에 넣음 */
        border-radius: 10px;
        font-weight: bold;
    }
    
    /* 구분선 간격 줄임 */
    hr { margin: 0.5rem 0; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로딩
@st.cache_data(ttl=300)
def get_market_data():
    tickers = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "GOLD": "GC=F", "환율": "KRW=X"}
    info = []
    for name, ticker in tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="5d")
            if not hist.empty and len(hist) >= 2:
                if isinstance(hist.columns, pd.MultiIndex): hist.columns = hist.columns.get_level_values(0)
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                diff = curr - prev
                info.append({"name": name, "val": f"{curr:,.1f}", "diff": f"{diff:,.1f}"})
            else: info.append({"name": name, "val": "N/A", "diff": "0"})
        except: info.append({"name": name, "val": "Error", "diff": "0"})
    return info

# 4. 사이드바 (종목 관리)
st.sidebar.header("📁 PORTFOLIO")
with st.sidebar.expander("🇺🇸 NASDAQ", expanded=False):
    nas_codes = [st.text_input(f"C{i+1}", key=f"nc{i}") for i in range(10)]
    nas_names = [st.text_input(f"N{i+1}", key=f"nn{i}") for i in range(10)]
with st.sidebar.expander("🇰🇷 KOSPI", expanded=False):
    kos_codes = [st.text_input(f"C{i+1}", key=f"kc{i}") for i in range(10)]
    kos_names = [st.text_input(f"N{i+1}", key=f"kn{i}") for i in range(10)]

# 5. 메인 레이아웃
st.subheader("🚀 SMART DASHBOARD")

# 지수 정보 4개 한 줄 배치
m_info = get_market_data()
m_cols = st.columns(4)
for i, info in enumerate(m_info):
    with m_cols[i]:
        st.metric(label=info['name'], value=info['val'], delta=info['diff'])

st.divider()

# 6. 버튼 5개 한 줄 배치
if 'tf' not in st.session_state: st.session_state.tf = "DAY"
if 'mk' not in st.session_state: st.session_state.mk = "NASDAQ"

# 가로 칸을 5개로 똑같이 나눔
b_cols = st.columns(5)
btns = ["HOUR", "DAY", "WEEK", "NAS", "KOS"]

with b_cols[0]:
    if st.button("HOUR", type="primary" if st.session_state.tf=="HOUR" else "secondary"): st.session_state.tf="HOUR"
with b_cols[1]:
    if st.button("DAY", type="primary" if st.session_state.tf=="DAY" else "secondary"): st.session_state.tf="DAY"
with b_cols[2]:
    if st.button("WEEK", type="primary" if st.session_state.tf=="WEEK" else "secondary"): st.session_state.tf="WEEK"
with b_cols[3]:
    if st.button("NAS", type="primary" if st.session_state.mk=="NASDAQ" else "secondary"): st.session_state.mk="NASDAQ"
with b_cols[4]:
    if st.button("KOS", type="primary" if st.session_state.mk=="KOSPI" else "secondary"): st.session_state.mk="KOSPI"

# 7. 차트 영역
analysis_list = []
codes = nas_codes if st.session_state.mk == "NASDAQ" else kos_codes
names = nas_names if st.session_state.mk == "NASDAQ" else kos_names

for c, n in zip(codes, names):
    if c: analysis_list.append((c.upper(), n if n else c.upper()))
analysis_list.append(("GC=F", "GOLD"))

tf_map = {"HOUR": ("1h", "7d", "%H:00"), "DAY": ("1d", "1y", "%m/%d"), "WEEK": ("1wk", "2y", "%m/%d")}
interval, period, d_fmt = tf_map[st.session_state.tf]

chart_cols = st.columns(2)
for idx, (ticker, name) in enumerate(analysis_list):
    with chart_cols[idx % 2]:
        try:
            data = yf.Ticker(ticker).history(period=period, interval=interval).tail(60)
            if not data.empty:
                mc = mpf.make_marketcolors(up='red', down='blue', inherit=True)
                s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=True)
                fig, ax = mpf.plot(data, type='candle', style=s, figsize=(10, 5), returnfig=True, volume=False)
                ax[0].set_title(f"{name}", fontsize=12, fontweight='bold', loc='left')
                
                total = len(data)
                xticks = list(range(total - 1, -1, -12))
                ax[0].set_xticks(xticks)
                ax[0].set_xticklabels([data.index[j].strftime(d_fmt) for j in xticks], fontsize=8)
                st.pyplot(fig)
        except: st.write(f"{ticker} 분석중...")
