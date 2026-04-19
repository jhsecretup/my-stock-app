import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 모든 주요 요소 크기를 1.5rem으로 통일하는 스타일
st.markdown("""
    <style>
    /* 상단 여백 유지 */
    .block-container { padding-top: 3.5rem !important; }
    
    /* 타이틀 크기: 1.5rem */
    .title-style {
        font-size: 1.5rem !important;
        font-weight: bold;
        margin-bottom: 1.5rem;
        color: #333;
    }

    /* 지수 이름 크기: 1rem (작게 유지하여 숫자 강조) */
    .metric-label { font-size: 1rem; color: #666; margin-bottom: 4px; }
    
    /* 지수 및 등락 숫자 크기: 1.5rem */
    .metric-text { 
        font-size: 1.5rem !important; 
        font-weight: bold; 
        white-space: nowrap; 
    }
    
    /* 상승/하락 색상 */
    .up { color: #ef5350; }
    .down { color: #1e88e5; }
    
    hr { margin: 1.5rem 0; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로딩 함수
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
                status = "up" if diff >= 0 else "down"
                symbol = "▲" if diff >= 0 else "▼"
                combined_val = f"{curr:,.1f} ({symbol}{abs(diff):,.1f})"
                info.append({"name": name, "val": combined_val, "status": status})
            else:
                info.append({"name": name, "val": "N/A", "status": "up"})
        except:
            info.append({"name": name, "val": "Error", "status": "up"})
    return info

# 4. 사이드바 설정
st.sidebar.title("🛠️ 설정")
with st.sidebar.expander("🇺🇸 NASDAQ 종목", expanded=False):
    nas_codes = [st.text_input(f"NAS 코드 {i+1}", key=f"nc{i}") for i in range(10)]
    nas_names = [st.text_input(f"NAS 이름 {i+1}", key=f"nn{i}") for i in range(10)]
with st.sidebar.expander("🇰🇷 KOSPI 종목", expanded=False):
    kos_codes = [st.text_input(f"KOS 코드 {i+1}", key=f"kc{i}") for i in range(10)]
    kos_names = [st.text_input(f"KOS 이름 {i+1}", key=f"kn{i}") for i in range(10)]

# 5. 메인 상단 (제목 및 지수)
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)

m_info = get_market_data()
cols = st.columns(4)
for i, info in enumerate(m_info):
    with cols[i]:
        st.markdown(f'''
            <div class="metric-label">{info['name']}</div>
            <div class="metric-text {info['status']}">{info['val']}</div>
        ''', unsafe_allow_html=True)

st.divider()

# 6. 제어부 (버튼)
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

# 7. 차트 영역
analysis_list = []
if st.session_state.mk == "NASDAQ":
    for c, n in zip(nas_codes, nas_names):
        if c: analysis_list.append((c.upper(), n if n else c.upper()))
else:
    for c, n in zip(kos_codes, kos_names):
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
                fig, ax = mpf.plot(data, type='candle', style=s, figsize=(8, 4.5), returnfig=True, volume=False)
                
                # 차트 위 종목 이름 크기도 1.5rem 수준으로 확대 (fontsize=16 정도가 1.5rem과 비슷합니다)
                ax[0].set_title(f"[{name}]", fontsize=16, fontweight='bold', loc='left')
                
                total = len(data)
                xticks = list(range(total - 1, -1, -10))
                ax[0].set_xticks(xticks)
                ax[0].set_xticklabels([data.index[j].strftime(d_fmt) for j in xticks], fontsize=8)
                st.pyplot(fig)
        except:
            pass
