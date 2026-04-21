import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import json
import os

# 1. 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 데이터 로드/저장 (기존 20개 로직 유지)
def load_settings():
    if os.path.exists('stock_settings.json'):
        try:
            with open('stock_settings.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key in ['nas_codes', 'nas_names', 'kos_codes', 'kos_names']:
                    if len(data.get(key, [])) < 20:
                        data[key] = data.get(key, []) + [""] * (20 - len(data.get(key, [])))
                return data
        except: pass
    return {"nas_codes": [""]*20, "nas_names": [""]*20, "kos_codes": [""]*20, "kos_names": [""]*20}

def save_settings(data):
    with open('stock_settings.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

saved_data = load_settings()

# 3. 스타일 시트 (모바일 가독성 및 레이아웃 강제 조정)
st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
    .title-style { font-size: 1.3rem !important; font-weight: bold; margin-bottom: 1rem; color: #333; text-align: center; }
    
    /* 모바일에서 입력칸 레이벨 숨기기 (공간 확보) */
    div[data-testid="stWidgetLabel"] p { font-size: 0.8rem !important; color: #888 !important; }
    
    /* 입력창 간격 극단적으로 줄이기 */
    div[data-testid="stVerticalBlock"] > div { margin-bottom: -15px !important; }
    
    /* 지표 텍스트 크기 모바일 최적화 */
    .metric-text { font-size: 1.1rem !important; font-weight: bold; }
    .metric-label { font-size: 0.8rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. 유틸리티 및 데이터 로직 (기존 V9.7 유지)
@st.cache_data(ttl=60)
def get_market_data():
    tickers = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "GOLD": "GC=F", "USD-KRW": "KRW=X"}
    info = []
    for name, ticker in tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="3d")
            if not hist.empty and len(hist) >= 2:
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                diff, pct = curr - prev, ((curr - prev) / prev) * 100
                status, symbol = ("up", "▲") if diff >= 0 else ("down", "▼")
                val = f"{int(curr):,} ({symbol}{int(abs(diff)):,})"
                info.append({"name": name, "val": val, "status": status, "ticker": ticker})
        except: pass
    return info

def get_stock_info(c, n, m_type):
    if not c: return None
    try:
        ticker_sym = c.strip().upper()
        hist = yf.Ticker(ticker_sym).history(period="2d")
        if not hist.empty and len(hist) >= 2:
            curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
            diff, pct = curr - prev, ((curr-prev)/prev)*100
            p_disp = f"{curr:,.2f}$" if m_type == "NASDAQ" else f"{int(curr):,}"
            c_disp = f"{abs(pct):.2f}%"
            return {"name": n if n else ticker_sym, "price": p_disp, "change": c_disp, "status": "up" if diff >= 0 else "down"}
    except: return None

# 5. 사이드바 설정 (모바일에서도 2열 유지 핵심 로직)
st.sidebar.title("🛠️ 모바일 종목 설정")

def render_mobile_sidebar(title, codes, names, prefix):
    new_codes, new_names = [], []
    with st.sidebar.expander(title, expanded=(prefix == "nc")):
        # 헤더 표시
        h1, h2 = st.columns(2)
        h1.caption("티커(코드)")
        h2.caption("표시 이름")
        
        for i in range(20):
            # st.columns의 gap을 'small'로 설정하여 모바일에서도 옆으로 붙게 유도
            c1, c2 = st.columns(2)
            with c1:
                # label_visibility="collapsed"를 사용해 레이벨을 없애고 공간 확보
                c = st.text_input(f"C{i}", value=codes[i], key=f"{prefix}_c{i}", label_visibility="collapsed", placeholder=f"코드 {i+1}")
            with c2:
                n = st.text_input(f"N{i}", value=names[i], key=f"{prefix}_n{i}", label_visibility="collapsed", placeholder=f"이름 {i+1}")
            new_codes.append(c)
            new_names.append(n)
    return new_codes, new_names

new_nas_codes, new_nas_names = render_mobile_sidebar("🇺🇸 NASDAQ (20)", saved_data['nas_codes'], saved_data['nas_names'], "nc")
new_kos_codes, new_kos_names = render_mobile_sidebar("🇰🇷 KOSPI (20)", saved_data['kos_codes'], saved_data['kos_names'], "kc")

if st.sidebar.button("💾 리스트 영구 저장"):
    save_settings({"nas_codes": new_nas_codes, "nas_names": new_nas_names, "kos_codes": new_kos_codes, "kos_names": new_kos_names})
    st.sidebar.success("저장 완료!")

# 6. 메인 레이아웃 (모바일 대응)
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🏠 지표", "📋 리스트", "📊 차트"])

with tab1:
    m_info = get_market_data()
    if m_info:
        # 모바일에서는 지표를 2개씩 2줄로 배치
        c1, c2 = st.columns(2)
        for i, m in enumerate(m_info):
            target = c1 if i % 2 == 0 else c2
            with target:
                st.markdown(f'<div class="metric-container"><div class="metric-label">{m["name"]}</div><div class="metric-text {m["status"]}">{m["val"]}</div></div>', unsafe_allow_html=True)
        st.divider()
        # 차트는 모바일에서 한 줄에 하나씩 크게
        for m in m_info:
            try:
                data = yf.Ticker(m['ticker']).history(period="1y").tail(40)
                fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(8, 5), returnfig=True)
                ax[0].set_title(m['name'], fontsize=12); st.pyplot(fig)
            except: pass

with tab2:
    for c, n in zip(new_nas_codes + new_kos_codes, new_nas_names + new_kos_names):
        m_type = "NASDAQ" if c in new_nas_codes else "KOSPI"
        s = get_stock_info(c, n, m_type)
        if s:
            st.markdown(f"""<div class="list-row"><div class="list-item" style="flex:1.5; text-align:left;">{s['name']}</div><div class="list-item" style="flex:1.2;">{s['price']}</div><div class="list-item {s['status']}" style="flex:0.8;">{s['change']}</div></div>""", unsafe_allow_html=True)

with tab3:
    c_m = st.radio("시장", ["NASDAQ", "KOSPI"], horizontal=True)
    sel_codes, sel_names = (new_nas_codes, new_nas_names) if c_m == "NASDAQ" else (new_kos_codes, new_kos_names)
    for c, n in zip(sel_codes, sel_names):
        s = get_stock_info(c, n, c_m)
        if s:
            try:
                data = yf.Ticker(c.strip().upper()).history(period="1y").tail(40)
                fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(8, 5), returnfig=True)
                ax[0].set_title(f"{s['name']} {s['price']}", fontsize=14, color="red" if s['status']=="up" else "blue"); st.pyplot(fig)
            except: pass
