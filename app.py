import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Title
st.title("🔍 Genealogy Search App")

# Google Drive Mount Instructions
st.markdown("""
1. Ensure your Google Drive is mounted.
2. Place all your Excel genealogy files in a single folder.
3. Enter the folder path and serial number below.
""")

# Input: Google Drive Folder Path and Serial Number
folder_path = st.text_input("📁 Enter Google Drive Folder Path:", "/content/drive/MyDrive/Penang AED DHRe")
serial_number = st.text_input("🔢 Enter Parent Serial Number to search:")

# Function to load and combine all Excel files from the folder
@st.cache_data
def load_all_data(folder_path):
    all_data = []
    for file in os.listdir(folder_path):
        if file.endswith(".xlsx") or file.endswith(".xls"):
            file_path = os.path.join(folder_path, file)
            try:
                df = pd.read_excel(file_path, sheet_name="Genealogy", engine="openpyxl")
                df["Source File"] = file
                all_data.append(df)
            except Exception as e:
                st.warning(f"⚠️ Error reading {file}: {e}")
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame()

# Load data when inputs are available
if folder_path and serial_number:
    all_data = load_all_data(folder_path)

    # Step 1: First-level search by Parent Serial Number
    filtered_df = all_data[all_data["Parent Serial No"] == serial_number]

    if filtered_df.empty:
        st.error(f"❌ No data found for serial number: {serial_number}")
    else:
        st.success(f"✅ Found {len(filtered_df)} matching records for: {serial_number}")
        st.dataframe(filtered_df[["Parent Part No", "Parent Serial No", "Part No", "Serial No"]])

        # Step 2: Look for ASI-MS-00071 in the results
        asi_00071 = filtered_df[filtered_df['Part No'] == 'ASI-MS-00071']
        if not asi_00071.empty:
            asi_00071_serial = asi_00071.iloc[0]['Serial No']

            # Step 3: Second-level search for children of ASI-MS-00071
            second_level = all_data[all_data['Parent Serial No'] == asi_00071_serial]

            asi_01550 = second_level[second_level['Part No'] == 'ASI-MS-01550']
            asi_01599 = second_level[second_level['Part No'] == 'ASI-MS-01599']

            if not asi_01550.empty:
                st.subheader("🔧 ASI-MS-01550 Details")
                st.dataframe(asi_01550[["Parent Part No", "Parent Serial No", "Part No", "Serial No"]])

            if not asi_01599.empty:
                st.subheader("🔧 ASI-MS-01599 Details")
                st.dataframe(asi_01599[["Parent Part No", "Parent Serial No", "Part No", "Serial No"]])

            if asi_01550.empty and asi_01599.empty:
                st.info("ℹ️ No ASI-MS-01550 or ASI-MS-01599 found under ASI-MS-00071.")
        else:
            st.warning("⚠️ ASI-MS-00071 not found in the initial search.")
