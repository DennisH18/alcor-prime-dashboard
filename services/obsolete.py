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
