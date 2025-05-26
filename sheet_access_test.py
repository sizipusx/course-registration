import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. 접근 권한(Scope) 정의
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 2. credentials.json 로드
import os

base_dir = os.path.dirname(__file__)
json_path = os.path.join(base_dir, "course-registration-461012-cccf9c22b64b.json")

creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)

# 3. 인증 클라이언트 생성
client = gspread.authorize(creds)

# 4. 스프레드시트 접근 (문서 키 사용)
sheet = client.open_by_key("1veluylbgXdoQ1ZUz7_SnCByUS3PQPJPU1HpDKO2YEGE").sheet1

# 5. 데이터 쓰기 예시
sheet.append_row(["홍길동", "23001", "2", "1", "문학", "4", "학교지정"])
