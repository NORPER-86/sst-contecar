import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

print(f"URL: {url}")
print(f"Key format valid? {key.startswith('eyJ')}")

try:
    supabase: Client = create_client(url, key)
    # Test a simple fetch
    res = supabase.table("observaciones").select("*").limit(1).execute()
    print("Supabase connection SUCCESS!")
    print(f"Data: {res.data}")
except Exception as e:
    print(f"Supabase connection FAILED: {e}")
