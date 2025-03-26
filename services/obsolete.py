def waterfall_chart(data, last_year_data, budget_data):
    datasets = {"Actual": data, "Last Year": last_year_data, "Budget": budget_data}

    df_list = []

    for label, dataset in datasets.items():
        running_total = 0
        df_temp = []

        for category, value in dataset.items():
            if category in ["GROSS PROFIT", "TOTAL EXPENSES"]:
                continue

            if category not in ["REVENUE", "Net Profit"]:
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
        "COGS": "COGS",
        "HR + BENEFIT": "HR+Benefits",
        "Operating Expenses": "Op Exp",
        "Depreciation & Maintenance": "Deprec+Maint",
        "OTHER INCOME / EXPENSES": "Other Exp/Inc",
    }
    df["Category"] = df["Category"].replace(rename_map)

    color_map = {"Actual": "#1f77b4", "Last Year": "#ff7f0e", "Budget": "#2ca02c"}

    bars = (
        alt.Chart(df)
        .mark_bar(size=30)
        .encode(
            x=alt.X(
                "Category:N",
                title="",
                sort=df["Category"].tolist(),
                axis=alt.Axis(labelAngle=0),
            ),
            y=alt.Y("Start:Q", title="Amount"),
            y2="End:Q",
            color=alt.Color(
                "Type:N",
                scale=alt.Scale(
                    domain=list(color_map.keys()), range=list(color_map.values())
                ),
                legend=alt.Legend(title=None),
            ),
            xOffset="Type:N",
            tooltip=["Category", "Values", "Type"],
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

    chart = (bars + text).properties(height=280)
    st.altair_chart(chart, use_container_width=True)


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
        "HUMAN RESOURCES": "HR+Benefit",
        "OPERATIONAL EXPENSES": "Op Exp",
        "DEPRECIATION & MAINTENANCE": "Depr+Maint",
        "OTHER INCOME / EXPENSES": "Other Inc/Exp",
        "NET PROFIT": "Net Profit",
    }

    df["Category"] = df["Category"].replace(rename_map)

    color_map = {
        "Revenue": {"Actual": "#006400", "Last Year": "#228B22", "Budget": "#32CD32"},  # Dark, Medium, Light Green
        "COGS": {"Actual": "#4B0082", "Last Year": "#800080", "Budget": "#DA70D6"},  # Dark, Medium, Light Purple
        "HR+Benefit": {"Actual": "#4B0082", "Last Year": "#800080", "Budget": "#DA70D6"},
        "Op Exp": {"Actual": "#4B0082", "Last Year": "#800080", "Budget": "#DA70D6"},
        "Depr+Maint": {"Actual": "#4B0082", "Last Year": "#800080", "Budget": "#DA70D6"},
        "Other Inc/Exp": {  # Red for negative, Green for positive
            "Actual": lambda v: "#8B0000" if v < 0 else "#006400",  # Dark Red or Dark Green
            "Last Year": lambda v: "#DC143C" if v < 0 else "#228B22",  # Crimson or Medium Green
            "Budget": lambda v: "#FF6347" if v < 0 else "#32CD32",  # Tomato or Light Green
        },
        "Net Profit": {  # Red for negative, Green for positive
            "Actual": lambda v: "#8B0000" if v < 0 else "#006400",  # Dark Red or Dark Green
            "Last Year": lambda v: "#DC143C" if v < 0 else "#228B22",  # Crimson or Medium Green
            "Budget": lambda v: "#FF6347" if v < 0 else "#32CD32",  # Tomato or Light Green
        }
    }

    # Assign colors to dataframe before plotting
    df["Color"] = df.apply(
        lambda row: (
            color_map[row["Category"]][row["Type"]](row["Values"])  # Use function for Net Profit
            if row["Category"] == "Net Profit"
            else color_map[row["Category"]][row["Type"]]  # Use predefined color for other categories
        ),
        axis=1
    )
    bars = (
        alt.Chart(df)
        .mark_bar(size=30)
        .encode(
            x=alt.X(
                "Category:N",
                title="",
                sort=df["Category"].tolist(),
                axis=alt.Axis(labelAngle=0),
            ),
            y=alt.Y("Start:Q", title="Amount"),
            y2="End:Q",
            color=alt.Color(
                "Color:N",
                legend=alt.Legend(title=None),
            ),
            xOffset="Type:N",
            tooltip=["Category", "Values", "Type"],
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

    chart = (bars + text).properties(height=280)
    st.altair_chart(chart, use_container_width=True)



    def get_color(row):
    category, data_type, value = row["Category"], row["Type"], row["Values"]
    
    if category not in color_map:
        return "#000000" 

    if data_type not in color_map[category]:
        return "#000000"

    color_value = color_map[category][data_type]

    return color_value(value) if callable(color_value) else color_value

    df["Color"] = df.apply(get_color, axis=1)

    df["Color"] = df["Color"].astype(str)

    # bars = (
    #     alt.Chart(df)
    #     .mark_bar(size=30)
    #     .encode(
    #         x=alt.X(
    #             "Category:N",
    #             title="",
    #             sort=df["Category"].tolist(),
    #             axis=alt.Axis(labelAngle=0),
    #         ),
    #         y=alt.Y("Start:Q", title="Amount"),
    #         y2="End:Q",
    #         color=alt.Color("Color:N", scale=None),
    #         xOffset="Type:N",
    #         tooltip=["Category", "Values", "Type"],
    #     )
    # )
