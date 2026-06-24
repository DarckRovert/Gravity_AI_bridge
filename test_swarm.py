import sys

# Add core to path
sys.path.append(r"f:\Gravity_AI_bridge")

from core.video.v13_ai_director import analyze_lyrics_sections

lyrics = """
[Intro]
The sun rises over the mountains
A new day begins

[Chorus]
And we fly away
To the stars above
"""

try:
    print("Iniciando prueba del Swarm...")
    result = analyze_lyrics_sections(lyrics, total_frames=100, fps=24)
    print("Prueba completada con exito.")
    print("Timeline generado:", len(result.get("timeline", [])))
except Exception as e:
    print("CRASH EN SWARM:", e)
    import traceback

    traceback.print_exc()
