# (앞부분 설정 및 스타일 코드는 동일하므로 중략하고 6번 메인 레이아웃의 Tab 3 부분만 집중 수정했습니다)

# --- Tab 3: 개별 종목 차트 ---
with tab3:
    valid_codes = [c.strip().upper() for c in (new_nas_codes if selected_market == "NASDAQ" else new_kos_codes) if c.strip()]
    
    if valid_codes:
        # 1. 종목 선택과 봉 선택을 한 줄에 배치하거나 깔끔하게 나열
        col1, col2 = st.columns([2, 1])
        with col1:
            target_code = st.selectbox("📊 분석할 종목", valid_codes)
        with col2:
            c_tf = st.radio("⏰ 봉 종류", ["시봉", "일봉", "주봉"], index=1, horizontal=True)
            
        # 한국 종목 보정 로직
        plot_code = target_code + ".KS" if selected_market == "KOSPI" and not (target_code.endswith(".KS") or target_code.endswith(".KQ")) else target_code
        
        t_map = {"시봉": ("1h", "7d"), "일봉": ("1d", "1y"), "주봉": ("1wk", "2y")}
        
        try:
            # 데이터 로드
            data = yf.Ticker(plot_code).history(period=t_map[c_tf][1], interval=t_map[c_tf][0]).tail(60)
            
            if not data.empty:
                curr, prev = data['Close'].iloc[-1], data['Close'].iloc[-2]
                diff, pct = curr - prev, ((curr - prev) / prev) * 100
                
                # 차트 그리기
                fig, ax = mpf.plot(data, type='candle', 
                                   style=mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='red', down='blue', inherit=True), 
                                   gridstyle=':', y_on_right=True), 
                                   figsize=(12, 7), returnfig=True)
                
                # 수치 표시 보정
                p_disp = f"{curr:,.2f}$" if selected_market == "NASDAQ" else f"{int(curr):,}"
                d_disp = f"{diff:+.2f}" if selected_market == "NASDAQ" else f"{int(diff):+,}"
                
                ax[0].set_title(f"{target_code} ({c_tf})   {p_disp}   {d_disp} ({pct:+.2f}%)", 
                               fontsize=24, fontweight='bold', 
                               color="red" if diff >= 0 else "blue", loc='center', pad=20)
                st.pyplot(fig)
            else:
                st.warning("해당 종목의 데이터가 없습니다.")
        except Exception as e:
            st.error(f"차트를 불러오는 중 오류가 발생했습니다: {e}")
    else:
        st.info("종목 리스트에 코드를 먼저 입력해 주세요!")
