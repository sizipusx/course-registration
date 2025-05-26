from fpdf import FPDF
import os

def generate_pdf(name, student_id, courses):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('Nanum', '', 'NanumSquare_acR.ttf', uni=True)
    pdf.set_font('Nanum', '', 14)

    pdf.cell(0, 10, "정현고 수강신청 내역", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font('Nanum', '', 12)
    pdf.cell(0, 10, f"이름: {name} / 학번: {student_id}", ln=True)
    pdf.ln(5)

    pdf.set_font('Nanum', '', 11)
    headers = ["학년", "학기", "과목명", "학점", "그룹"]
    col_widths = [20, 20, 80, 20, 40]
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 10, h, border=1, align='C')
    pdf.ln()

    total_hours = 0
    for c in courses:
        row = [str(c["year"]), str(c["semester"]), c["name"], str(c["hours"]), c["group"]]
        for i, cell in enumerate(row):
            pdf.cell(col_widths[i], 10, cell, border=1)
        pdf.ln()
        total_hours += c["hours"]

    pdf.ln(5)
    pdf.set_font('Nanum', '', 12)
    pdf.cell(0, 10, f"총 학점: {total_hours}", ln=True)

    filename = f"{student_id}_{name}_수강신청.pdf"
    pdf.output(filename)
    return filename
