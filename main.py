import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import json
import os

# --- 기존 설정 및 로드 함수 (V9.0 동일) ---
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

def load_settings():
    if os.path.exists('stock_settings.json'):
        with open('stock_settings.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"nas_codes": [""]*10, "nas_names": [""]*10, "kos_codes": [""]*10, "kos_names": [""]*10}

def save_settings(data):
    with open('stock_settings.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

saved_data = load_settings()

# --- 스타일 및 유틸리티 (기존 유지) ---
st.markdown("""
    <style>
    .block-container { padding-top: 3.5rem !important; }
    .title-style { font-size: 1.5rem !important; font-weight: bold; margin-bottom: 1.5rem; color: #333; text-align: center; }
    .metric-container { text-align: center; margin-bottom: 10px; }
    .metric-text { font-size: 1.5rem !important; font-weight: bold; white-space: nowrap; }
    .up { color: #ef5350; } .down { color: #1e88e5; }
    .bond-card { background-color: #f9f9f9; padding: 20px; border-radius: 10px; border-left: 5px solid #2e7d32; margin-bottom: 20px; }
    .bond-result { font-size: 1.2rem; font-weight: bold; color: #2e7d32; }
    </style>
    """, unsafe_allow_html=True)

# (기존 데이터 로딩 함수 생략 - V9.0과 동일)

# --- 사이드바 설정 (기존 유지) ---
st.sidebar.title("🛠️ 종목 설정")
# (NASDAQ/KOSPI 설정 및 저장 버튼 로직 동일)

# --- 메인 레이아웃 ---
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(["🏠 시장 지표", "📋 종목 리스트", "📊 개별 종목 차트", "🏦 채권 계산기"])

# (Tab 1, 2, 3 로직 동일)

# --- [신규] Tab 4: 채권 계산기 ---
with tab4:
    st.subheader("🏦 브라질 국채(BNTNF) 투자 관리")
    
    with st.container():
        st.markdown('<div class="bond-card">', unsafe_allow_html=True)
        st.write("📝 **매입 정보 입력**")
        col1, col2 = st.columns(2)
        with col1:
            buy_price = st.number_input("매수가격 (BRL)", min_value=0.0, value=780.0, step=0.1, format="%.2f")
            buy_fx = st.number_input("매수환율 (BRL/KRW)", min_value=0.0, value=250.0, step=0.1, format="%.2f")
        with col2:
            buy_amount_brl = st.number_input("매입금액 (BRL)", min_value=0.0, value=10000.0, step=100.0)
            # 매입금액 원화 자동 계산 표시
            buy_amount_krw = buy_amount_brl * buy_fx
            st.info(f"총 매입금액(원화): 약 {buy_amount_krw:,.0f}원")
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # 실시간 데이터 가져오기 (헤알 환율 및 채권 지표용)
    try:
        # BRL/KRW 환율 (Yahoo Finance에서는 USDBRL과 USDKRW를 조합하거나 KRWBRL=X 등을 사용)
        # 여기서는 가장 정확한 헤알-원 환율 추정을 위해 USDBRL과 USDKRW를 활용합니다.
        brl_usd = yf.Ticker("BRL=X").history(period="1d")['Close'].iloc[-1] # 1달러당 헤알
        usd_krw = yf.Ticker("KRW=X").history(period="1d")['Close'].iloc[-1] # 1달러당 원화
        current_fx = usd_krw / brl_usd # 1헤알당 원화
        
        # BNTNF 가격 (직접 티커가 없을 수 있어, 최근 검색된 시장가 778.88을 기본값으로 하되 실시간성을 위해 폼 제공)
        st.write("📊 **실시간 평가 지표**")
        eval_price = st.number_input("평가가격 (현재 BRL 시세)", value=778.88, step=0.01, format="%.2f")
        
        col3, col4, col5 = st.columns(3)
        
        # 1. 평가가격 표시
        with col3:
            st.metric("현재 채권가 (BRL)", f"{eval_price:.2f}")
            
        # 2. 평가환율 표시 (실시간 계산값)
        with col4:
            st.metric("평가환율 (BRL/KRW)", f"{current_fx:.2f}")
            
        # 3. 평가금액 계산 및 표시
        with col5:
            # 수량(Qty) 계산 = 매입금액(BRL) / 매수가격(BRL)
            qty = buy_amount_brl / buy_price if buy_price > 0 else 0
            # 현재 평가금액(원화) = 수량 * 현재채권가 * 현재환율
            eval_amount_krw = qty * eval_price * current_fx
            st.metric("평가금액 (원화)", f"{eval_amount_krw:,.0f}원")
            
        # 수익률 분석
        profit_krw = eval_amount_krw - buy_amount_krw
        profit_rate = (profit_krw / buy_amount_krw) * 100 if buy_amount_krw > 0 else 0
        
        st.markdown(f"""
            <div style="text-align: center; margin-top: 20px; padding: 15px; background-color: {'#fff5f5' if profit_krw < 0 else '#f1f8e9'}; border-radius: 10px;">
                <span style="font-size: 1.1rem;">예상 투자 수익: </span>
                <span class="bond-result" style="color: {'#1e88e5' if profit_krw < 0 else '#ef5350'};">
                    {profit_krw:+,,.0f}원 ({profit_rate:+.2f}%)
                </span>
            </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error("실시간 환율 정보를 가져오는 데 문제가 발생했습니다. 네트워크를 확인해 주세요.")
