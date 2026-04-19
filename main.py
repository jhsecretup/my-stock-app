import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd

# 1. 페이지 설정 (최적의 여백 확보)
st.set_page_config(page_title="나만의 투자 대시보드", layout="wide")

# 2. UI 개선용 CSS (상단 짤림 방지 및 가독성)
st.markdown("""
    <style>
    /* 상단 여백 확보 (짤림 방지) */
    .block-container { padding-top: 3rem !important; }
    
    /* 지수 카드 디자인 */
    [data-testid="stMetric"] {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 10px;
        border: 1px solid #eeeeee;
    }
    
    /* 버튼 스타일 조정 */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로딩 (에러 방지 로직)
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

# 4. 사이드바 종목 설정
st.sidebar.header("📁 PORTFOLIO")
with st.sidebar.expander("🇺🇸 NASDAQ 종목", expanded=False):
    nas_codes = [st.text_input(f"코드 {i+1}", key=f"nc{i}") for i in range(10)]
    nas_names = [st.text_input(f"이름 {i+1}", key=f"nn{i}") for i in range(10)]
with st.sidebar.expander("🇰🇷 KOSPI 종목", expanded=False):
    kos_codes = [st.text_input(f"코드 {i+1}", key=f"kc{i}") for i in range(10)]
    kos_names = [st.text_input(f"이름 {i+1}", key=f"kn{i}") for i in range(10)]

# 5. 메인 레이아웃 (지수 카드)
st.title("🚀 SMART DASHBOARD")

m_info = get_market_data()
m_cols = st.columns(4)
for i, info in enumerate(m_info):
    with m_cols[i]:
        st.metric(label=info['name'], value=info['val'], delta=info['diff'])

st.divider()

# 6. 제어부 (토글 버튼) - 자연스러운 배치
if 'tf' not in st.session_state: st.session_state.tf = "DAY"
if 'mk' not in st.session_state: st.session_state.mk = "NASDAQ"

col_tf, col_mk = st.columns([3, 2])

with col_tf:
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("HOUR", type="primary" if st.session_state.tf=="HOUR" else "secondary"): st.session_state.tf="HOUR"
    with b2:
        if st.button("DAY", type="primary" if st.session_state.tf=="DAY" else "secondary"): st.session_state.tf="DAY"
    with b3:
        if st.button("WEEK", type="primary" if st.session_state.tf=="WEEK" else "secondary"): st.session_state.tf="WEEK"

with col_mk:
    b4, b5 = st.columns(2)
    with b4:
        if st.button("NASDAQ", type="primary" if st.session_state.mk=="NASDAQ" else "secondary"): st.session_state.mk="NASDAQ"
    with b5:
        if st.button("KOSPI", type="primary" if st.session_state.mk=="KOSPI" else "secondary"): st.session_state.mk="KOSPI"

# 7. 차트 영역 (시원하게 복구)
analysis_list = []
codes = nas_codes if st.session_state.mk == "NASDAQ" else kos_codes
names = nas_names if st.session_state.mk == "NASDAQ" else kos_names

for c, n in zip(codes, names):
    if c: analysis_list.append((c.upper(), n if n else c.upper()))
analysis_list.append(("GC=F", "GOLD"))

tf_map = {"HOUR": ("1h", "7d", "%H:00"), "DAY": ("1d", "1y", "%m/%d"), "WEEK": ("1wk", "2y", "%m/%d")}
interval, period, d_fmt = tf_map[st.session_state.tf]

# 차트 출력 (스마트폰에서 1열, PC에서 2열로 자동 조절되도록 설정)
for ticker, name in analysis_list:
    try:
        data = yf.Ticker(ticker).history(period=period, interval=interval).tail(60)
        if not data.empty:
            mc = mpf.make_marketcolors(up='red', down='blue', inherit=True)
            s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=True)
            
            # 차트 크기를 다시 큼직하게 설정 (figsize 조절)
            fig, ax = mpf.plot(data, type='candle', style=s, figsize=(12, 6), returnfig=True, volume=False)
            ax[0].set_title(f"[{name}]", fontsize=15, fontweight='bold', loc='left')
            
            # X축 정렬 유지
            total = len(data)
            xticks = list(range(total - 1, -1, -12))
            ax[0].set_xticks(xticks)
            ax[0].set_xticklabels([data.index[j].strftime(d_fmt) for j in xticks], fontsize=10)
            
            st.pyplot(fig)
            st.write("") # 차트 간 간격
    except:
        pass
