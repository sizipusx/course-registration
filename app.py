import streamlit as st
import json
from pdf_utils import generate_pdf
from google_sheets import append_to_sheet

# 과목 데이터 로드
with open("courses.json", encoding="utf-8") as f:
    courses = json.load(f)

def get_courses(year, semester):
    return [c for c in courses if c["year"] == year and c["semester"] == semester]

st.set_page_config(page_title="정현고 수강신청", layout="wide")
st.title("정현고 수강신청")

# ✅ secrets 확인용 디버그 코드
st.subheader("Secrets 확인용 출력")
st.code(st.secrets["GOOGLE_SHEETS_JSON"])

with st.form("course_form"):
    name = st.text_input("학생 이름")
    student_id = st.text_input("학번")
    selected_courses = []

    for year in [2, 3]:
        for semester in [1, 2]:
            st.subheader(f"{year}학년 {semester}학기")
            sem_courses = get_courses(year, semester)
            mandatory = [c for c in sem_courses if c["mandatory"]]
            electives = {}
            for c in sem_courses:
                if not c["mandatory"]:
                    electives.setdefault(c["group"], []).append(c)

            st.markdown("**필수 과목**")
            for c in mandatory:
                st.checkbox(f"{c['name']} ({c['hours']}학점)", value=True, disabled=True)
                selected_courses.append(c)

            st.markdown("**선택 과목**")
            for group, group_courses in electives.items():
                quota = group_courses[0]["groupQuota"] or 1
                selections = st.multiselect(
                    f"{group} (최대 {quota}개)", 
                    [f"{c['id']} - {c['name']}" for c in group_courses],
                    max_selections=quota,
                    key=f"{year}_{semester}_{group}"
                )
                for item in selections:
                    course_id = item.split(" - ")[0]
                    course = next(c for c in group_courses if c["id"] == course_id)
                    selected_courses.append(course)

    submitted = st.form_submit_button("제출")

if submitted:
    if not name or not student_id:
        st.error("이름과 학번을 입력해주세요.")
    else:
        append_to_sheet(name, student_id, selected_courses)
        pdf_path = generate_pdf(name, student_id, selected_courses)
        with open(pdf_path, "rb") as f:
            st.download_button("PDF 다운로드", f, file_name=pdf_path)
        st.success("수강신청 완료! PDF 다운로드 가능")
