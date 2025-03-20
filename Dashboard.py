import streamlit as st
import pandas as pd
import openpyxl
import datetime as dt
import altair as alt
import calendar
import os
import streamlit.components.v1 as components
import dropbox
from io import BytesIO
import numpy as np
import services.helper as helper

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

cf_table_style = """
        <style>
            table { 
                width: 100%; 
                border-collapse: collapse; 
                font-family: Arial, sans-serif; 
                font-size: 14px; 
                border: 1px solid #ccc;
                overflow: scroll;
            }
            th, td { 
                padding: 8px; 
                border: 1px solid #ccc; 
                text-align: center; 
            }
            th { 
                background-color: #e6e6e6; 
                color: black; 
                font-weight: bold; 
                text-align: center;
                border-bottom: 2px solid #203354;
            }
            .actual-row td:first-child { 
                background-color: #e6e6e6; 
                font-weight: bold; 
                text-align: center; 
            }
            .actual-row td:nth-child(2) {  
                background-color: #e6e6e6; 
                font-weight: bold; 
                text-align: left; 
            }
            tbody tr:nth-last-child(-n+3) td { 
                background-color: #e6e6e6 !important;  
                font-weight: bold;  
            }
        </style>
    """

pnl_table_style = """ 
        <style>
        
        </style>
    """

def waterfall_chart(data):

    df = pd.DataFrame([
        {"Category": category, "Values": data.get(category, 0)}
        for category in [
            "Revenue",
            "Cost of Goods Sold",
            "HR + Benefit",
            "Operating Expenses",
            "Depreciation & Maintenance",
            "Other Non-Operating (Income)/Expense + Tax",
            "Net Profit",
        ]
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
    ).astype(int)

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
    color_map["Net Profit"] = "blue" if data.get("Net Profit", 0) > 0 else "red"

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


def pie_chart(pie_data, cost_data):

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
                .properties(width=180, height=200)
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


        col1, col2 = st.columns(2)
        with col1:
            st.altair_chart(create_pie_chart(df), use_container_width=True)
            
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
                

        with col2:
            st.altair_chart(create_pie_chart(df_ly), use_container_width=True)
            
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
    return round(((actual - budget) / budget) * 100)


def display_monthly(data, selected_month, selected_year):

    companies = sorted(set(key.split("_")[0] for key in data.keys()))
    
    for company in companies:

        st.markdown(f"<h4>{company}</h4>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns([1, 1, 2, 3])

        company_data = {key: value for key, value in data.items() if key.startswith(company)}
        selected_key = f"{company}_{selected_month}_{selected_year}"
        filtered_data = {item["Category"]: item["Value"] for item in company_data.get(selected_key, {}).get("filtered_data", [])}
        top_5_expenses = {item["Category"]: item["Value"] for item in company_data.get(selected_key, {}).get("top_5_expenses", [])}
        jpcc_vs_others = {item["Category"]: item["Value"] for item in company_data.get(selected_key, {}).get("jpcc_vs_others", [])}
        budget = {item["Category"]: item["Value"] for item in company_data.get(selected_key, {}).get("budget", [])}

        metrics = {
            "Revenue": ("revenue", filtered_data.get("Revenue", 0), budget.get("Revenue", 0)),
            "Total Expenses": ("expense", filtered_data.get("Total Expenses", 0), budget.get("Total Expenses", 0)),
            "COGS": ("cogs", filtered_data.get("Cost of Goods Sold", 0), budget.get("Cost of Goods Sold", 0)),
            "Net Profit": ("net", filtered_data.get("Net Profit", 0), budget.get("Net Profit", 0)),
        }

        for i, (label, (key, actual, budgeted)) in enumerate(metrics.items()):
            percentage_change = calculate_percentage_change(actual, budgeted)
            with (col1 if i % 2 == 0 else col2):
                display_metric(label, f"{key}_{company.lower()}", actual, percentage_change, 0)

        with col3:
            with st.container(border=True, height=335):
                st.markdown(f"<h5>{company} vs Other</h5>", unsafe_allow_html=True)
                pie_chart(jpcc_vs_others, top_5_expenses)

        with col4:
            with st.container(border=True, height=335):
                st.markdown("<h5>Income Statement</h5>", unsafe_allow_html=True)
                waterfall_chart(filtered_data)

        st.divider()


def display_cash_flow_table(data):

    companies = sorted({key.split("_")[0] for key in data.keys()})
    all_months = sorted({key.split("_")[1] for key in data.keys()}, key=lambda x: list(calendar.month_abbr).index(x))

    cash_flow = {comp: {} for comp in companies}
    for key, value in data.items():
        company, month = key.split("_")[0], key.split("_")[1]
        for item in value.get("filtered_data", []):
            category = item["Category"]
            amount = float(item["Value"] or 0)
            if category not in cash_flow[company]:
                cash_flow[company][category] = {"Actual": {m: 0 for m in all_months}, "Budget": {m: 0 for m in all_months}}
            cash_flow[company][category]["Actual"][month] = amount
            
        for item in value.get("budget", []):
            category = item["Category"]
            amount = float(item["Value"] or 0)
            if category not in cash_flow[company]:
                cash_flow[company][category] = {"Actual": {m: 0 for m in all_months}, "Budget": {m: 0 for m in all_months}}
            cash_flow[company][category]["Budget"][month] = amount

    for company in cash_flow:
        total_revenue = {"Actual": 0, "Budget": 0}
        total_net_profit = {"Actual": 0, "Budget": 0}

        for category in cash_flow[company]:
            cash_flow[company][category]["Actual"]["YTD"] = sum(cash_flow[company][category]["Actual"].values())
            cash_flow[company][category]["Budget"]["YTD"] = sum(cash_flow[company][category]["Budget"].values())

            if category.lower() == "revenue":
                total_revenue["Actual"] = cash_flow[company][category]["Actual"]["YTD"]
                total_revenue["Budget"] = cash_flow[company][category]["Budget"]["YTD"]
            elif category.lower() == "net profit":
                total_net_profit["Actual"] = cash_flow[company][category]["Actual"]["YTD"]
                total_net_profit["Budget"] = cash_flow[company][category]["Budget"]["YTD"]

        cash_flow[company]["Net Profit Margin (%)"] = {
            "Actual": {m: (cash_flow[company]["Net Profit"]["Actual"].get(m, 0) /
                            cash_flow[company]["Revenue"]["Actual"].get(m, 1) * 100)
                    if cash_flow[company]["Revenue"]["Actual"].get(m, 1) else 0
                    for m in all_months},
            "Budget": {m: (cash_flow[company]["Net Profit"]["Budget"].get(m, 0) /
                            cash_flow[company]["Revenue"]["Budget"].get(m, 1) * 100)
                    if cash_flow[company]["Revenue"]["Budget"].get(m, 1) else 0
                    for m in all_months},
        }

        cash_flow[company]["Net Profit Margin (%)"]["Actual"]["YTD"] = (
            sum(cash_flow[company]["Net Profit Margin (%)"]["Actual"].values()) / len(all_months)
            if all_months else 0
        )
        cash_flow[company]["Net Profit Margin (%)"]["Budget"]["YTD"] = (
            sum(cash_flow[company]["Net Profit Margin (%)"]["Budget"].values()) / len(all_months)
            if all_months else 0
        )

    for company in companies:
        headers = ["ID", "Category", "Actual/Target"] + all_months + ["YTD"]
        rows = ""
        row_id = 1

        for category in cash_flow[company]:
            actual_values = "".join(f"<td>{cash_flow[company][category]['Actual'].get(m, 0):,.0f}</td>" for m in all_months)
            budget_values = "".join(f"<td>{cash_flow[company][category]['Budget'].get(m, 0):,.0f}</td>" for m in all_months)
            
            actual_ytd = f"<td>{cash_flow[company][category]['Actual']['YTD']:,.0f}</td>"
            budget_ytd = f"<td>{cash_flow[company][category]['Budget']['YTD']:,.0f}</td>"

            #TODO: add last year values
            
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
                    {budget_values}
                    {budget_ytd}
                </tr>
            """
            row_id += 1
        
        table_html = f"""
            {cf_table_style}
            <h2 style='font-family: Arial, sans-serif;'>{company} Cash Flow</h2>
            <table>
                <thead>
                    <tr>{"".join(f"<th>{col}</th>" for col in headers)}</tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        """
        components.html(table_html, height=1100, scrolling=True)


def to_camel_case(month):
    return ''.join(word.capitalize() for word in month.lower().split())


@st.cache_data
def prepare_data(data_store, companies, selected_year):
    results = {}
    predefined_words = {
        "Total dari Pendapatan": "Revenue",
        "Total dari Beban Pokok Pendapatan": "Cost of Goods Sold",
        "Laba Kotor": "Gross Profit",
        "6201000000": "HR + Benefit",
        "Total dari Beban Operasional": "Operating Expenses",
        "6202000000": "Depreciation & Maintenance",
        "Total dari Pendapatan (Beban Lain-lain)": "Other Non-Operating (Income)/Expense + Tax",
        "Laba (Rugi)": "Net Profit",
    }

    predefined_budget = {
        "TOTAL REVENUES": "Revenue",
        "TOTAL COGS": "Cost of Goods Sold",
        "GROSS PROFIT": "Gross Profit",
        "TOTAL HUMAN RESOURCES": "HR + Benefit",
        "TOTAL OPERATING & GA EXPENSES": "Operating Expenses",
        "TOTAL DEPRECIATION & REPAIR MAINTENANCE": "Depreciation & Maint    enance",
        "GRAND TOTAL EXPENSES": "Total Expenses",
        "TOTAL OTHER INCOME / EXPENSES": "Other Non-Operating (Income)/Expense + Tax",
        "EARNINGS AFTER TAX (EAT)": "Net Profit",
    }

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

                    df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
                    df.iloc[:, 2] = pd.to_numeric(df.iloc[:, 2], errors="coerce")
                    filtered_df = df[df.iloc[:, 0].isin(predefined_words)][[df.columns[0], df.columns[2]]]
                    filtered_df.iloc[:, 0] = filtered_df.iloc[:, 0].map(predefined_words)
                    filtered_df.columns = ["Category", "Value"]

                    op_exp = filtered_df.loc[filtered_df["Category"] == "Operating Expenses", "Value"]

                    total_expenses_row = pd.DataFrame([{"Category": "Total Expenses", "Value": op_exp.sum()}])
                    filtered_df = pd.concat(
                        [filtered_df.iloc[: -3], total_expenses_row, filtered_df.iloc[-3:]],
                        ignore_index=True
                    )                
                    hr_benefit = filtered_df.loc[filtered_df["Category"] == "HR + Benefit", "Value"]
                    dep_maint = filtered_df.loc[filtered_df["Category"] == "Depreciation & Maintenance", "Value"]

                    if not op_exp.empty and not hr_benefit.empty and not dep_maint.empty:
                        filtered_df.loc[filtered_df["Category"] == "Operating Expenses", "Value"] = (
                            op_exp.iloc[0] - hr_benefit.iloc[0] - dep_maint.iloc[0]
                        )

                    df_filtered_6 = df[df.iloc[:, 0].astype(str).str.startswith(("6", "5"))]
                    df_top_5 = df_filtered_6.nlargest(5, df.columns[2])[[df.columns[1], df.columns[2]]] if not df_filtered_6.empty else pd.DataFrame()
                    df_top_5.columns = ["Category", "Value"]

                    if filtered_df["Value"].max() > 1_000_000:
                        filtered_df["Value"] /= 1_000_000
                    if df_top_5["Value"].max() > 1_000_000:
                        df_top_5["Value"] /= 1_000_000

                    key = f"{company}_{month_str}_{year}"
                    results[key] = {
                        "filtered_data": filtered_df.to_dict(orient="records"),
                        "top_5_expenses": df_top_5.to_dict(orient="records"),
                    }

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
                    df['nan_2'] = df['nan_2'].map(predefined_budget).fillna(df['nan_2'])

                    for month in df.columns[1:]:
                        key = f"{company}_{to_camel_case(month.split()[0])}_{year}"
                        if key not in results:
                            results[key] = {"filtered_data": [], "top_5_expenses": [], "budget": []}

                        budget_data = [{"Category": row["nan_2"], "Value": row[month]} for _, row in df.iterrows()]

                        if "budget" not in results[key]:
                            results[key]["budget"] = []

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
                        month_name, year = month.split("_")
                        year = int(year)
                        month_str = month_map.get(month_name, month_name)
                        key = f"{company}_{month_str}_{selected_year}"

                        if key not in results:
                            results[key] = {}

                        if "jpcc_vs_others" not in results[key]:  
                            results[key]["jpcc_vs_others"] = []  

                        for i, category in enumerate(df["Category"]): 
                            entry = {
                                "Category": category if selected_year == year else f"{category}_LY",
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
            display_monthly(data, selected_month, selected_year)

    with tab3:
        display_cash_flow_table(data)

if __name__ == "__main__":
    main()
