import streamlit as st
import pandas as pd
import datetime as dt
import altair as alt
import calendar

import services.helper as helper
import services.styles as styles
import services.auth as auth
from services.data import pnl_account_categories_dict

styles.style_page()
all_coa = helper.get_all_coa()
account_categories = helper.transform_to_category_codes(pnl_account_categories_dict)

def waterfall_chart(data, title):

    df = pd.DataFrame(
        [
            {"Category": category, "Values": data.get(category, 0)}
            for category in account_categories.keys()
            if category not in ["GROSS PROFIT", "TOTAL EXPENSES"]
        ]
    )

    rename_map = {
        "REVENUE": "Revenue",
        "HUMAN RESOURCES": "HR+Benefit",
        "OPERATIONAL EXPENSES": "Op Exp",
        "DEPRECIATION & MAINTENANCE": "Depr+Maint",
        "OTHER INCOME / EXPENSES": "Other Inc/Exp",
        "NET PROFIT": "Net Profit",
    }

    df["Category"] = df["Category"].replace(rename_map)

    df["Values"] = df.apply(
        lambda row: (
            row["Values"]
            if row["Category"] in ["Revenue", "Net Profit", "Other Inc/Exp"]
            else -abs(row["Values"])
        ),
        axis=1,
    ).round(0)

    df.loc[0, "Start"] = 0
    df.loc[0, "End"] = df.loc[0, "Values"]

    for i in range(1, len(df)):
        df.loc[i, "Start"] = df.loc[i - 1, "End"]
        df.loc[i, "End"] = df.loc[i, "Start"] + df.loc[i, "Values"]

    color_map = {
        "Revenue": "#008000",
        "COGS": "#d9224c",
        "HR+Benefit": "#d9224c",
        "Op Exp": "#d9224c",
        "Depr+Maint": "#d9224c",

    }

    color_map["Other Inc/Exp"] = (
        "#008000" if data.get("OTHER INCOME / EXPENSES", 0) > 0 else "#d9224c"
    )
    color_map["Net Profit"] = (
        "#008000" if data.get("NET PROFIT", 0) > 0 else "darkred"
    )

    bars = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(
                "Category:N",
                title="",
                sort=df["Category"].tolist(),
                axis=alt.Axis(labelAngle=0, labelOverlap="parity"),
            ),
            y=alt.Y(
                "Start:Q",
                title=None            ),
            y2="End:Q",
            color=alt.Color(
                "Category:N",
                scale=alt.Scale(
                    domain=list(color_map.keys()), range=list(color_map.values())
                ),
                legend=None,
            ),
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

    chart = (bars + text).properties(
        height=270, title=alt.TitleParams(text=title, fontSize=16)
    )
    st.altair_chart(chart, use_container_width=True)



def create_pie_chart(df):
    color_mapping = {
        "JPCC": "#36416d",
        "OTHERS": "#75aadb",
        "JPCC_LY": "#36416d",
        "OTHERS_LY": "#75aadb",
    }

    present_categories = df["Category"].unique().tolist()
    filtered_color_mapping = {k: v for k, v in color_mapping.items() if k in present_categories}

    df["Color"] = df["Category"].map(filtered_color_mapping)

    total = df["Values"].sum()
    df["theta"] = df["Values"] / total * 2 * 3.1415
    df["cumsum"] = df["theta"].cumsum()
    df["startAngle"] = df["cumsum"] - df["theta"]
    df["midAngle"] = df["startAngle"] + df["theta"] / 2
    df["midAngleDeg"] = df["midAngle"] * 180 / 3.1415
    df["Percentage"] = (df["Values"] / total * 100).round(0).astype(int).astype(str) + "%"

    pie_chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=20, outerRadius=45)
        .encode(
            theta=alt.Theta("Values:Q", stack=True),
            color=alt.Color(
                "Category:N",
                scale=alt.Scale(domain=list(filtered_color_mapping.keys()), 
                                range=list(filtered_color_mapping.values())),
                legend=alt.Legend(title=None, labelFontSize=12),
            ),
            tooltip=[
                alt.Tooltip("Category:N", title="Category"),
                alt.Tooltip("Values:Q", title="Values", format=","),
                alt.Tooltip("Percentage:N", title="Percentage"),
            ],
        )
        .properties(width=180, height=120)
    )

    text_labels = (
        alt.Chart(df)
        .mark_text(size=11, color="black", align="center", baseline="middle")
        .encode(
            text=alt.Text("Percentage:N"),
            theta=alt.Theta("Values:Q", stack=True),
            angle=alt.Angle("midAngleDeg:Q"),
            radius=alt.value(60),
            tooltip=[
                alt.Tooltip("Category:N", title="Category"),
                alt.Tooltip("Values:Q", title="Values", format=","),
                alt.Tooltip("Percentage:N", title="Percentage"),
            ],
        )
    )

    return pie_chart + text_labels



def comparison_pie_chart(pie_data):
    if pie_data:
        df = pd.DataFrame(
            [
                {"Category": "JPCC", "Values": pie_data["JPCC"]},
                {"Category": "OTHERS", "Values": pie_data["OTHERS"]},
            ]
        )
        df_ly = pd.DataFrame(
            [
                {"Category": "JPCC_LY", "Values": pie_data["JPCC_LY"]},
                {"Category": "OTHERS_LY", "Values": pie_data["OTHERS_LY"]},
            ]
        )

        st.altair_chart(create_pie_chart(df), use_container_width=True)
        st.altair_chart(create_pie_chart(df_ly), use_container_width=True)


def cost_pie_chart(pie_data):

    df = pd.DataFrame(list(pie_data.items()), columns=["Category", "Values"])

    df_sorted = df.sort_values("Values", ascending=False)
    df_top = df_sorted.head(4)
    df_others = pd.DataFrame(
        [["Others", df_sorted["Values"][4:].sum()]], columns=df.columns
    )
    df = pd.concat([df_top, df_others], ignore_index=True)

    fixed_colors = ["#7776a6", "#d9224c", "#6094cc", "#36416d", "#a55073"]
    df["Color"] = fixed_colors[: len(df)]

    total = df["Values"].sum()
    df["Percentage"] = (df["Values"] / total * 100).round(0).astype(int).astype(
        str
    ) + "%"
    df["Legend"] = df.apply(
        lambda row: f"{row['Category']} - {row['Percentage']}", axis=1
    )

    pie_chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=30, outerRadius=60)
        .encode(
            theta=alt.Theta("Values:Q", stack=True),
            color=alt.Color(
                "Legend:N",
                scale=alt.Scale(
                    domain=df["Legend"].tolist(), range=df["Color"].tolist()
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("Category:N", title="Category"),
                alt.Tooltip("Values:Q", title="Values", format=","),
                alt.Tooltip("Percentage:N", title="Percentage"),
            ],
        )
        .properties(width=200, height=140)
    )

    st.altair_chart(pie_chart, use_container_width=True)

    for category, color, percentage in zip(
        df["Category"], df["Color"], df["Percentage"]
    ):
        legend_html = """
        <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%;'>
        """
        legend_html += f"""
        <div style='display: flex; align-items: center; font-size: 12px; margin-bottom: 5px; border-bottom: 1px solid #ddd; padding-bottom: 0px;'>
            <div style='width: 14px; height: 14px; background-color: {color}; border-radius: 50%; margin-right: 10px;'></div>
            <div style='width: 220px; text-align: left;'>{category}</div>
            <div style='width: 50px; text-align: left;'>{percentage}</div>
        </div>
        """
        legend_html += "</div>"

        st.markdown(legend_html, unsafe_allow_html=True)


def format_metric(value):
    color = "green" if value > 0 else "#d9224c" if value < 0 else "orange"
    sign = "+" if value > 0 else ("&nbsp;&nbsp;" if value == 0 else "")

    return f"<p style='color:{color}; font-size:12px; font-weight:bold;'>{sign}{value}%</p>"


def display_metric(title, key, amount, metric1, metric2):
    with st.container(border=True, height=170):
        st.markdown(f"<h5>{title}</h5>", unsafe_allow_html=True)

        if title == "Revenue":
            st.markdown(
                f"<h4 style='color:#36416d;'>IDR  {amount:,.0f}</h4>",
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
                f"<h4 style='color:{color};'>IDR  {amount:,.0f}</h4>",
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
                f"<h4 style='color:#d9224c;'>IDR  {amount:,.0f}</h4>",
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

        company_data = {
            key: value for key, value in data.items() if key.startswith(company)
        }
        key = f"{company}_{selected_month}_{selected_year}"

        filtered_data = {
            item["Category"]: item["Value"]
            for item in company_data.get(key, {}).get("filtered_data", [])
        }
        operating_expenses = {
            item["Category"]: item["Value"]
            for item in company_data.get(key, {}).get("operating_expenses", [])
        }

        jpcc_vs_others = {
            item["Category"]: item["Value"]
            for item in company_data.get(key, {}).get("jpcc_vs_others", [])
        }
        budget = {
            item["Category"]: item["Value"]
            for item in company_data.get(key, {}).get("budget", [])
        }

        last_year_key = f"{company}_{selected_month}_{selected_year-1}"
        filtered_data_last_year = {
            item["Category"]: item["Value"]
            for item in company_data.get(last_year_key, {}).get("filtered_data", [])
        }

        metrics = {
            "Revenue": (
                "revenue",
                filtered_data.get("REVENUE", 0),
                filtered_data_last_year.get("REVENUE", 0),
                budget.get("REVENUE", 0),
            ),
            "Total Expenses": (
                "expense",
                filtered_data.get("TOTAL EXPENSES", 0),
                filtered_data_last_year.get("TOTAL EXPENSES", 0),
                budget.get("TOTAL EXPENSES", 0),
            ),
            "COGS": (
                "cogs",
                filtered_data.get("COGS", 0),
                filtered_data_last_year.get("COGS", 0),
                budget.get("COGS", 0),
            ),
            "Net Profit": (
                "net",
                filtered_data.get("NET PROFIT", 0),
                filtered_data_last_year.get("NET PROFIT", 0),
                budget.get("NET PROFIT", 0),
            ),
        }

        col1, col2, col3, col4 = st.columns([2, 2, 3, 3])

        for i, (label, (key, current, last_year, budgeted)) in enumerate(
            metrics.items()
        ):

            year_over_year_change = calculate_percentage_change(current, last_year)
            budget_percentage_change = calculate_percentage_change(current, budgeted)

            with col1 if i % 2 == 0 else col2:
                display_metric(
                    label,
                    f"{key}_{company.lower()}",
                    current,
                    budget_percentage_change,
                    year_over_year_change,
                )

        with col3:
            with st.container(border=True, height=355):
                st.markdown(f"<h5>JPCC vs Others</h5>", unsafe_allow_html=True)
                comparison_pie_chart(jpcc_vs_others)

        with col4:
            with st.container(border=True, height=355):
                st.markdown(
                    f"<h5>Operational Cost Overview</h5>", unsafe_allow_html=True
                )
                cost_pie_chart(operating_expenses)

        with st.container(border=True, height=355):
            st.markdown("<h5>Income Statement</h5>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)

            with col1:
                waterfall_chart(filtered_data, "Actual")
            with col2:
                waterfall_chart(budget, "Budget")

        st.divider()


def display_ytd(data, selected_month, selected_year):
    companies = sorted(set(key.split("_")[0] for key in data.keys()))

    month_names = list(calendar.month_abbr)
    selected_month_index = month_names.index(selected_month)
    valid_months = month_names[1 : selected_month_index + 1]

    for company in companies:
        st.markdown(f"<h4>{company}</h4>", unsafe_allow_html=True)

        company_data = {
            key: value for key, value in data.items() if key.startswith(company)
        }

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

            for item in sheet.get("operating_expenses", []):
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

            last_year_sheet = company_data.get(
                f"{company}_{month}_{selected_year-1}", {}
            )

            for item in last_year_sheet.get("operating_expenses", []):
                category = item["Category"]
                value = item["Value"]
                ytd_top_5_last_year[category] = (
                    ytd_top_5_last_year.get(category, 0) + value
                )

            for item in last_year_sheet.get("filtered_data", []):
                category = item["Category"]
                value = item["Value"]
                ytd_filtered_last_year[category] = (
                    ytd_filtered_last_year.get(category, 0) + value
                )

            metrics = {
                "Revenue": (
                    "revenue",
                    ytd_filtered.get("REVENUE", 0),
                    ytd_filtered_last_year.get("REVENUE", 0),
                    ytd_budget.get("REVENUE", 0),
                ),
                "Total Expenses": (
                    "expense",
                    ytd_filtered.get("TOTAL EXPENSES", 0),
                    ytd_filtered_last_year.get("TOTAL EXPENSES", 0),
                    ytd_budget.get("TOTAL EXPENSES", 0),
                ),
                "COGS": (
                    "cogs",
                    ytd_filtered.get("COGS", 0),
                    ytd_filtered_last_year.get("COGS", 0),
                    ytd_budget.get("COGS", 0),
                ),
                "Net Profit": (
                    "net",
                    ytd_filtered.get("NET PROFIT", 0),
                    ytd_filtered_last_year.get("NET PROFIT", 0),
                    ytd_budget.get("NET PROFIT", 0),
                ),
            }

        col1, col2, col3, col4 = st.columns([2, 2, 3, 3])

        for i, (label, (key, actual, last_year, budgeted)) in enumerate(
            metrics.items()
        ):
            budget_percentage_change = calculate_percentage_change(actual, budgeted)
            last_year_percentage_change = calculate_percentage_change(actual, last_year)

            with col1 if i % 2 == 0 else col2:
                display_metric(
                    label,
                    f"{key}_ytd_{company.lower()}",
                    actual,
                    budget_percentage_change,
                    last_year_percentage_change,
                )

        with col3:
            with st.container(border=True, height=355):
                st.markdown(f"<h5>JPCC vs Others</h5>", unsafe_allow_html=True)
                comparison_pie_chart(ytd_jpcc_vs)

        with col4:
            with st.container(border=True, height=355):
                st.markdown(
                    f"<h5>Operational Cost Overview</h5>", unsafe_allow_html=True
                )
                cost_pie_chart(ytd_top_5)

        with st.container(border=True, height=355):
            st.markdown("<h5>Income Statement</h5>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)

            with col1:
                waterfall_chart(ytd_filtered, "Actual")
            with col2:
                waterfall_chart(ytd_budget, "Budget")

        st.divider()


def display_cash_flow_table(data, selected_year):

    companies = sorted({key.split("_")[0] for key in data.keys()})
    all_months = sorted(
        {key.split("_")[1] for key in data.keys()},
        key=lambda x: list(calendar.month_abbr).index(x),
    )
    company_html_dict = {}

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
                    "Last": {m: 0 for m in all_months},
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
                    "Last": {m: 0 for m in all_months},
                }
            if year == str(selected_year):
                cash_flow[company][category]["Budget"][month] = amount
    for company in cash_flow:
        for category in cash_flow[company]:
            for metric in ["Actual", "Budget", "Last"]:
                cash_flow[company][category][metric]["YTD"] = sum(
                    cash_flow[company][category][metric].values()
                )
    for company in cash_flow:
        if "REVENUE" in cash_flow[company] and "NET PROFIT" in cash_flow[company]:
            np_margin = {"Actual": {}, "Budget": {}, "Last": {}}
            for metric in ["Actual", "Budget", "Last"]:
                for m in all_months:
                    rev = cash_flow[company]["REVENUE"][metric].get(m, 0)
                    net = cash_flow[company]["NET PROFIT"][metric].get(m, 0)
                    margin = (net / rev * 100) if rev != 0 else 0
                    np_margin[metric][m] = margin
                np_margin[metric]["YTD"] = (
                    sum(np_margin[metric][m] for m in all_months) / len(all_months)
                    if all_months
                    else 0
                )
            cash_flow[company]["NET PROFIT MARGIN (%)"] = np_margin

    col1, col2 = st.columns([4, 1])

    st.divider()

    for company in companies:
        headers = ["ID", "Category", "Actual/Target"] + all_months + ["YTD"]
        rows = ""
        row_id = 1
        for category in cash_flow[company]:
            if category == "NET PROFIT MARGIN (%)":
                continue
            actual_values = "".join(
                f"<td>{cash_flow[company][category]['Actual'].get(m, 0):,.0f}</td>"
                for m in all_months
            )
            budget_values = "".join(
                f"<td>{cash_flow[company][category]['Budget'].get(m, 0):,.0f}</td>"
                for m in all_months
            )
            last_values = "".join(
                f"<td>{cash_flow[company][category]['Last'].get(m, 0):,.0f}</td>"
                for m in all_months
            )

            actual_ytd = (
                f"<td>{cash_flow[company][category]['Actual']['YTD']:,.0f}</td>"
            )
            budget_ytd = (
                f"<td>{cash_flow[company][category]['Budget']['YTD']:,.0f}</td>"
            )
            last_ytd = f"<td>{cash_flow[company][category]['Last']['YTD']:,.0f}</td>"

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

        if "NET PROFIT MARGIN (%)" in cash_flow[company]:
            np = cash_flow[company]["NET PROFIT MARGIN (%)"]
            actual_values = "".join(
                f"<td>{np['Actual'].get(m, 0):,.0f}%</td>" for m in all_months
            )
            budget_values = "".join(
                f"<td>{np['Budget'].get(m, 0):,.0f}%</td>" for m in all_months
            )
            last_values = "".join(
                f"<td>{np['Last'].get(m, 0):,.0f}%</td>" for m in all_months
            )
            actual_ytd = f"<td>{np['Actual']['YTD']:,.0f}%</td>"
            budget_ytd = f"<td>{np['Budget']['YTD']:,.0f}%</td>"
            last_ytd = f"<td>{np['Last']['YTD']:,.0f}%</td>"

            rows += f"""
                <tr>
                    <td rowspan="3">{row_id}</td>
                    <td rowspan="3" style="text-align: left; padding-left: 10px;">NET PROFIT MARGIN (%)</td>
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
        st.components.v1.html(table_html, height=1050, scrolling=True)
        company_html_dict[company]  = table_html


    excel_file = helper.export_all_tables_to_excel(company_html_dict)

    with col1:
        st.write("")
        st.markdown("<h4>Profit and Loss Data</h4>", unsafe_allow_html=True)
    with col2:
        st.write("")
        st.download_button(
            label=":green[**Download to Excel**]",
            data=excel_file,
            file_name="Profit and Loss Data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


def to_camel_case(month):
    return "".join(word.capitalize() for word in month.lower().split())


@st.cache_data
def prepare_data(data_store, companies, selected_year):

    results = {}

    predefined_budget = {
        "TOTAL REVENUES": "REVENUE",
        "TOTAL COGS": "COGS",
        "GROSS PROFIT": "GROSS PROFIT",
        "TOTAL HUMAN RESOURCES": "HUMAN RESOURCES",
        "TOTAL OPERATING & GA EXPENSES": "OPERATIONAL EXPENSES",
        "TOTAL DEPRECIATION & REPAIR MAINTENANCE": "DEPRECIATION & MAINTENANCE",
        "GRAND TOTAL EXPENSES": "TOTAL EXPENSES",
        "TOTAL OTHER INCOME / EXPENSES": "OTHER INCOME / EXPENSES",
        "EARNINGS AFTER TAX (EAT)": "NET PROFIT",
    }

    month_abbr = set(calendar.month_abbr[1:])

    for company in companies:
        years_to_check = [selected_year, selected_year - 1]
        for year in years_to_check:

            for file_name, df in data_store[company][year].items():

                if "Management Report" in file_name:
                    month_str = next(
                        (month for month in month_abbr if month in file_name), None
                    )
                    if not month_str:
                        continue

                    key = f"{company}_{month_str}_{year}"

                    if pd.to_numeric(df.iloc[0], errors="coerce").notna().all():
                        df.iloc[0] = df.iloc[1]

                    df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
                    df.iloc[:, 2] = pd.to_numeric(df.iloc[:, 2], errors="coerce")

                    valid_codes = set(
                        str(code)
                        for codes in account_categories.values()
                        if codes
                        for code in codes
                    )
                    df = df[df.iloc[:, 0].isin(valid_codes)]

                    categorized_data = {category: 0 for category in account_categories}

                    for _, row in df.iterrows():
                        try:
                            account_code = int(row.iloc[0])
                            value = float(row.iloc[2])
                        except ValueError:
                            continue

                        for category, codes in account_categories.items():
                            if codes and account_code in codes:
                                categorized_data[category] += value

                    if categorized_data["REVENUE"] and categorized_data["COGS"]:
                        categorized_data["GROSS PROFIT"] = (
                            categorized_data["REVENUE"] - categorized_data["COGS"]
                        )

                    categorized_data["TOTAL EXPENSES"] = (
                        categorized_data["OPERATIONAL EXPENSES"]
                        + categorized_data["HUMAN RESOURCES"]
                        + categorized_data["DEPRECIATION & MAINTENANCE"]
                    )

                    if categorized_data["GROSS PROFIT"] is not None:
                        categorized_data["NET PROFIT"] = (
                            categorized_data["GROSS PROFIT"]
                            - categorized_data["TOTAL EXPENSES"]
                            + categorized_data["OTHER INCOME / EXPENSES"]
                        )

                    filtered_df = pd.DataFrame(
                        [
                            {"Category": category, "Value": value}
                            for category, value in categorized_data.items()
                            if value is not None
                        ]
                    )

                    # Top expenses
                    category_col = df.columns[0]
                    df[category_col] = df[category_col].astype(int)
                    operating_expense_df = df[
                        df[category_col].isin(
                            account_categories["OPERATIONAL EXPENSES"]
                        )
                    ].drop(columns=df.columns[0])
                    operating_expense_df.columns = ["Category", "Value"]

                    if filtered_df["Value"].max() > 1_000:
                        filtered_df["Value"] /= 1_000
                    if (
                        not operating_expense_df.empty
                        and operating_expense_df["Value"].max() > 1_000
                    ):
                        operating_expense_df["Value"] /= 1_000

                    if key not in results:
                        results[key] = {"filtered_data": [], "operating_expenses": []}

                    results[key].update(
                        {
                            "filtered_data": filtered_df.to_dict(orient="records"),
                            "operating_expenses": operating_expense_df.to_dict(
                                orient="records"
                            ),
                        }
                    )

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
                    df = df[["nan_2", "nan_3"] + month_cols]
                    df["nan_2"] = df["nan_2"].fillna(df["nan_3"])
                    df.drop(columns=["nan_3"], errors="ignore", inplace=True)
                    df = df[df["nan_2"].isin(predefined_budget.keys())][
                        ["nan_2"] + month_cols
                    ]
                    df["nan_2"] = df["nan_2"].map(predefined_budget)

                    for month in df.columns[1:]:
                        key = f"{company}_{to_camel_case(month.split()[0])}_{year}"

                        if key not in results:
                            results[key] = {
                                "filtered_data": [],
                                "operating_expenses": [],
                                "budget": [],
                            }
                        elif "budget" not in results[key]:
                            results[key]["budget"] = []

                        budget_data = [
                            {"Category": row["nan_2"], "Value": row[month]}
                            for _, row in df.iterrows()
                        ]

                        values = [item["Value"] for item in budget_data]
                        if max(values) > 1_000:
                            for item in budget_data:
                                item["Value"] /= 1_000

                        results[key]["budget"].extend(budget_data)

                elif "JPCC vs Others" in file_name:

                    df.iloc[4] = df.iloc[4].apply(
                        lambda x: (
                            str(int(x))
                            if isinstance(x, float) and x.is_integer()
                            else str(x)
                        )
                    )
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
                        "Desember": "Dec",
                    }

                    for month in df.columns[1:]:
                        month_name, budget_year = month.split("_")
                        budget_year = int(budget_year)
                        month_str = month_map.get(month_name, month_name)
                        key = f"{company}_{month_str}_{selected_year}"
                        if key not in results:
                            results[key] = {
                                "filtered_data": [],
                                "operating_expenses": [],
                                "budget": [],
                            }

                        if "jpcc_vs_others" not in results[key]:
                            results[key]["jpcc_vs_others"] = []

                        for i, category in enumerate(df["Category"]):
                            entry = {
                                "Category": (
                                    category
                                    if selected_year == budget_year
                                    else f"{category}_LY"
                                ),
                                "Value": df.at[i, month],
                            }

                            results[key]["jpcc_vs_others"].append(entry)

    return results


def main():

    auth.login()
    if not st.session_state.authenticated:
        return

    data_store = helper.fetch_all_data()
    available_companies, available_years = helper.get_available_companies_and_years(
        data_store
    )

    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        st.markdown("<h3>Finance Dashboard</h3>", unsafe_allow_html=True)
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

    data = prepare_data(data_store, companies, selected_year)
    available_months = helper.get_available_months(data, companies, selected_year)
    tab1, tab2, tab3 = st.tabs(["Monthly Dashboard", "YTD Dashboard", "Data"])

    with tab1:
        if available_months:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write("#")
                st.markdown("<h4>Monthly Dashboard</h4>", unsafe_allow_html=True)
            with col2:
                selected_month = st.selectbox(
                    "Select Month",
                    available_months,
                    index=len(available_months) - 1 if available_months else None,
                    key="monthly",
                )
            st.divider()
            display_monthly(data, selected_month, selected_year)

    with tab2:
        if available_months:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write("#")
                st.markdown("<h4>YTD Dashboard</h4>", unsafe_allow_html=True)
            with col2:
                selected_month = st.selectbox(
                    "Select Month",
                    available_months,
                    index=len(available_months) - 1 if available_months else None,
                    key="ytd",
                )
            st.divider()
            display_ytd(data, selected_month, selected_year)

    with tab3:
        display_cash_flow_table(data, selected_year)


if __name__ == "__main__":
    main()
