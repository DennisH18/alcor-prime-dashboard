import streamlit as st
import pandas as pd
import calendar

import services.styles as styles
import services.supabaseService as supabaseService
import services.helper as helper

styles.style_page()


def main():

    if not helper.verify_user():
        st.switch_page("Login.py")
        return

        
    df = pd.DataFrame(supabaseService.fetch_data("JPCC vs Others"))
    data_store = helper.fetch_all_data()
    save_success = False

    st.markdown("<h3>JPCC vs Others</h3>", unsafe_allow_html=True)

    companies = data_store.keys()

    selected_companies = st.multiselect("Select PT (Default = All)", companies)

    if not selected_companies:
        selected_companies = companies

    months = calendar.month_abbr[1:]

    for company in selected_companies:

        st.markdown(f"<h4>{company}</h4>", unsafe_allow_html=True)

        column_config = {
            "year": st.column_config.NumberColumn("Year", help="Year of data", format="%d"),
            "month": st.column_config.SelectboxColumn("Month", help="Month of data", options=months),
            "jpcc": st.column_config.NumberColumn("JPCC", help="JPCC value", format="localized"),
            "others": st.column_config.NumberColumn("Others", help="Others value", format="localized"),
        }
        
        if company in df["company"].values:
            company_df = df[df["company"] == company].drop(columns=["id", "company"], errors="ignore")
        else:
            company_df = pd.DataFrame([{"year": 2024, "month": None, "jpcc": 0.0, "others": 0.0}])

        company_df = company_df.sort_values("year").reset_index(drop=True)
        company_df = company_df[["year", "month", "jpcc", "others"]]
        edited_df = st.data_editor(
            company_df[["year", "month", "jpcc", "others"]], 
            num_rows="dynamic", 
            use_container_width=True, 
            key=company, 
            column_config=column_config, 
            hide_index=True
        )

        edited_df["company"] = company
        company_df["company"] = company

        if not edited_df.equals(company_df):
            if st.button("Save All Changes", key=f"save_{company}"):
                supabaseService.save_jpcc_data(edited_df, company_df)
                st.success("All data updated successfully! Refresh to see changes.")


if __name__ == "__main__":
    main()
