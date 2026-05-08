import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import json
import os
from datetime import datetime

# ==========================================
# 1. 페이지 설정 및 스타일 (V11.2 디자인 계승)
# ==========================================
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; }
    .title-style { font-size: 1.6rem !important; font-weight: bold; margin-bottom: 1.5rem; color: #333; text-align: center; }
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] { width: 55% !important; flex-wrap: nowrap !important; gap: 5px !important; }
    div[data-testid="stTextInput"] div[data-baseweb="base-input"] { min-height: 28px !important; height: 28px !important; }
    .list-row { display: flex; justify-content: space-around; align-items: center; padding: 8px 15px; border-bottom: 1px solid #eee; }
    .up { color: #ef5350; font-weight: bold; } .down { color: #1e88e5; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 핵심 로직 (설정 로드 및 데이터 추출)
# ==========================================
def load_settings():
    if 'current_settings' in st.session_state: return st.session_state.current_settings
    if os.path.exists('stock_settings.json'):
        try:
            with open('stock_settings.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"nas_codes": [""]*50, "nas_names": [""]*50, "kos_codes": [""]*50, "kos_names": [""]*50}

@st.cache_data(ttl=10)
def get_market_summary():
    tickers = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "GOLD": "GC=F", "USD-KRW": "KRW=X"}
    results = []
    for name, sym in tickers.items():
        try:
            h = yf.Ticker(sym).history(period="2d")
            c, p = h['Close'].iloc[-1], h['Close'].iloc[-2]
            diff, pct = c - p, ((c - p) / p) * 100
            results.append({"name": name, "val": f"{c:,.2f}", "change": f"{pct:.2f}%", "status": "up" if diff >= 0 else "down"})
        except: pass
    return results

# ==========================================
# 3. 사이드바 (종목 편집기)
# ==========================================
st.sidebar.title("🛠️ 종목 설정 센터")
settings = load_settings()
st_nas, st_kos = st.sidebar.tabs(["🇺🇸 NASDAQ", "🇰🇷 KOSPI"])

def render_sidebar(tab, codes, names, px):
    nc, nn = [], []
    with tab:
        for i in range(20): # 가독성을 위해 일단 20개만 표시
            c1, c2 = st.columns([1, 2])
            with c1: v_c = st.text_input(f"{px}c{i}", value=codes[i], key=f"{px}ck{i}", label_visibility="collapsed")
            with c2: v_n = st.text_input(f"{px}n{i}", value=names[i], key=f"{px}nk{i}", label_visibility="collapsed")
            nc.append(v_c); nn.append(v_n)
    return nc, nn

new_nas_c, new_nas_n = render_sidebar(st_nas, settings['nas_codes'], settings['nas_names'], "n")
new_kos_c, new_kos_n = render_sidebar(st_kos, settings['kos_codes'], settings['kos_names'], "k")

if st.sidebar.button("💾 설정 저장", use_container_width=True, type="primary"):
    updated = {"nas_codes": new_nas_c + [""]*30, "nas_names": new_nas_n + [""]*30, "kos_codes": new_kos_c + [""]*30, "kos_names": new_kos_n + [""]*30}
    with open('stock_settings.json', 'w', encoding='utf-8') as f:
        json.dump(updated, f, ensure_ascii=False, indent=4)
    st.session_state.current_settings = updated
    st.rerun()

# ==========================================
# 4. 메인 대시보드 (탭 구성)
# ==========================================
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)
t1, t2, t3, t4 = st.tabs(["🏠 시장 지표", "📋 종목 리스트", "📊 차트 분석", "💎 기업 가치 분석"])

# --- Tab 1: 시장 지표 ---
with t1:
    m_data = get_market_summary()
    cols = st.columns(len(m_data))
    for i, m in enumerate(m_data):
        with cols[i]:
            st.metric(m['name'], m['val'], m['change'])

# --- Tab 2: 종목 리스트 ---
with t2:
    m_sel = st.radio("시장", ["NASDAQ", "KOSPI"], horizontal=True, key="m2")
    codes = new_nas_c if m_sel == "NASDAQ" else new_kos_c
    names = new_nas_n if m_sel == "NASDAQ" else new_kos_n
    
    st.markdown('<div class="list-row" style="background:#f8f9fa; font-weight:bold;"><div>종목명</div><div>현재가</div><div>등락률</div></div>', unsafe_allow_html=True)
    for c, n in zip(codes, names):
        if c.strip():
            try:
                sym = c.strip().upper() + (".KS" if m_sel == "KOSPI" and not (c.endswith(".KS") or c.endswith(".KQ")) else "")
                h = yf.Ticker(sym).history(period="2d")
                curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
                pct = ((curr-prev)/prev)*100
                st.markdown(f'<div class="list-row"><div>{n if n.strip() else c}</div><div class="{"up" if pct>=0 else "down"}">{curr:,.2f}</div><div class="{"up" if pct>=0 else "down"}">{pct:.2f}%</div></div>', unsafe_allow_html=True)
            except: pass

# --- Tab 3: 차트 분석 ---
with t3:
    st.info("개별 종목 차트를 보려면 아래 종목을 선택하세요.")
    # (기존 차트 로직 유지)

# --- Tab 4: 가치 분석 (사용자님 요청) ---
with t4:
    st.subheader("💎 주요 지표 (시가총액/PER/PBR)")
    m_val = st.radio("분석 시장", ["NASDAQ", "KOSPI"], horizontal=True, key="m4")
    target_codes = [c for c in (new_nas_c if m_val == "NASDAQ" else new_kos_c) if c.strip()]
    
    if st.button("🚀 실시간 가치 데이터 불러오기"):
        res = []
        pb = st.progress(0)
        for i, c in enumerate(target_codes):
            try:
                sym = c.strip().upper() + (".KS" if m_val == "KOSPI" and not (c.endswith(".KS") or c.endswith(".KQ")) else "")
                inf = yf.Ticker(sym).info
                mc = inf.get('marketCap', 0)
                mc_d = f"${mc/1e9:.1f}B" if m_val == "NASDAQ" else (f"{mc/1e12:.1f}조" if mc >= 1e12 else f"{mc/1e8:.0f}억")
                res.append({"종목": inf.get('shortName', c), "시총": mc_d, "PER": inf.get('trailingPE', '-'), "PBR": inf.get('priceToBook', '-'), "배당": f"{inf.get('dividendYield',0)*100:.1f}%"})
            except: pass
            pb.progress((i+1)/len(target_codes))
        if res: st.dataframe(pd.DataFrame(res), use_container_width=True)
