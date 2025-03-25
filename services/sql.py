import os
import supabase

# Load environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Initialize Supabase client
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

# Example function to fetch data from a table
def fetch_data(table_name):
    response = supabase_client.table(table_name).select('*').execute()
    if response.error:
        print(f"Error fetching data: {response.error}")
    else:
        return response.data

# Example usage
if __name__ == "__main__":
    table_name = 'your_table_name'
    data = fetch_data(table_name)
    print(data)