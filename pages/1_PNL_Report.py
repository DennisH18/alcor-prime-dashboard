import streamlit as st
import pandas as pd
import datetime as dt
import calendar

import services.helper as helper
import services.styles as styles
from services.data import pnl_account_categories_dict
import services.auth as auth

styles.style_page()
account_categories = helper.transform_to_category_codes(pnl_account_categories_dict)


def to_camel_case(month):
    return "".join(word.capitalize() for word in month.lower().split())


@st.cache_data
def prepare_pnl_data(data_store, companies, selected_year):
    results = {}
    month_abbr = set(calendar.month_abbr[1:])

    for company in companies:
        if selected_year not in data_store.get(company, {}):
            continue

        years_to_check = [selected_year, selected_year - 1]

        for year in years_to_check:
            if year not in data_store.get(company, {}):
                continue

            for file_name, df in data_store[company][year].items():

                if "Management Report" in file_name:
                    month_str = next(
                        (month for month in month_abbr if month in file_name), None
                    )
                    if not month_str:
                        continue

                    key = f"{company}_{month_str}_{year}"

                    df.iloc[:, 2] = pd.to_numeric(df.iloc[:, 2], errors="coerce")
                    df.columns = ["COA", "Description", "Value"]
                    df["COA"] = pd.to_numeric(
                        df["COA"], errors="coerce", downcast="integer"
                    )

                    financial_data = []

                    for codes in account_categories.values():
                        if codes is not None:
                            category_data = df[df["COA"].isin(codes)]
                            if not category_data.empty:
                                for _, row in category_data.iterrows():
                                    financial_data.append(
                                        {"COA": row["COA"], "Value": row["Value"]}
                                    )

                    if key not in results:
                        results[key] = {"filtered_data": [], "budget": []}
                    results[key]["filtered_data"] = financial_data

                elif "Budget" in file_name:
                    header_row_index = 6
                    df.columns = df.iloc[header_row_index]
                    duplicates = df.columns.duplicated(keep=False)
                    df.columns = [
                        f"{col}_{i}" if duplicates[i] else col
                        for i, col in enumerate(df.columns)
                    ]
                    df = df.iloc[header_row_index + 1 :].reset_index(drop=True)
                    month_cols = [
                        col
                        for col in df.columns.astype(str)
                        if "nan" not in col.lower()
                    ]
                    df = df[["nan_0"] + month_cols]
                    df = df.dropna(subset=["nan_0"])

                    for month in df.columns[1:]:
                        month_str = str(month).strip()

                        if not month_str or month_str.lower() == "nan":
                            continue

                        key = f"{company}_{to_camel_case(month_str.split()[0])}_{year}"
                        budget_data = []

                        for codes in account_categories.values():
                            if codes is not None:
                                category_data = df[df["nan_0"].isin(codes)]
                                if not category_data.empty:
                                    for _, row in category_data.iterrows():
                                        budget_data.append(
                                            {"COA": row["nan_0"], "Value": row[month]}
                                        )

                        if key not in results:
                            results[key] = {"filtered_data": [], "budget": []}
                        results[key]["budget"] = budget_data

    return results


def transform_data(data, selected_year, selected_month):

    companies = sorted(set(key.split("_")[0] for key in data.keys()))
    month_order = list(calendar.month_abbr)[1:]
    company_html_dict = {}

    for company in companies:

        company_data = {
            key: value for key, value in data.items() if key.startswith(company)
        }

        key = f"{company}_{selected_month}_{selected_year}"
        table_data = []
        for company_month, data_dict in company_data.items():

            company, month, year = company_month.split("_")
            if month_order.index(month) > month_order.index(selected_month):
                continue

            year = int(year)

            for record in data_dict.get("filtered_data", []):
                table_data.append(
                    {
                        "Company": company,
                        "Month": month,
                        "Year": year,
                        "COA": record["COA"],
                        "Value": record["Value"],
                        "Type": "Actual",
                    }
                )
            for record in data_dict.get("budget", []):
                table_data.append(
                    {
                        "Company": company,
                        "Month": month,
                        "Year": year,
                        "COA": record["COA"],
                        "Value": record["Value"],
                        "Type": "Budget",
                    }
                )

        df = pd.DataFrame(table_data)
        df["Month"] = pd.Categorical(df["Month"], categories=month_order, ordered=True)

        df_pivot = df.pivot_table(
            index=["COA"],
            columns=["Month", "Year", "Type"],
            values="Value",
        ).reset_index()

        def sort_key(col):
            if isinstance(col, tuple) and len(col) == 3:
                type_order = {"Actual": 0, "Budget": 1}
                return (
                    (
                        month_order.index(col[0])
                        if col[0] in month_order
                        else float("inf")
                    ),
                    col[1],
                    type_order.get(col[2], 99),
                )
            return (float("inf"), float("inf"), float("inf"))

        code_col = df_pivot.columns[0]
        multi_cols = df_pivot.columns[1:]
        sorted_multi_cols = sorted(multi_cols.tolist(), key=sort_key)
        df_pivot = df_pivot[[code_col] + sorted_multi_cols]

        def rename_col(col):
            if isinstance(col, tuple) and len(col) == 3:
                return f"{col[2]} {col[0]} {col[1]}".strip()
            return col

        df_pivot.columns = ["COA"] + [rename_col(col) for col in df_pivot.columns[1:]]

        pnl_data = []
        for category, subcategories in pnl_account_categories_dict.items():
            for subcategory, codes in subcategories.items():
                for code, desc in codes.items():
                    pnl_data.append([category, subcategory, code, desc])
        df_categories = pd.DataFrame(
            pnl_data, columns=["Main Category", "Subcategory", "COA", "Description"]
        )

        df_final = df_categories.merge(df_pivot, on="COA", how="left")
        df_final = df_final[(df_final.iloc[:, 4:] != 0).any(axis=1)]
        df_final = df_final.dropna(subset=df_final.columns[4:], how="all")

        month_columns = [
            col
            for col in df_final.columns
            if any(month in col for month in month_order)
        ]

        total_revenue = df_final[df_final["Main Category"] == "REVENUE"][
            month_columns
        ].sum()
        total_cogs = df_final[df_final["Main Category"] == "COGS"][month_columns].sum()
        total_expenses = df_final[
            df_final["Main Category"].isin(
                [
                    "DEPRECIATION & MAINTENANCE",
                    "OPERATIONAL EXPENSES",
                    "HUMAN RESOURCES",
                ]
            )
        ][month_columns].sum()
        other_inc = df_final[df_final["Main Category"] == "OTHER INCOME / EXPENSES"][
            month_columns
        ].sum()

        gross_profit = total_revenue - total_cogs
        net_profit = gross_profit - total_expenses + other_inc

        def create_summary_row(category, values):
            row = pd.DataFrame(
                {
                    "Main Category": [category],
                    "Subcategory": [""],
                    "COA": [""],
                    "Description": [""],
                }
            )
            for col in month_columns:
                row[col] = [values[col]]
            return row

        gross_profit_row = create_summary_row("GROSS PROFIT", gross_profit)
        total_expenses_row = create_summary_row("TOTAL EXPENSES", total_expenses)
        net_profit_row = create_summary_row("NET PROFIT", net_profit)

        df_final = pd.concat(
            [df_final, gross_profit_row, total_expenses_row, net_profit_row],
            ignore_index=True,
        )

        df_final["Main Category"] = pd.Categorical(
            df_final["Main Category"],
            categories=account_categories.keys(),
            ordered=True,
        )

        df_final = df_final.sort_values(by=["Main Category"], ascending=[True])

        new_columns = {}

        for month in month_order:
            actual_col = f"Actual {month} {selected_year}"
            prev_actual_col = f"Actual {month} {selected_year - 1}"
            budget_col = f"Budget {month} {selected_year}"

            if actual_col in df_final.columns and prev_actual_col in df_final.columns:
                var_actual = (
                    f"Variance {month} (Actual {selected_year} vs {selected_year - 1})"
                )
                df_final[var_actual] = df_final[actual_col] - df_final[prev_actual_col]
                new_columns[actual_col] = var_actual

            if actual_col in df_final.columns and budget_col in df_final.columns:
                var_budget = f"Variance {month} (Budget vs Actual {selected_year})"
                df_final[var_budget] = df_final[actual_col] - df_final[budget_col]
                new_columns[budget_col] = var_budget

        ytd_actual_prev = f"YTD Actual {selected_year - 1}"
        ytd_actual_current = f"YTD Actual {selected_year}"
        ytd_budget_current = f"YTD Budget {selected_year}"

        df_final[ytd_actual_prev] = df_final[
            [
                f"Actual {month} {selected_year - 1}"
                for month in month_order
                if f"Actual {month} {selected_year - 1}" in df_final.columns
            ]
        ].sum(axis=1)

        df_final[ytd_actual_current] = df_final[
            [
                f"Actual {month} {selected_year}"
                for month in month_order
                if f"Actual {month} {selected_year}" in df_final.columns
            ]
        ].sum(axis=1)

        df_final[f"YTD Variance (Actual {selected_year} vs {selected_year - 1})"] = (
            df_final[ytd_actual_current] - df_final[ytd_actual_prev]
        )

        df_final[ytd_budget_current] = df_final[
            [
                f"Budget {month} {selected_year}"
                for month in month_order
                if f"Budget {month} {selected_year}" in df_final.columns
            ]
        ].sum(axis=1)

        df_final[f"YTD Variance (Budget vs Actual {selected_year})"] = (
            df_final[ytd_actual_current] - df_final[ytd_budget_current]
        )

        cols = list(df_final.columns)
        for key, value in new_columns.items():
            idx = cols.index(key)
            cols.insert(idx + 1, cols.pop(cols.index(value)))
        df_final = df_final[cols]

        st.markdown(f"<h4>{company}</h4>", unsafe_allow_html=True)

        company_html_table = display_pnl(df_final)
        company_html_dict[company] = company_html_table

    return company_html_dict


def format_value(value, is_percentage=False):
    try:
        if isinstance(value, str):
            value = value.replace(",", "").replace("(", "-").replace(")", "")
            value = float(value) if value.replace(".", "", 1).isdigit() else value
        
        if isinstance(value, (int, float)):
            if value == 0:
                return "-"  
            
            if is_percentage:
                return f"({abs(value):.1f}%)" if value < 0 else f"{value:.1f}%"
            return f"({abs(int(value)):,})" if value < 0 else f"{int(value):,}"
        
    except ValueError:
        pass 
    
    return value


def display_pnl(df_final):

    # Setting the headers
    headers = df_final.columns.tolist()
    month_columns = headers[4:]

    updated_headers = []
    for col in headers:
        updated_headers.append(col)
        if col in month_columns:
            updated_headers.append(f"{col} %")


    colors = ["#FFDDC1", "#FFABAB", "#D5AAFF", "#85E3FF", "#B9FBC0", "#FF9CEE"]

    header_html = "<tr>"
    for i, col in enumerate(updated_headers):
        if i < 2:
            header_html += f"<th class='header-row'></th>"
        elif i < 4:
            header_html += f"<th class='header-row'>{col}</th>"
        else:
            group_index = (i - 4) // 10 
            color = colors[group_index % len(colors)] 

            if "%" in col:
                header_html += f"<th class='header-row' style='background-color: {color};'>%</th>"
            elif "Variance" in col:
                header_html += f"<th class='header-row' style='background-color: {color};'>Variance</th>"
            else:
                header_html += f"<th class='header-row' style='background-color: {color};'>{col}</th>"

    header_html += "</tr>"


    # Generating Content
    html_rows = ""
    for main_cat, main_df in df_final.groupby("Main Category", sort=False):
        
        main_totals = {col: main_df[col].sum() for col in month_columns}

        if main_cat in ["GROSS PROFIT", "TOTAL EXPENSES", "NET PROFIT"]:
            total_row = [f"<td colspan='4'><b>{main_cat}</b></td>"]
            
            for col in headers[4:]:
                total_row.append(f"<td><b>{format_value(main_totals[col])}</b></td>")
                if col in month_columns:
                    total_row.append("<td><b>100%</b></td>")

            html_rows += f"<tr class='main-total'>{''.join(total_row)}</tr>"
            continue

        html_rows += f'<tr class="main-category"><td colspan="{len(updated_headers)}">{main_cat}</td></tr>'

        for sub_cat, sub_df in main_df.groupby("Subcategory", sort=False):
            html_rows += f'<tr class="sub-category"><td></td><td colspan="{len(updated_headers)-1}">{sub_cat}</td></tr>'
            
            sub_totals = {col: sub_df[col].sum() for col in month_columns}

            for _, row in sub_df.iterrows():
                row_cells = ["<td></td>", "<td></td>"]

                for col in headers[2:]:

                    value = row[col] if pd.notna(row[col]) else 0

                    if col != "COA":
                        row_cells.append(f"<td>{format_value(value)}</td>")
                    else:
                        row_cells.append(f"<td>{(value)}</td>")


                    if col in month_columns:
                        row_cells.append(f"<td></td>")

                html_rows += f"<tr class='code-row'>{''.join(row_cells)}</tr>"

            # Subcategory Total Row
            total_row = [f"<td></td><td colspan=3><b>Total {sub_cat}</b></td>"]
            for col in headers[4:]:
                if col in month_columns:
                    total_row.append(f"<td><b>{format_value(sub_totals[col])}</b></td>")
                    percentage = (sub_totals[col] / main_totals[col] * 100) if main_totals[col] != 0 else 0
                    total_row.append(f"<td><b>{format_value(percentage, is_percentage=True)}</b></td>")
                else:
                    total_row.append("<td><b></b></td>")

            html_rows += f"<tr class='sub-total'>{''.join(total_row)}</tr>"

        # Main Category Total Row
        total_row = [f"<td colspan=4><b>TOTAL {main_cat}</b></td>"]
        for col in headers[4:]:
            total_row.append(f"<td><b>{format_value(main_totals[col])}</b></td>")
            if col in month_columns:
                total_row.append("<td><b>100%</b></td>")

        html_rows += f"<tr class='main-total'>{''.join(total_row)}</tr>"





    html_table = f"""
    {styles.pnl_table_style}
    <table>
    <thead class="header">{header_html}</thead>
    <tbody>{html_rows}</tbody>
    </table>
    """

    st.components.v1.html(html_table, height=1000, scrolling=True)

    return html_table



def main():

    auth.login()
    if not st.session_state.authenticated:
        return

    data_store = helper.fetch_all_data()
    available_companies, available_years = helper.get_available_companies_and_years(
        data_store
    )

    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        st.markdown("<h3>PNL Report</h3>", unsafe_allow_html=True)
    with col2:
        companies = st.multiselect("Select PT (Default = All)", available_companies)
        if not companies:
            companies = available_companies
    with col3:
        current_year = dt.date.today().year
        selected_year = st.selectbox(
            "Select Year",
            available_years,
            index=(
                available_years.index(current_year)
                if current_year in available_years
                else 0
            ),
        )
        data = prepare_pnl_data(data_store, companies, selected_year)

    with col4:
        available_months = helper.get_available_months(
            data, available_companies, selected_year
        )

        if available_months:
            selected_month = st.selectbox(
                "Select Month",
                available_months,
                index=len(available_months) - 1 if available_months else None,
                key="monthly",
            )

    company_html_dict = transform_data(data, selected_year, selected_month)

    with col4:

        excel_file = helper.export_all_tables_to_excel(company_html_dict)

        st.download_button(
            label=":green[**Download to Excel**]",
            data=excel_file,
            file_name="Profit and Loss Statement.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


if __name__ == "__main__":
    main()
