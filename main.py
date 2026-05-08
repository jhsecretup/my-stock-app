import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import json
import os

# 1. 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 데이터 로드/보정
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

# 3. 스타일 시트 (리스트 정렬 및 굵기 수정)
st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; }
    .title-style { font-size: 1.6rem !important; font-weight: bold; margin-bottom: 1.5rem; color: #333; text-align: center; }
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] { width: 55% !important; flex-wrap: nowrap !important; gap: 5px !important; }
    div[data-testid="stTextInput"] div[data-baseweb="base-input"] { min-height: 28px !important; height: 28px !important; }
    
    .metric-container { text-align: center; margin-bottom: 15px; }
    .metric-text { font-size: 1.4rem !important; font-weight: bold; }
    
    /* 종목 리스트 전용 스타일: 정확히 3등분 + 가운데 정렬 + 굵은 글씨 */
    .list-header { 
        display: flex; background-color: #f8f9fa; padding: 12px 0; 
        border-top: 2px solid #333; border-bottom: 1px solid #dee2e6;
        font-weight: bold; font-size: 1rem;
    }
    .list-row { 
        display: flex; padding: 12px 0; border-bottom: 1px solid #eee; 
        font-weight: bold; font-size: 1.05rem;
    }
    .list-col { flex: 1; text-align: center; } /* 33.3%씩 등분 */
    
    .up { color: #ef5350; } .down { color: #1e88e5; }
    </style>
    """, unsafe_allow_html=True)

# 4. 유틸리티 로직
@st.cache_data(ttl=10)
def get_market_data():
    tickers = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "GOLD": "GC=F", "USD-KRW": "KRW=X"}
    info = []
    for name, ticker in tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            if not hist.empty and len(hist) >= 2:
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                diff, pct = curr - prev, ((curr - prev) / prev) * 100
                status, sym = ("up", "▲") if diff >= 0 else ("down", "▼")
                val = f"{curr:,.2f}   {sym}{abs(diff):,.2f} ({abs(pct):.2f}%)"
                info.append({"name": name, "val": val, "status": status, "ticker": ticker})
        except: pass
    return info

def get_stock_info(c, n, m_type):
    if not c: return None
    try:
        tsym = c.strip().upper()
        if m_type == "KOSPI" and not (tsym.endswith(".KS") or tsym.endswith(".KQ")): tsym += ".KS"
        hist = yf.Ticker(tsym).history(period="2d")
        if not hist.empty and len(hist) >= 2:
            curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
            diff, pct = curr - prev, ((curr-prev)/prev)*100
            p_disp = f"{curr:,.2f}$" if m_type == "NASDAQ" else f"{int(curr):,}"
            c_disp = f"{pct:+.2f}%" # + 기호 포함
            return {"name": n if n.strip() else c, "price": p_disp, "change": c_disp, "status": "up" if diff >= 0 else "down"}
    except: return None

# 5. 사이드바 설정
saved_data = load_settings()
st.sidebar.title("🛠️ 종목 설정 센터")
input_tab_nas, input_tab_kos = st.sidebar.tabs(["🇺🇸 NASDAQ", "🇰🇷 KOSPI"])

def render_inputs(tab, codes, names, prefix):
    new_c, new_n = [], []
    with tab:
        for i in range(50):
            c1, c2 = st.columns([1.5, 2])
            with c1: code = st.text_input(f"{prefix}C{i}", value=codes[i], key=f"{prefix}c{i}", label_visibility="collapsed")
            with c2: name = st.text_input(f"{prefix}N{i}", value=names[i], key=f"{prefix}n{i}", label_visibility="collapsed")
            new_c.append(code); new_n.append(name)
    return new_c, new_n

new_nas_codes, new_nas_names = render_inputs(input_tab_nas, saved_data['nas_codes'], saved_data['nas_names'], "nc")
new_kos_codes, new_kos_names = render_inputs(input_tab_kos, saved_data['kos_codes'], saved_data['kos_names'], "kc")

if st.sidebar.button("💾 설정 영구 저장", use_container_width=True, type="primary"):
    updated = {"nas_codes": new_nas_codes, "nas_names": new_nas_names, "kos_codes": new_kos_codes, "kos_names": new_kos_names}
    st.session_state.current_settings = updated
    with open('stock_settings.json', 'w', encoding='utf-8') as f:
        json.dump(updated, f, ensure_ascii=False, indent=4)
    st.rerun()

# 6. 메인 화면
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)
t1, t2, t3, t4 = st.tabs(["🏠 시장 지표", "📋 종목 리스트", "📊 차트 분석", "💎 기업 가치 분석"])

with t1:
    m_info = get_market_data()
    if m_info:
        cols = st.columns(4)
        for i, m in enumerate(m_info):
            with cols[i]:
                st.markdown(f'<div class="metric-container"><div style="color:#666; font-size:0.9rem;">{m["name"]}</div><div class="metric-text {m["status"]}">{m["val"]}</div></div>', unsafe_allow_html=True)
        st.divider()
        c_cols = st.columns(2)
        for idx, m in enumerate(m_info):
            with c_cols[idx % 2]:
                try:
                    data = yf.Ticker(m['ticker']).history(period="1y").tail(40)
                    fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':'), figsize=(10, 6), returnfig=True)
                    ax[0].set_title(m['name'], fontsize=16, fontweight='bold'); st.pyplot(fig)
                except: pass

with t2:
    sel_market = st.radio("시장 선택", ["NASDAQ", "KOSPI"], horizontal=True, key="m2_list")
    codes = new_nas_codes if sel_market == "NASDAQ" else new_kos_codes
    names = new_nas_names if sel_market == "NASDAQ" else new_kos_names
    
    # 헤더 부분
    st.markdown(f"""
        <div class="list-header">
            <div class="list-col">종목명</div>
            <div class="list-col">현재가</div>
            <div class="list-col">등락률</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 리스트 데이터 부분
    for c, n in zip(codes, names):
        if c.strip():
            s = get_stock_info(c, n, sel_market)
            if s:
                st.markdown(f"""
                    <div class="list-row">
                        <div class="list-col">{s['name']}</div>
                        <div class="list-col {s['status']}">{s['price']}</div>
                        <div class="list-col {s['status']}">{s['change']}</div>
                    </div>
                    """, unsafe_allow_html=True)

with t3:
    sel_market_c = st.radio("시장 선택", ["NASDAQ", "KOSPI"], horizontal=True, key="m3_chart")
    c_codes = new_nas_codes if sel_market_c == "NASDAQ" else new_kos_codes
    c_names = new_nas_names if sel_market_c == "NASDAQ" else new_kos_names
    stock_opts = { (n.strip() if n.strip() else c.strip().upper()): c.strip().upper() for c, n in zip(c_codes, c_names) if c.strip() }
    
    if stock_opts:
        col1, col2 = st.columns([2, 1])
        with col1: sel_stock = st.selectbox("📊 분석 종목", list(stock_opts.keys()), key="chart_select_box")
        with col2: tf = st.radio("⏰ 주기", ["시봉", "일봉", "주봉"], index=1, horizontal=True, key="chart_tf")
        
        target = stock_opts[sel_stock]
        if sel_market_c == "KOSPI" and not (target.endswith(".KS") or target.endswith(".KQ")): target += ".KS"
        t_map = {"시봉": ("1h", "7d"), "일봉": ("1d", "1y"), "주봉": ("1wk", "2y")}
        
        try:
            data = yf.Ticker(target).history(period=t_map[tf][1], interval=t_map[tf][0]).tail(60)
            if not data.empty:
                curr, prev = data['Close'].iloc[-1], data['Close'].iloc[-2]
                fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(12, 7), returnfig=True)
                p_disp = f"{curr:,.2f}$" if sel_market_c == "NASDAQ" else f"{int(curr):,}"
                ax[0].set_title(f"{sel_stock} ({tf})  {p_disp}", fontsize=20, fontweight='bold', color="red" if curr >= prev else "blue")
                st.pyplot(fig)
        except: st.error("데이터를 가져올 수 없습니다.")

with t4:
    st.subheader("💎 기업 가치 상세 분석 (시총/PER/PBR)")
    m_val = st.radio("분석 시장", ["NASDAQ", "KOSPI"], horizontal=True, key="m4_val")
    v_codes = [c for c in (new_nas_codes if m_val == "NASDAQ" else new_kos_codes) if c.strip()]
    
    if st.button("🚀 데이터 분석 시작", use_container_width=True):
        res = []
        pb = st.progress(0)
        for i, c in enumerate(v_codes):
            try:
                sym = c.strip().upper() + (".KS" if m_val == "KOSPI" and not (c.endswith(".KS") or c.endswith(".KQ")) else "")
                inf = yf.Ticker(sym).info
                mc = inf.get('marketCap', 0)
                mc_d = f"${mc/1e9:.1f}B" if m_val == "NASDAQ" else (f"{mc/1e12:.1f}조" if mc >= 1e12 else f"{mc/1e8:.0f}억")
                res.append({
                    "종목명": inf.get('shortName', c),
                    "시가총액": mc_d,
                    "현재가": f"{inf.get('currentPrice', 0):,}",
                    "PER": round(inf.get('trailingPE', 0), 2) if inf.get('trailingPE') else "-",
                    "PBR": round(inf.get('priceToBook', 0), 2) if inf.get('priceToBook') else "-",
                    "배당률": f"{inf.get('dividendYield', 0)*100:.1f}%" if inf.get('dividendYield') else "-"
                })
            except: pass
            pb.progress((i+1)/len(v_codes))
        if res: st.table(pd.DataFrame(res))
