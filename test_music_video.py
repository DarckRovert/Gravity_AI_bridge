import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from core.video.pipeline import add_job, start, get_queue_status
import threading

lyrics = """[Intro: Low structural drone and haunting organic cello note]

[Verse 1]
La arquitectura del miedo se desarma en el frío
donde la carne olvida su nombre y el código su herencia
no hay norte en este mapa de cables y ceniza cósmica
solo una grieta sangrando en el tejido de la conciencia

[Pre-Chorus: Heavy mechanical pulse and distorting sub bass]
La luz se curva buscando un dios que la rescate
mientras el peso de la nada devora la última mentira

[Chorus: Overwhelming cinematic wall of sound and dramatic brass]
Cruzo el horizonte de eventos descalzo y ciego
donde la eternidad colapsa en un solo segundo
Infinite es la herida que ya no necesita sanar
disuelto en la geometría perfecta de un nuevo mundo

[Verse 2]
Espectros de silicio flotan como estatuas rotas
testigos mudos de una era que no tuvo testigos
el silencio ya no es ausencia es una masa densa
que tritura mis recuerdos y me une a mis enemigos"""

print("Añadiendo trabajo de Video Musical a la base de datos...")
job_id = add_job(
    topic="Dark sci-fi, horror cósmico, arquitectura brutalista espacial",
    n_scenes=6,
    voice_speed=150,
    voice_id="",
    style="cinematic",
    narration_lang="es",
    transitions=True,
    resolution="720x1280",
    subtitles=False,
    title="Horizonte de Eventos (Test Remaster)",
    bgm_type="ninguna",
    quality="hd",
    use_lore=False,
    fps=24,
    scene_duration=5,
    duration_mode="auto",
    bgm_volume=0.3,
    codec="libx264",
    ken_burns=True,
    intro_card=False,
    color_grade="auto",
    animation_effect="kenburns",
    animation_level=2,
    niche_id="",
    job_type="music",
    audio_track_path=r"F:\PROYECTO VIDEOCLIP MUSICAL\input\Horizonte de Eventos.mp3",
    lyrics_text=lyrics
)

print(f"Trabajo agregado con ID: {job_id}")
start()
print("Worker iniciado, esperando a que termine...")

while True:
    status = get_queue_status()
    current_job = status.get('current_job')
    if current_job and current_job['id'] == job_id:
        print(f"Progreso: {current_job.get('progress', 0)}% - {current_job.get('current_step', '')}")
    
    # Check history to see if it finished
    history = status.get('history', [])
    finished = [j for j in history if j['id'] == job_id and j.get('status') in ['completed', 'done', 'failed', 'cancelled']]
    if finished:
        job = finished[0]
        print(f"\n¡Video completado! Status: {job.get('status')}")
        
        # Mover a carpeta limpia
        if job.get('status') in ['completed', 'done']:
            try:
                import glob, shutil
                videos = glob.glob(r"F:\Gravity_AI_bridge\_videos\video_" + str(job_id) + "*.mp4")
                if videos:
                    final_dir = r"F:\PROYECTO VIDEOCLIP MUSICAL\input"
                    os.makedirs(final_dir, exist_ok=True)
                    for v in videos:
                        fname = os.path.basename(v)
                        dest = os.path.join(final_dir, fname)
                        if os.path.exists(dest):
                            os.remove(dest)
                        shutil.move(v, dest)
                    print(f"-> Video movido exitosamente a: {final_dir}")
            except Exception as e:
                print(f"Error moviendo video final: {e}")
        break
    time.sleep(3)
