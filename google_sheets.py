import streamlit as st
from google.oauth2 import service_account
import textwrap

# Secrets.toml 포맷은 그대로 사용하거나, 필요하면 dedent 처리
info = st.secrets["google_sheets"].copy()
info["private_key"] = textwrap.dedent(info["private_key"]).strip()

# google-auth로 인증 객체 생성
creds = service_account.Credentials.from_service_account_info(
    info,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)


# 4. 시트 열기
# SPREADSHEET_KEY = "1veluylbgXdoQ1ZUz7_SnCByUS3PQPJPU1HpDKO2YEGE"
# sheet = client.open_by_key(SPREADSHEET_KEY).sheet1

# # ✅ 5. 저장 함수만 정의 (app.py에서 호출됨)
# def append_to_sheet(name, student_id, courses):
#     for c in courses:
#         row = [name, student_id, c["year"], c["semester"], c["name"], c["hours"], c["group"]]
#         sheet.append_row(row)
