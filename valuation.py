import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import json
import os

# 1. 페이지 설정
st.set_page_config(page_title="기업가치분석", layout="wide")

# 2. 데이터 로드 (stock_settings.json 연동)
def load_my_stocks():
    if os.path.exists('stock_settings.json'):
        try:
            with open('stock_settings.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"nas_codes": [], "nas_names": [], "kos_codes": [], "kos_names": []}

# RSI(Relative Strength Index) 계산 함수
def calculate_rsi(ticker_sym, period="1mo"):
    try:
        # RSI 14를 안정적으로 구하기 위해 여유 있게 과거 데이터를 가져옵니다.
        hist = yf.Ticker(ticker_sym).history(period=period)
        if len(hist) < 15:
            hist = yf.Ticker(ticker_sym).history(period="3mo")
            
        if hist.empty or len(hist) < 15:
            return "-"
            
        close_prices = hist['Close']
        delta = close_prices.diff()
        
        # 상승분과 하락분 분리
        gain = (delta.where(delta > 0, 0)).copy()
        loss = (-delta.where(delta < 0, 0)).copy()
        
        # 웰레스 와일더(Welles Wilder) 이동평균 방식 적용
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        
        # 두 번째 값부터는 Wilder 공식 적용을 위해 보정 계산
        for i in range(14, len(delta)):
            avg_gain.iloc[i] = (avg_gain.iloc[i-1] * 13 + gain.iloc[i]) / 14
            avg_loss.iloc[i] = (avg_loss.iloc[i-1] * 13 + loss.iloc[i]) / 14
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        last_rsi = rsi.iloc[-1]
        return round(last_rsi, 2) if not np.isnan(last_rsi) else "-"
    except:
        return "-"

# 3. 스타일 설정
st.markdown("""
    <style>
    /* 상단 여백 보정: 잘림 방지를 위해 대시보드와 유사한 3rem 확보 */
    .block-container { padding-top: 3rem !important; }
    
    /* 타이틀 스타일 */
    .main-title { 
        font-size: 1.6rem !important; 
        font-weight: bold; 
        color: #333; 
        text-align: center; 
        margin-bottom: 2rem; 
    }
    
    /* 버튼 및 라디오 버튼 높이 조절 */
    .stButton>button { height: 2.8rem; border-radius: 8px; font-weight: bold; }
    
    /* 테이블 가독성 */
    .stDataFrame { font-size: 0.95rem; }
    </style>
    """, unsafe_allow_html=True)

# 상단 타이틀
st.markdown('<div class="main-title">💎 기업가치분석</div>', unsafe_allow_html=True)

# 4. 데이터 준비
stocks = load_my_stocks()

# 상단 컨트롤바
col1, col2 = st.columns([3, 1])

with col1:
    market = st.radio("시장 선택", ["NASDAQ", "KOSPI"], horizontal=True, label_visibility="collapsed")

# 종목 데이터 필터링
codes = stocks['nas_codes'] if market == "NASDAQ" else stocks['kos_codes']
names = stocks['nas_names'] if market == "NASDAQ" else stocks['kos_names']
valid_stocks = [(c.strip(), n.strip()) for c, n in zip(codes, names) if c.strip()]

with col2:
    run_analysis = st.button("🚀 분석 시작", use_container_width=True)

st.divider()

# 5. 분석 로직
if run_analysis:
    if not valid_stocks:
        st.warning("등록된 종목이 없습니다.")
    else:
        results = []
        progress_bar = st.progress(0)
        
        for i, (code, name) in enumerate(valid_stocks):
            try:
                ticker = code.upper()
                if market == "KOSPI" and not (ticker.endswith(".KS") or ticker.endswith(".KQ")):
                    ticker += ".KS"
                
                stock_obj = yf.Ticker(ticker)
                info = stock_obj.info
                
                # 순수 수치 데이터 수집 (완벽한 숫자 정렬을 위해 텍스트 기호 제외)
                m_cap = info.get('marketCap', None)
                curr_price = info.get('currentPrice', None)
                
                # 가치 지표 추출
                per = info.get('trailingPE', None)
                pbr = info.get('priceToBook', None)
                
                # PSR 계산 (YFinance 기본 정보에 없으면 시가총액 / 총매출로 계산)
                psr = info.get('priceToSalesTrailing12Months', None)
                if psr is None and m_cap and info.get('totalRevenue'):
                    psr = m_cap / info.get('totalRevenue')
                
                # ROE 계산
                roe = info.get('returnOnEquity', None)
                if roe is not None:
                    roe = roe * 100 # 퍼센트 수치화
                
                # RSI 계산
                rsi = calculate_rsi(ticker)
                
                results.append({
                    "종목명": name if name else code,
                    "시가총액": m_cap,
                    "현재가": curr_price,
                    "PER": round(per, 2) if per else None,
                    "PBR": round(pbr, 2) if pbr else None,
                    "PSR": round(psr, 2) if psr else None,
                    "ROE(%)": round(roe, 1) if roe else None,
                    "RSI(14)": rsi if rsi != "-" else None
                })
            except:
                pass
            progress_bar.progress((i + 1) / len(valid_stocks))
        
        if results:
            df = pd.DataFrame(results)
            
            # --- 숫자가 글자순으로 정렬되던 문제를 해결하기 위한 화면 표시 포맷 설정 ---
            if market == "NASDAQ":
                # 미국 주식: 시가총액을 Billion달러($B) 단위로 가독성 있게 포맷팅
                df["시가총액"] = df["시가총액"] / 1e9
                m_cap_config = st.column_config.NumberColumn("시가총액", format="$%.1f B")
                price_config = st.column_config.NumberColumn("현재가", format="$%.2f")
            else:
                # 한국 주식: 시가총액을 억 원 단위를 기본으로 표현 (원화 표시)
                df["시가총액"] = df["시가총액"] / 1e8
                m_cap_config = st.column_config.NumberColumn("시가총액(억 원)", format="%d")
                price_config = st.column_config.NumberColumn("현재가", format="%d")

            # 컬럼 설정 취합
            column_configuration = {
                "종목명": st.column_config.TextColumn("종목명"),
                "시가총액": m_cap_config,
                "현재가": price_config,
                "PER": st.column_config.NumberColumn("PER(이익)", format="%.2f"),
                "PBR": st.column_config.NumberColumn("PBR(자산)", format="%.2f"),
                "PSR": st.column_config.NumberColumn("PSR(매출)", format="%.2f"),
                "ROE(%)": st.column_config.NumberColumn("ROE(%)", format="%.1f%%"),
                "RSI(14)": st.column_config.NumberColumn("RSI(14)", format="%.2f")
            }
            
            # 결과 테이블 출력 (정렬 에러 방지 및 디자인 포맷 적용)
            st.dataframe(
                df, 
                use_container_width=True, 
                hide_index=True,
                column_config=column_configuration
            )
            st.caption(f"최근 분석 시점: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} (PER, PBR, PSR, ROE 데이터는 Yahoo Finance TTM 기준)")
        else:
            st.error("데이터 수집 실패")
