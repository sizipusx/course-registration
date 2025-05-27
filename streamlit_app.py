# streamlit_app.py
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json # URL 파라미터로 전달된 JSON 문자열을 파싱하기 위함

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

SPREADSHEET_NAME = "1veluylbgXdoQ1ZUz7_SnCByUS3PQPJPU1HpDKO2YEGE"
WORKSHEET_NAME = "Sheet1" # 예: CourseSubmissions (선택 사항, 없으면 기본값 사용)

# try:
#     creds_dict = st.secrets["gcp_service_account"]
#     SPREADSHEET_NAME = st.secrets["SPREADSHEET_NAME"]
#     WORKSHEET_NAME = st.secrets.get("WORKSHEET_NAME", "CourseSubmissions") # WORKSHEET_NAME이 없으면 기본값 "CourseSubmissions" 사용
# except KeyError as e:
#     st.error(f"Streamlit Secrets 설정 오류: '{e}' 키를 찾을 수 없습니다. Secrets 설정을 확인해주세요.")
#     st.caption("Secrets에는 `gcp_service_account` 섹션과 `SPREADSHEET_NAME` 키가 반드시 포함되어야 합니다.")
#     st.stop() # 중요한 설정이 없으면 앱 중단

# SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

@st.cache_resource(ttl=600) # 10분 동안 인증 객체 캐싱
def get_gspread_client():
    """Google Sheets API 클라이언트를 반환합니다."""
    try:
        creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]
    )
        client = gspread.authorize(creds)
        st.success("Google Sheets 인증 성공!")
        return client
    except Exception as e:
        st.error(f"Google Sheets 인증 중 오류 발생: {e}")
        return None

def get_worksheet(client):
    """주어진 클라이언트를 사용하여 워크시트 객체를 반환합니다."""
    if not client:
        return None
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        try:
            worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            # 워크시트가 없으면 새로 만들고 헤더 추가
            worksheet = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows="100", cols="10") # 열 개수는 필요에 따라 조절
            header = ["Timestamp", "Student Name", "Student ID", "Course ID", "Course Name", "Year", "Semester", "Hours", "Raw Query Params"]
            worksheet.append_row(header)
            st.info(f"워크시트 '{WORKSHEET_NAME}'을(를) 새로 만들고 헤더를 추가했습니다.")
        return worksheet
    except Exception as e:
        st.error(f"Google Spreadsheet ('{SPREADSHEET_NAME}') 또는 Worksheet ('{WORKSHEET_NAME}') 접근 중 오류: {e}")
        return None

# --- Streamlit 앱 로직 ---
st.set_page_config(page_title="수강신청 데이터 수신", layout="centered")
st.title("📋 수강신청 데이터 저장소")

# URL 쿼리 파라미터에서 데이터 가져오기
query_params = st.experimental_get_query_params()

# 'studentName', 'studentId', 'selectedCourses' 파라미터가 있는지 확인
if 'studentName' in query_params and 'selectedCourses' in query_params:
    student_name = query_params.get('studentName', ["정보 없음"])[0]
    student_id = query_params.get('studentId', ["정보 없음"])[0]
    selected_courses_str = query_params.get('selectedCourses', ["[]"])[0] # 기본값으로 빈 JSON 배열 문자열

    raw_query_params_for_sheet = json.dumps(query_params) # 디버깅 및 기록용

    try:
        # selectedCourses는 JSON 문자열로 전달되므로 Python 객체로 파싱
        selected_courses = json.loads(selected_courses_str)
        if not isinstance(selected_courses, list): # 파싱 결과가 리스트가 아니면 오류 처리
            st.error("전달된 'selectedCourses' 데이터가 올바른 리스트 형식이 아닙니다.")
            selected_courses = [] # 빈 리스트로 초기화하여 아래 로직에서 오류 방지
    except json.JSONDecodeError:
        st.error(f"전달된 과목 정보(selectedCourses)가 올바른 JSON 형식이 아닙니다. 수신된 값: {selected_courses_str}")
        selected_courses = [] # 오류 발생 시 빈 리스트로
    except Exception as e:
        st.error(f"과목 정보 처리 중 예상치 못한 오류 발생: {e}")
        selected_courses = []

    if student_name != "정보 없음" and selected_courses: # 유효한 데이터가 있을 경우
        st.success("데이터를 성공적으로 수신했습니다!")
        with st.expander("수신된 데이터 확인"):
            st.write(f"**학생 이름:** {student_name}")
            st.write(f"**학번:** {student_id}")
            st.write("**선택 과목:**")
            st.json(selected_courses) # 파싱된 객체를 예쁘게 출력

        gspread_client = get_gspread_client()
        worksheet = get_worksheet(gspread_client)

        if worksheet:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            rows_to_append = []

            for course in selected_courses:
                # course 딕셔너리에서 값 가져오기 (get 사용으로 안전하게)
                rows_to_append.append([
                    timestamp,
                    student_name,
                    student_id,
                    course.get('id', 'N/A'),
                    course.get('name', 'N/A'),
                    course.get('year', 'N/A'),
                    course.get('semester', 'N/A'),
                    course.get('hours', 'N/A'),
                    raw_query_params_for_sheet # 원본 쿼리 파라미터를 저장하여 추후 문제 발생 시 확인 용이
                ])

            if rows_to_append:
                try:
                    # 워크시트가 비어있거나 헤더가 올바르지 않으면 헤더 추가
                    current_header = []
                    if worksheet.row_count > 0:
                        current_header = worksheet.row_values(1)

                    expected_header = ["Timestamp", "Student Name", "Student ID", "Course ID", "Course Name", "Year", "Semester", "Hours", "Raw Query Params"]
                    if not current_header or current_header != expected_header:
                        if worksheet.row_count > 0: # 기존 내용이 있다면 주의 메시지
                            st.warning("워크시트의 헤더가 예상과 다릅니다. 기존 데이터를 덮어쓰지 않도록 주의하세요.")
                        # 헤더를 새로 쓰거나, 현재는 그냥 데이터만 추가 (필요시 헤더 추가 로직 강화)
                        # worksheet.insert_row(expected_header, 1) # 이렇게 하면 기존 1행이 밀려남. 또는 clear 후 새로 작성

                    worksheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
                    st.success(f"'{student_name}' 학생의 수강신청 내역이 Google Sheets에 성공적으로 저장되었습니다!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Google Sheets에 데이터 저장 중 오류 발생: {e}")
                    st.error("Google Sheets API 할당량이 초과되었거나 권한 문제가 있을 수 있습니다. 잠시 후 다시 시도해주세요.")
            else:
                st.warning("Google Sheets에 저장할 유효한 과목 데이터가 없습니다.")
        else:
            st.error("Google Sheets 워크시트를 가져올 수 없어 데이터를 저장할 수 없습니다. Streamlit 앱 로그 및 Secrets 설정을 확인해주세요.")
    elif 'studentName' in query_params: # studentName은 있지만 selectedCourses가 비어있는 등
        st.warning("수신된 데이터가 충분하지 않아 처리할 수 없습니다. (예: 과목 정보 누락 또는 형식 오류)")
        with st.expander("수신된 쿼리 파라미터 보기"):
            st.json(query_params)
    else:
        # 일반적인 방문객을 위한 안내 메시지
        st.info("이 페이지는 외부 애플리케이션으로부터 수강신청 데이터를 수신하여 Google Sheets에 저장하는 용도로 사용됩니다.")
        st.markdown("""
        ### 개발자 참고사항
        - 데이터는 HTTP `GET` 요청의 URL 쿼리 파라미터를 통해 전달받습니다.
        - 필수 파라미터: `studentName`, `studentId`, `selectedCourses`
        - `selectedCourses`는 선택된 과목 정보를 담은 **JSON 문자열**이어야 하며, URL 인코딩되어야 합니다.
        - 예시: `.../?studentName=홍길동&studentId=2025001&selectedCourses=%5B%7B%22id%22%3A%22c1%22%2C%22name%22%3A%22과목1%22%2C...%7D%5D`
        """)

# (선택 사항) Google Sheets 내용 미리보기 기능 (디버깅용)
if st.checkbox("Google Sheets 최신 데이터 5개 미리보기 (디버깅용)"):
    gspread_client = get_gspread_client()
    worksheet = get_worksheet(gspread_client)
    if worksheet:
        try:
            # 모든 데이터를 가져오면 매우 느릴 수 있으므로, 최근 몇 개만 가져오거나,
            # 헤더를 포함하여 전체 레코드를 가져온 후 파이썬에서 슬라이싱합니다.
            all_records = worksheet.get_all_records(head=1) # 첫 번째 행을 헤더로 사용
            if all_records:
                st.dataframe(all_records[-5:]) # 최근 5개 데이터 표시
                st.caption(f"총 {len(all_records)}개의 데이터가 시트에 저장되어 있습니다.")
            else:
                st.write("시트에 데이터가 없습니다.")
        except Exception as e:
            st.error(f"Google Sheets 데이터 로드 중 오류: {e}")