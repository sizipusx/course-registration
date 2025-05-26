import json
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread

json_key = json.loads(st.secrets["GOOGLE_SHEETS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(json_key, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
client = gspread.authorize(creds)
