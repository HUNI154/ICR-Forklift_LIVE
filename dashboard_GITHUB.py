import streamlit as st
import requests
import time
import os
from datetime import datetime, timedelta

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbymDytZUmijx0gZhQBZpQU15Rf4V4YAA9o-hWTrVACsQyD_xgX_iYJ0nLm4Tgj592wy/exec"
CACHE_FILE = "last_location.txt" 

LOCATION_MAP = {
    "ICR-AP-3F": "3층 신축동",
    "ICR-AP-3F-2.4G-성능동": "3층 성능동",
    "ICR-AP-2F-2.4": "2층 성능동",
    "ICR EX 2F": "2층 신축동",
    "ICR-AP-1F_2 2.4": "안전동",
    "ICR-AP-1FA": "1층 신축동",
    "ICR-AP-1F-2.4": "1층 성능동",
}

st.set_page_config(page_title="ICR 배터리시험센터 지게차 모니터링", layout="wide")
st.markdown("## 🚜 ICR 배터리시험센터 지게차 실시간 위치")
st.markdown("---")

# 💡 1. 과거 전파 수치를 5개까지 기억하는 뇌 장착
if 'stand_rssi_history' not in st.session_state:
    st.session_state.stand_rssi_history = []
if 'sit_rssi_history' not in st.session_state:
    st.session_state.sit_rssi_history = []

def update_history(history_list, new_val):
    if new_val and new_val != "-" and new_val != "None":
        if not history_list or history_list[-1] != new_val:
            history_list.append(new_val)
        if len(history_list) > 5:
            history_list.pop(0)
    return history_list

placeholder = st.empty()
# 초기값: 이제 데이터가 3개씩(시간,위치,전파) 옵니다.
saved_raw_data = "수신 대기 중...,위치 파악 중...,-|수신 대기 중...,위치 파악 중...,-" 

def draw_ui(stand_data, sit_data):
    # 💡 2. 데이터 3등분 쪼개기 (시간, 위치, 전파)
    try:
        stand_time, stand_raw, stand_rssi = stand_data.split(',', 2)
        sit_time, sit_raw, sit_rssi = sit_data.split(',', 2)
    except:
        stand_time, stand_raw, stand_rssi = "알수없음", "알수없음", "-"
        sit_time, sit_raw, sit_rssi = "알수없음", "알수없음", "-"
        
    stand_display = LOCATION_MAP.get(stand_raw, stand_raw)
    sit_display = LOCATION_MAP.get(sit_raw, sit_raw)

    # 💡 3. 메모리에 최신 전파 업데이트 및 추세선 텍스트 만들기
    st.session_state.stand_rssi_history = update_history(st.session_state.stand_rssi_history, stand_rssi)
    st.session_state.sit_rssi_history = update_history(st.session_state.sit_rssi_history, sit_rssi)

    stand_trend = " ➔ ".join(st.session_state.stand_rssi_history) + " dBm" if st.session_state.stand_rssi_history else "측정 대기"
    sit_trend = " ➔ ".join(st.session_state.sit_rssi_history) + " dBm" if st.session_state.sit_rssi_history else "측정 대기"

    # 연구원님의 완벽한 한국 시간 패치 유지!
    now = datetime.utcnow() + timedelta(hours=9)

    # 💡 4. 상태 및 시간 체크 로직 (완전체 버전)
    def check_status(time_str, display_loc, rssi_val, trend_str):
        if "대기 중" in time_str or "알수없음" in time_str:
            return f"# 🟡 **{display_loc}**\n> ⏳ 데이터 수신 대기 중..."

        try:
            # 새로 바뀐 구글 서버는 "2026-08-26 14:30:00" 처럼 예쁘게 보내주므로 복잡한 텍스트 자르기 불필요!
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            pretty_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            
            diff = (now - dt).total_seconds()
            
            if diff > 60:  
                # 🤖 대시보드 자동 추론 로직 (전원 OFF vs 사각지대)
                try:
                    rssi_num = int(rssi_val)
                    if rssi_num > -75:
                        reason = "💡 전원 OFF (정상 종료 추정)"
                    else:
                        reason = "⚠️ 통신 사각지대 (음영지역 진입)"
                except:
                    reason = "🔌 통신 끊김"

                return f"# 🔴 **{display_loc}**\n### {reason}\n> 🕒 마지막 통신: `{pretty_time}`\n> 📉 전파 변화: `{trend_str}`"
            else:
                return f"# 🟢 **{display_loc}**\n> 🕒 실시간 갱신 중: `{pretty_time}`\n> 📈 전파 변화: `{trend_str}`"
        except:
            return f"# 🟡 **{display_loc}**\n> ⏳ 시간 형식 분석 중: `{time_str}`"

    with placeholder.container():
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### 🧍 입식 지게차\n{check_status(stand_time, stand_display, stand_rssi, stand_trend)}")
        with col2:
            st.markdown(f"### 💺 좌식 지게차\n{check_status(sit_time, sit_display, sit_rssi, sit_trend)}")

if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            saved_raw_data = f.read()
            if '|' in saved_raw_data:
                sd, sid = saved_raw_data.split('|')
                draw_ui(sd, sid) 
    except:
        pass 

while True:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        success = False
        for attempt in range(2):
            try:
                response = requests.get(WEBAPP_URL, headers=headers, timeout=15)
                response.raise_for_status() 
                success = True
                break  
            except requests.exceptions.Timeout:
                time.sleep(2) 
                
        if not success:
            raise Exception("구글 서버 응답 지연")
            
        data = response.text 
        
        stand_data, sit_data = data.split('|')
        draw_ui(stand_data, sit_data)
        
        if data != saved_raw_data:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                f.write(data)
            saved_raw_data = data
            
    except Exception as e:
        pass
            
    time.sleep(7)
