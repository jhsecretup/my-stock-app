import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import json
import os
from datetime import datetime, timedelta

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
    .bond-card { background-color: #f8f9fa; padding: 25px; border-radius: 12px; border-left: 6px solid #1a5f7a; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .bond-val { font-size: 1.3rem; font-weight: bold; color: #1a5f7a; }
    </style>
    """, unsafe_allow_html=True)

# 4. 유틸리티 함수 (생략 없이 통합)
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

# [신규] 과거 환율 데이터 가져오기 함수
def get_historical_fx(date_obj):
    try:
        start_date = date_obj.strftime('%Y-%m-%d')
        end_date = (date_obj + timedelta(days=5)).strftime('%Y-%m-%d')
        # 브라질 헤알화 환율 계산 (USDBRL과 USDKRW 활용)
        brl_data = yf.download("BRL=X", start=start_date, end=end_date, progress=False)
        krw_data = yf.download("KRW=X", start=start_date, end=end_date, progress=False)
        if not brl_data.empty and not krw_data.empty:
            brl_val = brl_data['Close'].iloc[0]
            krw_val = krw_data['Close'].iloc[0]
            return float(krw_val / brl_val)
    except: pass
    return 250.0 # 실패 시 기본값

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
tab1, tab2, tab3, tab4 = st.tabs(["🏠 시장 지표", "📋 종목 리스트", "📊 개별 종목 차트", "🏦 채권 관리"])

# --- Tab 1~3: 기존 로직 유지 (안전하게 포함) ---
with tab1:
    m_info = get_market_data()
    if m_info:
        cols = st.columns(len(m_info))
        for i, m in enumerate(m_info):
            with cols[i]: st.markdown(f'<div class="metric-container"><div class="metric-label">{m["name"]}</div><div class="metric-text {m["status"]}">{m["val"]}</div></div>', unsafe_allow_html=True)
with tab2:
    st.markdown("""<div class="list-row" style="background-color: #f8f9fa; border-top: 2px solid #333; margin-top: 10px;"><div class="list-header">종목명</div><div class="list-header">현재가</div><div class="list-header">등락 (퍼센트)</div></div>""", unsafe_allow_html=True)
    for c, n in zip(new_nas_codes + new_kos_codes, new_nas_names + new_kos_names):
        s = get_stock_info(c, n, "NAS" if c in new_nas_codes else "KOS")
        if s: st.markdown(f"""<div class="list-row"><div class="list-item">{s['name']}</div><div class="list-item">{s['price']}</div><div class="list-item {s['status']}">{s['change']}</div></div>""", unsafe_allow_html=True)
with tab3:
    st.info("사이드바에서 설정한 종목의 실시간 차트를 확인하세요.")

# --- Tab 4: 채권 관리 (새로운 로직) ---
with tab4:
    st.subheader("🏦 채권 투자 현황 분석")
    
    # [입력부]
    with st.expander("➕ 새로운 투자 정보 입력", expanded=True):
        col_a, col_b, col_c = st.columns([2, 1, 1])
        with col_a: bond_name = st.text_input("채권명", value="BNTNF 10 01/01/27")
        with col_b: buy_date = st.date_input("구매 날짜", value=datetime(2024, 1, 15))
        with col_c: buy_qty = st.number_input("구매 수량 (주)", min_value=1, value=10)

    # [매수 시점 데이터 계산]
    hist_fx = get_historical_fx(buy_date)
    st.markdown(f'<div class="bond-card">', unsafe_allow_html=True)
    st.markdown(f"### 🗓️ 매수 시점 정보 ({buy_date.strftime('%Y-%m-%d')})")
    
    # 채권 가격은 사용자 입력 혹은 기준가(일반적으로 1000 혹은 할인금액) 설정
    c1, c2, c3 = st.columns(3)
    with c1: buy_price_brl = st.number_input("매수가격 (주당 BRL)", value=780.0, format="%.2f")
    with c2: st.write(f"**매수 시 환율**"); st.write(f"{hist_fx:.2f} BRL/KRW")
    
    total_buy_krw = buy_price_brl * buy_qty * hist_fx
    with c3: st.write(f"**매입금액 (원화)**"); st.markdown(f'<span class="bond-val">{total_buy_krw:,.0f}원</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # [현재 시점 데이터 계산]
    try:
        # 실시간 환율
        now_brl_usd = yf.Ticker("BRL=X").history(period="1d")['Close'].iloc[-1]
        now_usd_krw = yf.Ticker("KRW=X").history(period="1d")['Close'].iloc[-1]
        now_fx = now_usd_krw / now_brl_usd
        
        st.markdown(f'<div class="bond-card" style="border-left-color: #2e7d32;">', unsafe_allow_html=True)
        st.markdown(f"### 🚀 현재 시점 평가 (오늘)")
        
        c4, c5, c6 = st.columns(3)
        with c4: now_price_brl = st.number_input("현재 평가가격 (BRL)", value=778.88, format="%.2f")
        with c5: st.write(f"**현재 평가환율**"); st.write(f"{now_fx:.2f} BRL/KRW")
        
        total_eval_krw = now_price_brl * buy_qty * now_fx
        with c6: st.write(f"**평가금액 (원화)**"); st.markdown(f'<span class="bond-val" style="color: #2e7d32;">{total_eval_krw:,.0f}원</span>', unsafe_allow_html=True)
        
        # 수익률 분석
        profit = total_eval_krw - total_buy_krw
        profit_rate = (profit / total_buy_krw * 100) if total_buy_krw > 0 else 0
        color = "#ef5350" if profit >= 0 else "#1e88e5"
        st.markdown(f'<div style="text-align: center; margin-top: 20px; padding: 15px; background-color: #fff; border: 1px solid #ddd; border-radius: 8px;">'
                    f'<span style="font-size: 1.2rem;">총 예상 손익: </span>'
                    f'<span style="font-size: 1.5rem; font-weight: bold; color: {color};">{profit:+,.0f}원 ({profit_rate:+.2f}%)</span>'
                    f'</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    except:
        st.warning("실시간 환율 정보를 불러오는 중입니다...")
