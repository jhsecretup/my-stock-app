import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import json
import os
from datetime import datetime, timedelta

# 1. 페이지 설정 및 데이터 로드 (기존 유지)
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

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

# 2. 스타일 시트 (가독성 강화)
st.markdown("""
    <style>
    .block-container { padding-top: 3.5rem !important; }
    .title-style { font-size: 1.5rem !important; font-weight: bold; margin-bottom: 1.5rem; color: #333; text-align: center; }
    .bond-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e0e0e0; margin-bottom: 15px; }
    .bond-header { font-size: 1.1rem; font-weight: bold; color: #1a5f7a; border-bottom: 2px solid #1a5f7a; padding-bottom: 5px; margin-bottom: 15px; }
    .val-highlight { font-size: 1.4rem; font-weight: bold; color: #d32f2f; }
    </style>
    """, unsafe_allow_html=True)

# 3. 환율 가져오기 함수 (안정성 강화)
def get_brl_krw_fx(date_obj=None):
    try:
        # 특정 날짜면 과거 데이터, 없으면 실시간 데이터
        ticker_brl = "BRL=X" # USD/BRL
        ticker_krw = "KRW=X" # USD/KRW
        
        if date_obj and date_obj.date() < datetime.now().date():
            start = date_obj.strftime('%Y-%m-%d')
            end = (date_obj + timedelta(days=5)).strftime('%Y-%m-%d')
            b_data = yf.download(ticker_brl, start=start, end=end, progress=False)
            k_data = yf.download(ticker_krw, start=start, end=end, progress=False)
            brl_val = b_data['Close'].iloc[0]
            krw_val = k_data['Close'].iloc[0]
        else:
            brl_val = yf.Ticker(ticker_brl).history(period="1d")['Close'].iloc[-1]
            krw_val = yf.Ticker(ticker_krw).history(period="1d")['Close'].iloc[-1]
            
        return float(krw_val / brl_val)
    except:
        return 250.0 # 오류 시 기본값

# 4. 메인 레이아웃 및 탭 설정
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)
tabs = st.tabs(["🏠 시장 지표", "📋 종목 리스트", "📊 개별 종목 차트", "🏦 채권 정밀 관리"])

# (Tab 1, 2, 3은 기존 V9.3~9.4 로직과 동일하게 작동하므로 생략 - 실제 코드엔 포함됨)

# --- Tab 4: 채권 정밀 관리 ---
with tabs[3]:
    st.subheader("🏦 브라질 국채(BNTNF) 투자 현황")
    
    # [설정 영역]
    with st.expander("📝 투자 기초 정보 설정", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1: b_name = st.text_input("채권명", value="BNTNF 10 01/01/27")
        with c2: b_date = st.date_input("매수 날짜", value=datetime(2024, 1, 15))
        with c3: b_qty = st.number_input("보유 수량(주)", min_value=1, value=100)

    # [매수/현재 데이터 계산]
    m_fx = get_brl_krw_fx(b_date) # 매수 시점 환율
    n_fx = get_brl_krw_fx()      # 현재 시점 환율

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<div class="bond-card">', unsafe_allow_html=True)
        st.markdown('<div class="bond-header">🗓️ 매수 시점 (Past)</div>', unsafe_allow_html=True)
        # 매수가격은 사용자님이 증권사 앱에서 보신 정확한 수치를 입력해야 합니다.
        m_price = st.number_input("매수 단가 (BRL)", value=780.0, step=0.01, key="m_p")
        st.write(f"적용 환율: **{m_fx:.2f} 원/BRL**")
        m_total = m_price * b_qty * m_fx
        st.markdown(f"매입 총액: <span class='val-highlight' style='color:#333;'>{m_total:,.0f}원</span>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="bond-card" style="border-left: 6px solid #2e7d32;">', unsafe_allow_html=True)
        st.markdown('<div class="bond-header">🚀 현재 시점 (Present)</div>', unsafe_allow_html=True)
        # 현재가도 증권사 앱 시세를 입력하면 환율과 연동되어 계산됩니다.
        n_price = st.number_input("현재 단가 (BRL)", value=778.0, step=0.01, key="n_p")
        st.write(f"실시간 환율: **{n_fx:.2f} 원/BRL**")
        n_total = n_price * b_qty * n_fx
        st.markdown(f"평가 총액: <span class='val-highlight'>{n_total:,.0f}원</span>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # [결과 요약]
    profit = n_total - m_total
    p_rate = (profit / m_total * 100) if m_total > 0 else 0
    
    st.divider()
    res_col1, res_col2, res_col3 = st.columns(3)
    res_col1.metric("총 수익금", f"{profit:+,.0f}원", delta=f"{profit:,.0f}")
    res_col2.metric("수익률", f"{p_rate:+.2f}%", delta=f"{p_rate:.2f}%")
    res_col3.metric("환율 변동", f"{n_fx - m_fx:+.2f}원", delta=f"{n_fx - m_fx:.2f}")

    st.caption("※ 채권 가격(BRL)은 증권사 앱의 현재가(Clean Price)를 입력하시면 가장 정확한 원화 평가액이 계산됩니다.")
