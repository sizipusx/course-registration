# generate_secret_format.py
import json

with open("course-registration-461012-cccf9c22b64b.json", encoding="utf-8") as f:
    creds = json.load(f)

# 줄바꿈 이스케이프
creds["private_key"] = creds["private_key"].replace("\n", "\\n")

# 전체를 TOML용 스트링으로 출력
print("GOOGLE_SHEETS_JSON = '''")
print(json.dumps(creds, indent=2))
print("'''")
