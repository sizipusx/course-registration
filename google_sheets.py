import streamlit as st
import textwrap
from google.oauth2 import service_account  # 또는 oauth2client 쪽을 쓰실 땐 ServiceAccountCredentials

# 1. Streamlit Secrets에서 가져온 매핑을 일반 dict로 변환
raw_secrets = st.secrets["google_sheets"]
info = dict(raw_secrets)  # 이제 일반 dict

# 2. private_key 전처리: dedent+strip
info["private_key"] = textwrap.dedent(info["private_key"]).strip()

# 3. google-auth 방식 인증 객체 생성
creds = service_account.Credentials.from_service_account_info(
    info,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)

# — 만약 oauth2client를 계속 사용하실 경우:
# from oauth2client.service_account import ServiceAccountCredentials
# creds = ServiceAccountCredentials.from_json_keyfile_dict(
#     info,
#     scopes=["https://www.googleapis.com/auth/spreadsheets"]
# )
# 4. Google Sheets API 클라이언트 생성
from gspread import authorize   # gspread 라이브러리 사용           

#4. 시트 열기
SPREADSHEET_KEY = "1veluylbgXdoQ1ZUz7_SnCByUS3PQPJPU1HpDKO2YEGE"
sheet = client.open_by_key(SPREADSHEET_KEY).sheet1

# ✅ 5. 저장 함수만 정의 (app.py에서 호출됨)
def append_to_sheet(name, student_id, courses):
    for c in courses:
        row = [name, student_id, c["year"], c["semester"], c["name"], c["hours"], c["group"]]
        sheet.append_row(row)
