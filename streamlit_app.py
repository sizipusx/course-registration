# streamlit_app.py
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json # courses.json 로드용
from fpdf import FPDF # PDF 생성을 위한 라이브러리 (pip install fpdf2)

# --- 0. 설정값 및 상수 ---
COURSES_JSON_PATH = 'courses.json' # Streamlit 앱과 같은 경로에 courses.json 파일이 있어야 함
MANDATORY_GROUP_NAME = "학교지정"

# 미술/음악, 국영수 관련 과목 ID (courses.json의 ID와 일치해야 함)
ART_MUSIC_COURSE_IDS = ["c19", "c20", "c40", "c41", "c55", "c56", "c82", "c83"]
KES_MAX_COURSE_IDS = ["c34", "c57", "c58", "c59", "c60", "c84", "c85"]
EXACT_ART_MUSIC_SELECTION = 2
MAX_KES_SELECTION = 3

# 학년별, 학기별 필요 총 학점
REQUIRED_TOTAL_HOURS_MAP = {
    "Y2S1": 29, "Y2S2": 29,
    "Y3S1": 29, "Y3S2": 29
}


try:
    # st.secrets에서 google_sheets 섹션 전체를 가져옵니다.
    creds_dict_original = st.secrets["google_sheets"]
    # 수정 가능하도록 .to_dict() 또는 deepcopy 사용 (st.secrets는 불변일 수 있음)
    creds_dict = creds_dict_original.to_dict()

    SPREADSHEET_NAME = "1veluylbgXdoQ1ZUz7_SnCByUS3PQPJPU1HpDKO2YEGE"
    WORKSHEET_NAME = "Sheet1" # 예: CourseSubmissions (선택 사항, 없으면 기본값 사용)

except KeyError as e:
    st.error(f"Streamlit Secrets 설정 오류: '{e}' 키를 찾을 수 없습니다. Secrets 설정을 확인해주세요.")
    st.caption("Secrets에는 `google_sheets` 섹션이 반드시 포함되어야 합니다.")
    st.stop()

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

@st.cache_resource(ttl=600) # 클라이언트를 인자로 받도록 수정
def get_worksheet(_client): # 파라미터 이름 변경하여 내부 변수와 충돌 방지
    if not _client:
        return None
    try:
        spreadsheet = _client.open(SPREADSHEET_NAME)
        try:
            worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows="100", cols="10")
            header = ["Timestamp", "Student Name", "Student ID", "Course ID", "Course Name", "Year", "Semester", "Hours"]
            worksheet.append_row(header)
            st.info(f"워크시트 '{WORKSHEET_NAME}'을(를) 새로 만들고 헤더를 추가했습니다.")
        return worksheet
    except Exception as e:
        st.error(f"Google Spreadsheet ('{SPREADSHEET_NAME}') 또는 Worksheet ('{WORKSHEET_NAME}') 접근 중 오류: {e}")
        return None

# --- 2. 과목 데이터 로드 및 처리 함수 ---
@st.cache_data # 과목 데이터는 변경되지 않으므로 캐싱
def load_courses():
    try:
        with open(COURSES_JSON_PATH, 'r', encoding='utf-8') as f:
            all_courses_list = json.load(f)
        # 리스트를 ID를 키로 하는 딕셔너리로 변환하여 접근 용이하게 함
        all_courses_dict = {course['id']: course for course in all_courses_list}
        return all_courses_list, all_courses_dict
    except FileNotFoundError:
        st.error(f"과목 정보 파일({COURSES_JSON_PATH})을 찾을 수 없습니다.")
        return [], {}
    except json.JSONDecodeError:
        st.error(f"과목 정보 파일({COURSES_JSON_PATH})의 형식이 올바르지 않습니다.")
        return [], {}

def get_courses_by_year_semester(all_courses_list, year, semester):
    return [c for c in all_courses_list if c['year'] == year and c['semester'] == semester]

def group_courses(courses_for_semester):
    grouped = {}
    for course in courses_for_semester:
        group_name = course['group']
        if group_name not in grouped:
            is_mandatory_group = (group_name == MANDATORY_GROUP_NAME)
            grouped[group_name] = {
                'courses': [],
                'quota': 0 if is_mandatory_group else course.get('groupQuota', 0), # groupQuota가 없을 수 있으므로 get 사용
                'isMandatory': is_mandatory_group,
            }
        grouped[group_name]['courses'].append(course)
    # 그룹 이름 정렬 (학교지정 우선, 그 외 가나다 순)
    sorted_group_names = sorted(
        grouped.keys(),
        key=lambda g: (grouped[g]['isMandatory'], g) if grouped[g]['isMandatory'] else (False, g)
    )
    return {name: grouped[name] for name in sorted_group_names}


# --- 3. PDF 생성 함수 (fpdf2 사용) ---
class PDF(FPDF):
    def header(self):
        # 한글 폰트 추가 (streamlit 앱과 같은 경로에 폰트 파일 필요)
        # 예시: NanumGothic.ttf (streamlit 앱 실행 환경에 폰트 파일이 있어야 함)
        # PDF 클래스 내 header 함수 또는 폰트 추가하는 부분
        try:
            # 현재 스크립트 파일의 디렉토리를 기준으로 폰트 파일 경로 설정
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            font_path = os.path.join(current_dir, 'NanumGothic.ttf') # 또는 사용하는 폰트 파일명

            if not os.path.exists(font_path):
                # 이 경고는 Streamlit 앱 실행 시 로그에만 나올 수 있습니다.
                # 사용자에게 직접 보이지 않을 수 있으므로, Streamlit UI에 st.warning을 사용하는 것이 좋습니다.
                print(f"WARNING: Font file not found at {font_path}")
                # raise FileNotFoundError(f"TTF Font file not found: {font_path}") # 여기서 바로 에러를 발생시키기보다 아래 로직에서 처리

            self.add_font('NanumGothic', '', font_path, uni=True) # 경로를 font_path 변수로 전달
            self.set_font('NanumGothic', '', 12)
        except RuntimeError as e: # add_font에서 파일 못찾으면 RuntimeError 발생 가능
            self.set_font('Arial', '', 12)
            if not hasattr(self, '_font_warning_shown'):
                st.warning(f"PDF 생성: NanumGothic 폰트 파일을 찾을 수 없거나 로드 중 오류({e}). 기본 폰트(Arial)를 사용합니다. 한글이 깨질 수 있습니다.")
                self._font_warning_shown = True
        except FileNotFoundError as e: # os.path.exists 등으로 미리 체크했다면 이 부분은 덜 필요할 수 있음
            self.set_font('Arial', '', 12)
            if not hasattr(self, '_font_warning_shown'):
                st.warning(f"PDF 생성: 지정된 경로에 NanumGothic 폰트 파일이 없습니다({e}). 기본 폰트(Arial)를 사용합니다.")
                self._font_warning_shown = True

            self.cell(0, 10, '수강신청 내역서', 0, 1, 'C')
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        try:
            self.set_font('NanumGothic', '', 8)
        except RuntimeError:
            self.set_font('Arial', '', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        try:
            self.set_font('NanumGothic', 'B', 12)
        except RuntimeError:
            self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, data_list): # data_list는 (과목명, 학점) 튜플의 리스트
        try:
            self.set_font('NanumGothic', '', 10)
        except RuntimeError:
            self.set_font('Arial', '', 10)

        col_widths = [self.w - 20 - 20 - 20, 20] # 과목명, 학점
        self.set_fill_color(200, 220, 255)
        self.cell(col_widths[0], 7, "과목명", 1, 0, 'C', True)
        self.cell(col_widths[1], 7, "학점", 1, 1, 'C', True)

        total_hours_semester = 0
        for item_name, item_hours in data_list:
            self.cell(col_widths[0], 6, str(item_name), 1)
            self.cell(col_widths[1], 6, str(item_hours), 1, 0, 'R')
            self.ln()
            total_hours_semester += item_hours
        
        self.set_font_size(10)
        self.cell(col_widths[0], 7, "학기 총 학점:", 1, 0, 'R')
        self.cell(col_widths[1], 7, str(total_hours_semester), 1, 1, 'R')
        return total_hours_semester

def generate_pdf_bytes(student_name, student_id, selected_courses_details_by_semester):
    pdf = PDF()
    pdf.add_page()
    
    try:
        pdf.set_font('NanumGothic', '', 11)
    except RuntimeError:
        pdf.set_font('Arial', '', 11)

    pdf.cell(0, 10, f"학생 이름: {student_name}", 0, 1)
    pdf.cell(0, 10, f"학번: {student_id}", 0, 1)
    pdf.ln(5)

    overall_total_hours = 0
    for semester_key, courses in selected_courses_details_by_semester.items():
        year, semester = int(semester_key[1]), int(semester_key[3])
        if courses: # 해당 학기에 선택한 과목이 있을 경우에만 섹션 추가
            pdf.chapter_title(f"{year}학년 {semester}학기 선택과목")
            semester_data = [(c['name'], c['hours']) for c in courses]
            overall_total_hours += pdf.chapter_body(semester_data)
            pdf.ln(5)
    
    pdf.ln(5)
    try:
        pdf.set_font('NanumGothic', 'B', 11)
    except RuntimeError:
        pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, f"전체 총 선택 학점: {overall_total_hours}", 0, 1, 'R')

    return pdf.output(dest='S').encode('latin-1') # 바이트 문자열로 반환

# --- 4. Streamlit UI 및 로직 ---
st.set_page_config(page_title="수강신청 시스템 (정현고)", layout="wide")
st.title("📋 수강신청 시스템 (2025학년도 입학생 대상)")

# 헤더 공지사항 등
st.markdown("""
<div style="background-color:#fff3cd; padding:15px; border-radius:5px; margin-bottom:20px;">
    <p style="color:#856404; font-weight:bold;">[중요 선택 조건 안내]</p>
    <ul style="color:#856404;">
        <li>미술/음악 관련 과목 (미술창작, 음악연주와창작, 음악감상과비평, 미술감상과비평 등) 중 <strong>정확히 2개</strong>를 수강해야 합니다.</li>
        <li>지정된 국영수 관련 과목 (기하, 매체의사소통, 심화영어, 미적분2, 경제수학, 언어생활탐구, 인공지능수학 등) 중 <strong>3개 이하</strong>로 수강할 수 있습니다.</li>
    </ul>
</div>
""", unsafe_allow_html=True)


# --- 학생 정보 입력 ---
st.header("1. 학생 정보 입력")
col1, col2 = st.columns(2)
with col1:
    student_name_input = st.text_input("학생 이름", key="student_name", placeholder="이름 입력")
with col2:
    student_id_input = st.text_input("학번", key="student_id", placeholder="예: 2025001")

# --- 과목 데이터 로드 ---
all_courses_list, all_courses_dict = load_courses()
if not all_courses_list:
    st.stop() # 과목 데이터 없으면 진행 불가


# --- 세션 상태 초기화 (최초 실행 시 또는 학년/학기 변경 시) ---
if 'selected_courses' not in st.session_state:
    st.session_state.selected_courses = {} # 학기별 선택 과목 ID 저장 (예: {'Y2S1': set(), 'Y2S2': set()})
    # 학교지정 과목 자동 선택
    for course in all_courses_list:
        if course.get('mandatory', False):
            semester_key = f"Y{course['year']}S{course['semester']}"
            if semester_key not in st.session_state.selected_courses:
                st.session_state.selected_courses[semester_key] = set()
            st.session_state.selected_courses[semester_key].add(course['id'])


# --- 과목 선택 UI (학년별/학기별 탭 또는 expander 사용) ---
st.header("2. 과목 선택")

YEARS = [2, 3]
SEMESTERS = [1, 2]

# 전체 선택된 과목 ID Set (유효성 검사용)
current_all_selected_ids = set()
for sem_key in st.session_state.selected_courses:
    current_all_selected_ids.update(st.session_state.selected_courses[sem_key])


tabs = st.tabs([f"{y}학년 {s}학기" for y in YEARS for s in SEMESTERS])
tab_idx = 0

validation_results_all_semesters = {}
total_hours_all_semesters = {}

for year_val in YEARS:
    for semester_val in SEMESTERS:
        with tabs[tab_idx]:
            semester_key = f"Y{year_val}S{semester_val}"
            st.subheader(f"{year_val}학년 {semester_val}학기 선택")

            courses_this_semester = get_courses_by_year_semester(all_courses_list, year_val, semester_val)
            grouped_this_semester = group_courses(courses_this_semester)

            if semester_key not in st.session_state.selected_courses:
                st.session_state.selected_courses[semester_key] = set()

            # 학기별 선택 현황 표시용 변수
            selected_in_semester_ids = st.session_state.selected_courses[semester_key]
            current_semester_hours = sum(all_courses_dict[cid]['hours'] for cid in selected_in_semester_ids if cid in all_courses_dict)

            # 유효성 검사 메시지 표시 영역
            semester_validation_messages_placeholder = st.empty()
            semester_summary_placeholder = st.empty()
            semester_summary_placeholder.info(f"현재 선택 학점: {current_semester_hours} / {REQUIRED_TOTAL_HOURS_MAP[semester_key]}")


            for group_name, group_data in grouped_this_semester.items():
                with st.expander(f"{group_name}" + (f" ({group_data['quota']}개 선택)" if not group_data['isMandatory'] and group_data['quota'] > 0 else ""), expanded=True):
                    for course in sorted(group_data['courses'], key=lambda c: c['name']): # 과목명 가나다순 정렬
                        course_id = course['id']
                        label = f"{course['name']} ({course['hours']}학점)"
                        is_mandatory_course = course.get('mandatory', False)
                        
                        # 학교지정 과목은 항상 선택됨 & 비활성화
                        is_checked = course_id in selected_in_semester_ids
                        
                        # UI에서 체크박스 상태 변경 시 selected_courses 업데이트
                        # 주의: Streamlit 위젯의 key는 고유해야 함
                        checkbox_key = f"cb_{semester_key}_{course_id}"

                        if st.checkbox(label, value=is_checked, key=checkbox_key, disabled=is_mandatory_course,
                                       help="학교지정 과목은 변경할 수 없습니다." if is_mandatory_course else ""):
                            if not is_checked: # 새로 선택된 경우
                                selected_in_semester_ids.add(course_id)
                                current_all_selected_ids.add(course_id)
                        else:
                            if is_checked and not is_mandatory_course: # 선택 해제된 경우 (필수과목 제외)
                                selected_in_semester_ids.discard(course_id)
                                current_all_selected_ids.discard(course_id)
                        
                        # 변경 즉시 반영을 위해 session_state에 다시 할당 (Streamlit 1.12+ 에서는 on_change 콜백 권장)
                        st.session_state.selected_courses[semester_key] = selected_in_semester_ids
            
            # --- 학기별 유효성 검사 (간단 버전) ---
            # (app.js의 validateSelectionsForYearSemester 함수 로직을 Python으로 변환)
            semester_messages = []
            semester_is_valid = True
            
            # 1. 그룹별 선택 개수
            for group_name, group_data in grouped_this_semester.items():
                if not group_data['isMandatory'] and group_data['quota'] > 0:
                    selected_in_group_count = sum(1 for c in group_data['courses'] if c['id'] in selected_in_semester_ids)
                    if selected_in_group_count != group_data['quota']:
                        semester_messages.append(f"❌ '{group_name}' 그룹에서 {group_data['quota']}개를 선택해야 합니다. (현재 {selected_in_group_count}개)")
                        semester_is_valid = False
                    else:
                         semester_messages.append(f"✅ '{group_name}' 그룹 선택 완료 ({selected_in_group_count}/{group_data['quota']}개)")


            # 2. 총 학점
            current_semester_hours_recalc = sum(all_courses_dict[cid]['hours'] for cid in selected_in_semester_ids if cid in all_courses_dict)
            required_hours_sem = REQUIRED_TOTAL_HOURS_MAP[semester_key]
            if current_semester_hours_recalc != required_hours_sem:
                semester_messages.append(f"❌ 총 학점이 정확히 {required_hours_sem}학점이어야 합니다. (현재 {current_semester_hours_recalc}학점)")
                semester_is_valid = False
            else:
                semester_messages.append(f"✅ 총 학점 조건 충족! ({current_semester_hours_recalc}/{required_hours_sem}학점)")

            total_hours_all_semesters[semester_key] = current_semester_hours_recalc
            validation_results_all_semesters[semester_key] = {'isValid': semester_is_valid, 'messages': semester_messages}

            # 유효성 검사 메시지 업데이트
            with semester_validation_messages_placeholder.container():
                if semester_is_valid:
                    st.success(f"{year_val}학년 {semester_val}학기 선택 조건 충족!")
                for msg in semester_messages:
                    if "❌" in msg: st.error(msg)
                    elif "✅" in msg : st.info(msg) # 성공/정보 메시지는 info로
            semester_summary_placeholder.info(f"현재 선택 학점: {current_semester_hours_recalc} / {required_hours_sem}")


        tab_idx += 1


# --- 3. 전체 유효성 검사 및 제출 ---
st.header("3. 최종 확인 및 제출")
overall_validation_placeholder = st.container() # 전체 유효성 메시지 표시 영역

# 전체 유효성 검사 로직
all_semesters_valid_flag = all(res['isValid'] for res in validation_results_all_semesters.values())
overall_messages_list = []

# 1. 미술/음악 과목 수
selected_art_music_count = sum(1 for cid in current_all_selected_ids if cid in ART_MUSIC_COURSE_IDS)
art_music_valid = (selected_art_music_count == EXACT_ART_MUSIC_SELECTION)
if not art_music_valid:
    overall_messages_list.append(f"❌ 미술/음악 관련 과목 중 정확히 {EXACT_ART_MUSIC_SELECTION}개를 선택해야 합니다. (현재 {selected_art_music_count}개)")
else:
    overall_messages_list.append(f"✅ 미술/음악 과목 선택 조건 충족 ({selected_art_music_count}/{EXACT_ART_MUSIC_SELECTION}개)")


# 2. 국영수 과목 수
selected_kes_count = sum(1 for cid in current_all_selected_ids if cid in KES_MAX_COURSE_IDS)
kes_valid = (selected_kes_count <= MAX_KES_SELECTION)
if not kes_valid:
    overall_messages_list.append(f"❌ 지정 국영수 관련 과목 중 {MAX_KES_SELECTION}개 이하로 선택해야 합니다. (현재 {selected_kes_count}개)")
else:
    overall_messages_list.append(f"✅ 국영수 과목 선택 조건 충족 (최대 {MAX_KES_SELECTION}개, 현재 {selected_kes_count}개)")

# 3. 중복 과목명 검사 (다른 학기에 동일 과목명 선택 불가 - 기존 app.js 로직과 유사)
duplicate_course_error = None
selected_courses_details_all = [all_courses_dict[cid] for cid in current_all_selected_ids if cid in all_courses_dict]
course_name_semester_map = {}
for course_detail in selected_courses_details_all:
    if course_detail['name'] not in course_name_semester_map:
        course_name_semester_map[course_detail['name']] = set()
    course_name_semester_map[course_detail['name']].add(course_detail['semester']) # 학기(1 또는 2)만 비교

for course_name, semesters_set in course_name_semester_map.items():
    if len(semesters_set) > 1: # 같은 과목명이 서로 다른 학기(1학기 vs 2학기)에 선택된 경우
        selected_offerings = [f"{c['year']}학년 {c['semester']}학기" for c in selected_courses_details_all if c['name'] == course_name]
        duplicate_course_error = f"❌ 과목 '{course_name}'은(는) 여러 학기에 중복 선택할 수 없습니다. (선택된 시점: {', '.join(selected_offerings)})"
        overall_messages_list.append(duplicate_course_error)
        break
if not duplicate_course_error and selected_courses_details_all : # 중복 없고, 선택과목 있을 때 성공 메시지 (선택적)
    overall_messages_list.append("✅ 과목명 중복 선택 조건 충족 (동일 과목명을 다른 학기에 선택하지 않음)")


# 최종 제출 가능 여부
can_submit = all_semesters_valid_flag and art_music_valid and kes_valid and not duplicate_course_error and student_name_input and student_id_input

with overall_validation_placeholder:
    if not student_name_input or not student_id_input:
        st.warning("학생 이름과 학번을 먼저 입력해주세요.")
    
    for msg in overall_messages_list:
        if "❌" in msg: st.error(msg)
        elif "✅" in msg: st.success(msg) # 전체 조건 성공은 success로

    if not all_semesters_valid_flag:
        st.error("일부 학기의 선택 조건이 충족되지 않았습니다. 각 학기 탭을 확인해주세요.")

    if can_submit:
        st.success("🎉 모든 수강신청 조건이 충족되었습니다! 아래 버튼으로 제출 및 PDF 다운로드가 가능합니다.")
    else:
        st.error("⚠️ 일부 수강신청 조건이 충족되지 않았습니다. 위의 메시지를 확인하고 수정해주세요.")


# --- 제출 버튼 및 PDF 다운로드 버튼 ---
submit_col, pdf_col = st.columns(2)

with submit_col:
    if st.button("수강신청 내역 제출", type="primary", disabled=not can_submit, use_container_width=True):
        gspread_client = get_gspread_client()
        worksheet = get_worksheet(gspread_client) # client 전달
        
        if worksheet and student_name_input and student_id_input:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            rows_to_append = []
            for cid in current_all_selected_ids:
                if cid in all_courses_dict:
                    course = all_courses_dict[cid]
                    rows_to_append.append([
                        timestamp, student_name_input, student_id_input,
                        course['id'], course['name'], course['year'], course['semester'], course['hours']
                    ])
            
            if rows_to_append:
                try:
                    worksheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
                    st.success(f"'{student_name_input}' 학생의 수강신청 내역이 Google Sheets에 성공적으로 저장되었습니다!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Google Sheets 저장 중 오류: {e}")
            else:
                st.warning("제출할 선택 과목이 없습니다.")
        elif not student_name_input or not student_id_input:
            st.error("학생 이름과 학번을 입력해야 제출할 수 있습니다.")
        else:
            st.error("Google Sheets 워크시트에 연결할 수 없습니다.")

with pdf_col:
    selected_courses_details_for_pdf_by_semester = {}
    for sem_key, id_set in st.session_state.selected_courses.items():
        selected_courses_details_for_pdf_by_semester[sem_key] = sorted(
            [all_courses_dict[cid] for cid in id_set if cid in all_courses_dict],
            key=lambda c: (c.get('mandatory', False), all_courses_dict[c['id']]['group'], c['name']), reverse=True # 학교지정, 그룹명, 과목명 순 정렬
        )

    pdf_bytes = generate_pdf_bytes(student_name_input, student_id_input, selected_courses_details_for_pdf_by_semester)
    
    st.download_button(
        label="수강신청 내역 PDF 다운로드",
        data=pdf_bytes,
        file_name=f"수강신청_{student_id_input}_{student_name_input}.pdf" if student_name_input and student_id_input else "수강신청_내역.pdf",
        mime="application/pdf",
        disabled=not can_submit, # 모든 조건 만족 시 활성화
        use_container_width=True
    )


# --- (선택 사항) 디버깅 정보 ---
# with st.expander("디버깅: 현재 선택된 과목 ID"):
# st.json( {k: list(v) for k, v in st.session_state.selected_courses.items()} )
# st.write("전체 선택 ID:", list(current_all_selected_ids))
# st.write("유효성 검사 결과:", validation_results_all_semesters)
# st.write("최종 제출 가능:", can_submit)