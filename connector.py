import pandas as pd
from supabase import create_client, Client

url = "https://myltahcejskoaxlrtilc.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im15bHRhaGNlanNrb2F4bHJ0aWxjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjE5ODUxMzMsImV4cCI6MjAzNzU2MTEzM30.dJNW_f70uN5WZ8UbaOcpJAmGlu6E3ahyptp608YxL8o"

supabase: Client = create_client(url, key)

def fetch_data_as_dataframe(table_name: str, columns: list = None) -> pd.DataFrame:
  query = supabase.table(table_name)
  if columns:
      query = query.select(*columns)

  response = query.execute()
  data = response.data
  print(data)


  return pd.DataFrame(data)