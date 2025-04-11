import streamlit as st

st.set_page_config(layout="wide", page_icon="logo.png")

import pandas as pd
import datetime as dt
import altair as alt
import calendar

import services.helper as helper
import services.styles as styles
import services.supabaseService as supabaseService


styles.style_page()

all_coa = helper.get_all_coa()
pnl_account_categories_dict = helper.get_pnl_account_categories_dict()
account_categories = helper.transform_to_category_codes(pnl_account_categories_dict)


def waterfall_chart(data, last_year_data, budget_data):

    datasets = {"Actual": data, "Last Year": last_year_data, "Budget": budget_data}

    df_list = []

    for label, dataset in datasets.items():
        running_total = 0
        df_temp = []

        for category, value in dataset.items():
            if category in ["GROSS PROFIT", "TOTAL EXPENSES"]:
                continue

            if category not in ["REVENUE", "NET PROFIT"]:
                value = -abs(value)

            start = running_total
            end = start + value
            running_total = end

            df_temp.append(
                {
                    "Category": category,
                    "Start": start,
                    "End": end,
                    "Values": value,
                    "Type": label,
                }
            )

        df_list.append(pd.DataFrame(df_temp))

    df = pd.concat(df_list, ignore_index=True)

    rename_map = {
        "REVENUE": "Revenue",
        "COGS": "COGS",
        "HUMAN RESOURCES": "HR+Benefit",
        "OPERATIONAL EXPENSES": "Op Exp",
        "DEPRECIATION & MAINTENANCE": "Depr+Maint",
        "OTHER INCOME / EXPENSES": "Other Inc/Exp",
        "NET PROFIT": "Net Profit",
    }

    df["Category"] = df["Category"].replace(rename_map)

    bars = (
        alt.Chart(df)
        .mark_bar(size=30)
        .encode(
            x=alt.X(
                "Category:N",
                title="",
                sort=alt.Sort(rename_map.values()),
                axis=alt.Axis(labelAngle=0),
            ),
            y=alt.Y("Start:Q", title="Amount"),
            y2="End:Q",
            color=alt.Color(
                "Type:N",
                scale=alt.Scale(
                    range=["#a55073", "#75aadb", "#733c96"],
                ),
                legend=alt.Legend(title=None),
            ),
            xOffset="Type:N",
            tooltip=[
                alt.Tooltip("Category:N", title="Category"),
                alt.Tooltip("Values:Q", title="Values", format=",.2f"),
                alt.Tooltip("Type:N", title="Type"),
            ],
        )
    )

    text = bars.mark_text(
        align="center",
        fontSize=10,
        dy=alt.expr(alt.expr.if_(alt.datum.Values > 0, 10, -10)),
    ).encode(
        text=alt.Text("Values:Q", format=",.0f"),
        color=alt.value("black"),
    )

    chart = (bars + text).properties(height=260)
    st.altair_chart(chart, use_container_width=True)


def create_pie_chart(df, title):
    color_mapping = {"JPCC": "#75aadb", "Others": "#36416d"}

    df["CategoryPrefix"] = df["Category"].str.split("_").str[0]

    present_mapping = {
        k: v for k, v in color_mapping.items() if k in df["CategoryPrefix"].unique()
    }

    total = df["Values"].sum()
    df["theta"] = df["Values"] / total * 2 * 3.1415
    df["cumsum"] = df["theta"].cumsum()
    df["startAngle"] = df["cumsum"] - df["theta"]
    df["midAngle"] = df["startAngle"] + df["theta"] / 2
    df["midAngleDeg"] = df["midAngle"] * 180 / 3.1415
    df["Percentage"] = (df["Values"] / total * 100).round(0).astype(int).astype(
        str
    ) + "%"

    color_enc = alt.Color(
        "CategoryPrefix:N", legend=alt.Legend(title=None, labelFontSize=12)
    )

    if present_mapping:
        color_enc = alt.Color(
            "CategoryPrefix:N",
            scale=alt.Scale(
                domain=list(present_mapping.keys()),
                range=list(present_mapping.values()),
            ),
            legend=alt.Legend(title=str(title), titleColor="black"),
        )

    pie_chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=20, outerRadius=45)
        .encode(
            theta=alt.Theta("Values:Q", stack=True),
            color=color_enc,
            tooltip=[
                alt.Tooltip("Category:N", title="Category"),
                alt.Tooltip("Values:Q", title="Values", format=",.2f"),
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
                alt.Tooltip("Values:Q", title="Values", format=",.2f"),
                alt.Tooltip("Percentage:N", title="Percentage"),
            ],
        )
    )

    return pie_chart + text_labels


def comparison_pie_chart(pie_data, selected_year):

    if not pie_data:
        st.info(f"No data available")
        return

    if pie_data:
        df = pd.DataFrame(
            [
                {
                    "Category": f"JPCC_{selected_year}",
                    "Values": pie_data[f"JPCC_{selected_year}"],
                },
                {
                    "Category": f"Others_{selected_year}",
                    "Values": pie_data[f"Others_{selected_year}"],
                },
            ]
        )
        df_ly = pd.DataFrame(
            [
                {
                    "Category": f"JPCC_{selected_year-1}",
                    "Values": pie_data[f"JPCC_{selected_year-1}"],
                },
                {
                    "Category": f"Others_{selected_year-1}",
                    "Values": pie_data[f"Others_{selected_year-1}"],
                },
            ]
        )

        st.altair_chart(create_pie_chart(df, selected_year), use_container_width=True)
        st.altair_chart(
            create_pie_chart(df_ly, selected_year - 1), use_container_width=True
        )


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
                alt.Tooltip("Values:Q", title="Values", format=",.2f"),
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
            <div style='width: 50px; text-align: left;'><b>{percentage}</b></div>
        </div>
        """
        legend_html += "</div>"

        st.markdown(legend_html, unsafe_allow_html=True)


def format_metric(value):
    color = "green" if value > 0 else "#d9224c" if value < 0 else "orange"
    sign = "+" if value > 0 else ("&nbsp;&nbsp;" if value == 0 else "")

    return f"<p style='color:{color}; font-size:12px; font-weight:bold; padding:0px; margin:0px;'>{sign}{value}%</p>"


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
                    "<p style='font-size:12px; padding:0px; margin:0px;'>Target Achievement</p>",
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
                    "<p style='font-size:12px; padding:0px; margin:0px;'>Compare to Budget</p>",
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
                    "<p style='font-size:12px; padding:0px; margin:0px;'>Compare to Budget</p>",
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(format_metric(metric1), unsafe_allow_html=True)

        col1, col2 = st.columns([5, 2], gap="small")
        with col1:
            st.markdown(
                "<p style='font-size:12px; padding:0px; margin:0px;'>Change from Last Year</p>",
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
        last_year_key = f"{company}_{selected_month}_{selected_year-1}"

        if not data[key]["filtered_data"]:
            st.warning(f"Data for {company} available for {selected_month}.")
            continue
        elif not data[last_year_key]["filtered_data"]:
            st.warning(f"Last Year Data for {company} available for {selected_month}.")
            continue
        elif not data[key]["budget"]:
            st.warning(f"Budget Data for {company} available for {selected_month}.")
            continue

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
                comparison_pie_chart(jpcc_vs_others, selected_year)

        with col4:
            with st.container(border=True, height=355):
                st.markdown(
                    f"<h5>Operational Cost Overview</h5>", unsafe_allow_html=True
                )
                cost_pie_chart(operating_expenses)

        with st.container(border=True, height=355):
            st.markdown("<h5>Income Statement</h5>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)

            waterfall_chart(filtered_data, filtered_data_last_year, budget)

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
                comparison_pie_chart(ytd_jpcc_vs, selected_year)

        with col4:
            with st.container(border=True, height=355):
                st.markdown(
                    f"<h5>Operational Cost Overview</h5>", unsafe_allow_html=True
                )
                cost_pie_chart(ytd_top_5)

        with st.container(border=True, height=355):
            st.markdown("<h5>Income Statement</h5>", unsafe_allow_html=True)

            waterfall_chart(ytd_filtered, ytd_filtered_last_year, ytd_budget)

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
        category_order = list(account_categories.keys())
        sorted_categories = sorted(
            cash_flow[company].keys(),
            key=lambda x: (
                category_order.index(x) if x in category_order else float("inf")
            ),
        )
        for category in sorted_categories:
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
        company_html_dict[company] = table_html

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
        "NET REVENUE": "REVENUE",
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
    jpcc_vs_others = pd.DataFrame(supabaseService.fetch_data("JPCC vs Others"))

    for company in companies:

        years_to_check = [selected_year, selected_year - 1]

        for year in years_to_check:

            if year not in data_store[company]:
                continue

            for file_name, df in data_store[company][year].items():

                if df is None or df.empty:
                    st.warning(
                        f"File '{file_name}' for '{company}' in year '{year}' is empty or missing."
                    )
                    continue

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
                        results[key] = {
                            "filtered_data": [],
                            "operating_expenses": [],
                            "jpcc_vs_others": [],
                        }

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
                    df.drop(columns=["nan_3"], inplace=True)

                    def clean_string(s):
                        return str(s).strip().upper()

                    predefined_budget_cleaned = {
                        clean_string(k): v for k, v in predefined_budget.items()
                    }
                    df["nan_2"] = df["nan_2"].apply(clean_string)
                    df = df[df["nan_2"].isin(predefined_budget_cleaned.keys())]
                    df["nan_2"] = df["nan_2"].map(predefined_budget_cleaned)

                    for month in df.columns[1:]:
                        key = f"{company}_{to_camel_case(month.split()[0])}_{year}"

                        if key not in results:
                            results[key] = {
                                "filtered_data": [],
                                "operating_expenses": [],
                                "budget": [],
                                "jpcc_vs_others": [],
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

        df = jpcc_vs_others[
            (jpcc_vs_others["company"] == company)
            & (jpcc_vs_others["year"].isin([selected_year, selected_year - 1]))
        ]

        for month in df["month"].unique():
            month_data = df[df["month"] == month]

            current_year_data = month_data[month_data["year"] == selected_year]
            last_year_data = month_data[month_data["year"] == selected_year - 1]

            key = f"{company}_{month}_{selected_year}"

            if key not in results:
                results[key] = {"jpcc_vs_others": []}

            result = []

            for _, row in current_year_data.iterrows():
                result.append(
                    {"Category": f"JPCC_{selected_year}", "Value": row["jpcc"]}
                )
                result.append(
                    {"Category": f"Others_{selected_year}", "Value": row["others"]}
                )

            for _, row in last_year_data.iterrows():
                result.append(
                    {"Category": f"JPCC_{selected_year-1}", "Value": row["jpcc"]}
                )
                result.append(
                    {"Category": f"Others_{selected_year-1}", "Value": row["others"]}
                )

            results[key]["jpcc_vs_others"] = result

    return results


def main():

    if not helper.verify_user():
        st.switch_page("Login.py")
        return

    data_store = helper.fetch_dropbox_data()
    available_companies, available_years = helper.get_available_companies_and_years(
        data_store
    )

    col1, col2, col3, col4 = st.columns([4, 2, 2, 1])
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
    with col4:
        st.markdown("<div style='width: 1px; height: 28px'></div>", unsafe_allow_html=True)
        if st.button("**Refresh**"):
            st.cache_data.clear()

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
