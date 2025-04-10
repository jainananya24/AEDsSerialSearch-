import streamlit as st
import pandas as pd
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from io import BytesIO
import openpyxl

# Google Drive Authentication
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

drive_service = build('drive', 'v3', credentials=credentials)

# Search all Excel files in a specific folder
FOLDER_ID = 'Penang AED DHR'

@st.cache_data
def list_excel_files_from_drive(folder_id):
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'",
        fields="files(id, name)").execute()
    return results.get('files', [])

@st.cache_data
def read_excel_from_drive(file_id):
    request = drive_service.files().get_media(fileId=file_id)
    file_data = request.execute()
    df = pd.read_excel(BytesIO(file_data), sheet_name='Genealogy')
    return df

st.title("Genealogy Lookup Tool 🔍")
serial_input = st.text_input("Enter Serial Number")

if serial_input:
    all_files = list_excel_files_from_drive(FOLDER_ID)
    result_data = []

    for file in all_files:
        try:
            df = read_excel_from_drive(file['id'])
            match = df[df['Parent Serial No'] == serial_input]
            if not match.empty:
                result_data.append((file['name'], match))
        except Exception as e:
            st.warning(f"Failed to read {file['name']}: {e}")

    if result_data:
        for filename, df_match in result_data:
            st.subheader(f"Results from: {filename}")
            st.dataframe(df_match[['Parent Part No', 'Parent Serial No', 'Part No', 'Serial No']])
    else:
        st.warning("No matches found in any file.")
