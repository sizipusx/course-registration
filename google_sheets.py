import streamlit as st
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. secrets에서 JSON 문자열을 로드
json_key = json.loads(st.secrets["GOOGLE_SHEETS_JSON"])

# 2. 인증 객체 생성
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(json_key, scope)

# 3. Google Sheets 클라이언트 생성
client = gspread.authorize(creds)

# 4. 문서 열기 (문서 ID 사용)
SPREADSHEET_KEY = "1veluylbgXdoQ1ZUz7_SnCByUS3PQPJPU1HpDKO2YEGE"  # 본인의 문서 ID로 바꿔야 함
sheet = client.open_by_key(SPREADSHEET_KEY).sheet1

# 5. 예시: 한 줄 추가
sheet.append_row(["홍길동", "23001", "2", "1", "문학", "4", "학교지정"])
