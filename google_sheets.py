import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import re # 정규 표현식 사용

# st.secrets에서 google_sheets 섹션 전체를 가져옵니다.
creds_dict_original = st.secrets["google_sheets"]
# 수정 가능하도록 .to_dict() 또는 deepcopy 사용 (st.secrets는 불변일 수 있음)
creds_dict = creds_dict_original.to_dict()


raw_private_key = creds_dict["private_key"]

st.subheader("Private Key 검증 시작")

# 1. 캐리지 리턴 문자(\r) 및 불필요한 공백 제거 시도
# Windows 스타일 줄바꿈(\r\n)을 Unix 스타일(\n)로 통일하고, 각 줄의 앞뒤 공백 제거
lines = []
corrupted_line_found = False
original_lines = raw_private_key.splitlines() # 모든 종류의 줄바꿈 문자를 기준으로 분리

for i, line_text in enumerate(original_lines):
    cleaned_line = line_text.strip() # 앞뒤 공백 제거
    lines.append(cleaned_line)
    if i == 0 and cleaned_line != "-----BEGIN PRIVATE KEY-----":
        st.warning(f"헤더 문제: '{cleaned_line}'")
        corrupted_line_found = True
    # 마지막 푸터는 모든 라인 처리 후 검사

# PEM 형식으로 재구성 (중간에 빈 줄이 있었을 경우 제거)
normalized_key = "\n".join(filter(None, lines)) # 빈 줄 제거하고 \n으로 합침
creds_dict["private_key"] = normalized_key # 정제된 키로 교체

st.text_area("정제 시도 후 Private Key", normalized_key, height=300)

# 2. 정제된 키의 각 줄 길이 확인
pem_lines = normalized_key.split('\n')
header_ok = False
footer_ok = False

if pem_lines:
    if pem_lines[0] == "-----BEGIN PRIVATE KEY-----":
        header_ok = True
    else:
        st.error(f"정제 후에도 Private Key 헤더가 올바르지 않습니다: '{pem_lines[0]}'")

    if pem_lines[-1] == "-----END PRIVATE KEY-----":
        footer_ok = True
    else:
        st.error(f"정제 후에도 Private Key 푸터가 올바르지 않습니다: '{pem_lines[-1]}'")

if header_ok and footer_ok:
    st.success("Private Key 헤더와 푸터가 정상입니다.")
    base64_data_lines = pem_lines[1:-1]
    problematic_lines_info = []
    for i, line_content in enumerate(base64_data_lines):
        line_len = len(line_content)
        # Base64 유효 문자 검사 (간단하게)
        is_valid_base64_chars = all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in line_content)

        if not is_valid_base64_chars:
            problematic_lines_info.append(f"데이터 라인 {i+1}: 유효하지 않은 Base64 문자 포함 (길이: {line_len}): '{line_content}'")
            corrupted_line_found = True
        elif line_len == 65: # 에러 메시지에서 언급된 길이
            problematic_lines_info.append(f"데이터 라인 {i+1}: 길이가 정확히 65입니다! (에러 원인 유력): '{line_content}'")
            corrupted_line_found = True
        # 마지막 데이터 라인이 아니면서 길이가 64가 아닌 경우 (Base64 표준은 64자씩 끊음)
        elif line_len != 64 and i < len(base64_data_lines) - 1:
            problematic_lines_info.append(f"데이터 라인 {i+1}: 길이가 64가 아님 (길이: {line_len}): '{line_content}'")
            # 이 자체가 항상 에러는 아닐 수 있지만, 주의해야 함
        # 마지막 데이터 라인의 길이는 4의 배수여야 함
        elif i == len(base64_data_lines) - 1 and line_len % 4 != 0:
            problematic_lines_info.append(f"마지막 데이터 라인: 길이가 4의 배수가 아님 (길이: {line_len}): '{line_content}'")
            corrupted_line_found = True

    if problematic_lines_info:
        st.error("Private Key 데이터 라인 검증 중 문제 발견:")
        for info in problematic_lines_info:
            st.warning(info)
    elif not corrupted_line_found : # 헤더/푸터 OK, 데이터 라인 문제 없음
        st.success("Private Key 데이터 라인 구조 검증 통과.")
else:
    corrupted_line_found = True
    st.error("Private Key 헤더 또는 푸터 문제로 데이터 라인 검증을 진행할 수 없습니다.")

st.subheader("Private Key 검증 종료")

if corrupted_line_found:
    st.error("Private Key에 문제가 있어 인증을 시도하지 않습니다. 위의 경고/에러를 확인하고 Streamlit Secrets를 수정하세요.")
    st.stop()

try:
    # Credentials 객체 생성 시 정제된 creds_dict 사용
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]
    )
    gc = gspread.authorize(creds)
    st.success("Google Sheets 인증 성공!")

    # (기존 스프레드시트 작업 코드)

except Exception as e:
    st.error(f"Google Sheets 인증 또는 작업 중 에러 발생: {e}")
    st.error(f"인증 시 사용된 Secrets (private_key는 정제된 버전일 수 있음): {creds_dict}")