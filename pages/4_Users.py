import streamlit as st
import pandas as pd
import services.styles as styles
import services.supabaseService as supabaseService
import services.helper as helper


styles.style_page()

def main():
    df = pd.DataFrame(supabaseService.fetch_data("Users"))
    data_store = helper.fetch_all_data()
    companies, _ = helper.get_available_companies_and_years(data_store)

    st.markdown("<h3>Users</h3>", unsafe_allow_html=True)

    df = df.sort_values("role").reset_index(drop=True)
    
    original_df = df.copy()

    editable_df = df.drop(columns=["id"], errors="ignore")
    editable_df = editable_df[["name", "role", "company"]]

    column_config = {
        "name": st.column_config.TextColumn("Name"),
        "role": st.column_config.TextColumn("Role"),
        "company": st.column_config.SelectboxColumn("Company", options=companies),
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

    if not edited_df.equals(original_df[["name", "role", "company", "id"]]):
        if st.button("Save All Changes"):
            supabaseService.save_user_data(edited_df, original_df)
            st.success("All data updated successfully! Refresh to see changes.")

if __name__ == "__main__":
    main()
