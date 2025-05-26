import streamlit as st
import json

try:
    json_key = json.loads(st.secrets["GOOGLE_SHEETS_JSON"])
    st.success("GOOGLE_SHEETS_JSON 파싱 성공 ✅")
except Exception as e:
    st.error(f"GOOGLE_SHEETS_JSON 파싱 실패 ❌: {e}")
