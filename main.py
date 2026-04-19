import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 스타일 시트 (1.5rem 통일 및 중앙 정렬)
st.markdown("""
    <style>
    .block-container { padding-top: 3.5rem !important; }
    
    /* 타이틀 중앙 정렬 및 크기 */
    .title-style {
        font-size: 1.5rem !important;
        font-weight: bold;
        margin-bottom: 1.5rem;
        color: #333;
        text-align: left; /* 제목은 왼쪽 정렬 유지 */
    }

    /* 지수 영역 스타일 */
    .metric-container {
        text-align: center; /* 지수 정보를 칸 안에서 중앙으로 */
    }
    .metric-label { font-size: 1rem; color: #666; margin-bottom: 4px; }
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

# 3. 데이터 로딩 함수 (등락률 % 계산 추가)
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
                prev = hist['Close'].iloc[-2]
                diff = curr - prev
                percent = (diff / prev) * 100 # 등락률 계산
                
                status = "up" if diff >= 0 else "down"
                symbol = "▲" if diff >= 0 else "▼"
                sign = "+" if diff >= 0 else "" # 퍼센트 앞 기호
                
                # 형식: 2,500.0 (▲10.0, +0.45%)
                combined_val = f"{curr:,.1f} ({symbol}{abs(diff):,.1;f}, {sign}{percent:,.2f}%)"
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

# 5. 메인 상단
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)

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

# 6. 제어부 (시/일/주 삭제, 시장 선택만 유지)
if 'mk' not in st.session_state: st.session_state.mk = "NASDAQ"

c1, c2 = st.columns([1, 1])
with c1:
    if st.button("NASDAQ", type="primary" if st.session_state.mk=="NASDAQ" else "secondary", use_container_width=True): 
        st.session_state.mk="NASDAQ"
with c2:
    if st.button("KOSPI", type="primary" if st.session_state.mk=="KOSPI" else "secondary", use_container_width=True): 
        st.session_state.mk="KOSPI"

# 7. 차트 영역 (중앙 정렬 적용)
analysis_list = []
if st.session_state.mk == "NASDAQ":
    for c, n in zip(nas_codes, nas_names):
        if c: analysis_list.append((c.upper(), n if n else c.upper()))
else:
    for c, n in zip(kos_codes, kos_names):
        if c: analysis_list.append((c.upper(), n if n else c.upper()))
analysis_list.append(("GC=F", "GOLD"))

# 기본값 '일(DAY)' 기준으로 차트 고정
interval, period, d_fmt = "1d", "1y", "%m/%d"

chart_cols = st.columns(2)
for idx, (ticker, name) in enumerate(analysis_list):
    with chart_cols[idx % 2]:
        try:
            data = yf.Ticker(ticker).history(period=period, interval=interval).tail(60)
            if not data.empty:
                mc = mpf.make_marketcolors(up='red', down='blue', inherit=True)
                s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=True)
                fig, ax = mpf.plot(data, type='candle', style=s, figsize=(8, 4.5), returnfig=True, volume=False)
                
                # 종목 이름 중앙 정렬 (loc='center') 및 크기 1.5rem 수준
                ax[0].set_title(f"[{name}]", fontsize=16, fontweight='bold', loc='center')
                
                total = len(data)
                xticks = list(range(total - 1, -1, -10))
                ax[0].set_xticks(xticks)
                ax[0].set_xticklabels([data.index[j].strftime(d_fmt) for j in xticks], fontsize=8)
                st.pyplot(fig)
        except:
            pass
