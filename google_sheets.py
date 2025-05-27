import streamlit as st
from google.oauth2 import service_account

# 1) Streamlit Secrets에서 매핑을 가져와 일반 dict로 복사
raw_map = st.secrets["google_sheets"]
info = dict(raw_map)

# 2) 원본 private_key 로깅 (Cloud Logs에서 실제 문자열을 확인해 보세요)
# import logging
# logging.error("PRIVATE_KEY repr: %r", raw_map["private_key"][:200])

# 3) PEM 포맷 재조립
raw_key = raw_map["private_key"]
#  - strip()으로 앞뒤 공백·개행 제거
#  - splitlines()로 행별 분리
#  - 빈 줄/공백 줄은 제거하고, 각 행도 strip()
lines = [
    line.strip()
    for line in raw_key.strip().splitlines()
    if line.strip()
]

#  - 맨 앞·뒤 라인이 헤더·푸터인지 검증 (로그로 확인 가능)
assert lines[0] == "-----BEGIN PRIVATE KEY-----", "헤더가 없습니다"
assert lines[-1] == "-----END PRIVATE KEY-----", "푸터가 없습니다"

#  - 재조립: 각 행을 '\n'으로 합치고, 마지막에 개행 한 번 추가
fixed_pem = "\n".join(lines) + "\n"
info["private_key"] = fixed_pem

# 4) 인증 객체 생성
creds = service_account.Credentials.from_service_account_info(
    info,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
# 5) Google Sheets API 클라이언트 생성
from gspread import Client   

#4. 시트 열기
SPREADSHEET_KEY = "1veluylbgXdoQ1ZUz7_SnCByUS3PQPJPU1HpDKO2YEGE"
sheet = client.open_by_key(SPREADSHEET_KEY).sheet1

# ✅ 5. 저장 함수만 정의 (app.py에서 호출됨)
def append_to_sheet(name, student_id, courses):
    for c in courses:
        row = [name, student_id, c["year"], c["semester"], c["name"], c["hours"], c["group"]]
        sheet.append_row(row)
