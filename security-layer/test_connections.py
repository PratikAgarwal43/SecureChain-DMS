import os
import psycopg2
from dotenv import load_dotenv

def test_database():
    load_dotenv()
    db_url = os.environ.get("DATABASE_URL")
    
    print("\n--- Testing Vault 1 (PostgreSQL) ---")
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Count tables in public schema
        cur.execute("""
            SELECT count(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = cur.fetchone()[0]
        
        if table_count >= 17:
            print(f"[PASS] Successfully connected to PostgreSQL! Found {table_count} tables.")
        else:
            print(f"[WARN] Connected, but only found {table_count} tables. Expected 17. Did the migration run?")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[FAIL] Could not connect to PostgreSQL: {e}")

if __name__ == "__main__":
    test_database()
