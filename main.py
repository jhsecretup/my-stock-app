import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd

# 1. 페이지 설정 및 배경색 커스텀
st.set_page_config(page_title="나만의 투자 대시보드", layout="wide")

# 2. 강력한 CSS 스타일 (색상, 크기, 위치 조절)
st.markdown("""
    <style>
    /* 메인 배경색 */
    .main { background-color: #ffffff; }
    
    /* 상단 지수 카드 디자인 */
    [data-testid="stMetric"] {
        background-color: #f1f3f5;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #dee2e6;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    
    /* 버튼 색상 및 크기 */
    .stButton>button {
        border-radius: 20px;
        height: 3em;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    /* 구분선 스타일 */
    hr { margin-top: 1rem; margin-bottom: 1rem; border-top: 2px solid #bbb; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로딩 (에러 방지 로직 포함)
@st.cache_data(ttl=300) # 5분마다 갱신
def get_market_data():
    tickers = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "GOLD": "GC=F", "USD/KRW": "KRW=X"}
    info = []
    for name, ticker in tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="5d")
            if not hist.empty and len(hist) >= 2:
                if isinstance(hist.columns, pd.MultiIndex): hist.columns = hist.columns.get_level_values(0)
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                diff = curr - prev
                info.append({"name": name, "val": f"{curr:,.2f}", "diff": f"{diff:,.2f}"})
            else: info.append({"name": name, "val": "N/A", "diff": "0"})
        except: info.append({"name": name, "val": "Error", "diff": "0"})
    return info

# 4. 사이드바 설정 (종목 관리)
st.sidebar.header("📁 MY PORTFOLIO")
with st.sidebar.expander("🇺🇸 NASDAQ 종목 (최대 10개)", expanded=False):
    nas_codes = [st.text_input(f"코드 {i+1}", key=f"nc{i}") for i in range(10)]
    nas_names = [st.text_input(f"이름 {i+1}", key=f"nn{i}") for i in range(10)]

with st.sidebar.expander("🇰🇷 KOSPI 종목 (최대 10개)", expanded=False):
    kos_codes = [st.text_input(f"코드 {i+1}", key=f"kc{i}") for i in range(10)]
    kos_names = [st.text_input(f"이름 {i+1}", key=f"kn{i}") for i in range(10)]

# 5. 메인 레이아웃 시작
st.title("🚀 SMART DASHBOARD")

# 상단 지수 카드 배치 (위치 조절)
m_info = get_market_data()
m_cols = st.columns(4)
for i, info in enumerate(m_info):
    with m_cols[i]:
        st.metric(label=info['name'], value=info['val'], delta=info['diff'])

st.write("---")

# 6. 제어부 (토글 버튼 위치 및 색상)
if 'tf' not in st.session_state: st.session_state.tf = "DAY"
if 'mk' not in st.session_state: st.session_state.mk = "NASDAQ"

# 버튼을 가로로 정렬
c1, c2, c3, c4, c5 = st.columns([1,1,1,1.5,1.5])
with c1:
    if st.button("HOUR", use_container_width=True, type="primary" if st.session_state.tf=="HOUR" else "secondary"):
        st.session_state.tf="HOUR"
with c2:
    if st.button("DAY", use_container_width=True, type="primary" if st.session_state.tf=="DAY" else "secondary"):
        st.session_state.tf="DAY"
with c3:
    if st.button("WEEK", use_container_width=True, type="primary" if st.session_state.tf=="WEEK" else "secondary"):
        st.session_state.tf="WEEK"
with c4:
    if st.button("NASDAQ MARKET", use_container_width=True, type="primary" if st.session_state.mk=="NASDAQ" else "secondary"):
        st.session_state.mk="NASDAQ"
with c5:
    if st.button("KOSPI MARKET", use_container_width=True, type="primary" if st.session_state.mk=="KOSPI" else "secondary"):
        st.session_state.mk="KOSPI"

# 7. 차트 영역 (크기 및 색상 커스텀)
st.subheader(f"📍 {st.session_state.mk} : {st.session_state.tf} VIEW")

# 종목 리스트 구성
analysis_list = []
base_idx = 0 if st.session_state.mk == "NASDAQ" else 0
codes = nas_codes if st.session_state.mk == "NASDAQ" else kos_codes
names = nas_names if st.session_state.mk == "NASDAQ" else kos_names

for c, n in zip(codes, names):
    if c: analysis_list.append((c.upper(), n if n else c.upper()))
analysis_list.append(("GC=F", "GOLD(선물)"))

# 시간 설정
tf_map = {"HOUR": ("1h", "7d", "%H:00"), "DAY": ("1d", "1y", "%m/%d"), "WEEK": ("1wk", "2y", "%m/%d")}
interval, period, d_fmt = tf_map[st.session_state.tf]

# 차트 출력 (크기 조절)
chart_cols = st.columns(2)
for idx, (ticker, name) in enumerate(analysis_list):
    with chart_cols[idx % 2]:
        try:
            data = yf.Ticker(ticker).history(period=period, interval=interval).tail(60)
            if not data.empty:
                mc = mpf.make_marketcolors(up='#ef5350', down='#26a69a', inherit=True) # 색상 커스텀
                s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=True, facecolor='#fafafa')
                
                # 차트 크기 (figsize) 조절
                fig, ax = mpf.plot(data, type='candle', style=s, figsize=(10, 5), returnfig=True, volume=False)
                
                ax[0].set_title(f" {name}", fontsize=14, fontweight='bold', loc='left')
                
                # X축 우측 정렬 유지
                total = len(data)
                xticks = list(range(total - 1, -1, -12))
                ax[0].set_xticks(xticks)
                ax[0].set_xticklabels([data.index[j].strftime(d_fmt) for j in xticks], fontsize=9)
                
                st.pyplot(fig)
            else: st.warning(f"{ticker} 데이터 없음")
        except: st.error(f"{ticker} 분석 불가")
