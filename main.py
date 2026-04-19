import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 고도화된 스타일 시트 (지수 한 줄 배치 및 크기 조절)
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem !important; }
    
    /* 상단 타이틀 스타일 */
    .main-title {
        font-size: 1.1rem !important;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #333;
    }

    /* 지수 라인 스타일 (한 줄 정렬) */
    .metric-container {
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 10px;
    }
    .metric-box {
        display: flex;
        align-items: center;
        font-size: 1rem; /* 지수 및 등락 숫자 크기 */
        font-weight: bold;
        white-space: nowrap;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #666;
        margin-right: 5px;
    }
    .up { color: #ef5350; margin-left: 5px; }   /* 상승 시 빨간색 */
    .down { color: #1e88e5; margin-left: 5px; } /* 하락 시 파란색 */

    /* 버튼 스타일 (6.0 버전 느낌 유지) */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로딩
@st.cache_data(ttl=300)
def get_market_data():
    tickers = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "GOLD": "GC=F", "환율": "KRW=X"}
    results = []
    for name, ticker in tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="5d")
            if not hist.empty and len(hist) >= 2:
                if isinstance(hist.columns, pd.MultiIndex): hist.columns = hist.columns.get_level_values(0)
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                diff = curr - prev
                status = "up" if diff >= 0 else "down"
                symbol = "▲" if diff >= 0 else "▼"
                results.append({"name": name, "val": f"{curr:,.1f}", "diff": f"{symbol}{abs(diff):,.1f}", "status": status})
            else: results.append({"name": name, "val": "N/A", "diff": "0.0", "status": "up"})
        except: results.append({"name": name, "val": "Err", "diff": "0.0", "status": "up"})
    return results

# 4. 사이드바 (종목 설정)
st.sidebar.title("📁 설정")
with st.sidebar.expander("🇺🇸 NASDAQ", expanded=False):
    nas_codes = [st.text_input(f"C{i+1}", key=f"nc{i}") for i in range(10)]
    nas_names = [st.text_input(f"N{i+1}", key=f"nn{i}") for i in range(10)]
with st.sidebar.expander("🇰🇷 KOSPI", expanded=False):
    kos_codes = [st.text_input(f"C{i+1}", key=f"kc{i}") for i in range(10)]
    kos_names = [st.text_input(f"N{i+1}", key=f"kn{i}") for i in range(10)]

# 5. 메인 레이아웃 상단
st.markdown('<div class="main-title">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)

# 커스텀 지수 영역 (HTML 사용으로 한 줄 강제)
m_info = get_market_data()
m_html = '<div class="metric-container">'
for info in m_info:
    m_html += f'''
        <div class="metric-box">
            <span class="metric-label">{info['name']}</span>
            <span>{info['val']}</span>
            <span class="{info['status']}">{info['diff']}</span>
        </div>
    '''
m_html += '</div>'
st.markdown(m_html, unsafe_allow_html=True)

st.divider()

# 6. 제어부 (토글 버튼)
if 'tf' not in st.session_state: st.session_state.tf = "DAY"
if 'mk' not in st.session_state: st.session_state.mk = "NASDAQ"

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    if st.button("HOUR", type="primary" if st.session_state.tf=="HOUR" else "secondary"): st.session_state.tf="HOUR"
with c2:
    if st.button("DAY", type="primary" if st.session_state.tf=="DAY" else "secondary"): st.session_state.tf="DAY"
with c3:
    if st.button("WEEK", type="primary" if st.session_state.tf=="WEEK" else "secondary"): st.session_state.tf="WEEK"
with c4:
    if st.button("NASDAQ", type="primary" if st.session_state.mk=="NASDAQ" else "secondary"): st.session_state.mk="NASDAQ"
with c5:
    if st.button("KOSPI", type="primary" if st.session_state.mk=="KOSPI" else "secondary"): st.session_state.mk="KOSPI"

# 7. 차트 영역
analysis_list = []
codes = nas_codes if st.session_state.mk == "NASDAQ" else kos_codes
names = nas_names if st.session_state.mk == "NASDAQ" else kos_names

for c, n in zip(codes, names):
    if c: analysis_list.append((c.upper(), n if n else c.upper()))
analysis_list.append(("GC=F", "GOLD"))

tf_map = {"HOUR": ("1h", "7d", "%H:00"), "DAY": ("1d", "1y", "%m/%d"), "WEEK": ("1wk", "2y", "%m/%d")}
interval, period, d_fmt = tf_map[st.session_state.tf]

for ticker, name in analysis_list:
    try:
        data = yf.Ticker(ticker).history(period=period, interval=interval).tail(60)
        if not data.empty:
            mc = mpf.make_marketcolors(up='red', down='blue', inherit=True)
            s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=True)
            fig, ax = mpf.plot(data, type='candle', style=s, figsize=(12, 5), returnfig=True, volume=False)
            ax[0].set_title(f" {name}", fontsize=12, fontweight='bold', loc='left')
            
            total = len(data)
            xticks = list(range(total - 1, -1, -12))
            ax[0].set_xticks(xticks)
            ax[0].set_xticklabels([data.index[j].strftime(d_fmt) for j in xticks], fontsize=9)
            st.pyplot(fig)
    except: pass
