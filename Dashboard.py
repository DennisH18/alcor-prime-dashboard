import streamlit as st
import pandas as pd
import datetime as dt
import altair as alt
import calendar
import streamlit.components.v1 as components
import numpy as np
import services.helper as helper
import io
import services.styles as styles
from services.data import account_categories


styles.style_page()


def convert_to_excel_styled(cash_flow, all_months):
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        for company, data in cash_flow.items():
            workbook = writer.book
            sheet_name = company[:31]  # Excel sheet names must be ≤ 31 characters
            
            df_rows = []
            for category, metrics in data.items():
                if category == "Net Profit Margin (%)":
                    continue  # Handled separately

                for metric_type in ["Actual", "Budget", "Last"]:
                    row = ["", category, metric_type]  # Empty column for ID
                    row += [metrics[metric_type].get(m, 0) for m in all_months]
                    row.append(metrics[metric_type]["YTD"])
                    df_rows.append(row)

            df = pd.DataFrame(df_rows, columns=["ID", "Category", "Type"] + all_months + ["YTD"])
            df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, header=False)

            # Apply formatting
            worksheet = writer.sheets[sheet_name]
            header_format = workbook.add_format({"bold": True, "bg_color": "#e6e6e6", "border": 1, "align": "center"})
            num_format = workbook.add_format({"num_format": "#,##0", "border": 1})
            percent_format = workbook.add_format({"num_format": "0.0%", "border": 1})
            bold_center = workbook.add_format({"bold": True, "align": "center", "border": 1})

            # Write headers
            headers = ["ID", "Category", "Actual/Target"] + all_months + ["YTD"]
            worksheet.write_row(0, 0, headers, header_format)

            # Apply styles to the table
            for row_num in range(1, len(df) + 1):
                for col_num in range(len(headers)):
                    if col_num in [0, 1, 2]:  # First 3 columns (ID, Category, Type)
                        worksheet.write(row_num, col_num, df.iloc[row_num - 1, col_num], bold_center)
                    else:  # Numeric columns
                        worksheet.write(row_num, col_num, df.iloc[row_num - 1, col_num], num_format)

            # Handle Net Profit Margin (%) separately
            if "Net Profit Margin (%)" in data:
                np = data["Net Profit Margin (%)"]
                np_rows = [["", "Net Profit Margin (%)", metric] + 
                           [np[metric].get(m, 0) / 100 for m in all_months] + 
                           [np[metric]["YTD"] / 100] for metric in ["Actual", "Budget", "Last"]]
                
                for row in np_rows:
                    df.loc[len(df)] = row  # Append to DataFrame
                
                for row_num, row in enumerate(np_rows, start=len(df_rows) + 1):
                    for col_num, value in enumerate(row):
                        fmt = percent_format if col_num > 2 else bold_center
                        worksheet.write(row_num, col_num, value, fmt)

            # Set column widths
            worksheet.set_column(0, 0, 5)  # ID
            worksheet.set_column(1, 1, 25)  # Category
            worksheet.set_column(2, 2, 15)  # Actual/Target
            worksheet.set_column(3, len(headers) - 1, 12)  # Months + YTD

    excel_buffer.seek(0)
    return excel_buffer


def waterfall_chart(data):

    df = pd.DataFrame([
        {"Category": category, "Values": data.get(category, 0)}
        for category in account_categories.keys()
    ])

    rename_map = {
        "Cost of Goods Sold": "COGS",
        "HR + Benefit": "HR+Benefits",
        "Operating Expenses": "Op Exp",
        "Depreciation & Maintenance": "Deprec+Maint",
        "Other Non-Operating (Income)/Expense + Tax": "Other Exp/Inc",
    }

    df["Category"] = df["Category"].replace(rename_map)

    df["Values"] = df.apply(
        lambda row: row["Values"] if row["Category"] in ["Revenue", "Net Profit", "Other Exp/Inc"] else -abs(row["Values"]),
        axis=1
    ).round(0)

    df.loc[0, "Start"] = 0
    df.loc[0, "End"] = df.loc[0, "Values"]

    for i in range(1, len(df)):
        df.loc[i, "Start"] = df.loc[i - 1, "End"]
        df.loc[i, "End"] = df.loc[i, "Start"] + df.loc[i, "Values"]

    color_map = {
        "Revenue": "lightgreen",
        "COGS": "red",
        "HR+Benefits": "red",
        "Op Exp": "red",
        "Deprec+Maint": "red",
        "Net Profit": "blue",
    }

    color_map["Other Exp/Inc"] = "lightgreen" if data.get("Other Non-Operating (Income)/Expense + Tax", 0) > 0 else "red"
    color_map["Net Profit"] = "blue" if data.get("Net Profit", 0) > 0 else "darkred"

    bars = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Category:N", title="", sort=df["Category"].tolist(),
                    axis=alt.Axis(labelAngle=0, labelOverlap="parity")),
            y=alt.Y("Start:Q", title=None),
            y2="End:Q",
            color=alt.Color("Category:N", scale=alt.Scale(domain=list(color_map.keys()), 
                                                           range=list(color_map.values())), legend=None),
            tooltip=["Category", "Values"],
        )
    )

    text = bars.mark_text(
        align="center",
        fontSize=12,
        dy=alt.expr(alt.expr.if_(alt.datum.Values > 0, -10, 10)),
    ).encode(
        text=alt.Text("Values:Q", format=","),
        color=alt.value("black"),
        y=alt.Y("End:Q"),
    )

    chart = (bars + text).properties(height=280)
    st.altair_chart(chart, use_container_width=True)


def display_top_expenses(cost_data):
    for label, value in cost_data.items():
        formatted_value = f"Rp. {value:.0f}"
        st.markdown(
            f"""
            <div class='container'>
                <span class='left'>{label[:15] + "..." if len(label) > 15 else label}</span>
                <span class='right'>{formatted_value}</span>
            </div>
        """,
            unsafe_allow_html=True,
        )


def create_pie_chart(df):

    total = df["Values"].sum()

    df["theta"] = df["Values"] / total * 2 * np.pi
    df["cumsum"] = df["theta"].cumsum()
    df["startAngle"] = df["cumsum"] - df["theta"]
    df["midAngle"] = df["startAngle"] + df["theta"] / 2
    df["midAngleDeg"] = df["midAngle"] * 180 / np.pi
    df["Percentage"] = (df["Values"] / total * 100).round(0).astype(int)
    df["Percentage"] = df["Percentage"].astype(str) + "%"

    pie_chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=30, outerRadius=50)
        .encode(
            theta=alt.Theta("Values:Q", stack=True),
            color=alt.Color(
                "Category:N",
                legend=alt.Legend(
                    orient="bottom",
                    title=None,
                    direction="horizontal",
                    offset=65,
                    labelFontSize=12,
                ),
            ),
            tooltip=[
                alt.Tooltip("Category:N", title="Category"),
                alt.Tooltip("Values:Q", title="Values", format=","),
                alt.Tooltip("Percentage:N", title="Percentage")
            ]
        )
        .properties(width=180, height=155)
    )

    text_labels = (
        alt.Chart(df)
        .mark_text(size=11, color="black", align="center", baseline="middle")
        .encode(
            text=alt.Text("Percentage:N"),
            theta=alt.Theta("Values:Q", stack=True),
            angle=alt.Angle("midAngleDeg:Q"),
            radius=alt.value(65),
            tooltip=[
                alt.Tooltip("Category:N", title="Category"),
                alt.Tooltip("Values:Q", title="Values", format=","),
                alt.Tooltip("Percentage:N", title="Percentage")
            ]
        )
    )

    return pie_chart + text_labels


def pie_chart(pie_data, cost_data, cost_data_last_year):

    if pie_data:
        
        df = pd.DataFrame([
            {"Category": "JPCC", "Values": pie_data["JPCC"]},
            {"Category": "OTHERS", "Values": pie_data["OTHERS"]}
        ])
        df_ly = pd.DataFrame([
            {"Category": "JPCC_LY", "Values": pie_data["JPCC_LY"]},
            {"Category": "OTHERS_LY", "Values": pie_data["OTHERS_LY"]}
        ])
        
        st.markdown(
            """
            <style>
                .container { 
                    display: flex; 
                    justify-content: space-between; 
                    border-bottom: 1px solid #ddd;
                    margin: -20px 0 20px 0;
                }
                .left { font-size: 12px; color: #333; } 
                .right { font-size: 12px; color: black; font-weight: bold; text-align: right; }
            </style>
        """,
            unsafe_allow_html=True,
        )
            

        col1, col2 = st.columns(2)
        with col1:
            st.altair_chart(create_pie_chart(df), use_container_width=True)
            display_top_expenses(cost_data)
                
        with col2:
            st.altair_chart(create_pie_chart(df_ly), use_container_width=True)
            display_top_expenses(cost_data_last_year)
             

def format_metric(value):
    color = "green" if value > 0 else "red" if value < 0 else "orange"
    sign = "+" if value > 0 else ("&nbsp;&nbsp;" if value == 0 else "")

    return f"<p style='color:{color}; font-size:12px; font-weight:bold;'>{sign}{value}%</p>"


def display_metric(title, key, amount, metric1, metric2):
    with st.container(border=True, height=160):
        st.markdown(f"<h5>{title}</h5>", unsafe_allow_html=True)

        if title == "Revenue":
            st.markdown(
                f"<h4 style='color:darkblue;'>Rp. {amount:,.0f}</h4>",
                unsafe_allow_html=True,
            )
            col1, col2 = st.columns([5, 2], gap="small")
            with col1:
                st.markdown(
                    "<p style='font-size:12px;'>Target Achievement</p>",
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(format_metric(metric1), unsafe_allow_html=True)
        elif title == "Net Profit":
            color = "darkred" if amount < 0 else "green"
            st.markdown(
                f"<h4 style='color:{color};'>Rp. {amount:,.0f}</h4>",
                unsafe_allow_html=True,
            )
            col1, col2 = st.columns([5, 2], gap="small")
            with col1:
                st.markdown(
                    "<p style='font-size:12px;'>Compare to Budget</p>",
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(format_metric(metric1), unsafe_allow_html=True)
        else:
            st.markdown(
                f"<h4 style='color:red;'>Rp. {amount:,.0f}</h4>", unsafe_allow_html=True
            )
            col1, col2 = st.columns([5, 2], gap="small")
            with col1:
                st.markdown(
                    "<p style='font-size:12px;'>Compare to Budget</p>",
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(format_metric(metric1), unsafe_allow_html=True)

        col1, col2 = st.columns([5, 2], gap="small")
        with col1:
            st.markdown(
                "<p style='font-size:12px;'>Change from Last Year</p>",
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(format_metric(metric2), unsafe_allow_html=True)


def calculate_percentage_change(actual, budget):
    if budget == 0:
        return 0 
    
    return round(((actual - budget) / abs(budget)) * 100, 1)


def display_monthly(data, selected_month, selected_year):

    companies = sorted(set(key.split("_")[0] for key in data.keys()))
    
    for company in companies:

        st.markdown(f"<h4>{company}</h4>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns([1, 1, 2, 3])

        company_data = {key: value for key, value in data.items() if key.startswith(company)}
        key = f"{company}_{selected_month}_{selected_year}"

        filtered_data = {item["Category"]: item["Value"] for item in company_data.get(key, {}).get("filtered_data", [])}
        top_5_expenses = {item["Category"]: item["Value"] for item in company_data.get(key, {}).get("top_5_expenses", [])}

        jpcc_vs_others = {item["Category"]: item["Value"] for item in company_data.get(key, {}).get("jpcc_vs_others", [])}
        budget = {item["Category"]: item["Value"] for item in company_data.get(key, {}).get("budget", [])}

        last_year_key = f"{company}_{selected_month}_{selected_year-1}"
        filtered_data_last_year = {item["Category"]: item["Value"] for item in company_data.get(last_year_key, {}).get("filtered_data", [])}
        top_5_expenses_last_year = {item["Category"]: item["Value"] for item in company_data.get(last_year_key, {}).get("top_5_expenses", [])}

        metrics = {
            "Revenue": ("revenue", filtered_data.get("Revenue", 0), filtered_data_last_year.get("Revenue", 0), budget.get("Revenue", 0)),
            "Total Expenses": ("expense", filtered_data.get("Total Expenses", 0), filtered_data_last_year.get("Total Expenses", 0), budget.get("Total Expenses", 0)),
            "COGS": ("cogs", filtered_data.get("Cost of Goods Sold", 0), filtered_data_last_year.get("Cost of Goods Sold", 0), budget.get("Cost of Goods Sold", 0)),
            "Net Profit": ("net", filtered_data.get("Net Profit", 0), filtered_data_last_year.get("Net Profit", 0), budget.get("Net Profit", 0)),
        }

        for i, (label, (key, current, last_year, budgeted)) in enumerate(metrics.items()):

            year_over_year_change = calculate_percentage_change(current, last_year)
            budget_percentage_change = calculate_percentage_change(current, budgeted)

            with (col1 if i % 2 == 0 else col2):
                display_metric(label, f"{key}_{company.lower()}", current, budget_percentage_change, year_over_year_change)

        with col3:
            with st.container(border=True, height=335):
                st.markdown(f"<h5>{company} vs Other</h5>", unsafe_allow_html=True)
                pie_chart(jpcc_vs_others, top_5_expenses, top_5_expenses_last_year)
        
        with col4:
            with st.container(border=True, height=335):
                st.markdown("<h5>Income Statement</h5>", unsafe_allow_html=True)
                waterfall_chart(filtered_data)

        st.divider()


def display_ytd(data, selected_month, selected_year):
    companies = sorted(set(key.split("_")[0] for key in data.keys()))
    
    month_names = list(calendar.month_abbr)
    selected_month_index = month_names.index(selected_month)
    valid_months = month_names[1:selected_month_index + 1]

    for company in companies:
        st.markdown(f"<h4>{company}</h4>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns([1, 1, 2, 3])
        
        company_data = {key: value for key, value in data.items() if key.startswith(company)}
        
        ytd_filtered = {}
        ytd_top_5 = {}
        ytd_filtered_last_year = {}
        ytd_top_5_last_year = {}
        ytd_jpcc_vs = {}
        ytd_budget = {}
        
        for month in valid_months:
            selected_key = f"{company}_{month}_{selected_year}"
            sheet = company_data.get(selected_key, {})
            
            for item in sheet.get("filtered_data", []):
                category = item["Category"]
                value = item["Value"]
                ytd_filtered[category] = ytd_filtered.get(category, 0) + value
            
            for item in sheet.get("top_5_expenses", []):
                category = item["Category"]
                value = item["Value"]
                ytd_top_5[category] = ytd_top_5.get(category, 0) + value
                
            for item in sheet.get("jpcc_vs_others", []):
                category = item["Category"]
                value = item["Value"]
                ytd_jpcc_vs[category] = ytd_jpcc_vs.get(category, 0) + value
            
            for item in sheet.get("budget", []):
                category = item["Category"]
                value = item["Value"]
                ytd_budget[category] = ytd_budget.get(category, 0) + value

            last_year_sheet = company_data.get(f"{company}_{month}_{selected_year-1}", {})

            for item in last_year_sheet.get("top_5_expenses", []):
                category = item["Category"]
                value = item["Value"]
                ytd_top_5_last_year[category] = ytd_top_5_last_year.get(category, 0) + value

            for item in last_year_sheet.get("filtered_data", []):
                category = item["Category"]
                value = item["Value"]
                ytd_filtered_last_year[category] = ytd_filtered_last_year.get(category, 0) + value

            metrics = {
                "Revenue": ("revenue", ytd_filtered.get("Revenue", 0), ytd_filtered_last_year.get("Revenue", 0), ytd_budget.get("Revenue", 0)),
                "Total Expenses": ("expense", ytd_filtered.get("Total Expenses", 0), ytd_filtered_last_year.get("Total Expenses", 0), ytd_budget.get("Total Expenses", 0)),
                "COGS": ("cogs", ytd_filtered.get("Cost of Goods Sold", 0), ytd_filtered_last_year.get("Cost of Goods Sold", 0), ytd_budget.get("Cost of Goods Sold", 0)),
                "Net Profit": ("net", ytd_filtered.get("Net Profit", 0), ytd_filtered_last_year.get("Net Profit", 0), ytd_budget.get("Net Profit", 0)),
            }

        for i, (label, (key, actual, last_year, budgeted)) in enumerate(metrics.items()):
            budget_percentage_change = calculate_percentage_change(actual, budgeted)
            last_year_percentage_change = calculate_percentage_change(actual, last_year)

            with (col1 if i % 2 == 0 else col2):
                display_metric(label, f"{key}_ytd_{company.lower()}", actual, budget_percentage_change, last_year_percentage_change)

        with col3:
            with st.container(border=True, height=335):
                st.markdown(f"<h5>{company} vs Other (YTD)</h5>", unsafe_allow_html=True)
                pie_chart(ytd_jpcc_vs, ytd_top_5, ytd_top_5_last_year)

        with col4:
            with st.container(border=True, height=335):
                st.markdown("<h5>Income Statement (YTD)</h5>", unsafe_allow_html=True)
                waterfall_chart(ytd_filtered)

        st.divider()


def display_cash_flow_table(data, selected_year):

    companies = sorted({key.split("_")[0] for key in data.keys()})
    all_months = sorted({key.split("_")[1] for key in data.keys()},
                        key=lambda x: list(calendar.month_abbr).index(x))
    
    cash_flow = {comp: {} for comp in companies}
    for key, value in data.items():
        parts = key.split("_")
        if len(parts) < 3:
            continue
        company, month, year = parts[0], parts[1], parts[2]
        for item in value.get("filtered_data", []):
            category = item["Category"]
            amount = float(item["Value"] or 0)
            if category not in cash_flow[company]:
                cash_flow[company][category] = {
                    "Actual": {m: 0 for m in all_months},
                    "Budget": {m: 0 for m in all_months},
                    "Last": {m: 0 for m in all_months}
                }
            if year == str(selected_year):
                cash_flow[company][category]["Actual"][month] = amount
            elif year == str(selected_year - 1):
                cash_flow[company][category]["Last"][month] = amount
        for item in value.get("budget", []):
            category = item["Category"]
            amount = float(item["Value"] or 0)
            if category not in cash_flow[company]:
                cash_flow[company][category] = {
                    "Actual": {m: 0 for m in all_months},
                    "Budget": {m: 0 for m in all_months},
                    "Last": {m: 0 for m in all_months}
                }
            if year == str(selected_year):
                cash_flow[company][category]["Budget"][month] = amount
    for company in cash_flow:
        for category in cash_flow[company]:
            for metric in ["Actual", "Budget", "Last"]:
                cash_flow[company][category][metric]["YTD"] = sum(cash_flow[company][category][metric].values())
    for company in cash_flow:
        if "Revenue" in cash_flow[company] and "Net Profit" in cash_flow[company]:
            np_margin = {"Actual": {}, "Budget": {}, "Last": {}}
            for metric in ["Actual", "Budget", "Last"]:
                for m in all_months:
                    rev = cash_flow[company]["Revenue"][metric].get(m, 0)
                    net = cash_flow[company]["Net Profit"][metric].get(m, 0)
                    margin = (net / rev * 100) if rev != 0 else 0
                    np_margin[metric][m] = margin
                np_margin[metric]["YTD"] = sum(np_margin[metric][m] for m in all_months) / len(all_months) if all_months else 0
            cash_flow[company]["Net Profit Margin (%)"] = np_margin

    excel_file = convert_to_excel_styled(cash_flow, all_months)

    col1, col2 = st.columns([4, 1])
    with col1:
        st.write("")
        st.markdown("<h4>Profit and Loss Data</h4>", unsafe_allow_html=True)
    with col2:
        st.write("")
        st.download_button(
            label="Download Excel File",
            data=excel_file,
            file_name="cash_flow_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    st.divider()

    for company in companies:
        headers = ["ID", "Category", "Actual/Target"] + all_months + ["YTD"]
        rows = ""
        row_id = 1
        for category in cash_flow[company]:
            if category == "Net Profit Margin (%)":
                continue
            actual_values = "".join(f"<td>{cash_flow[company][category]['Actual'].get(m, 0):,.0f}</td>" for m in all_months)
            budget_values = "".join(f"<td>{cash_flow[company][category]['Budget'].get(m, 0):,.0f}</td>" for m in all_months)
            last_values   = "".join(f"<td>{cash_flow[company][category]['Last'].get(m, 0):,.0f}</td>" for m in all_months)
            
            actual_ytd = f"<td>{cash_flow[company][category]['Actual']['YTD']:,.0f}</td>"
            budget_ytd = f"<td>{cash_flow[company][category]['Budget']['YTD']:,.0f}</td>"
            last_ytd   = f"<td>{cash_flow[company][category]['Last']['YTD']:,.0f}</td>"

            rows += f"""
                <tr class="actual-row">
                    <td rowspan="3">{row_id}</td>
                    <td rowspan="3">{category}</td>
                    <td>Actual</td>
                    {actual_values}
                    {actual_ytd}
                </tr>
                <tr class="budget-row">
                    <td>Target</td>
                    {budget_values}
                    {budget_ytd}
                </tr>
                <tr class="last-year-row">
                    <td>Last Year</td>
                    {last_values}
                    {last_ytd}
                </tr>
            """
            row_id += 1

        if "Net Profit Margin (%)" in cash_flow[company]:
            np = cash_flow[company]["Net Profit Margin (%)"]
            actual_values = "".join(f"<td>{np['Actual'].get(m, 0):,.0f}%</td>" for m in all_months)
            budget_values = "".join(f"<td>{np['Budget'].get(m, 0):,.0f}%</td>" for m in all_months)
            last_values   = "".join(f"<td>{np['Last'].get(m, 0):,.0f}%</td>" for m in all_months)
            actual_ytd = f"<td>{np['Actual']['YTD']:,.0f}%</td>"
            budget_ytd = f"<td>{np['Budget']['YTD']:,.0f}%</td>"
            last_ytd   = f"<td>{np['Last']['YTD']:,.0f}%</td>"

            rows += f"""
                <tr>
                    <td rowspan="3">{row_id}</td>
                    <td rowspan="3" style="text-align: left; padding-left: 10px;">Net Profit Margin (%)</td>
                    <td>Actual</td>
                    {actual_values}
                    {actual_ytd}
                </tr>
                <tr>
                    <td>Target</td>
                    {budget_values}
                    {budget_ytd}
                </tr>
                <tr>
                    <td>Last Year</td>
                    {last_values}
                    {last_ytd}
                </tr>
            """
            row_id += 1

        table_html = f"""
            {styles.cf_table_style}
            <div style="overflow-x: auto; white-space: nowrap; max-width: 100%;">
            <table>
                <thead>
                    <tr>{"".join(f"<th>{col}</th>" for col in headers)}</tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            </div>
        """

        st.markdown(f"<h4>{company}</h4>", unsafe_allow_html=True)
        components.html(table_html, height=1050, scrolling=True)

def to_camel_case(month):
    return ''.join(word.capitalize() for word in month.lower().split())


@st.cache_data
def prepare_data(data_store, companies, selected_year):
    
    results = {}

    predefined_budget = {
        "TOTAL REVENUES": "Revenue",
        "TOTAL COGS": "Cost of Goods Sold",
        "GROSS PROFIT": "Gross Profit",
        "TOTAL HUMAN RESOURCES": "HR + Benefit",
        "TOTAL OPERATING & GA EXPENSES": "Operating Expenses",
        "TOTAL DEPRECIATION & REPAIR MAINTENANCE": "Depreciation & Maintenance",
        "GRAND TOTAL EXPENSES": "Total Expenses",
        "TOTAL OTHER INCOME / EXPENSES": "Other Non-Operating (Income)/Expense + Tax",
        "EARNINGS AFTER TAX (EAT)": "Net Profit",
    }

    month_abbr = set(calendar.month_abbr[1:])

    for company in companies:
        years_to_check = [selected_year, selected_year-1]
        for year in years_to_check:
    
            for file_name, df in data_store[company][year].items():

                if "Management Report" in file_name:
                    month_str = next((month for month in month_abbr if month in file_name), None)
                    if not month_str:
                        continue

                    key = f"{company}_{month_str}_{year}"

                    if pd.to_numeric(df.iloc[0], errors='coerce').notna().all():
                        df.iloc[0] = df.iloc[1]

                    df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
                    df.iloc[:, 2] = pd.to_numeric(df.iloc[:, 2], errors="coerce")
                    
                    valid_codes = set(str(code) for codes in account_categories.values() if codes for code in codes)
                    df = df[df.iloc[:, 0].isin(valid_codes)]

                    categorized_data = {category: 0 for category in account_categories}

                    for _, row in df.iterrows():
                        try:
                            account_code = int(row.iloc[0])  # Convert to integer for matching
                            value = float(row.iloc[2])  # Ensure value is a float
                        except ValueError:
                            continue  # Skip non-numeric account codes

                        for category, codes in account_categories.items():
                            if codes and account_code in codes:
                                categorized_data[category] += value

                    if categorized_data["Revenue"] and categorized_data["Cost of Goods Sold"]:
                        categorized_data["Gross Profit"] = (
                            categorized_data["Revenue"] - categorized_data["Cost of Goods Sold"]
                        )

                    categorized_data["Total Expenses"] = (
                        categorized_data["Operating Expenses"] +
                        categorized_data["HR + Benefit"] +
                        categorized_data["Depreciation & Maintenance"]
                    )

                    if categorized_data["Gross Profit"] is not None:
                        categorized_data["Net Profit"] = (
                            categorized_data["Gross Profit"] - categorized_data["Total Expenses"] +
                            categorized_data["Other Non-Operating (Income)/Expense + Tax"]
                        )

                    filtered_df = pd.DataFrame([
                        {"Category": category, "Value": value}
                        for category, value in categorized_data.items() if value is not None
                    ])

                    cost_df = df[df.iloc[:, 0].astype(str).str.startswith(("6", "5"))]

                    column_name = df.columns[2]  # Replace with actual column name
                    df_top_5 = cost_df.nlargest(4, column_name)[[df.columns[1], column_name]]
                    df_top_5.columns = ["Category", "Value"]

                    others_value = cost_df[~cost_df.index.isin(df_top_5.index)][df.columns[2]].sum()
                    others_row = pd.DataFrame({"Category": ["Others"], "Value": [others_value]})

                    df_top_5 = pd.concat([df_top_5, others_row], ignore_index=True)


                    if filtered_df["Value"].max() > 1_000_000:
                        filtered_df["Value"] /= 1_000_000
                    if not df_top_5.empty and df_top_5["Value"].max() > 1_000_000:
                        df_top_5["Value"] /= 1_000_000

                    if key not in results:
                        results[key] = {"filtered_data": [], "top_5_expenses": []}

                    results[key].update({
                        "filtered_data": filtered_df.to_dict(orient="records"),
                        "top_5_expenses": df_top_5.to_dict(orient="records"),
                    })
                    

                elif "Budget" in file_name:
                    header_row_index = 6
                    df.columns = df.iloc[header_row_index]
                    duplicates = df.columns.duplicated(keep=False)
                    df.columns = [f"{col}_{i}" if duplicates[i] else col for i, col in enumerate(df.columns)]
                    df = df.iloc[header_row_index + 1:].reset_index(drop=True)
                    month_cols = [col for col in df.columns.astype(str) if "nan" not in col.lower()]
                    df = df[['nan_2', 'nan_3'] + month_cols]
                    df['nan_2'] = df['nan_2'].fillna(df['nan_3'])
                    df.drop(columns=['nan_3'], errors='ignore', inplace=True)
                    df = df[df['nan_2'].isin(predefined_budget.keys())][['nan_2'] + month_cols]
                    df['nan_2'] = df['nan_2'].map(predefined_budget)
                    
                    for month in df.columns[1:]:
                        key = f"{company}_{to_camel_case(month.split()[0])}_{year}"
                        
                        if key not in results:
                            results[key] = {"filtered_data": [], "top_5_expenses": [], "budget": []}
                        elif "budget" not in results[key]:
                            results[key]["budget"] = []

                        budget_data = [{"Category": row["nan_2"], "Value": row[month]} for _, row in df.iterrows()]

                        values = [item["Value"] for item in budget_data]
                        if max(values) > 1_000_000:
                            for item in budget_data:
                                item["Value"] /= 1_000_000

                        results[key]["budget"].extend(budget_data)


                elif "JPCC vs Others" in file_name:
                    
                    df.iloc[4] = df.iloc[4].apply(lambda x: str(int(x)) if isinstance(x, float) and x.is_integer() else str(x))
                    df.iloc[2] = df.iloc[2].replace("", None).ffill()                
                    df.iloc[3] = df.iloc[2].astype(str) + "_" + df.iloc[4].astype(str)
                    df.columns = df.iloc[3]
                    df = df.iloc[5:7]
                    df.reset_index(drop=True, inplace=True)
                    df.fillna(0, inplace=True)
                    df.rename(columns={df.columns[0]: "Category"}, inplace=True)

                    month_map = {
                        "Januari": "Jan",
                        "Februari": "Feb",
                        "Maret": "Mar",
                        "April": "Apr",
                        "Mei": "May",
                        "Juni": "Jun",
                        "Juli": "Jul",
                        "Agustus": "Aug",
                        "September": "Sep",
                        "Oktober": "Oct",
                        "November": "Nov",
                        "Desember": "Dec"
                    }

                    for month in df.columns[1:]:
                        month_name, budget_year = month.split("_")
                        budget_year = int(budget_year)
                        month_str = month_map.get(month_name, month_name)
                        key = f"{company}_{month_str}_{selected_year}"
                        if key not in results:
                            results[key] = {"filtered_data": [], "top_5_expenses": [], "budget": []}

                        if "jpcc_vs_others" not in results[key]:  
                            results[key]["jpcc_vs_others"] = []  

                        for i, category in enumerate(df["Category"]): 
                            entry = {
                                "Category": category if selected_year == budget_year else f"{category}_LY",
                                "Value": df.at[i, month]
                            }

                            results[key]["jpcc_vs_others"].append(entry)
    
    return results


def main():


    data_store = helper.fetch_all_data()    
    available_companies, available_years = helper.get_available_companies_and_years(data_store)
    
    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        st.markdown("<h3>Finance Dashboard</h3>", unsafe_allow_html=True)
    with col2:
        companies = st.multiselect("Select PT (Default = All)", available_companies)
        if not companies:
            companies = available_companies
    with col3:
        current_year = dt.date.today().year
        selected_year = st.selectbox("Select Year", available_years, index=available_years.index(current_year) if current_year in available_years else 0)
        
    data = prepare_data(data_store, companies, selected_year)
    available_months = helper.get_available_months(data, companies, selected_year)
    tab1, tab2, tab3 = st.tabs(["Monthly Dashboard", "YTD Dashboard","Data"])
    
    with tab1:
        if available_months:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write("#")
                st.markdown("<h4>Monthly Dashboard</h4>", unsafe_allow_html=True)
            with col2:
                selected_month = st.selectbox("Select Month", available_months, index=len(available_months) - 1 if available_months else None, key="monthly")
            st.divider()
            display_monthly(data, selected_month, selected_year)

    with tab2:
        if available_months:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write("#")
                st.markdown("<h4>YTD Dashboard</h4>", unsafe_allow_html=True)
            with col2:
                selected_month = st.selectbox("Select Month", available_months, index=len(available_months) - 1 if available_months else None, key="ytd")
            st.divider()
            display_ytd(data, selected_month, selected_year)

    with tab3:
        display_cash_flow_table(data, selected_year)

if __name__ == "__main__":
    main()
