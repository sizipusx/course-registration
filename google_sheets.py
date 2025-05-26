import gspread
from oauth2client.service_account import ServiceAccountCredentials

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SPREADSHEET_KEY = "여기에-문서-고유-키-삽입"

def append_to_sheet(name, student_id, courses):
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_KEY).sheet1

    for c in courses:
        row = [name, student_id, c["year"], c["semester"], c["name"], c["hours"], c["group"]]
        sheet.append_row(row)
