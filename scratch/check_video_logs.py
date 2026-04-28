import sqlite3
import os

db_path = r'F:\Gravity_AI_bridge\_video_queue.sqlite'
try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT id, status, current_step, error, output_path FROM video_jobs ORDER BY id DESC LIMIT 3')
    rows = cursor.fetchall()
    print('Últimos 3 trabajos en DB:')
    for row in rows:
        print(f"Job {row['id']}: Status={row['status']} | Step={row['current_step']}")
        print(f"  Error: {row['error']}")
        print(f"  Path: {row['output_path']}")
except Exception as e:
    print('Error leyendo DB:', e)

print('\n-- Últimos errores en bridge.log --')
try:
    with open(r'F:\Gravity_AI_bridge\bridge.log', 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
        for l in lines[-50:]:
            if 'ERROR' in l or 'fall' in l.lower() or 'Exception' in l:
                print(l.strip())
except Exception as e:
    print('Error leyendo log:', e)
