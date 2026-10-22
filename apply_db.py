import sqlite3
import os

db_path = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), "Gravity", "Databases", "gravity_brain.db")
print(f"Opening DB at {db_path}")

try:
    conn = sqlite3.connect(db_path)
    
    # Try adding the columns
    try:
        conn.execute("ALTER TABLE tiktok_snapshots ADD COLUMN room_id TEXT DEFAULT ''")
        print("Added room_id")
    except sqlite3.OperationalError as e:
        print(f"room_id: {e}")
        
    try:
        conn.execute("ALTER TABLE tiktok_snapshots ADD COLUMN user_id TEXT DEFAULT ''")
        print("Added user_id")
    except sqlite3.OperationalError as e:
        print(f"user_id: {e}")
        
    try:
        conn.execute("ALTER TABLE tiktok_snapshots ADD COLUMN geo_city TEXT DEFAULT ''")
        print("Added geo_city")
    except sqlite3.OperationalError as e:
        print(f"geo_city: {e}")
        
    conn.commit()
    conn.close()
    print("Done")
except Exception as e:
    print(f"Error: {e}")
