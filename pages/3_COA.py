import streamlit as st
import pandas as pd

import services.styles as styles
import services.supabaseService as supabaseService
import services.helper as helper

styles.style_page()

def main():

    if not helper.verify_user():
        st.switch_page("Login.py")
        return


    df = pd.DataFrame(supabaseService.fetch_data("COA"))

    st.markdown("<h3>COA</h3>", unsafe_allow_html=True)


    main_category = df["main_category"].unique()

    selected_categories = st.multiselect("Select Category (Default = All)", main_category)

    if not selected_categories:
        selected_categories = main_category

    for cat in selected_categories:

        st.markdown(f"<h4>{cat}</h4>", unsafe_allow_html=True)

        subcat_df = df[df["main_category"] == cat]
        subcat_df = subcat_df.sort_values("coa").reset_index(drop=True).drop(columns=["main_category"], errors="ignore")

        column_config = {
            "coa": st.column_config.NumberColumn("COA", help="Year of data"),
            "description": st.column_config.TextColumn("Description", help="Month of data"),
            "subcategory": st.column_config.TextColumn("Subcategory", help="Year of data"),
        }

        edited_df = st.data_editor(
            subcat_df, 
            num_rows="dynamic", 
            use_container_width=True, 
            column_config=column_config,
            key=cat, 
            hide_index=True
        )

        edited_df["main_category"] = cat
        subcat_df["main_category"] = cat

        if not edited_df.equals(subcat_df):
            if st.button("Save All Changes", key=f"save_{cat}"):
                supabaseService.save_coa_data(edited_df, subcat_df)
                st.success("All data updated successfully! Refresh to see changes.")

    st.write("#")


if __name__ == "__main__":
    main()
