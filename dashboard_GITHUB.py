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

# 💡 화면 깜빡임(블러) 방지 도화지
placeholder = st.empty()
saved_raw_data = "대기중,대기중,-|대기중,대기중,-" 

def draw_ui(stand_data, sit_data):
    try:
        stand_time, stand_raw, stand_rssi = stand_data.split(',', 2)
        sit_time, sit_raw, sit_rssi = sit_data.split(',', 2)
    except:
        stand_time, stand_raw, stand_rssi = "알수없음", "알수없음", "-"
        sit_time, sit_raw, sit_rssi = "알수없음", "알수없음", "-"

    stand_display = LOCATION_MAP.get(stand_raw, stand_raw)
    sit_display = LOCATION_MAP.get(sit_raw, sit_raw)

    st.session_state.stand_rssi_history = update_history(st.session_state.stand_rssi_history, stand_rssi)
    st.session_state.sit_rssi_history = update_history(st.session_state.sit_rssi_history, sit_rssi)

    def format_trend(history):
        if not history:
            return "측정 대기"
        if len(history) == 1:
            return f"**{history[0]}** dBm"
        
        current = history[-1]
        past = " ➔ ".join(history[:-1])
        return f"**{current}** dBm (이전: {past})"

    stand_trend = format_trend(st.session_state.stand_rssi_history)
    sit_trend = format_trend(st.session_state.sit_rssi_history)

    now = datetime.utcnow() + timedelta(hours=9)

    def check_status(time_str, display_loc, rssi_val, trend_str):
        if time_str == "대기중" or time_str == "알수없음":
            return f"# ⚪ **{display_loc}**\n> ⏳ 데이터 수신 대기 중..."

        try:
            try:
                dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            except:
                clean_time_str = time_str.split(" GMT")[0].strip()
                dt = datetime.strptime(clean_time_str, "%a %b %d %Y %H:%M:%S")
            
            # 💡 [핵심 수정] 대문자 %Y(2026)를 소문자 %y(26)로 변경하여 깔끔한 형식으로 출력!
            pretty_time = dt.strftime("%y-%m-%d %H:%M:%S")
            diff = (now - dt).total_seconds()
            
            if diff > 180:  
                try:
                    rssi_num = int(rssi_val)
                    if rssi_num > -75:
                        reason = "🔌 전원 OFF (시동 꺼짐 추정)"
                    else:
                        reason = "📡 통신 사각지대 (음영지역 진입)"
                except:
                    reason = "🚨 통신 끊김"

                return f"# 🔴 **{display_loc}**\n### {reason}\n> 🕒 마지막 통신: `{pretty_time}`\n> 📉 전파 변화: {trend_str}"
            
            else:
                try:
                    rssi_num = int(rssi_val)
                    if rssi_num <= -65:
                        return f"# 🟢 **{display_loc}** <span style='font-size: 18px; font-weight: normal; color: #ff9900; vertical-align: middle;'>(⚠️신호약함)</span>\n> 🕒 실시간 갱신 중: `{pretty_time}`\n> 📉 전파 변화: {trend_str}"
                except:
                    pass
                
                return f"# 🟢 **{display_loc}**\n> 🕒 실시간 갱신 중: `{pretty_time}`\n> 📈 전파 변화: {trend_str}"
                
        except:
            return f"# ⚪ **{display_loc}**\n> ⏳ 시간 파악 중: `{time_str}`"

    # 도화지(placeholder) 덮어쓰기 적용
    with placeholder.container():
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### 🧍 입식 지게차\n{check_status(stand_time, stand_display, stand_rssi, stand_trend)}", unsafe_allow_html=True)
        with col2:
            st.markdown(f"### 💺 좌식 지게차\n{check_status(sit_time, sit_display, sit_rssi, sit_trend)}", unsafe_allow_html=True)


if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            saved_raw_data = f.read()
            if '|' in saved_raw_data:
                sd, sid = saved_raw_data.split('|')
                draw_ui(sd, sid) 
    except:
        pass 

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0',
    'Connection': 'close' # 💡 연결 찌꺼기 방지 (3분 딜레이 해결용)
}

while True:
    try:
        success = False
        for attempt in range(3):
            try:
                # 💡 구글 캐시 부수기 + 딜레이 완벽 제거
                nocache_url = f"{WEBAPP_URL}?dummy={int(time.time())}"
                response = requests.get(nocache_url, headers=headers, timeout=15)
                response.raise_for_status() 
                success = True
                break  
            except requests.exceptions.RequestException:
                time.sleep(3) 
                
        if not success:
            time.sleep(7)
            continue
            
        data = response.text 
        
        if '|' not in data:
            time.sleep(7)
            continue

        stand_data, sit_data = data.split('|', 1)
        draw_ui(stand_data, sit_data)
        
        if data != saved_raw_data:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                f.write(data)
            saved_raw_data = data
            
    except Exception:
        pass
            
    time.sleep(7)
