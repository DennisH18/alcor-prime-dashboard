import supabase
import streamlit as st
import pandas as pd

SUPABASE_URL = st.secrets["supabase"]["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["supabase"]["SUPABASE_KEY"]

supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_data(table_name):
    response = supabase_client.table(table_name).select('*').execute()

    return response.data


def save_jpcc_data(updated_data, original_data):
    for _, row in updated_data.iterrows():
        try:
            data_dict = {
                "company": row["company"],
                "year": int(row["year"]),
                "month": row["month"],
                "jpcc": int(row["jpcc"]),
                "others": int(row["others"])
            }

            existing = (
                supabase_client.table("JPCC vs Others")
                .select("id")
                .eq("company", data_dict["company"])
                .eq("year", data_dict["year"])
                .eq("month", data_dict["month"])
                .execute()
            )

            if existing.data:
                existing_id = existing.data[0]["id"]
                supabase_client.table("JPCC vs Others")\
                    .update(data_dict)\
                    .eq("id", existing_id)\
                    .execute()
            else:
                supabase_client.table("JPCC vs Others")\
                    .insert(data_dict)\
                    .execute()

        except Exception as e:
            print(f"Error updating/inserting row for {row['company']} {row['month']} {row['year']}: {e}")

    deleted_rows = original_data[~original_data[["year", "month", "company"]].apply(
        lambda row: ((updated_data["year"] == row["year"]) & 
                     (updated_data["month"] == row["month"]) & 
                     (updated_data["company"] == row["company"])).any(), axis=1
    )]

    for _, row in deleted_rows.iterrows():
        try:
            supabase_client.table("JPCC vs Others")\
                .delete()\
                .eq("company", row["company"])\
                .eq("year", int(row["year"]))\
                .eq("month", row["month"])\
                .execute()
        except Exception as e:
            print(f"Error deleting row for {row['company']} {row['month']} {row['year']}: {e}")


def save_coa_data(updated_data, original_data):
    for _, row in updated_data.iterrows():
        try:
            data_dict = row.to_dict()

            existing = (
                supabase_client.table("COA")
                .select("coa")
                .eq("coa", data_dict["coa"])
                .execute()
            )

            if existing.data:
                supabase_client.table("COA")\
                    .update(data_dict)\
                    .eq("coa", data_dict["coa"])\
                    .execute()
            else:
                supabase_client.table("COA")\
                    .insert(data_dict)\
                    .execute()
        except Exception as e:
            print(f"Error updating/inserting COA {row['coa']}: {e}")

    deleted_rows = original_data[~original_data["coa"].isin(updated_data["coa"])]

    for _, row in deleted_rows.iterrows():
        try:
            supabase_client.table("COA")\
                .delete()\
                .eq("coa", row["coa"])\
                .execute()
        except Exception as e:
            print(f"Error deleting COA {row['coa']}: {e}")
            

def save_user_data(updated_data, original_data):

    #add to auth first
    
    updated_ids = []

    for _, row in updated_data.iterrows():
        data_dict = row.to_dict()

        if "id" in data_dict and pd.notnull(data_dict["id"]):
            updated_ids.append(data_dict["id"])
            supabase_client.table("Users") \
                .update(data_dict) \
                .eq("id", data_dict["id"]) \
                .execute()
        else:
            inserted = supabase_client.table("Users") \
                .insert(data_dict) \
                .execute()
            if inserted.data and "id" in inserted.data[0]:
                updated_ids.append(inserted.data[0]["id"])

    if "id" in original_data.columns:
        original_ids = set(original_data["id"].dropna())
        to_delete_ids = original_ids - set(updated_ids)

        for delete_id in to_delete_ids:
            supabase_client.table("Users") \
                .delete() \
                .eq("id", delete_id) \
                .execute()