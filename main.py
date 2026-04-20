import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import json
import os

# 1. 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 2. 데이터 로드/저장 함수
def load_settings():
    if os.path.exists('stock_settings.json'):
        try:
            with open('stock_settings.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"nas_codes": [""]*10, "nas_names": [""]*10, "kos_codes": [""]*10, "kos_names": [""]*10}

def save_settings(data):
    with open('stock_settings.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

saved_data = load_settings()

# 3. 스타일 시트
st.markdown("""
    <style>
    .block-container { padding-top: 3.5rem !important; }
    .title-style { font-size: 1.5rem !important; font-weight: bold; margin-bottom: 1.5rem; color: #333; text-align: center; }
    .metric-container { text-align: center; margin-bottom: 10px; }
    .metric-label { font-size: 1rem; color: #666; }
    .metric-text { font-size: 1.5rem !important; font-weight: bold; white-space: nowrap; }
    .up { color: #ef5350; } .down { color: #1e88e5; }
    .list-row { display: flex; justify-content: space-around; align-items: center; padding: 10px 15px; border-bottom: 1px solid #eee; text-align: center; }
    .list-item { font-size: 1.1rem; font-weight: bold; flex: 1; }
    .list-header { font-size: 1rem; font-weight: bold; color: #555; flex: 1; }
    .bond-card { background-color: #f9f9f9; padding: 20px; border-radius: 10px; border-left: 5px solid #2e7d32; margin-bottom: 20px; }
    .bond-result { font-size: 1.2rem; font-weight: bold; color: #2e7d32; }
    </style>
    """, unsafe_allow_html=True)

# 4. 유틸리티 및 데이터 함수
def parse_display_names(raw_name, ticker):
    if not raw_name: return ticker, ticker
    if '/' in raw_name:
        parts = [p.strip() for p in raw_name.split('/')]
        l_name = parts[0] if parts[0] else ticker
        c_name = parts[1] if len(parts) > 1 and parts[1] else l_name
        return l_name, c_name
    return raw_name, raw_name

@st.cache_data(ttl=300)
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
                val = f"{curr:,.1f} ({symbol}{abs(diff):,.1f} {abs(pct):.2f}%)"
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
            l_name, c_name = parse_display_names(n, ticker_sym)
            p_disp = f"{curr:,.2f}$" if m_type == "NAS" else f"{int(curr):,}"
            c_disp = f"{abs(diff):,.2f} ({abs(pct):.2f}%)" if m_type == "NAS" else f"{int(abs(diff)):,} ({abs(pct):.2f}%)"
            return {"name": l_name, "c_name": c_name, "price": p_disp, "pct": pct, "change": c_disp, "status": "up" if diff >= 0 else "down", "curr": curr, "prev": prev}
    except: return None

# 5. 사이드바 설정
st.sidebar.title("🛠️ 종목 설정")
new_nas_codes, new_nas_names = [], []
with st.sidebar.expander("🇺🇸 NASDAQ 종목", expanded=True):
    for i in range(10):
        new_nas_codes.append(st.text_input(f"NAS 코드 {i+1}", value=saved_data['nas_codes'][i] if i < len(saved_data['nas_codes']) else "", key=f"nc{i}"))
        new_nas_names.append(st.text_input(f"NAS 이름 {i+1}", value=saved_data['nas_names'][i] if i < len(saved_data['nas_names']) else "", key=f"nn{i}"))

new_kos_codes, new_kos_names = [], []
with st.sidebar.expander("🇰🇷 KOSPI 종목", expanded=False):
    for i in range(10):
        new_kos_codes.append(st.text_input(f"KOS 코드 {i+1}", value=saved_data['kos_codes'][i] if i < len(saved_data['kos_codes']) else "", key=f"kc{i}"))
        new_kos_names.append(st.text_input(f"KOS 이름 {i+1}", value=saved_data['kos_names'][i] if i < len(saved_data['kos_names']) else "", key=f"kn{i}"))

if st.sidebar.button("💾 리스트 영구 저장"):
    save_settings({"nas_codes": new_nas_codes, "nas_names": new_nas_names, "kos_codes": new_kos_codes, "kos_names": new_kos_names})
    st.sidebar.success("설정이 저장되었습니다!")

# 6. 메인 레이아웃
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(["🏠 시장 지표", "📋 종목 리스트", "📊 개별 종목 차트", "🏦 채권 계산기"])

# --- Tab 1: 시장 지표 ---
with tab1:
    m_info = get_market_data()
    if len(m_info) >= 4:
        cols = st.columns(4)
        for i in range(4):
            with cols[i]: st.markdown(f'<div class="metric-container"><div class="metric-label">{m_info[i]["name"]}</div><div class="metric-text {m_info[i]["status"]}">{m_info[i]["val"]}</div></div>', unsafe_allow_html=True)
        st.divider()
        re_idx = [0, 2, 1, 3]
        c_cols = st.columns(2)
        for idx, t_idx in enumerate(re_idx):
            if t_idx < len(m_info): # Index 안전장치 추가
                with c_cols[idx % 2]:
                    try:
                        data = yf.Ticker(m_info[t_idx]['ticker']).history(period="1y").tail(60)
                        fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(10, 6), returnfig=True)
                        ax[0].set_title(m_info[t_idx]['name'], fontsize=16, fontweight='bold'); st.pyplot(fig)
                    except: pass

# --- Tab 2: 종목 리스트 ---
with tab2:
    st.markdown("""<div class="list-row" style="background-color: #f8f9fa; border-top: 2px solid #333; margin-top: 10px;"><div class="list-header">종목명</div><div class="list-header">현재가</div><div class="list-header">등락 (퍼센트)</div></div>""", unsafe_allow_html=True)
    for c, n in zip(new_nas_codes + new_kos_codes, new_nas_names + new_kos_names):
        m_type = "NAS" if c in new_nas_codes else "KOS"
        s = get_stock_info(c, n, m_type)
        if s: st.markdown(f"""<div class="list-row"><div class="list-item">{s['name']}</div><div class="list-item">{s['price']}</div><div class="list-item {s['status']}">{s['change']}</div></div>""", unsafe_allow_html=True)

# --- Tab 3: 개별 종목 차트 ---
with tab3:
    c_m = st.radio("시장", ["NASDAQ", "KOSPI"], horizontal=True)
    c_tf = st.radio("시간축", ["시봉", "일봉", "주봉"], index=1, horizontal=True)
    t_map = {"시봉": ("1h", "7d"), "일봉": ("1d", "1y"), "주봉": ("1wk", "2y")}
    sel_codes, sel_names = (new_nas_codes, new_nas_names) if c_m == "NASDAQ" else (new_kos_codes, new_kos_names)
    chart_cols = st.columns(2); v_idx = 0
    for c, n in zip(sel_codes, sel_names):
        s = get_stock_info(c, n, c_m)
        if s:
            with chart_cols[v_idx % 2]:
                try:
                    data = yf.Ticker(c.strip().upper()).history(period=t_map[c_tf][1], interval=t_map[c_tf][0]).tail(60)
                    fig, ax = mpf.plot(data, type='candle', style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), gridstyle=':', y_on_right=True), figsize=(10, 6), returnfig=True)
                    if c_m == "NASDAQ": ax[0].set_ylabel('')
                    ax[0].set_title(f"{s['c_name']}  {s['price']} ({abs(s['pct']):.2f}%)", fontsize=30, fontweight='bold', color="red" if s['curr'] >= s['prev'] else "blue", loc='center', pad=20)
                    st.pyplot(fig); v_idx += 1
                except: pass

# --- Tab 4: 채권 계산기 (오류 수정 완료) ---
with tab4:
    st.subheader("🏦 브라질 국채(BNTNF) 투자 관리")
    st.markdown('<div class="bond-card">', unsafe_allow_html=True)
    st.write("📝 **매입 정보 입력**")
    col1, col2 = st.columns(2)
    with col1:
        buy_price = st.number_input("매수가격 (BRL)", min_value=0.0, value=780.0, step=0.1, format="%.2f")
        buy_fx = st.number_input("매수환율 (BRL/KRW)", min_value=0.0, value=250.0, step=0.1, format="%.2f")
    with col2:
        buy_amount_brl = st.number_input("매입금액 (BRL)", min_value=0.0, value=10000.0, step=100.0)
        buy_amount_krw = buy_amount_brl * buy_fx
        # 아래 행에서 'Korean' 오타를 제거했습니다.
        st.info(f"총 매입금액(원화): 약 {buy_amount_krw:,.0f}원")
    st.markdown('</div>', unsafe_allow_html=True)
    st.divider()
    try:
        brl_usd = yf.Ticker("BRL=X").history(period="1d")['Close'].iloc[-1]
        usd_krw = yf.Ticker("KRW=X").history(period="1d")['Close'].iloc[-1]
        current_fx = usd_krw / brl_usd
        eval_price = st.number_input("평가가격 (현재 BRL 시세)", value=778.88, step=0.01, format="%.2f")
        c3, c4, c5 = st.columns(3)
        with c3: st.metric("현재 채권가 (BRL)", f"{eval_price:.2f}")
        with c4: st.metric("평가환율 (BRL/KRW)", f"{current_fx:.2f}")
        with c5:
            qty = buy_amount_brl / buy_price if buy_price > 0 else 0
            eval_amount_krw = qty * eval_price * current_fx
            st.metric("평가금액 (원화)", f"{eval_amount_krw:,.0f}원")
        pk, pr = eval_amount_krw - buy_amount_krw, ((eval_amount_krw - buy_amount_krw) / buy_amount_krw) * 100 if buy_amount_krw > 0 else 0
        st.markdown(f'<div style="text-align: center; margin-top: 20px; padding: 15px; background-color: {"#fff5f5" if pk < 0 else "#f1f8e9"}; border-radius: 10px;"><span style="font-size: 1.1rem;">예상 투자 수익: </span><span class="bond-result" style="color: {"#1e88e5" if pk < 0 else "#ef5350"};">{pk:+,,.0f}원 ({pr:+.2f}%)</span></div>', unsafe_allow_html=True)
    except: st.error("환율 데이터를 가져오는 중입니다... 잠시만 기다려 주세요.")
