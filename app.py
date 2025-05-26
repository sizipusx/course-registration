import streamlit as st
import json
from google_sheets import append_to_sheet
from pdf_utils import generate_pdf

# 앱 설정
st.set_page_config(page_title="정현고 수강신청", layout="wide")
st.title("정현고 수강신청 시스템")

# 과목 데이터 불러오기
with open("courses.json", encoding="utf-8") as f:
    courses = json.load(f)

def get_courses(year, semester):
    return [c for c in courses if c["year"] == year and c["semester"] == semester]

# 사용자 입력
with st.form("course_form"):
    name = st.text_input("🧑 학생 이름", max_chars=20)
    student_id = st.text_input("🎓 학번", max_chars=10)
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

            # 필수 과목
            st.markdown("**✅ 필수 과목 (자동 선택)**")
            for c in mandatory:
                st.checkbox(f"{c['name']} ({c['hours']}학점)", value=True, disabled=True)
                selected_courses.append(c)

            # 선택 과목
            st.markdown("**📚 선택 과목**")
            for group, group_courses in electives.items():
                quota = group_courses[0]["groupQuota"] or 1
                options = [f"{c['id']} - {c['name']}" for c in group_courses]
                selections = st.multiselect(
                    f"{group} (최대 {quota}개 선택)", options, max_selections=quota,
                    key=f"{year}_{semester}_{group}"
                )
                for sel in selections:
                    course_id = sel.split(" - ")[0]
                    course = next(c for c in group_courses if c["id"] == course_id)
                    selected_courses.append(course)

    # 제출 버튼
    submitted = st.form_submit_button("📩 수강신청 제출")

if submitted:
    if not name or not student_id:
        st.error("이름과 학번을 모두 입력해야 제출할 수 있습니다.")
    elif len(selected_courses) == 0:
        st.warning("최소 한 과목 이상을 선택해야 합니다.")
    else:
        try:
            append_to_sheet(name, student_id, selected_courses)
            pdf_file = generate_pdf(name, student_id, selected_courses)
            with open(pdf_file, "rb") as f:
                st.success("✅ 수강신청 완료! PDF 파일을 다운로드하세요.")
                st.download_button(
                    label="📄 수강신청 내역 PDF 다운로드",
                    data=f,
                    file_name=pdf_file,
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
