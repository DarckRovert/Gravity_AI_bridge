"""
restore_functions.py
Restaura las funciones _create_title_card y _extract_thumbnail que fueron
truncadas por errores de edición anteriores.
"""

TARGET = r"F:\Gravity_AI_bridge\core\video_pipeline.py"

with open(TARGET, "rb") as f:
    raw = f.read()

# Bloque corrupto exacto presente en el archivo
old_block = (
    b"def _create_title_card(\r\r\r\n"
    b"    title: str,\r\r\r\n"
    b"    subtitle: str,\r\r\r\n"
    b"    output_mp4: str,\r\r\r\n"
    b"    w: int,\r\r\r\n"
    b"    h: int,\r\r\r\n"
    b"    fps: int,\r\r\r\n"
    b"    duration: float,\r\r\r\n"
    b"        r = subprocess.run(cmd, capture_output=True, timeout=30,\r\r\r\n"
    b"                           creationflags=subprocess.CREATE_NO_WINDOW)\r\r\r\n"
    b"        return r.returncode == 0 and os.path.isfile(output_jpg)\r\r\r\n"
    b"    except Exception:\r\r\r\n"
    b"        return False\r\r\r\n"
    b"\r\r\r\n"
)

assert old_block in raw, "ERROR: bloque corrupto no encontrado — revisar manualmente"

# Bloque correcto a inyectar (title_card completa + extract_thumbnail completa)
new_block = b"""\
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
    \"\"\"Genera un clip de intro con titulo y subtitulo sobre fondo negro.\"\"\"
    if not os.path.isfile(FFMPEG_EXE):
        return False
    import re as _re
    safe_title    = _re.sub(r\"[:'%]\", '', title)[:60]
    safe_subtitle = _re.sub(r\"[:'%]\", '', subtitle)[:80]
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
    \"\"\"Extrae un frame del video como thumbnail JPEG.\"\"\"
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

"""

# Los \n del new_block son \n simples — el archivo usa \r\r\r\n pero Python
# interpreta igualmente; mantenemos los \r\r\r\n del archivo solo en old_block.
# new_block usa \n, el archivo puede mixear sin problemas para Python.

raw_new = raw.replace(old_block, new_block, 1)
assert raw_new != raw, "ERROR: el reemplazo no tuvo efecto"

with open(TARGET, "wb") as f:
    f.write(raw_new)

print(f"Restauracion OK. {len(raw)} -> {len(raw_new)} bytes")

# Verificar sintaxis
import ast
src_clean = raw_new.replace(b"\r\r\r\n", b"\n").replace(b"\r\r\n", b"\n").replace(b"\r\n", b"\n").replace(b"\r", b"\n")
try:
    ast.parse(src_clean)
    print("SYNTAX OK - video_pipeline.py es valido")
except SyntaxError as e:
    print(f"SyntaxError en linea {e.lineno}: {e.msg}")
    lines = src_clean.split(b"\n")
    s = max(0, e.lineno - 5)
    en = min(len(lines), e.lineno + 4)
    for i in range(s, en):
        prefix = ">>>" if i + 1 == e.lineno else "   "
        print(f"{prefix} {i+1:4d}: {lines[i].decode('utf-8', errors='replace')}")
