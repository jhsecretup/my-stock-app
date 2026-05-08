import streamlit as st
import json
import os
import market_tab, list_tab, chart_tab, valuation_tab

# 페이지 설정
st.set_page_config(page_title="비서표 투자 대시보드", layout="wide")

# 스타일 시트
st.markdown("""
    <style>
    .block-container { padding-top: 3rem !important; }
    .title-style { font-size: 1.6rem !important; font-weight: bold; margin-bottom: 1.5rem; color: #333; text-align: center; }
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] { width: 55% !important; flex-wrap: nowrap !important; gap: 5px !important; }
    div[data-testid="stTextInput"] div[data-baseweb="base-input"] { min-height: 28px !important; height: 28px !important; }
    </style>
    """, unsafe_allow_html=True)

# 데이터 로드 함수
def load_settings():
    if 'current_settings' in st.session_state:
        return st.session_state.current_settings
    if os.path.exists('stock_settings.json'):
        try:
            with open('stock_settings.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key in ['nas_codes', 'nas_names', 'kos_codes', 'kos_names']:
                    if key not in data: data[key] = [""] * 50
                    else: data[key] = (data[key] + [""] * 50)[:50]
                return data
        except: pass
    return {"nas_codes": [""]*50, "nas_names": [""]*50, "kos_codes": [""]*50, "kos_names": [""]*50}

settings = load_settings()

# 사이드바 설정
st.sidebar.title("🛠️ 종목 설정 센터")
input_tab_nas, input_tab_kos = st.sidebar.tabs(["🇺🇸 NASDAQ", "🇰🇷 KOSPI"])

def render_sidebar(tab, codes, names, prefix):
    new_c, new_n = [], []
    with tab:
        for i in range(50):
            c1, c2 = st.columns([1.5, 2])
            with c1: code = st.text_input(f"{prefix}C{i}", value=codes[i], key=f"{prefix}c{i}", label_visibility="collapsed")
            with c2: name = st.text_input(f"{prefix}N{i}", value=names[i], key=f"{prefix}n{i}", label_visibility="collapsed")
            new_c.append(code); new_n.append(name)
    return new_c, new_n

n_codes, n_names = render_sidebar(input_tab_nas, settings['nas_codes'], settings['nas_names'], "nc")
k_codes, k_names = render_sidebar(input_tab_kos, settings['kos_codes'], settings['kos_names'], "kc")

if st.sidebar.button("💾 설정 저장", use_container_width=True, type="primary"):
    updated = {"nas_codes": n_codes, "nas_names": n_names, "kos_codes": k_codes, "kos_names": k_names}
    st.session_state.current_settings = updated
    with open('stock_settings.json', 'w', encoding='utf-8') as f:
        json.dump(updated, f, ensure_ascii=False, indent=4)
    st.rerun()

# 메인 화면 탭 구성
st.markdown('<div class="title-style">📈 비서표 투자 대시보드</div>', unsafe_allow_html=True)
t1, t2, t3, t4 = st.tabs(["🏠 시장 지표", "📋 종목 리스트", "📊 차트 분석", "💎 기업 가치 분석"])

with t1: market_tab.run()
with t2: list_tab.run(n_codes, n_names, k_codes, k_names)
with t3: chart_tab.run(n_codes, n_names, k_codes, k_names)
with t4: valuation_tab.run(n_codes, n_names, k_codes, k_names)
