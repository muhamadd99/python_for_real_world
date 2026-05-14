import sqlite3
import json
import os
from pathlib import Path

def init_db(db_path):
    """Initializes the SQLite database and creates the jobs table."""
    conn = sqlite3.connect(db_path) #create database and connect
    cursor = conn.cursor() #like a worker. the one who enable pointing rows and running cmd
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            source_id TEXT PRIMARY KEY,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            description TEXT NOT NULL,
            tech_stack TEXT
        )
    """)
    conn.commit() #save button for database
    return conn

def load_all_jsons(input_dir, output_dir):
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    db_path = os.path.join(output_dir, "jobs.db")
    
    conn = init_db(db_path)
    cursor = conn.cursor()
    
    input_path = Path(input_dir)
    json_files = list(input_path.glob("*.json"))
    
    stats = {"inserted": 0, "skipped": 0, "total": len(json_files)}
    
    print("🥇 Gold: ...")

    for file_path in json_files:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        try:
            # INSERT OR IGNORE handles idempotency at the SQL level
            cursor.execute("""
                INSERT OR IGNORE INTO jobs (source_id, job_title, company, description)
                VALUES (?, ?, ?, ?)
            """, (data["source_id"], data["job_title"], data["company"], data["description"]))
            
            if cursor.rowcount > 0:
                print(f"✅ Inserted: {file_path.name}")
                stats["inserted"] += 1
            else: #means if rowcount == 0. got error
                print(f"⏭️ Skipped (duplicate): {file_path.name}")
                stats["skipped"] += 1
                
        except sqlite3.Error as e: #disk issue and database correction
            print(f"❌ Failed: {file_path.name} - {e}")

    conn.commit()
    conn.close()

    print(f"\n📊 Gold Summary:")
    print(f"Total: {stats['total']} | Inserted: {stats['inserted']} | Skipped: {stats['skipped']}")