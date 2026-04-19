import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 스타일 시트 (중앙 정렬 및 1.5rem 통일)
st.markdown("""
    <style>
    .block-container { padding-top: 3.5rem !important; }
    
    /* 타이틀 중앙 정렬 */
    .title-style {
        font-size: 1.5rem !important;
        font-weight: bold;
        margin-bottom: 1.5rem;
        color: #333;
        text-align: center; /* 타이틀 중앙 정렬 */
    }

    .metric-container {
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-label { font-size: 1rem; color: #666; }
    .metric-text { 
        font-size: 1.5rem !important; 
        font-weight: bold; 
        white-space: nowrap; 
    }
    
    .up { color: #ef5350; }
    .down { color: #1e88e5; }
    
    hr { margin: 1.5rem 0; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로딩 함수 (환율 이름 변경 및 괄호 형식)
@st.cache_data(ttl=300)
def get_market_data():
    # 환율 이름을 USD-KRW로 변경
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
                
                # 형식: 2,500.0 (▲10.0 +0.45%)
                combined_val = f"{curr:,.1f} ({symbol}{abs(diff):,.1f} {pct_sign}{percent:.2f}%)"
                info.append({"name": name, "val": combined_val, "status": status, "ticker": ticker})
            else:
                info.append({"name": name, "val": "N/A", "status": "up", "ticker": ticker})
        except:
            info.append({"name": name, "val": "Data Error", "status": "up", "ticker": ticker})
    return info

# 4. 사이드바 설정 (설정창 유지)
st.sidebar.title("🛠️ 설정")
with st.sidebar.expander("🇺🇸 NASDAQ 종목", expanded=False):
    nas_codes = [st.text_input(f"NAS 코드 {i+1}", key=f"nc{i}") for i in range(10)]
with st.sidebar.expander("🇰🇷 KOSPI 종목", expanded=False):
    kos_codes = [st.text_input(f"KOS 코드 {i+1}", key=f"kc{i}") for i in range(10)]

# 5. 메인 상단 (제목 중앙 정렬)
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

# 6. 시장 지수 차트 영역
st.markdown('<div style="text-align: center; font-size: 1.2rem; font-weight: bold; margin-bottom: 20px;">📊 주요 시장 지수 차트 (일봉)</div>', unsafe_allow_html=True)

interval, period, d_fmt = "1d", "1y", "%m/%d"

# 차트 순서 재배치 (모바일 환경 고려: 나스닥과 골드 순서 교체)
# 기존 m_info 순서: 0:KOSPI, 1:NASDAQ, 2:GOLD, 3:USD-KRW
# 변경 목표 순서: 0:KOSPI, 2:GOLD, 1:NASDAQ, 3:USD-KRW
reordered_indices = [0, 2, 1, 3]
reordered_info = [m_info[i] for i in reordered_indices]

chart_cols = st.columns(2)
for idx, info in enumerate(reordered_info):
    with chart_cols[idx % 2]:
        try:
            data = yf.Ticker(info['ticker']).history(period=period, interval=interval).tail(60)
            if not data.empty:
                mc = mpf.make_marketcolors(up='red', down='blue', inherit=True)
                s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=True)
                
                fig, ax = mpf.plot(data, type='candle', style=s, figsize=(10, 6), returnfig=True, volume=False)
                
                # 종목명 중앙 정렬
                ax[0].set_title(f"[{info['name']}]", fontsize=16, fontweight='bold', loc='center', pad=10)
                
                total = len(data)
                xticks = list(range(total - 1, -1, -12))
                ax[0].set_xticks(xticks)
                ax[0].set_xticklabels([data.index[j].strftime(d_fmt) for j in xticks], fontsize=9)
                
                st.pyplot(fig)
        except:
            pass
