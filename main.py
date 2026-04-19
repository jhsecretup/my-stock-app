import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 (스마트폰 최적화)
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 스타일 커스터마이징 (CSS)
st.markdown("""
    <style>
    .stButton>button { width: 100%; font-weight: bold; }
    .main { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로딩 함수 (캐싱으로 속도 향상)
@st.cache_data(ttl=3600)
def get_market_data():
    tickers = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "GOLD": "GC=F", "환율": "KRW=X"}
    info = []
    for name, ticker in tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            curr = hist['Close'].iloc[-1]
            diff = curr - hist['Close'].iloc[-2]
            color = "red" if diff > 0 else "blue"
            sym = "▲" if diff > 0 else "▼"
            info.append({"name": name, "val": f"{curr:,.2f}", "diff": f"{sym}{abs(diff):,.2f}", "color": color})
        except:
            info.append({"name": name, "val": "Error", "diff": "-", "color": "black"})
    return info

# 4. 사이드바 - 종목 설정 관리
st.sidebar.title("🛠️ 종목 설정")

with st.sidebar.expander("🇺🇸 나스닥 설정", expanded=False):
    nas_codes = [st.text_input(f"NAS 코드 {i+1}", key=f"nc{i}") for i in range(10)]
    nas_names = [st.text_input(f"NAS 이름 {i+1}", key=f"nn{i}") for i in range(10)]

with st.sidebar.expander("🇰🇷 코스피 설정", expanded=False):
    kos_codes = [st.text_input(f"KOS 코드 {i+1}", key=f"kc{i}") for i in range(10)]
    kos_names = [st.text_input(f"KOS 이름 {i+1}", key=f"kn{i}") for i in range(10)]

# 5. 메인 화면 상단 - 지수 정보
st.title("📈 비서표 투자 대시보드")
m_info = get_market_data()
cols = st.columns(4)
for i, info in enumerate(m_info):
    with cols[i]:
        st.metric(label=info['name'], value=info['val'], delta=info['diff'], delta_color="normal")

st.divider()

# 6. 첫째 줄 - 토글 버튼 (Session State 사용)
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
st.subheader(f"📊 {st.session_state.mk} - {st.session_state.tf} 차트")

# 분석 리스트 구성
analysis_list = []
if st.session_state.mk == "NASDAQ":
    for c, n in zip(nas_codes, nas_names):
        if c: analysis_list.append((c.upper(), n if n else c.upper()))
else:
    for c, n in zip(kos_codes, kos_names):
        if c: analysis_list.append((c.upper(), n if n else c.upper()))
analysis_list.append(("GC=F", "GOLD"))

# 시간 설정
tf_map = {"HOUR": ("1h", "7d", "%H:00"), "DAY": ("1d", "1y", "%m/%d"), "WEEK": ("1wk", "2y", "%m/%d")}
interval, period, d_fmt = tf_map[st.session_state.tf]

# 2열 레이아웃 (스마트폰에서는 자동으로 1열로 겹쳐 보임)
chart_cols = st.columns(2)
for idx, (ticker, name) in enumerate(analysis_list):
    with chart_cols[idx % 2]:
        try:
            data = yf.Ticker(ticker).history(period=period, interval=interval).tail(60)
            if not data.empty:
                # 캔들차트 생성
                mc = mpf.make_marketcolors(up='red', down='blue', inherit=True)
                s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=True)
                
                fig, ax = mpf.plot(data, type='candle', style=s, figsize=(8, 4.5), 
                                   returnfig=True, volume=False, ylabel='')
                
                # 최고/최저가 표시 로직
                hi, lo, curr = data['High'].max(), data['Low'].min(), data['Close'].iloc[-1]
                ax[0].set_title(f"[{name}]  NOW: {curr:,.2f}", fontsize=12, fontweight='bold')
                
                # X축 오른쪽 기준 정렬 (스트림릿은 인터랙티브 차트도 지원하지만, 요청하신 이미지 방식 유지)
                # 눈금 설정
                total = len(data)
                xticks = list(range(total - 1, -1, -10))
                ax[0].set_xticks(xticks)
                ax[0].set_xticklabels([data.index[j].strftime(d_fmt) for j in xticks], fontsize=8)
                
                st.pyplot(fig)
            else:
                st.error(f"{ticker} 데이터 없음")
        except Exception as e:
            st.error(f"{ticker} 에러: {e}")