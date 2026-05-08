import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import json
import os
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 데이터 로드/보정 함수
def load_settings():
    if 'current_settings' in st.session_state:
        data = st.session_state.current_settings
    elif os.path.exists('stock_settings.json'):
        try:
            with open('stock_settings.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: data = {}
    else: data = {}
    
    for key in ['nas_codes', 'nas_names', 'kos_codes', 'kos_names']:
        if key not in data: data[key] = [""] * 50
        else: data[key] = (data[key] + [""] * 50)[:50]
    return data

# 3. 스타일 시트 (가로 폭 55% 및 디자인)
st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; }
    .title-style { font-size: 1.6rem !important; font-weight: bold; margin-bottom: 1.5rem; color: #333; text-align: center; }
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] { width: 55% !important; flex-wrap: nowrap !important; gap: 5px !important; }
    div[data-testid="stTextInput"] div[data-baseweb="base-input"] { min-height: 28px !important; height: 28px !important; }
    .list-row { display: flex; justify-content: space-around; align-items: center; padding: 10px 15px; border-bottom: 1px solid #eee; text-align: center; }
    .list-item { font-size: 1rem; font-weight: bold; flex: 1; }
    .up { color: #ef5350; } .down { color: #1e88e5; }
    </style>
    """, unsafe_allow_html=True)

# 4. 데이터 추출 보조 함수들
@st.cache_data(ttl=10)
def get_market_data():
    tickers = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "GOLD": "GC=F", "USD-KRW": "KRW=X"}
    info = []
    for name, ticker in tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            if len(hist) >= 2:
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                diff, pct = curr - prev, ((curr - prev) / prev) * 100
                status = "up" if diff >= 0 else "down"
                sym = "▲" if diff >= 0 else "▼"
                val = f"{curr:,.2f}  {sym}{abs(diff):,.2f} ({abs(pct):.2f}%)"
                info.append({"name": name, "val": val, "status": status, "ticker": ticker})
        except: pass
    return info

def get_stock_info(c, n, m_type):
    try:
        tsym = c.strip().upper()
        if m_type == "KOSPI" and not (tsym.endswith(".KS") or tsym.endswith(".KQ")): tsym += ".KS"
        hist = yf.Ticker(tsym).history(period="2d")
        if len(hist) >= 2:
            curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
            diff, pct = curr - prev, ((curr-prev)/prev)*100
            p_disp = f"{curr:,.2f}$" if m_type == "NASDAQ" else f"{int(curr):,}"
            c_disp = f"{abs(diff):,.2f}({abs(pct):.2f}%)" if m_type == "NASDAQ" else f"{int(abs(diff)):,}({abs(pct):.2f}%)"
            return {"name": n if n.strip() else c, "price": p_disp, "change": c_disp, "status": "up" if diff >= 0 else "down"}
    except: return None

@st.cache_data(ttl=3600)
def get_valuation(c, m_type):
    try:
        tsym = c.strip().upper()
        if m_type == "KOSPI" and not (tsym.endswith(".KS") or tsym.endswith(".KQ")): tsym += ".KS"
        inf = yf.Ticker(tsym).info
        mc = inf.get('marketCap', 0)
        mc_d = f"${mc/1e9:.1f}B" if m_type == "NASDAQ" else (f"{mc/1e12:.1f}조" if mc >= 1e12 else f"{mc/1e8:.0f}억")
        return {"name": inf.get('shortName', c), "m_cap": mc_d, "price": inf.get('currentPrice', 0), "per": inf.get('trailingPE', "-"), "pbr": inf.get('priceToBook', "-"), "div": f"{inf.get('dividendYield', 0)*100:.1f}%" if inf.get('dividendYield') else "-"}
    except: return None

# 5. 사이드바 편집 (사라졌던 부분 복구)
saved_data = load_settings()
st.sidebar.title("🛠️ 종목 설정 센터")
st.sidebar.subheader("📌 리스트 편집")
tab_n, tab_k = st.sidebar.tabs(["🇺🇸 NAS", "🇰🇷 KOS"])

def render_side(tab, codes, names, px):
    nc, nn = [], []
    with tab:
        for i in range(50):
            c1, c2 = st.columns([1.5, 2])
            with c1: v_c = st.text_input(f"{px}c{i}", value=codes[i], key=f"{px}ck{i}", label_visibility="collapsed", placeholder="코드")
            with c2: v_n = st.text_input(f"{px}n{i}", value=names[i], key=f"{px}nk{i}", label_visibility="collapsed", placeholder="종목명")
            nc.append(v_c); nn.append(v_n)
    return nc, nn

new_nc, new_nn = render_side(tab_n, saved_data['nas_codes'], saved_data['nas_names'], "n")
new_kc, new_kn = render_side(tab_k, saved_data['kos_codes'], saved_data['kos_names'], "k")

if st.sidebar.button("💾 설정 저장", use_container_width=True, type="primary"):
    upd = {"nas_codes": new_nc, "nas_names": new_nn, "kos_codes": new_kc, "kos_names": new_kn}
    st.session_state.current_settings = upd
    with open('stock_settings.json', 'w', encoding='utf-8') as f: json.dump(upd, f, ensure_ascii=False, indent=4)
    st.rerun()

# 6. 메인 화면
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)
t1, t2, t3, t4 = st.tabs(["🏠 시장 지표", "📋 종목 리스트", "📊 차트 분석", "💎 기업 가치 분석"])

with t1:
    m_info = get_market_data()
    if m_info:
        cols = st.columns(4)
        for i, m in enumerate(m_info):
            with cols[i]: st.markdown(f'<div style="text-align:center"><div style="color:#666;font-size:0.9rem">{m["name"]}</div><div class="list-item {m["status"]}">{m["val"]}</div></div>', unsafe_allow_html=True)

with t2:
    sel_m = st.radio("시장", ["NASDAQ", "KOSPI"], horizontal=True, label_visibility="collapsed")
    cs = new_nc if sel_m == "NASDAQ" else new_kc
    ns = new_nn if sel_m == "NASDAQ" else new_kn
    st.markdown('<div class="list-row" style="background:#f8f9fa; font-weight:bold"><div>종목명</div><div>현재가</div><div>등락률</div></div>', unsafe_allow_html=True)
    for c, n in zip(cs, ns):
        if c.strip():
            s = get_stock_info(c, n, sel_m)
            if s: st.markdown(f'<div class="list-row"><div>{s["name"]}</div><div class="{s["status"]}">{s["price"]}</div><div class="{s["status"]}">{s["change"]}</div></div>', unsafe_allow_html=True)

with t3:
    st.info("개별 종목 코드를 선택하여 상세 차트를 확인하세요.")
    # (기존 차트 로직 추가 가능)

with t4:
    st.subheader("💎 기업 가치 상세 분석 (시총/PER/PBR)")
    m_val = st.radio("분석 시장", ["NASDAQ", "KOSPI"], horizontal=True, key="mv")
    v_cs = [c for c in (new_nc if m_val == "NASDAQ" else new_kc) if c.strip()]
    if st.button("🚀 데이터 분석 시작", use_container_width=True):
        res = []
        pb = st.progress(0)
        for i, c in enumerate(v_cs):
            d = get_valuation(c, m_val)
            if d: res.append(d)
            pb.progress((i+1)/len(v_cs))
        if res:
            df = pd.DataFrame(res)
            st.table(df) # 깔끔하게 표로 출력
