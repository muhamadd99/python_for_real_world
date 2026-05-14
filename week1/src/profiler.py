import sqlite3
from pathlib import Path

def run_data_profile(db_path):
    if not Path(db_path).exists():
        print(f"❌ Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Total Records
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_records = cursor.fetchone()[0]

        # 2. Missing Values
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN job_title IS NULL OR job_title = '' THEN 1 ELSE 0 END),
                SUM(CASE WHEN company IS NULL OR company = '' THEN 1 ELSE 0 END),
                SUM(CASE WHEN description IS NULL OR description = '' THEN 1 ELSE 0 END)
            FROM jobs
        """)
        null_title, null_company, null_desc = cursor.fetchone()

        # 3. Avg Length
        cursor.execute("SELECT AVG(LENGTH(description)) FROM jobs")
        avg_len = int(cursor.fetchone()[0] or 0)

        # 4. Shortest Description
        cursor.execute("""
            SELECT LENGTH(description) as len, source_id, job_title 
            FROM jobs ORDER BY len ASC LIMIT 1
        """)
        short = cursor.fetchone()

        # 5. Longest Description
        cursor.execute("""
            SELECT LENGTH(description) as len, source_id, job_title 
            FROM jobs ORDER BY len DESC LIMIT 1
        """)
        long = cursor.fetchone()

        # --- OUTPUT FORMAT ---
        print("--- 🔍 DATA QUALITY REPORT ---")
        print(f"📈 Total Records: {total_records}")
        print(f"❓ Missing Values -> job_title: {null_title}, company: {null_company}, description: {null_desc}")
        print(f"📝 Avg Description Length: {avg_len} chars")
        
        if short:
            print(f"⚠️  Shortest Description: {short[0]} chars")
            print(f"   ↳ source_id: {short[1]} | job_title: {short[2]}")
        
        if long:
            print(f"🚨 Longest Description: {long[0]} chars")
            print(f"   ↳ source_id: {long[1]} | job_title: {long[2]}")

        conn.close()

    except sqlite3.Error as e:
        print(f"❌ Profiling failed: {e}")