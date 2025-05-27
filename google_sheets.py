import streamlit as st
import gspread
from google.oauth2.service_account import Credentials # gspread 5.x+ 에서는 Credentials 객체 직접 사용 가능

# st.secrets에서 google_sheets 섹션 전체를 가져옵니다.
creds_dict = st.secrets["google_sheets"]

# gspread 5.x 이상 버전
try:
    # Credentials 객체 생성
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file' # 필요시 drive scope 추가
        ]
    )
    # gspread 클라이언트 인증
    gc = gspread.authorize(creds)

    # 또는 gspread.service_account_from_dict(creds_dict) 직접 사용 (scopes 명시 불가)
    # gc = gspread.service_account_from_dict(creds_dict) # 이 경우 기본 scope 사용

    st.success("Google Sheets 인증 성공!")

    # 예시: 특정 스프레드시트 열고 데이터 쓰기
    spreadsheet_id = "YOUR_SPREADSHEET_ID" # 실제 스프레드시트 ID로 변경
    # 또는 스프레드시트 URL
    # spreadsheet_url = "https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit#gid=0"


    # worksheet_name = "Sheet1" # 실제 시트 이름으로 변경

    # # ID로 열기
    # sh = gc.open_by_key(spreadsheet_id)
    # # URL로 열기
    # # sh = gc.open_by_url(spreadsheet_url)
    # # 이름으로 열기 (느릴 수 있음)
    # # sh = gc.open(spreadsheet_name) # 스프레드시트 파일 이름

    # worksheet = sh.worksheet(worksheet_name)
    # worksheet.append_row(["이름", "나이", "도시"])
    # worksheet.append_row(["홍길동", 30, "서울"])
    # st.write("데이터가 성공적으로 기록되었습니다.")

except Exception as e:
    st.error(f"Google Sheets 인증 또는 작업 중 에러 발생: {e}")
    st.error(f"Secrets 내용 확인: {st.secrets['google_sheets']}") # 디버깅용