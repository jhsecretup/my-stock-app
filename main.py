import streamlit as st

# 버전 정보: 10.7 (불필요한 라이브러리 제거 및 괄호 위치 수정본)

def format_index_display(name, value, change, pct):
    """
    지수 등락 표시 포맷 수정: 
    기존: 지수 +1.23 (1.05%) -> 이 형태를 유지하며 괄호 시작점만 정확히 조정
    """
    color = "red" if change > 0 else "blue" if change < 0 else "black"
    sign = "+" if change > 0 else ""
    
    # HTML을 사용하여 색상과 괄호 위치를 정교하게 제어합니다.
    return f"""
        <div style="font-size: 1.1rem; font-weight: 500;">
            {name}: <span style="color:black;">{value}</span> 
            <span style="color:{color};">{sign}{change}</span> 
            <span style="color:{color};">({sign}{pct:.2f}%)</span>
        </div>
    """

def main():
    st.set_page_config(layout="wide")
    
    tab1, tab2, tab3 = st.tabs(["시장 지수", "포트폴리오", "상세 차트"])
    
    with tab1:
        # 지수 정보를 가로로 배치하거나 리스트로 보여줄 때 사용
        col1, col2 = st.columns(2)
        with col1:
            # 예시: 코스피
            st.markdown(format_index_display("KOSPI", 2650.12, 15.42, 0.58), unsafe_allow_html=True)
        with col2:
            # 예시: 나스닥
            st.markdown(format_index_display("NASDAQ", 16340.25, -25.15, -0.15), unsafe_allow_html=True)

    with tab2:
        st.write("포트폴리오 탭 (기존 로직 유지)")
        # 나스닥/코스피 전환 시 딜레이를 줄이기 위해 
        # 불필요한 연산을 최소화한 기존 코드를 여기에 위치시키시면 됩니다.

    with tab3:
        st.write("상세 차트 탭 (기존 기본 차트 유지)")
        # 텍스트 포맷 수정을 위해 시도했던 plotly 코드는 모두 제거했습니다.

if __name__ == "__main__":
    main()
