import streamlit as st
import requests
import time
import os
# 💡 [수정 1] 시간을 더하고 뺄 수 있는 timedelta 도구를 추가했습니다.
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

placeholder = st.empty()
saved_raw_data = "수신 대기 중...,위치 파악 중...|수신 대기 중...,위치 파악 중..."

def draw_ui(stand_data, sit_data):
    try:
        stand_time, stand_raw = stand_data.split(',', 1)
        sit_time, sit_raw = sit_data.split(',', 1)
    except:
        stand_time, stand_raw, sit_time, sit_raw = "알수없음", "알수없음", "알수없음", "알수없음"
        
    stand_display = LOCATION_MAP.get(stand_raw, stand_raw)
    sit_display = LOCATION_MAP.get(sit_raw, sit_raw)

    # 💡 [수정 2] 미국에 있는 서버 시간(UTC)에 9시간을 더해서 완벽한 한국 시간(KST)으로 만듭니다!
    now = datetime.utcnow() + timedelta(hours=9)

    # 구글의 복잡한 시간을 예쁜 형식(YYYY-MM-DD)으로 바꾸는 기능
    def check_status(time_str, display_loc):
        try:
            # 1. " GMT" 글자를 기준으로 앞부분(알맹이 시간)만 잘라냅니다.
            clean_time_str = time_str.split(" GMT")[0].strip()
            
            # 2. 영문 요일/월 형식(%a %b %d %Y %H:%M:%S)을 파이썬 시간으로 번역합니다.
            dt = datetime.strptime(clean_time_str, "%a %b %d %Y %H:%M:%S")
            
            # 3. 화면에 보여줄 예쁜 한국식 디자인으로 포장합니다. (예: 2026-08-24 16:21:08)
            pretty_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            
            # 4. 현재 시간과 비교 (120초 이상 차이나면 전원 꺼짐으로 판단)
            diff = (now - dt).total_seconds()
            
            if diff > 60:  
                return f"# 🔴 **{display_loc}**\n### 🔌 통신 끊김 (전원 꺼짐)\n> ⚠️ 마지막 확인: `{pretty_time}`"
            else:
                return f"# 🟢 **{display_loc}**\n> 🕒 실시간 갱신 중: `{pretty_time}`"
        except:
            return f"# 🟡 **{display_loc}**\n> ⏳ 시간 파악 중: `{time_str}`"

    with placeholder.container():
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### 🧍 입식 지게차\n{check_status(stand_time, stand_display)}")
        with col2:
            st.markdown(f"### 💺 좌식 지게차\n{check_status(sit_time, sit_display)}")

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
