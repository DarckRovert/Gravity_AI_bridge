"""
Gravity AI Bridge - Pipeline Upgrade Script
Añade: Ken Burns, color grading, intro/outro cards, thumbnail, más BGM, transiciones avanzadas.
"""
import re

PATH = r'F:\Gravity_AI_bridge\core\video_pipeline.py'

with open(PATH, 'r', encoding='utf-8', errors='replace') as f:
    src = f.read()

# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 1: Constantes nuevas (después de BGM_GENERATORS)
# ─────────────────────────────────────────────────────────────────────────────
NEW_CONSTANTS = r"""
# -- Grading de color cinematico por estilo -----------------------------------
STYLE_COLOR_GRADES: dict[str, str] = {
    "documental":  "eq=contrast=1.1:brightness=0.02:saturation=1.1:gamma=1.05",
    "anime":       "eq=contrast=1.15:brightness=0.03:saturation=1.45:gamma=1.0",
    "epico":       "eq=contrast=1.2:brightness=-0.02:saturation=1.15:gamma=0.95",
    "noir":        "eq=contrast=1.4:brightness=-0.05:saturation=0.0:gamma=0.95",
    "infantil":    "eq=contrast=1.05:brightness=0.05:saturation=1.5:gamma=1.1",
    "naturaleza":  "eq=contrast=1.1:brightness=0.03:saturation=1.3:gamma=1.05",
    "cyberpunk":   "eq=contrast=1.3:brightness=-0.03:saturation=1.5:gamma=0.9",
    "historico":   "eq=contrast=1.15:brightness=-0.02:saturation=0.85:gamma=1.0",
    "lofi":        "eq=contrast=0.95:brightness=0.05:saturation=0.8:gamma=1.1",
    "retro80s":    "eq=contrast=1.2:brightness=0.02:saturation=1.6:gamma=0.95",
}

# -- BGM géneros adicionales --------------------------------------------------
BGM_GENERATORS.update({
    "ambient": (
        "0.12*sin(110*2*PI*t)+0.10*sin(146.83*2*PI*t)+"
        "0.08*sin(164.81*2*PI*t)+0.05*sin(220*2*PI*t)+"
        "0.04*sin(293.66*2*PI*t)+0.03*sin(55*2*PI*t)"
    ),
    "tension": (
        "0.25*sin(55*2*PI*t*(1+0.005*sin(0.5*2*PI*t)))+"
        "0.15*sin(73.42*2*PI*t)+0.10*sin(92.5*2*PI*t)+"
        "0.08*sin(110*2*PI*t*(1+0.003*sin(1.2*2*PI*t)))"
    ),
    "lofi_beats": (
        "0.18*sin(130.81*2*PI*t)+0.14*sin(164.81*2*PI*t)+"
        "0.10*sin(196*2*PI*t)+0.08*sin(261.63*2*PI*t)+"
        "0.12*sin(65.41*2*PI*t*(1+0.001*sin(0.25*2*PI*t)))"
    ),
    "heroico": (
        "0.30*sin(65.41*2*PI*t)+0.22*sin(130.81*2*PI*t)+"
        "0.18*sin(196*2*PI*t)+0.14*sin(261.63*2*PI*t)+"
        "0.10*sin(392*2*PI*t)+0.06*sin(523.25*2*PI*t)"
    ),
    "corporativo": (
        "0.14*sin(261.63*2*PI*t)+0.12*sin(329.63*2*PI*t)+"
        "0.10*sin(392*2*PI*t)+0.08*sin(440*2*PI*t)+"
        "0.06*sin(523.25*2*PI*t)+0.08*sin(130.81*2*PI*t)"
    ),
})

"""

# Insertar después de la última llave de BGM_GENERATORS
insert_after = "BGM_GENERATORS.update" 
if insert_after not in src:
    # Primera vez: insertar después del cierre de BGM_GENERATORS dict
    marker = "}\n\n\n# ── Estilos"
    src = src.replace(marker, "}\n" + NEW_CONSTANTS + "\n\n# ── Estilos", 1)
    print("OK: Constantes insertadas (primera vez)")
else:
    print("INFO: BGM_GENERATORS.update ya existe")

# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 2: Helpers antes de _assemble_clip
# ─────────────────────────────────────────────────────────────────────────────
HELPERS = '''
# -- Ken Burns: zoom+pan cinematico sobre imagen estatica ---------------------

def _kenburns_vf(clip_dur: float, fps: int, w: int, h: int, scene_idx: int) -> str:
    """Genera filtro zoompan alterno: escena par=zoom-in, impar=zoom-out+pan."""
    total_frames = max(1, int(clip_dur * fps))
    if scene_idx % 2 == 0:
        z  = "'min(zoom+0.0008,1.18)'"
        x  = "'iw/2-(iw/zoom/2)'"
        y  = "'ih/2-(ih/zoom/2)'"
    else:
        z  = "'if(eq(on,1),1.18,max(zoom-0.0008,1.0))'"
        x  = "'iw/2-(iw/zoom/2)+(iw*0.03*on/" + str(total_frames) + ")'"
        y  = "'ih/2-(ih/zoom/2)'"
    return (
        'zoompan=z=' + z + ':d=' + str(total_frames) +
        ':x=' + x + ':y=' + y +
        ':s=' + str(w) + 'x' + str(h) + ':fps=' + str(fps)
    )


# -- Title card: intro animado con drawtext -----------------------------------

def _create_title_card(
    title: str,
    subtitle: str,
    output_mp4: str,
    w: int,
    h: int,
    fps: int,
    duration: float,
    codec: str,
) -> bool:
    """Genera un clip de intro con título y subtítulo sobre fondo negro."""
    if not os.path.isfile(FFMPEG_EXE):
        return False
    safe_title    = title.replace("'", "\\'").replace(":", "\\:").replace("%", "\\%")[:60]
    safe_subtitle = subtitle.replace("'", "\\'").replace(":", "\\:").replace("%", "\\%")[:80]
    vf = (
        "color=c=black:s=" + str(w) + "x" + str(h) + ":d=" + str(duration) + "[bg];"
        "[bg]drawtext=fontsize=" + str(max(24, h // 20)) + ":fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2-40"
        ":text='" + safe_title + "':alpha='if(lt(t,0.5),t/0.5,if(gt(t," + str(duration - 0.5) + "),(1-(t-" + str(duration - 0.5) + ")/0.5),1))',"
        "drawtext=fontsize=" + str(max(14, h // 35)) + ":fontcolor=0xAAAAAA:x=(w-text_w)/2:y=(h-text_h)/2+40"
        ":text='" + safe_subtitle + "':alpha='if(lt(t,0.8),t/0.8,if(gt(t," + str(duration - 0.5) + "),(1-(t-" + str(duration - 0.5) + ")/0.5),1))'"
    )
    cmd = [
        FFMPEG_EXE, "-y",
        "-f", "lavfi", "-i", vf,
        "-t", str(duration),
        "-c:v", codec, "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_mp4,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=60,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        ok = r.returncode == 0 and os.path.isfile(output_mp4)
        if ok:
            log.info("[VideoStudio] Intro card generada: " + os.path.basename(output_mp4))
        else:
            log.warning("[VideoStudio] Intro card fallida: " + r.stderr.decode(errors="replace")[-200:])
        return ok
    except Exception as e:
        log.warning("[VideoStudio] Intro card excepcion: " + str(e))
        return False


# -- Thumbnail: extraer frame destacado del video final ----------------------

def _extract_thumbnail(video_path: str, output_jpg: str, at_sec: float = 3.0) -> bool:
    """Extrae un frame del video como thumbnail JPEG."""
    if not os.path.isfile(video_path) or not os.path.isfile(FFMPEG_EXE):
        return False
    cmd = [
        FFMPEG_EXE, "-y",
        "-ss", str(at_sec),
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "3",
        output_jpg,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=30,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        return r.returncode == 0 and os.path.isfile(output_jpg)
    except Exception:
        return False

'''

marker_assemble = "# ── Paso 5: Ensamblado"
if "_kenburns_vf" not in src:
    # buscar la primera aparicion del marker (con caracteres raros de encoding)
    idx = src.find("def _assemble_clip(")
    if idx != -1:
        src = src[:idx] + HELPERS + src[idx:]
        print("OK: Helpers insertados antes de _assemble_clip")
    else:
        print("ERROR: no encontre _assemble_clip")
else:
    print("INFO: _kenburns_vf ya existe")

# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 3: Actualizar firma de _assemble_clip (añadir ken_burns, color_grade, scene_idx)
# ─────────────────────────────────────────────────────────────────────────────
OLD_SIG = '''def _assemble_clip(
    image_path: str,
    audio_path: str,
    output_mp4: str,
    fade: bool = True,
    resolution: str = "1024x1024",
    text: str = "",
    subtitles: bool = True,
    fps: int = DEFAULT_FPS,
    scene_duration: int = SECONDS_PER_SCENE,
    duration_mode: str = "auto",
    codec: str = "libx264",
) -> bool:'''

NEW_SIG = '''def _assemble_clip(
    image_path: str,
    audio_path: str,
    output_mp4: str,
    fade: bool = True,
    resolution: str = "1024x1024",
    text: str = "",
    subtitles: bool = True,
    fps: int = DEFAULT_FPS,
    scene_duration: int = SECONDS_PER_SCENE,
    duration_mode: str = "auto",
    codec: str = "libx264",
    ken_burns: bool = True,
    color_grade: str = "",
    scene_idx: int = 0,
) -> bool:'''

if OLD_SIG in src:
    src = src.replace(OLD_SIG, NEW_SIG, 1)
    print("OK: Firma _assemble_clip actualizada")
else:
    print("WARN: Firma _assemble_clip no encontrada (puede ya estar actualizada)")

# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 4: Inyectar Ken Burns y color grade en vf_parts de _assemble_clip
# ─────────────────────────────────────────────────────────────────────────────
OLD_VF = '''        vf_parts = [
            f"scale={w_val}:{h_val}:force_original_aspect_ratio=decrease",
            f"pad={w_val}:{h_val}:(ow-iw)/2:(oh-ih)/2:black",
            f"fps={fps}",
        ]'''

NEW_VF = '''        if ken_burns and not (subtitles and text):
            # Ken Burns: zoompan (no compatible con subtitles filter en misma cadena)
            vf_parts = [_kenburns_vf(clip_dur, fps, w_val, h_val, scene_idx)]
        else:
            vf_parts = [
                f"scale={w_val}:{h_val}:force_original_aspect_ratio=decrease",
                f"pad={w_val}:{h_val}:(ow-iw)/2:(oh-ih)/2:black",
                f"fps={fps}",
            ]
        if color_grade:
            vf_parts.append(color_grade)'''

if OLD_VF in src:
    src = src.replace(OLD_VF, NEW_VF, 1)
    print("OK: Ken Burns y color grade inyectados en vf_parts")
else:
    print("WARN: vf_parts no encontrado con el formato esperado")

# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 5: Nuevas columnas en _init_db migrations
# ─────────────────────────────────────────────────────────────────────────────
OLD_MIGRATIONS = '        (\"bgm_volume\",     \"REAL NOT NULL DEFAULT 0.1\"),\n        (\"codec\",          \"TEXT NOT NULL DEFAULT \'libx264\'\"),\n    ]'
NEW_MIGRATIONS  = ('        ("bgm_volume",     "REAL NOT NULL DEFAULT 0.1"),\n'
                   '        ("codec",          "TEXT NOT NULL DEFAULT \'libx264\'"),\n'
                   '        ("ken_burns",      "INTEGER NOT NULL DEFAULT 1"),\n'
                   '        ("intro_card",     "INTEGER NOT NULL DEFAULT 0"),\n'
                   '        ("color_grade",    "TEXT NOT NULL DEFAULT \'auto\'"),\n'
                   '        ("thumbnail_path", "TEXT NOT NULL DEFAULT \'\'"),\n'
                   '    ]')

# buscar de forma más robusta
if '"thumbnail_path"' not in src:
    # Buscar la linea de codec en migrations
    src = src.replace(
        '("codec",          "TEXT NOT NULL DEFAULT \'libx264\'"),\n    ]',
        '("codec",          "TEXT NOT NULL DEFAULT \'libx264\'"),\n'
        '        ("ken_burns",      "INTEGER NOT NULL DEFAULT 1"),\n'
        '        ("intro_card",     "INTEGER NOT NULL DEFAULT 0"),\n'
        '        ("color_grade",    "TEXT NOT NULL DEFAULT \'auto\'"),\n'
        '        ("thumbnail_path", "TEXT NOT NULL DEFAULT \'\'"),\n'
        '    ]',
        1
    )
    print("OK: Nuevas columnas DB insertadas")
else:
    print("INFO: columnas DB ya existen")

# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 6: Actualizar add_job signature + INSERT
# ─────────────────────────────────────────────────────────────────────────────
OLD_ADD_SIG = '    bgm_volume: float   = DEFAULT_BGM_VOLUME,\n    codec: str          = "libx264",\n) -> int:'
NEW_ADD_SIG = ('    bgm_volume: float   = DEFAULT_BGM_VOLUME,\n'
               '    codec: str          = "libx264",\n'
               '    ken_burns: bool     = True,\n'
               '    intro_card: bool    = False,\n'
               '    color_grade: str    = "auto",\n'
               ') -> int:')

if 'ken_burns: bool     = True,' not in src:
    src = src.replace(OLD_ADD_SIG, NEW_ADD_SIG, 1)
    print("OK: Firma add_job actualizada")

OLD_INSERT = (
    '"(topic, n_scenes, voice_speed, voice_id, style, narration_lang, transitions, "\n'
    '         " resolution, subtitles, title, bgm_type, quality, use_lore, fps, scene_duration, duration_mode, bgm_volume, codec, created_at) "\n'
    '        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"'
)
NEW_INSERT = (
    '"(topic, n_scenes, voice_speed, voice_id, style, narration_lang, transitions, "\n'
    '         " resolution, subtitles, title, bgm_type, quality, use_lore, fps, scene_duration, duration_mode, bgm_volume, codec,"\n'
    '         " ken_burns, intro_card, color_grade, created_at) "\n'
    '        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"'
)
if 'ken_burns, intro_card' not in src:
    src = src.replace(OLD_INSERT, NEW_INSERT, 1)
    print("OK: INSERT de add_job actualizado")

OLD_VALUES = (
    '            topic, n_scenes, voice_speed, voice_id, style, narration_lang,\n'
    '            1 if transitions else 0, resolution, 1 if subtitles else 0,\n'
    '            title, bgm_type, quality, 1 if use_lore else 0,\n'
    '            fps, scene_duration, duration_mode, float(bgm_volume), codec, now'
)
NEW_VALUES = (
    '            topic, n_scenes, voice_speed, voice_id, style, narration_lang,\n'
    '            1 if transitions else 0, resolution, 1 if subtitles else 0,\n'
    '            title, bgm_type, quality, 1 if use_lore else 0,\n'
    '            fps, scene_duration, duration_mode, float(bgm_volume), codec,\n'
    '            1 if ken_burns else 0, 1 if intro_card else 0, color_grade, now'
)
if '1 if ken_burns else 0' not in src:
    src = src.replace(OLD_VALUES, NEW_VALUES, 1)
    print("OK: VALUES de add_job actualizados")

# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 7: _process_job - añadir parámetros nuevos
# ─────────────────────────────────────────────────────────────────────────────
OLD_PROC_SIG = '    bgm_volume: float = DEFAULT_BGM_VOLUME,\n    codec: str = "libx264",\n) -> None:\n    """\n    Pipeline completo con Character Consistency Engine.'
NEW_PROC_SIG = ('    bgm_volume: float = DEFAULT_BGM_VOLUME,\n'
                '    codec: str = "libx264",\n'
                '    ken_burns: bool = True,\n'
                '    intro_card: bool = False,\n'
                '    color_grade: str = "auto",\n'
                ') -> None:\n    """\n    Pipeline completo con Character Consistency Engine.')

if 'ken_burns: bool = True,' not in src[src.find('def _process_job'):]:
    src = src.replace(OLD_PROC_SIG, NEW_PROC_SIG, 1)
    print("OK: Firma _process_job actualizada")

# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 8: En _process_job, inyectar intro card y thumbnail, pasar ken_burns/color_grade a _assemble_clip
# ─────────────────────────────────────────────────────────────────────────────
OLD_CLIP_CALL = (
    "            if _assemble_clip(img_path, audio_path if audio_ok else None, clip_path, fade=transitions, resolution=resolution, text=narration, subtitles=subtitles, fps=fps, scene_duration=scene_duration, duration_mode=duration_mode, codec=codec):"
)
NEW_CLIP_CALL = (
    "            _cgrade = STYLE_COLOR_GRADES.get(style, '') if color_grade == 'auto' else (color_grade if color_grade != 'none' else '')\n"
    "            if _assemble_clip(img_path, audio_path if audio_ok else None, clip_path, fade=transitions, resolution=resolution, text=narration, subtitles=subtitles, fps=fps, scene_duration=scene_duration, duration_mode=duration_mode, codec=codec, ken_burns=ken_burns, color_grade=_cgrade, scene_idx=scene_num):"
)
if 'ken_burns=ken_burns' not in src:
    src = src.replace(OLD_CLIP_CALL, NEW_CLIP_CALL, 1)
    print("OK: _assemble_clip call actualizada con ken_burns y color_grade")

# Inyectar intro card antes del loop de escenas
OLD_LOOP_START = (
    "        total_steps = n_scenes * 3 + 1\n"
    "        step        = 0\n"
    "        clip_paths: list[str] = []\n"
    "\n"
    "        for i, scene in enumerate(scenes):"
)
NEW_LOOP_START = (
    "        # -- Grading de color efectivo\n"
    "        effective_grade = STYLE_COLOR_GRADES.get(style, '') if color_grade == 'auto' else (color_grade if color_grade != 'none' else '')\n"
    "\n"
    "        total_steps = n_scenes * 3 + 1\n"
    "        step        = 0\n"
    "        clip_paths: list[str] = []\n"
    "\n"
    "        # -- Intro card opcional\n"
    "        if intro_card:\n"
    "            intro_path = os.path.join(job_dir, 'intro_card.mp4')\n"
    "            w_ic, h_ic = DEFAULT_IMG_W, DEFAULT_IMG_H\n"
    "            if 'x' in resolution:\n"
    "                _p = resolution.split('x')\n"
    "                if len(_p) == 2 and _p[0].isdigit() and _p[1].isdigit():\n"
    "                    w_ic, h_ic = int(_p[0]), int(_p[1])\n"
    "            if _create_title_card(title or topic[:50], style_prefix[:60], intro_path, w_ic, h_ic, fps, 3.5, codec):\n"
    "                clip_paths.insert(0, intro_path)\n"
    "\n"
    "        for i, scene in enumerate(scenes):"
)
if 'effective_grade = STYLE_COLOR_GRADES' not in src:
    src = src.replace(OLD_LOOP_START, NEW_LOOP_START, 1)
    print("OK: Intro card y color grade inyectados en _process_job")

# Inyectar extracción de thumbnail tras completar el video
OLD_COMPLETION = (
    "            log.info(f\"[VideoStudio] Job #{job_id} completado -> {final_path}\")"
)
NEW_COMPLETION = (
    "            log.info(f\"[VideoStudio] Job #{job_id} completado -> {final_path}\")\n"
    "            # -- Thumbnail\n"
    "            thumb_path = os.path.join(OUTPUT_DIR, f'thumb_{job_id}.jpg')\n"
    "            if _extract_thumbnail(final_path, thumb_path):\n"
    "                _update_job(job_id, thumbnail_path=thumb_path)\n"
    "                log.info(f'[VideoStudio] Thumbnail: {os.path.basename(thumb_path)}')"
)
if 'thumb_path = os.path.join' not in src:
    src = src.replace(OLD_COMPLETION, NEW_COMPLETION, 1)
    print("OK: Thumbnail inyectado tras completar job")

# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 9: Actualizar _update_job para aceptar thumbnail_path
# ─────────────────────────────────────────────────────────────────────────────
OLD_VALID = '    valid  = {"status", "progress", "current_step", "output_path",\n              "error", "started_at", "finished_at"}'
NEW_VALID = '    valid  = {"status", "progress", "current_step", "output_path",\n              "error", "started_at", "finished_at", "thumbnail_path"}'
if '"thumbnail_path"' not in src:
    src = src.replace(OLD_VALID, NEW_VALID, 1)
    print("OK: _update_job acepta thumbnail_path")

# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 10: _worker_loop — pasar nuevos parámetros
# ─────────────────────────────────────────────────────────────────────────────
OLD_WORKER_END = (
    "                    bgm_volume     = float(row[\"bgm_volume\"]) if \"bgm_volume\"     in keys else DEFAULT_BGM_VOLUME,\n"
    "                    codec          = row[\"codec\"]             if \"codec\"           in keys else \"libx264\",\n"
    "                )"
)
NEW_WORKER_END = (
    "                    bgm_volume     = float(row[\"bgm_volume\"]) if \"bgm_volume\"     in keys else DEFAULT_BGM_VOLUME,\n"
    "                    codec          = row[\"codec\"]             if \"codec\"           in keys else \"libx264\",\n"
    "                    ken_burns      = bool(row[\"ken_burns\"]    if \"ken_burns\"       in keys else 1),\n"
    "                    intro_card     = bool(row[\"intro_card\"]   if \"intro_card\"      in keys else 0),\n"
    "                    color_grade    = row[\"color_grade\"]       if \"color_grade\"     in keys else \"auto\",\n"
    "                )"
)
if 'ken_burns      = bool(row' not in src:
    src = src.replace(OLD_WORKER_END, NEW_WORKER_END, 1)
    print("OK: _worker_loop actualizado con nuevos params")

# ─────────────────────────────────────────────────────────────────────────────
# GUARDAR
# ─────────────────────────────────────────────────────────────────────────────
with open(PATH, 'w', encoding='utf-8') as f:
    f.write(src)
print("DONE: video_pipeline.py guardado.")
