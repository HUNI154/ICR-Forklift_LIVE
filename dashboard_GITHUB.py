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

    stand_trend = " ➔ ".join(st.session_state.stand_rssi_history) + " dBm" if st.session_state.stand_rssi_history else "측정 대기"
    sit_trend = " ➔ ".join(st.session_state.sit_rssi_history) + " dBm" if st.session_state.sit_rssi_history else "측정 대기"

    # 💡 [핵심] 스트림릿 클라우드의 미국 시계를 버리고, 한국 시간(UTC+9) 강제 적용!
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
            
            pretty_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            diff = (now - dt).total_seconds()
            
            # 💡 [핵심] 90초(1분 30초) 동안 데이터 안 오면 즉각 빨간불로 전환!
            if diff > 90:  
                try:
                    rssi_num = int(rssi_val)
                    if rssi_num > -75:
                        reason = "🔌 전원 OFF (시동 꺼짐 추정)"
                    else:
                        reason = "📡 통신 사각지대 (음영지역 진입)"
                except:
                    reason = "🚨 통신 끊김"

                return f"# 🔴 **{display_loc}**\n### {reason}\n> 🕒 마지막 통신: `{pretty_time}`\n> 📉 전파 변화: `{trend_str}`"
            
            else:
                try:
                    rssi_num = int(rssi_val)
                    if rssi_num <= -65:
                        return f"# ⚠️ **{display_loc} (신호약함)**\n> 🕒 실시간 갱신 중: `{pretty_time}`\n> 📉 전파 변화: `{trend_str}`"
                except:
                    pass
                
                return f"# 🟢 **{display_loc}**\n> 🕒 실시간 갱신 중: `{pretty_time}`\n> 📈 전파 변화: `{trend_str}`"
                
        except:
            return f"# ⚪ **{display_loc}**\n> ⏳ 시간 파악 중: `{time_str}`"

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

# 💡 [핵심] 구글이 봇(Bot)으로 차단하지 못하도록 'Session'을 열어 정상적인 브라우저처럼 위장합니다.
session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

while True:
    try:
        success = False
        for attempt in range(3):
            try:
                # 파라미터를 URL 뒤에 붙이지 않고 session.get 내부에 안전하게 담아서 보냄
                response = session.get(WEBAPP_URL, params={'dummy': int(time.time())}, headers=headers, timeout=25)
                response.raise_for_status() 
                success = True
                break  
            except requests.exceptions.RequestException:
                time.sleep(3) 
                
        # 💡 [핵심] 404 에러나 지연이 생겨도 보기 싫은 텍스트를 띄우지 않고, 그냥 조용히 다음 턴으로 넘김
        if not success:
            time.sleep(7)
            continue
            
        data = response.text 
        
        # 구글 서버 렉으로 인해 엉뚱한 HTML 에러 페이지가 날아왔을 때 튕기는 현상 완벽 방어
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
        # 혹시 모를 내부 에러가 나도 화면을 멈추지 않고 계속 돌아가도록 조용히 패스(pass)
        pass
            
    time.sleep(7)
