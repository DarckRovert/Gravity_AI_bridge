import re

PATH = r'F:\Gravity_AI_bridge\core\video_pipeline.py'
with open(PATH, 'r', encoding='utf-8', errors='replace') as f:
    src = f.read()

# 1. Actualizar firma de _assemble_clip para incluir scene_title
OLD_SIG = '    scene_idx: int = 0,\n) -> bool:'
NEW_SIG = '    scene_idx: int = 0,\n    scene_title: str = "",\n) -> bool:'
src = src.replace(OLD_SIG, NEW_SIG, 1)

# 2. Usar scene_title en el overlay en lugar de inferirlo del nombre del archivo
OLD_OVERLAY = """        # -- NUEVO: Cinematic Scene Title Overlay --
        # Si la escena tiene un título (extraído del guión), se muestra en la esquina 3 segundos.
        scene_title = os.path.basename(os.path.dirname(output_mp4)) # placeholder para el título real de la escena si se pasa
        # Buscamos si tenemos el título real en el contexto (se puede pasar como parámetro text_title)
        # Por ahora usamos un placeholder estilizado o el nombre de la escena
        t_display = scene_name.replace("_", " ").title() if "scene" in scene_name else ""
        if t_display:
            safe_t = t_display.replace("'", "").replace(":", "")
            # Dibujar título en la esquina inferior izquierda con fade
            draw_t = (
                f"drawtext=text='{safe_t}':fontcolor=white@0.8:fontsize={h_val//25}:"
                f"x=40:y=h-80:alpha='if(lt(t,0.5),t/0.5,if(lt(t,3),1,if(lt(t,3.5),1-(t-3)/0.5,0)))'"
            )
            vf_parts.append(draw_t)"""

NEW_OVERLAY = """        # -- Cinematic Scene Title Overlay --
        if scene_title:
            # Limpiar caracteres conflictivos para ffmpeg
            safe_t = scene_title.replace("'", "").replace(":", "").replace("%", "")[:40].upper()
            # Overlay elegante: inferior izquierda, tipografía grande, semi-transparente con fade
            draw_t = (
                f"drawtext=text='{safe_t}':fontcolor=white@0.7:fontsize={h_val//22}:"
                f"x=50:y=h-100:fontfile='C\\\\:/Windows/Fonts/arialbd.ttf':"
                f"alpha='if(lt(t,0.8),t/0.8,if(lt(t,3.5),1,if(lt(t,4.2),1-(t-3.5)/0.7,0)))'"
            )
            vf_parts.append(draw_t)"""

src = src.replace(OLD_OVERLAY, NEW_OVERLAY, 1)

# 3. Pasar scene_title desde _process_job
OLD_CALL = 'ken_burns=ken_burns, color_grade=_cgrade, scene_idx=scene_num):'
NEW_CALL = 'ken_burns=ken_burns, color_grade=_cgrade, scene_idx=scene_num, scene_title=scene_title):'
src = src.replace(OLD_CALL, NEW_CALL, 1)

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(src)
print("DONE: Títulos de escena sincronizados y profesionalizados.")
