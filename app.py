import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO
import os
import tempfile
import zipfile

# --- Setup credentials from secrets ---
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["google_drive"],
    scopes=["https://www.googleapis.com/auth/drive"]
)

# --- Google Drive API setup ---
drive_service = build('drive', 'v3', credentials=credentials)

# --- Set your folder ID (from the shared Drive folder URL) ---
FOLDER_ID = "https://drive.google.com/drive/folders/1DamS7q05EoXoco3qqwTozTlSBJRkQavL?usp=drive_link"  # <-- Replace this with your actual folder ID

# --- Function to list all Excel files in the folder ---
def list_excel_files(folder_id):
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'",
        fields="files(id, name)"
    ).execute()
    return results.get('files', [])

# --- Function to download and read Excel file ---
def read_excel_from_drive(file_id, file_name):
    try:
        request = drive_service.files().get_media(fileId=file_id)
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        fh.seek(0)
        df = pd.read_excel(fh, engine='openpyxl')
        return df
    except Exception as e:
        st.warning(f"Error reading {file_name}: {e}")
        return pd.DataFrame()

# --- Load all Excel files into a single DataFrame ---
@st.cache_data(show_spinner=True)
def load_all_data():
    all_files = list_excel_files(FOLDER_ID)
    all_data = []
    for file in all_files:
        df = read_excel_from_drive(file["id"], file["name"])
        if not df.empty:
            df['Source File'] = file["name"]
            all_data.append(df)
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame()

# --- Streamlit App UI ---
st.title("Genealogy Search App")
st.markdown("Enter a serial number to look up details from your synchronized Google Drive Excel files.")

# Load data
data = load_all_data()

# Serial search
serial_input = st.text_input("Enter Serial Number", "")
if serial_input and not data.empty:
    result = data[data.apply(lambda row: serial_input.lower() in row.astype(str).str.lower().values, axis=1)]
    if not result.empty:
        st.success(f"Found {len(result)} matching rows.")
        st.dataframe(result)
    else:
        st.warning("No matching serial number found.")

# Rerun option
if st.button("Search another serial"):
    st.experimental_rerun()
