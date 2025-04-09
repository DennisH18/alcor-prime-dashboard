import streamlit as st
import pandas as pd

import services.styles as styles
import services.supabaseService as supabaseService
import services.helper as helper

st.set_page_config(layout="wide", page_icon="logo.png")
st.logo("logo.png")

styles.style_page()

def main():

    if not helper.verify_user():
        st.switch_page("Login.py")
        return

    df = pd.DataFrame(supabaseService.fetch_data("Users"))
    data_store = helper.fetch_all_data()
    companies, _ = helper.get_available_companies_and_years(data_store)

    st.markdown("<h3>Users</h3>", unsafe_allow_html=True)

    with st.form(key="form_users" ):

        df = df.sort_values("role").reset_index(drop=True)
        
        original_df = df.copy()

        editable_df = df.drop(columns=["id"], errors="ignore")
        editable_df = editable_df[["email", "name", "role", "company"]]

        column_config = {
            "email": st.column_config.TextColumn("Email"),
            "name": st.column_config.TextColumn("Name"),
            "role": st.column_config.TextColumn("Role"),
            "company": st.column_config.SelectboxColumn("Company", options=companies + ["ALL"]),
        }

        edited_df = st.data_editor(
            editable_df.copy(),  
            num_rows="dynamic", 
            column_config=column_config,
            use_container_width=True, 
            hide_index=True
        )

        if "id" in df.columns and len(edited_df) == len(original_df):
            edited_df["id"] = original_df["id"]

        if st.form_submit_button("Save All Changes"):
            supabaseService.save_user_data(edited_df, original_df)
            st.success("All data updated successfully! Refresh to see changes.")

if __name__ == "__main__":
    main()
