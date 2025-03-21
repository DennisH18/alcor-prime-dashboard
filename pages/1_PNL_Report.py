import streamlit as st
import pandas as pd
import datetime as dt
import calendar
import streamlit.components.v1 as components

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from bs4 import BeautifulSoup

import services.helper as helper
import services.styles as styles
from services.data import account_categories
import services.auth as auth

styles.style_page()

st.markdown(
    """
    <style>
    .block-container {
        padding: 3rem;
    }
    h4, h5, p, div {
        margin: 0; 
        padding: 0;
    }
    .stMarkdown {
        margin: -5px;
    }
    [data-testid='stHeaderActionElements'] {
    display: none;
    }
    </style>
""",
    unsafe_allow_html=True,
)

pnl_table_style = """ 
    <style>
        .table-container {{
            overflow-y: auto;
            height: 500px;
            border: 1px solid #ddd;
            box-shadow: 2px 2px 12px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            color: white;
            position: sticky;
            top: 0;
        }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        tr:hover {{ background-color: #ddd; }}
    </style>
"""

def to_camel_case(month):
    return ''.join(word.capitalize() for word in month.lower().split())

@st.cache_data
def prepare_pnl_data(data_store, companies, selected_year):
    results = {}
    month_abbr = set(calendar.month_abbr[1:])

    for company in companies:
        if selected_year not in data_store.get(company, {}):
            continue
        years_to_check = [selected_year]
        prev_year = selected_year - 1
        if prev_year in data_store.get(company, {}):
            years_to_check.append(prev_year)
        
        for year in years_to_check:
            for file_name, df in data_store[company][year].items():
                if "Management Report" in file_name:
                    month_str = next((month for month in month_abbr if month in file_name), None)
                    if not month_str:
                        continue

                    key = f"{company}_{month_str}_{year}"

                    df.iloc[:, 2] = pd.to_numeric(df.iloc[:, 2], errors="coerce")
                    df.columns = ["Code", "Description", "Value"]
                    df = df[df["Value"].notna()]
                    df.fillna("-", inplace=True)

                    results[key] = {
                        "filtered_data": df.to_dict(orient="records"),
                    }
            
    return results


def display_pnl(data):
    companies = sorted({key.split("_")[0] for key in data.keys()})
    all_months = sorted(
        {key.split("_")[1] for key in data.keys()},
        key=lambda x: list(calendar.month_abbr).index(x)
    )
    
    pnl = {comp: {} for comp in companies}

    for key, value in data.items():
        company, month = key.split("_")[0], key.split("_")[1]
        if company not in pnl:
            pnl[company] = {}
        if month not in pnl[company]:
            pnl[company][month] = {}

        for item in value.get("filtered_data", []):
            code = item["Code"]
            description = item["Description"]
            amount = float(item["Value"] or 0)

            if code not in pnl[company][month]:
                pnl[company][month][code] = {"description": description, "amount": 0}
            pnl[company][month][code]["amount"] += amount

    pnl_table_style = """
        <style>
            .table-container {
                overflow-x: auto;
                border: 1px solid #ddd;
                box-shadow: 2px 2px 12px rgba(0,0,0,0.1);
                font-family: Arial, sans-serif;
                white-space: nowrap;
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: gray;
                color: white;
                position: sticky;
                top: 0;
            }
            tr:nth-child(even) { background-color: #f2f2f2; }
            tr:hover { background-color: #ddd; }
        </style>
    """

    for company in companies:
        table_headers = "<th>COA</th><th>Description</th>" + "".join(f"<th>{month}</th>" for month in all_months)
        table_rows = ""

        all_codes = set()
        for month in all_months:
            if month in pnl[company]:
                all_codes.update(pnl[company][month].keys())

        for code in sorted(all_codes, key=str):

            for month in all_months:
                if month in pnl[company] and code in pnl[company][month]:
                    description = pnl[company][month][code]["description"]
                    break

            row_values = "".join(f"<td>{pnl[company].get(month, {}).get(code, {'amount': 0})['amount']:,.2f}</td>" for month in all_months)

            table_rows += f"""<tr>
                <td>{code}</td>
                <td>{description}</td>
                {row_values}
            </tr>"""

        table_html = f"""
            {pnl_table_style}
            <h2 style='font-family: Arial, sans-serif;'>{company} Cash Flow</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            {table_headers}
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
        """

        components.html(table_html, height=1500, scrolling=True)

    return


def save_html_to_excel(table_html, output_filename="PNL_Report.xlsx"):
    soup = BeautifulSoup(table_html, "html.parser")

    headers = [th.get_text(strip=True) for th in soup.find_all("th")]

    rows = []
    for row in soup.find_all("tr")[1:]:
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if cells:
            rows.append(cells)

    df = pd.DataFrame(rows, columns=headers)

    df.to_excel(output_filename, index=False)


def main():   

    auth.login()

    if not st.session_state.authenticated:
        return
    
    data_store = helper.fetch_all_data()    
    available_companies, available_years = helper.get_available_companies_and_years(data_store)
    
    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        st.markdown("<h3>PNL Report</h3>", unsafe_allow_html=True)
    with col2:
        companies = st.multiselect("Select PT (Default = All)", available_companies)
        if not companies:
            companies = available_companies
    with col3:
        current_year = dt.date.today().year
        selected_year = st.selectbox("Select Year", available_years, index=available_years.index(current_year) if current_year in available_years else 0)

    data = prepare_pnl_data(data_store, companies, selected_year)

    display_pnl(data)


if __name__ == "__main__":
    main()