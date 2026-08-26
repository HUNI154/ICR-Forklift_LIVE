def draw_ui(stand_data, sit_data):
    # 1. 데이터 쪼개기
    try:
        stand_time, stand_raw, stand_rssi = stand_data.split(',', 2)
        sit_time, sit_raw, sit_rssi = sit_data.split(',', 2)
    except:
        stand_time, stand_raw, stand_rssi = "알수없음", "알수없음", "-"
        sit_time, sit_raw, sit_rssi = "알수없음", "알수없음", "-"

    stand_display = LOCATION_MAP.get(stand_raw, stand_raw)
    sit_display = LOCATION_MAP.get(sit_raw, sit_raw)

    # 2. 메모리에 최신 전파 수치 밀어넣기
    st.session_state.stand_rssi_history = update_history(st.session_state.stand_rssi_history, stand_rssi)
    st.session_state.sit_rssi_history = update_history(st.session_state.sit_rssi_history, sit_rssi)

    # 3. 화살표(➔) 추세선 텍스트
    stand_trend = " ➔ ".join(st.session_state.stand_rssi_history) + " dBm" if st.session_state.stand_rssi_history else "측정 대기"
    sit_trend = " ➔ ".join(st.session_state.sit_rssi_history) + " dBm" if st.session_state.sit_rssi_history else "측정 대기"

    now = datetime.now()

    def check_status(time_str, display_loc, rssi_val, trend_str):
        if time_str == "대기중" or time_str == "알수없음":
            return f"# ⚪ **{display_loc}**\n> ⏳ 데이터 수신 대기 중..."

        try:
            try:
                dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            except:
                clean_time_str = time_str.split(" GMT")[0].strip()
                dt = datetime.strptime(clean_time_str, "%a %b %d %Y %H:%M:%S")
            
            pretty_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            diff = (now - dt).total_seconds()
            
            if diff > 120:  
                # 🔴 3단계: 통신 완전 끊김 (2분 경과)
                try:
                    rssi_num = int(rssi_val)
                    if rssi_num > -75:
                        reason = "💡 전원 OFF (정상 종료 추정)"
                    else:
                        reason = "📡 통신 사각지대 (음영지역 진입)"
                except:
                    reason = "🔌 통신 끊김"

                return f"# 🔴 **{display_loc}**\n### {reason}\n> 🕒 마지막 통신: `{pretty_time}`\n> 📉 전파 변화: `{trend_str}`"
            
            else:
                # 💡 [황금 비율 적용!] -65 이하일 때 미리 ⚠️ 경고 띄우기
                try:
                    rssi_num = int(rssi_val)
                    if rssi_num <= -65:  # 👈 여기를 -65로 수정!
                        return f"# ⚠️ **{display_loc} (신호약함)**\n> 🕒 실시간 갱신 중: `{pretty_time}`\n> 📉 전파 변화: `{trend_str}`"
                except:
                    pass
                
                # 🟢 1단계: 수신 빵빵하고 아주 정상일 때
                return f"# 🟢 **{display_loc}**\n> 🕒 실시간 갱신 중: `{pretty_time}`\n> 📈 전파 변화: `{trend_str}`"
                
        except:
            return f"# ⚪ **{display_loc}**\n> ⏳ 시간 파악 중: `{time_str}`"

    with placeholder.container():
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### 🧍 입식 지게차\n{check_status(stand_time, stand_display, stand_rssi, stand_trend)}")
        with col2:
            st.markdown(f"### 💺 좌식 지게차\n{check_status(sit_time, sit_display, sit_rssi, sit_trend)}")
