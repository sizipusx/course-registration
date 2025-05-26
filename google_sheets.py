import json
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. secrets에서 JSON 문자열 로드
json_key = json.loads(st.secrets["GOOGLE_SHEETS_JSON"])

# 2. 인증 범위 정의
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 3. 인증 객체 생성
creds = ServiceAccountCredentials.from_json_keyfile_dict(json_key, scope)
client = gspread.authorize(creds)

# 4. 시트 열기
SPREADSHEET_KEY = "1veluylbgXdoQ1ZUz7_SnCByUS3PQPJPU1HpDKO2YEGE"
sheet = client.open_by_key(SPREADSHEET_KEY).sheet1

# ✅ 5. 저장 함수만 정의 (app.py에서 호출됨)
def append_to_sheet(name, student_id, courses):
    for c in courses:
        row = [name, student_id, c["year"], c["semester"], c["name"], c["hours"], c["group"]]
        sheet.append_row(row)
