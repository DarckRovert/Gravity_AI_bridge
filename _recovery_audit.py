import sqlite3
import os
import sys
import glob

def check_db(db_path):
    if not os.path.exists(db_path):
        return f"Missing: {db_path}"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()[0]
        conn.close()
        return f"OK" if result.lower() == 'ok' else f"CORRUPT: {result}"
    except Exception as e:
        return f"ERROR: {str(e)}"

def main():
    print("--- 1. AUDITORIA DE BASES DE DATOS ---")
    app_data = os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), 
        "Gravity", 
        "Databases"
    )
    dbs = [
        os.path.join(app_data, "_cache.sqlite"),
        os.path.join(app_data, "_video_queue.sqlite"),
        os.path.join(app_data, "_image_queue.sqlite"),
        os.path.join(app_data, "gravity_brain.db"),
        os.path.join(app_data, "tinka_history.db")
    ]
    for db in dbs:
        print(f"[{db}]: {check_db(db)}")
        
    print("\n--- 2. AUDITORIA DE INTEGRACIONES ---")
    bins = [
        "_integrations/Fooocus/python_embeded/python.exe",
        "_integrations/ffmpeg/bin/ffmpeg.exe",
        "C:/Program Files/flm/flm.exe"
    ]
    for b in bins:
        if os.path.exists(b):
            print(f"[OK] {b}")
        else:
            print(f"[MISSING] {b}")

if __name__ == '__main__':
    main()
