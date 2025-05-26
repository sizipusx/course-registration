import json

with open("credentials.json", encoding="utf-8") as f:
    creds = json.load(f)

# 핵심: private_key 줄바꿈 이스케이프
creds["private_key"] = creds["private_key"].replace("\n", "\\n")

# secrets.toml 형식 출력
print("GOOGLE_SHEETS_JSON = '''")
print(json.dumps(creds, indent=2))
print("'''")
