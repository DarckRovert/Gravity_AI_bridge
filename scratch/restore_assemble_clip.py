"""
restore_assemble_clip.py v2
Restaura el cuerpo truncado de _assemble_clip.
Usa fromhex() para las lineas con caracteres de escape conflictivos.
"""

TARGET = r"F:\Gravity_AI_bridge\core\video_pipeline.py"

with open(TARGET, "rb") as f:
    raw = f.read()

old_truncated = (
    b'            parts = resolution.split("x")\r\r\r\n'
    b'def _ensure_bgm'
)

assert old_truncated in raw, "ERROR: patron de corte no encontrado"
print("Patron encontrado. Restaurando cuerpo de _assemble_clip...")

CRLF = b'\r\r\r\n'

lines = [
    b'            parts = resolution.split("x")',
    b'            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():',
    b'                w_val, h_val = int(parts[0]), int(parts[1])',
    b'',
    b'        # Filtro de video con fade',
    b'        if ken_burns and not (subtitles and text):',
    b'            # Ken Burns: zoompan (no compatible con subtitles en misma cadena)',
    b'            vf_parts = [_kenburns_vf(clip_dur, fps, w_val, h_val, scene_idx)]',
    b'        else:',
    b'            vf_parts = [',
    b'                f"scale={w_val}:{h_val}:force_original_aspect_ratio=decrease",',
    b'                f"pad={w_val}:{h_val}:(ow-iw)/2:(oh-ih)/2:black",',
    b'                f"fps={fps}",',
    b'            ]',
    b'        if color_grade:',
    b'            vf_parts.append(color_grade)',
    b'',
    b'        # VFX de grano de pelicula sutil para cohesion visual',
    b'        vf_parts.append("noise=alls=7:allf=t+u")',
    b'',
    b'        if subtitles and text:',
    b'            def fmt_time(s: float) -> str:',
    b'                ms = int((s % 1) * 1000)',
    b'                m, s_int = divmod(int(s), 60)',
    b'                _h, _m = divmod(m, 60)',
    b'                return f"{_h:02d}:{_m:02d}:{s_int:02d},{ms:03d}"',
    b'',
    b'            job_dir = os.path.dirname(image_path)',
    b'            scene_name = os.path.splitext(os.path.basename(image_path))[0]',
    b'            srt_path = os.path.join(job_dir, f"{scene_name}.srt")',
    # Linea de escritura SRT — sin backslash issues
    b'            with open(srt_path, "w", encoding="utf-8") as srt_f:',
    b'                srt_f.write(f"1\\n00:00:00,000 --> {fmt_time(clip_dur)}\\n{text}\\n")',
    b'',
    # Linea de replace path — sin backslash issues usando repr trick
    b"            safe_srt = srt_path.replace('\\\\', '/').replace(':', '\\\\:')",
    b"            vf_parts.append(f\"subtitles='{safe_srt}':force_style='FontSize=20,PrimaryColour=&H00FFFFFF,BorderStyle=3,Outline=2,Shadow=1,Alignment=2,MarginV=20'\")",
    b'',
    b'        # -- Cinematic Scene Title Overlay --',
    b'        if scene_title:',
    b"            safe_t = scene_title.replace(\"'\", \"\").replace(\":\", \"\").replace(\"%\", \"\")[:40].upper()",
    b'            draw_t = (',
    b"                f\"drawtext=text='{safe_t}':fontcolor=white@0.7:fontsize={h_val//22}:\"",
    b"                f\"x=50:y=h-100:fontfile='C\\\\:/Windows/Fonts/arialbd.ttf':\"",
    b"                f\"alpha='if(lt(t,0.8),t/0.8,if(lt(t,3.5),1,if(lt(t,4.2),1-(t-3.5)/0.7,0)))'\"",
    b'            )',
    b'            vf_parts.append(draw_t)',
    b'',
    b'        if fade and fade_d > 0:',
    b'            vf_parts.append(f"fade=t=in:st=0:d={fade_d}")',
    b'            vf_parts.append(f"fade=t=out:st={fade_out_t:.3f}:d={fade_d}")',
    b'        vf = ",".join(vf_parts)',
    b'',
    b'        if has_audio:',
    b'            cmd = [',
    b'                FFMPEG_EXE, "-y",',
    b'                "-loop", "1", "-i", image_path,',
    b'                "-i",  audio_path,',
    b'                "-c:v", codec, "-preset", "fast",',
    b'                "-c:a", "aac", "-b:a", "128k"',
    b'            ]',
    b'            if duration_mode == "manual":',
    b'                cmd.extend(["-t", str(scene_duration)])',
    b'            else:',
    b'                cmd.append("-shortest")',
    b'',
    b'            cmd.extend([',
    b'                "-vf", vf,',
    b'                "-pix_fmt", "yuv420p",',
    b'                "-movflags", "+faststart",',
    b'                output_mp4,',
    b'            ])',
    b'        else:',
    b'            cmd = [',
    b'                FFMPEG_EXE, "-y",',
    b'                "-loop", "1", "-i", image_path,',
    b'                "-t", str(scene_duration),',
    b'                "-c:v", codec, "-preset", "fast",',
    b'                "-vf", vf,',
    b'                "-pix_fmt", "yuv420p",',
    b'                "-movflags", "+faststart",',
    b'                output_mp4,',
    b'            ]',
    b'',
    b'        result = subprocess.run(',
    b'            cmd, capture_output=True, timeout=180,',
    b'            creationflags=subprocess.CREATE_NO_WINDOW',
    b'        )',
    b'        if result.returncode == 0 and os.path.isfile(output_mp4):',
    b'            log.info(f"[VideoStudio] Clip: {os.path.basename(output_mp4)}")',
    b'            return True',
    b'        else:',
    b'            err = result.stderr.decode(errors="replace")[-400:]',
    b'            log.error(f"[VideoStudio] ffmpeg error clip: {err}")',
    b'            return False',
    b'    except Exception as e:',
    b'        log.error(f"[VideoStudio] Error ensamblando clip: {e}")',
    b'        return False',
    b'',
    b'',
    b'# -- Paso 6: Concatenacion final ------------------------------------------',
    b'',
    b'',
    b'# -- BGM local: generacion instrumental sin internet ----------------------',
    b'',
    b'def _ensure_bgm',
]

new_full = CRLF.join(lines)

raw_new = raw.replace(old_truncated, new_full, 1)
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
    src_lines = src_clean.split(b"\n")
    s = max(0, e.lineno - 5)
    en = min(len(src_lines), e.lineno + 4)
    for i in range(s, en):
        prefix = ">>>" if i + 1 == e.lineno else "   "
        print(f"{prefix} {i+1:4d}: {src_lines[i].decode('utf-8', errors='replace')}")
