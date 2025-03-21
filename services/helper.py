import streamlit as st
import pandas as pd
import calendar
import streamlit.components.v1 as components
import dropbox
from io import BytesIO
import dropbox
import streamlit as st
import services.dropboxAuth as dropboxAuth


access_token = dropboxAuth.get_access_token()
dbx = dropbox.Dropbox(access_token)


@st.cache_data
def fetch_all_data():
    data_store = {}
    try:
        for entry in dbx.files_list_folder("").entries:
            if isinstance(entry, dropbox.files.FolderMetadata):
                company = entry.name
                data_store[company] = {}

                try:
                    year_entries = dbx.files_list_folder(f"/{company}").entries
                except dropbox.exceptions.ApiError as e:
                    st.warning(f"Skipping {company} due to API error: {e}")
                    continue

                for year_entry in year_entries:
                    if isinstance(year_entry, dropbox.files.FolderMetadata) and year_entry.name.isdigit():
                        year = int(year_entry.name)
                        data_store[company][year] = {}

                        try:
                            file_entries = dbx.files_list_folder(f"/{company}/{year}").entries
                        except dropbox.exceptions.ApiError as e:
                            st.warning(f"Skipping {company}/{year} due to API error: {e}")
                            continue

                        for file_entry in file_entries:
                            if isinstance(file_entry, dropbox.files.FileMetadata) and file_entry.name.endswith(".xlsx"):
                                file_path = f"/{company}/{year}/{file_entry.name}"

                                try:
                                    _, res = dbx.files_download(file_path)
                                    xls = pd.ExcelFile(BytesIO(res.content))

                                    if "Management Report" in file_entry.name:
                                        df = pd.read_excel(xls, sheet_name="PL", engine="openpyxl")
                                        data_store[company][year][file_entry.name] = df
                                    elif "Budget" in file_entry.name:        
                                        df = pd.read_excel(xls, sheet_name=company, engine="openpyxl")
                                        data_store[company][year][file_entry.name] = df
                                    elif "JPCC vs Others" in file_entry.name:
                                        jpcc_sheet_name = next((s for s in xls.sheet_names if "jpcc vs others" in s.lower()), None)
                                        if jpcc_sheet_name:
                                            df = pd.read_excel(xls, sheet_name=jpcc_sheet_name, engine="openpyxl")
                                            data_store[company][year][file_entry.name] = df

                                except Exception as e:
                                    st.error(f"Error reading {file_entry.name}: {e}")

    except dropbox.exceptions.ApiError as e:
        st.error(f"Dropbox API error: {e}")

    return data_store


@st.cache_data
def get_available_months(data, companies, selected_year):
    months = set()

    for key in data.keys(): 
        parts = key.split("_")
        if len(parts) == 3:
            company, month, year = parts
            if company in companies and year == str(selected_year):
                months.add(month)

    return sorted(months, key=lambda m: list(calendar.month_abbr).index(m)) if months else []


@st.cache_data
def get_available_companies_and_years(data_store):
    companies = sorted(data_store.keys())
    years = sorted({year for company in data_store for year in data_store[company]})
    return companies, years[1:] if len(years) > 1 else []