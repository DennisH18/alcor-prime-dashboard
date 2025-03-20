import streamlit as st
import pandas as pd
import datetime as dt
import calendar
import services.helper as helper
import streamlit.components.v1 as components

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    .block-container {
        padding: 3rem 2rem 2rem 2rem;
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
            background-color: #4CAF50;
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

code_category_dict = {
    "4301001000": "Music",
    "4301002000": "Sermon",
    "4301003000": "Book",
    "4301005000": "Apparel & Accessories",
    "4301007000": "Sales Consignment",
    "4702000000": "Other",
    "4500000000": "Sales discount",
    "4800000000": "Sales Return",
    "5101000000": "Music",
    "5102000000": "Sermon",
    "5103000000": "Book",
    "5105000000": "Apparel & Accessories",
    "5300000000": "Consignment",
    "5701000000": "Royalty Digital",
    "5702000000": "Royalty Music",
    "5703000000": "Royalty kotbah",
    "5704000000": "Royalty Others",
    "5600000000": "Others",
    "6201001010": "Basic Salary",
    "6201001020": "Meal Allowance",
    "6201001030": "Transportation Allowance",
    "6201001040": "Communication Allowance",
    "6201001090": "Positional Allowance",
    "6201001200": "Over Time",
    "6201001070": "Service Charge",
    "6201003001": "Jamsostek (JKK+JKM/Social Security Insurance)",
    "6201003010": "BPJS Kesehatan",
    "6201007042": "Insurance",
    "6201007045": "Outpatient",
    "6201007040": "T. Kesehatan",
    "6201001300": "Traveling Allowance",
    "6201009000": "Retirement Fee",
    "6213000000": "Retirement Benefit",
    "6203007000": "Place Accommodation",
    "6201001050": "THR & Bonus",
    "6201001060": "Incentive",
    "6206000104": "Crew Casual",
    "6206000101": "Banquet Casual",
    "6206000102": "Cleaning Service Casual",
    "6206000103": "Sound Engineer Casual",
    "6206000105": "Engineering Casual",
    "6206000106": "Security Casual",
    "6206000107": "Usher Casual",
    "6206000108": "Catering Casual",
    "6201001100": "Freelance",
    "6206000200": "Volunteers",
    "6205000000": "Outsourcing / Workers Expenses",
    "6101001000": "Printing Media",
    "6101002000": "Electronic Media",
    "6101005000": "Special Event",
    "6101008000": "Sales Promotion",
    "6102000001": "Commission",
    "6203001000": "Water",
    "6203002000": "Electricity",
    "6203002100": "Gas",
    "6203003000": "Telephone & Faximile",
    "6203004000": "Internet & Hosting",
    "6203006010": "Stationary & Supplies",
    "6203006020": "Computer Supplies",
    "6203006030": "Household Supplies",
    "6203006040": "Hardware Equipment Supplies",
    "6203005000": "Cleaning Materials",
    "6203006060": "Department Supplies",
    "6203006080": "Stage & Decoration Supplies",
    "6203013090": "Rental - Venue",
    "6203013080": "Rental - Equipment",
    "6203013010": "Rental - Office",
    "6203013020": "Rental - Warehouse",
    "6203013030": "Rental - Photocopy",
    "6203013040": "Rental - Vehicle",
    "6203013060": "Rental - Store",
    "6206000500": "Rental - Banquet Equipment",
    "6203013070": "Rental - Rehearsal & Studio",
    "6206000501": "Rental - Catering Equipment",
    "6203021000": "Gift & Condolences",
    "6203010000": "Consumption",
    "6203018000": "Entertainments",
    "6203028000": "Consultant Fee",
    "6203023010": "Traveling National",
    "6203023020": "Traveling International",
    "6206000801": "Complimentary Banquet",
    "6206000802": "Complimentary Food and Beverage",
    "6206000803": "Complimentary Other",
    "6203025001": "Training & Seminar National",
    "6203025002": "Training & Seminar International",
    "6203026010": "Bensin",
    "6203026020": "Tol & Parkir",
    "6203026030": "Kendaraan Umum",
    "6203026040": "Transportation Expense",
    "6203008000": "Expedition",
    "6203006050": "Shop Supplies",
    "6203009000": "Printing & Photocopy",
    "6203015000": "Uniform",
    "6203016000": "Retribution",
    "6206000700": "Laundry",
    "6208000000": "Legal & Permit",
    "6211000000": "Mailing & Stamp Expense",
    "6202003100": "PPE Tax Expenses",
    "6202003200": "PPE Insurance Expense",
    "6203017000": "Subscriptions & Software Program",
    "6203027000": "Recruitment Fee",
    "6206000300": "Production Expense",
    "6210000000": "Management Fee",
    "6209000000": "Bad Debt Expense",
    "7103000000": "Inventory Gain/Loss",
    "6202001010": "Building",
    "6202001020": "Vehicles",
    "6202001030": "Equipment",
    "6202001040": "Computer",
    "6202001050": "Software",
    "6202002102": "Warehouse",
    "6202002103": "Office",
    "6202002201": "Vehicles I",
    "6202002202": "Vehicles II",
    "6202002300": "Deprec Exp - Furniture & Fixture",
    "6202002401": "Equipment - Office",
    "6202002402": "Equipment - Computer",
    "6202002403": "Equipment - Building",
    "6202002405": "Equipment - Sound System",
    "6202002406": "Equipment - Communication Equipment",
    "6202002407": "Equipment - MultiMedia",
    "6202002408": "Equipment - Production",
    "6202002411": "Equipment - Engineering",
    "6202002412": "Equipment - Lighting",
    "6202002413": "Equipment - Store",
    "6202002512": "Software",
    "6202002700": "Deprec - Leasehold Improvement",
    "7101000000": "Interest Income",
    "7102000000": "Foreign Exchange Gain/Loss",
    "7104000000": "Gain/Loss on Disposal of Fixed Assets",
    "7105000000": "Miscellaneous Income",
    "7106000000": "Gain/Loss on Investasi",
    "7201000000": "Interest Expense",
    "7202000000": "Bank Administration & Wire Expense",
    "7203000000": "Merchant Fees",
    "7204000000": "Miscellaneous Expense",
    "7205000000": "Company Gathering",
    "8100000000": "Current Tax",
    "8200000000": "Deferred Tax",
    "8300000000": "Miscellaneous Tax",
    "Total dari Beban Operasional": None,
    "Laba Operasional": None,
    "Total dari Pendapatan (Beban Lain-lain)": None,
    "Laba (Rugi)": None,
    "Total dari Beban Pokok Pendapatan": None,
    "Laba Kotor": None,
    "Total dari Pendapatan": None
}


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

                    df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
                    df.iloc[:, 2] = pd.to_numeric(df.iloc[:, 2], errors="coerce")

                    filtered_df = df[df.iloc[:, 0].isin(code_category_dict.keys())][[df.columns[0], df.columns[2]]]
                    filtered_df.columns = ["Code", "Value"]
                    
                    results[key] = {
                        "filtered_data": filtered_df.to_dict(orient="records"),
                        "pnl_data": filtered_df.to_dict(orient="records"),
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
            amount = float(item["Value"] or 0)

            if code not in pnl[company][month]:
                pnl[company][month][code] = 0
            pnl[company][month][code] += amount

    pnl_table_style = """
        <style>
            .table-container {
                overflow-y: auto;
                border: 1px solid #ddd;
                box-shadow: 2px 2px 12px rgba(0,0,0,0.1);
                font-family: Arial, sans-serif;
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
                background-color: #4CAF50;
                color: white;
                position: sticky;
                top: 0;
            }
            tr:nth-child(even) { background-color: #f2f2f2; }
            tr:hover { background-color: #ddd; }
        </style>
    """

    for company in companies:
        table_rows = ""
        for month in all_months:
            if month in pnl[company]:
                for code, amount in pnl[company][month].items():
                    table_rows += f"""<tr>
                    <td>{month}</td>
                    <td>{code}</td>
                    <td>{code_category_dict[code]}</td>
                    <td>{amount:,.2f}</td>
                    </tr>
                    """

        table_html = f"""
            {pnl_table_style}
            <h2 style='font-family: Arial, sans-serif;'>{company} Cash Flow</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Month</th>
                            <th>COA</th>
                            <th>Description</th>
                            <th>Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
        """

        components.html(table_html, height=1100, scrolling=True)

    return


def main():
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