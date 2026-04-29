import sqlite3
db = 'F:/Gravity_AI_bridge/_video_queue.sqlite'
c = sqlite3.connect(db)
running = c.execute("SELECT id,topic,status FROM video_jobs WHERE status='running'").fetchall()
failed  = c.execute("SELECT id,topic,error FROM video_jobs WHERE status='failed'").fetchall()
print("running:", running)
print("failed:", failed)
# Resetear jobs atascados en running -> failed (proceso murió sin limpiar)
if running:
    c.execute("UPDATE video_jobs SET status='failed', error='Proceso interrumpido por reinicio del servidor' WHERE status='running'")
    c.commit()
    print(f"[FIX] {len(running)} jobs en 'running' reseteados a 'failed'.")
c.close()
print("DB check completo.")
