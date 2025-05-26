# 로컬에서 실행하여 변환된 문자열 만들기 (한 줄로 붙여넣기 용)
import json

with open("course-registration-461012-cccf9c22b64b.json", "r", encoding="utf-8") as f:
    raw = json.load(f)
    raw["private_key"] = raw["private_key"].replace("\n", "\\n")
    print("GOOGLE_SHEETS_JSON = '''")
    print(json.dumps(raw, indent=2))
    print("'''")
