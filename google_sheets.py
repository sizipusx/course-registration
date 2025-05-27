import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# st.secrets["google_sheets"] 는 이미 dict 타입으로 넘어옵니다.
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["google_sheets"],
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
client = gspread.authorize(creds)

# 4. 시트 열기
SPREADSHEET_KEY = "1veluylbgXdoQ1ZUz7_SnCByUS3PQPJPU1HpDKO2YEGE"
sheet = client.open_by_key(SPREADSHEET_KEY).sheet1

# ✅ 5. 저장 함수만 정의 (app.py에서 호출됨)
def append_to_sheet(name, student_id, courses):
    for c in courses:
        row = [name, student_id, c["year"], c["semester"], c["name"], c["hours"], c["group"]]
        sheet.append_row(row)
