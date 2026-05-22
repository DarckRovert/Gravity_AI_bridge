import os
import subprocess
import time
from typing import Optional
from core.logger import log
from core.video.script_builder import CINEMA_STYLES, DEFAULT_STYLE
from core.video.audio_processor import _ensure_bgm

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FFMPEG_EXE = os.path.join(BASE_DIR, "_integrations", "ffmpeg", "ffmpeg.exe")
OUTPUT_DIR = os.path.join(BASE_DIR, "_videos")

DEFAULT_IMG_W = 1216
DEFAULT_IMG_H = 832
DEFAULT_FPS = 24
SECONDS_PER_SCENE = 8
FADE_DURATION = 0.4
DEFAULT_BGM_VOLUME = 0.1

_branding_cache = None
def _get_branding_config() -> dict:
    global _branding_cache
    if _branding_cache is None:
        try:
            import yaml
            with open(os.path.join(BASE_DIR, "config.yaml"), "r", encoding="utf-8") as f:
                _branding_cache = (yaml.safe_load(f) or {}).get("branding", {})
        except Exception:
            _branding_cache = {}
    return _branding_cache

def _generate_scene_image(
    prompt: str,
    scene_idx: int,
    job_id: int,
    job_seed: int,
    style: str,
    resolution: str = "1024x1024",
) -> Optional[str]:
    """
    Genera imagen de una escena con consistencia visual garantizada.
    """
    job_dir    = os.path.join(OUTPUT_DIR, f"job_{job_id}")
    out_path   = os.path.join(job_dir, f"scene_{scene_idx:02d}_image.png")
    os.makedirs(job_dir, exist_ok=True)

    style_info   = CINEMA_STYLES.get(style, CINEMA_STYLES[DEFAULT_STYLE])
    negative     = style_info.get("negative", "")
    scene_seed   = (job_seed + scene_idx * 7) % 2147483647

    # ── Motor 1: Pollinations.ai ────────────────────────────────────────────
    w, h = DEFAULT_IMG_W, DEFAULT_IMG_H
    if "x" in resolution:
        parts = resolution.split("x")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            w, h = int(parts[0]), int(parts[1])

    try:
        from tools.pollinations_generator import generate as poll_gen
        result = poll_gen(
            prompt          = prompt,
            output_path     = out_path,
            width           = w,
            height          = h,
            seed            = scene_seed,
            enhance         = False,
            negative_prompt = negative,
        )
        if result.get("success") and os.path.isfile(out_path):
            log.info(f"[VideoStudio] [Pollinations] Escena {scene_idx}: {os.path.basename(out_path)} (seed={scene_seed})")
            return out_path
        else:
            log.warning(f"[VideoStudio] [Pollinations] Falló escena {scene_idx}: {result.get('error')}")
    except Exception as e:
        log.warning(f"[VideoStudio] [Pollinations] Exception escena {scene_idx}: {e}")

    # ── Motor 2: Fooocus (fallback local) ──────────────────────────────────────
    try:
        from tools.fooocus_client import trigger_gradio_generation, health_check
        if health_check().get("online"):
            result = trigger_gradio_generation(
                prompt       = prompt,
                performance  = "Speed",
                aspect_ratio = f"{w}*{h}",
            )
            if result.get("success") and result.get("images"):
                img_src = result["images"][0]
                if os.path.isfile(img_src):
                    import shutil
                    shutil.copy2(img_src, out_path)
                    log.info(f"[VideoStudio] [Fooocus] Escena {scene_idx}: {os.path.basename(out_path)}")
                    return out_path
        else:
            log.info("[VideoStudio] Fooocus offline — saltando fallback.")
    except Exception as e:
        log.warning(f"[VideoStudio] [Fooocus] Exception escena {scene_idx}: {e}")

    return None


def _create_placeholder_image(text: str, output_path: str) -> None:
    """Genera imagen negra con texto usando Pillow como placeholder."""
    try:
        from PIL import Image, ImageDraw
        img  = Image.new("RGB", (DEFAULT_IMG_W, DEFAULT_IMG_H), color=(10, 12, 20))
        draw = ImageDraw.Draw(img)
        draw.text((DEFAULT_IMG_W // 2, DEFAULT_IMG_H // 2),
                  text[:80], fill=(100, 100, 140), anchor="mm")
        img.save(output_path, "PNG")
    except Exception:
        with open(output_path, "wb") as f:
            f.write(bytes([
                0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A,
                0x00,0x00,0x00,0x0D,0x49,0x48,0x44,0x52,
                0x00,0x00,0x00,0x01,0x00,0x00,0x00,0x01,
                0x08,0x02,0x00,0x00,0x00,0x90,0x77,0x53,
                0xDE,0x00,0x00,0x00,0x0C,0x49,0x44,0x41,
                0x54,0x08,0xD7,0x63,0xF8,0xCF,0xC0,0x00,
                0x00,0x00,0x02,0x00,0x01,0xE2,0x21,0xBC,
                0x33,0x00,0x00,0x00,0x00,0x49,0x45,0x4E,
                0x44,0xAE,0x42,0x60,0x82,
            ]))


def _kenburns_vf(clip_dur: float, fps: int, w: int, h: int, scene_idx: int) -> str:
    """Wrapper legacy → delega a animation_engine para compatibilidad."""
    from core.animation_engine import build_animation_vf
    return build_animation_vf("kenburns", clip_dur, fps, w, h, scene_idx)


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
    """Genera un clip de intro con titulo y subtitulo sobre fondo negro."""
    if not os.path.isfile(FFMPEG_EXE):
        return False
    import re as _re
    safe_title    = _re.sub(r"[:'%]", '', title)[:60]
    safe_subtitle = _re.sub(r"[:'%]", '', subtitle)[:80]
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
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t", str(duration),
        "-c:v", codec, "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
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


def _assemble_clip(
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
    scene_title: str = "",
    animation_effect: str = "kenburns",
) -> bool:
    """
    Combina imagen + audio en clip mp4 con efectos de animación/ken burns.
    """
    if not os.path.isfile(FFMPEG_EXE):
        log.error(f"[VideoStudio] ffmpeg no encontrado en {FFMPEG_EXE}")
        return False

    try:
        _input_is_video = image_path.lower().endswith((".mp4", ".webm", ".mov", ".avi"))
        has_audio = audio_path and os.path.isfile(audio_path) and os.path.getsize(audio_path) > 0

        audio_dur = SECONDS_PER_SCENE
        if has_audio:
            try:
                probe = subprocess.run(
                    [FFMPEG_EXE, "-i", audio_path],
                    capture_output=True, timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                for line in probe.stderr.decode(errors="replace").splitlines():
                    if "Duration:" in line:
                        t = line.split("Duration:")[1].split(",")[0].strip()
                        h, m, s = t.split(":")
                        audio_dur = int(h)*3600 + int(m)*60 + float(s)
                        break
            except Exception:
                pass

        if duration_mode == "manual":
            clip_dur = float(scene_duration)
        else:
            clip_dur = audio_dur + 0.5 if has_audio else float(scene_duration)
        fade_d     = min(FADE_DURATION, clip_dur / 3) if fade else 0.0
        fade_out_t = max(0, clip_dur - fade_d)

        w_val, h_val = DEFAULT_IMG_W, DEFAULT_IMG_H
        if "x" in resolution:
            parts = resolution.split("x")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                w_val, h_val = int(parts[0]), int(parts[1])

        from core.animation_engine import build_animation_vf

        if ken_burns:
            animation_vf = build_animation_vf(animation_effect, clip_dur, fps, w_val, h_val, scene_idx)
        else:
            animation_vf = (
                f"scale={w_val}:{h_val}:force_original_aspect_ratio=decrease,"
                f"pad={w_val}:{h_val}:(ow-iw)/2:(oh-ih)/2:black,fps={fps}"
            )

        vf_parts = [animation_vf]

        if color_grade:
            vf_parts.append(color_grade)

        vf_parts.append("noise=alls=7:allf=t+u")

        if subtitles and text:
            def fmt_time(s: float) -> str:
                ms = int((s % 1) * 1000)
                m, s_int = divmod(int(s), 60)
                _h, _m = divmod(m, 60)
                return f"{_h:02d}:{_m:02d}:{s_int:02d},{ms:03d}"

            srt_dir = os.path.dirname(output_mp4)
            scene_name = os.path.splitext(os.path.basename(image_path))[0]
            srt_path = os.path.join(srt_dir, f"{scene_name}.srt")
            with open(srt_path, "w", encoding="utf-8") as srt_f:
                srt_f.write(f"1\n00:00:00,000 --> {fmt_time(clip_dur)}\n{text}\n")

            safe_srt = srt_path.replace('\\', '/').replace(':', '\\:')
            vf_parts.append(f"subtitles='{safe_srt}':force_style='FontSize=26,PrimaryColour=&H0000FFFF,BorderStyle=1,Outline=3,Shadow=2,Bold=1,Alignment=2,MarginV=35'")

        if scene_title:
            safe_t = scene_title.replace("'", "").replace(":", "").replace("%", "")[:40].upper()
            draw_t = (
                f"drawtext=text='{safe_t}':fontcolor=white@0.7:fontsize={h_val//22}:"
                f"x=50:y=h-100:fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
                f"alpha='if(lt(t,0.8),t/0.8,if(lt(t,3.5),1,if(lt(t,4.2),1-(t-3.5)/0.7,0)))'"
            )
            vf_parts.append(draw_t)

        try:
            _wcfg = _get_branding_config()
            if _wcfg.get("watermark_enabled", True):
                _wtext   = _wcfg.get("watermark_text", "@DarckRovert").replace("'", "").replace(":", "").replace("%", "")
                _wopacity = float(_wcfg.get("watermark_opacity", 0.55))
                _wsize   = max(16, h_val // 38)
                _wmark   = (
                    f"drawtext=text='{_wtext}':fontcolor=white@{_wopacity:.2f}:fontsize={_wsize}:"
                    f"x=w-tw-18:y=h-th-18:fontfile='C\\:/Windows/Fonts/arial.ttf'"
                )
                vf_parts.append(_wmark)
        except Exception:
            pass

        if fade and fade_d > 0:
            vf_parts.append(f"fade=t=in:st=0:d={fade_d}")
            vf_parts.append(f"fade=t=out:st={fade_out_t:.3f}:d={fade_d}")
        vf = ",".join(vf_parts)

        if has_audio:
            if _input_is_video:
                cmd = [
                    FFMPEG_EXE, "-y",
                    "-stream_loop", "-1", "-i", image_path,
                    "-i", audio_path,
                    "-c:v", codec, "-preset", "fast",
                    "-c:a", "aac", "-b:a", "192k",
                    "-ar", "44100", "-ac", "2",
                ]
            else:
                if "zoompan" in vf:
                    cmd = [
                        FFMPEG_EXE, "-y",
                        "-i", image_path,
                        "-i", audio_path,
                        "-c:v", codec, "-preset", "fast",
                        "-c:a", "aac", "-b:a", "192k",
                        "-ar", "44100", "-ac", "2",
                    ]
                else:
                    cmd = [
                        FFMPEG_EXE, "-y",
                        "-loop", "1", "-i", image_path,
                        "-i", audio_path,
                        "-c:v", codec, "-preset", "fast",
                        "-c:a", "aac", "-b:a", "192k",
                        "-ar", "44100", "-ac", "2",
                    ]

            if duration_mode == "manual" and audio_dur > 0:
                raw_tempo = audio_dur / clip_dur
                tempo = max(0.85, min(raw_tempo, 1.25))
                if abs(tempo - 1.0) > 0.05:
                    cmd.extend(["-filter:a", f"atempo={tempo:.4f}"])
                    log.info(f"[VideoStudio] Alineación de audio limitada: raw_tempo={raw_tempo:.2f} -> atempo={tempo:.4f}")

            if duration_mode == "manual":
                cmd.extend(["-t", str(scene_duration)])
            else:
                cmd.append("-shortest")

            cmd.extend([
                "-vf", vf,
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_mp4,
            ])
        else:
            if _input_is_video:
                cmd = [
                    FFMPEG_EXE, "-y",
                    "-stream_loop", "-1", "-i", image_path,
                    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                    "-t", str(scene_duration),
                    "-c:v", codec, "-preset", "fast",
                    "-c:a", "aac", "-b:a", "128k",
                    "-vf", vf,
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    output_mp4,
                ]
            else:
                cmd = [
                    FFMPEG_EXE, "-y",
                    "-loop", "1", "-i", image_path,
                    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                    "-t", str(scene_duration),
                    "-c:v", codec, "-preset", "fast",
                    "-c:a", "aac", "-b:a", "128k",
                    "-vf", vf,
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    output_mp4,
                ]

        result = subprocess.run(
            cmd, capture_output=True, timeout=180,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0 and os.path.isfile(output_mp4):
            log.info(f"[VideoStudio] Clip: {os.path.basename(output_mp4)}")
            return True
        else:
            err = result.stderr.decode(errors="replace")[-400:]
            log.error(f"[VideoStudio] ffmpeg error clip: {err}")
            return False
    except Exception as e:
        log.error(f"[VideoStudio] Error ensamblando clip: {e}")
        return False


def _concatenate_clips(
    clip_paths: list[str],
    output_mp4: str,
    bgm_type: str = "ninguna",
    bgm_volume: float = 0.1,
    codec: str = "libx264",
    resolution: str = "1024x1024"
) -> bool:
    """
    Concatena clips en el video final.
    """
    if not clip_paths:
        return False

    if len(clip_paths) == 1:
        import shutil
        shutil.copy2(clip_paths[0], output_mp4)
        return True

    missing = [p for p in clip_paths if not os.path.isfile(p) or os.path.getsize(p) == 0]
    if missing:
        log.error(f"[VideoStudio] Clips faltantes o vacíos: {[os.path.basename(m) for m in missing]}")
        clip_paths = [p for p in clip_paths if os.path.isfile(p) and os.path.getsize(p) > 0]
        if not clip_paths:
            return False

    dyn_timeout = 120 + len(clip_paths) * 90

    def _write_list(path: str, clips: list[str]) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            for cp in clips:
                safe = cp.replace("\\", "/")
                fh.write(f"file '{safe}'\n")

    def _cleanup(path: str) -> None:
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass

    list_file = output_mp4 + ".list.txt"

    bgm_path = os.path.join(BASE_DIR, "inputs", f"bgm_{bgm_type.lower()}.mp3")
    if bgm_type != "ninguna" and not (os.path.isfile(bgm_path) and os.path.getsize(bgm_path) > 4096):
        _ensure_bgm(bgm_type, bgm_path)
    has_bgm = bgm_type != "ninguna" and os.path.isfile(bgm_path) and os.path.getsize(bgm_path) > 4096

    # ══ CAPA 1: Re-encode completo con normalización A/V ════════════════════
    try:
        _write_list(list_file, clip_paths)

        if has_bgm:
            temp_concat = output_mp4 + ".temp.mp4"
            cmd_concat = [
                FFMPEG_EXE, "-y",
                "-f", "concat", "-safe", "0",
                "-i", list_file,
                "-c:v", codec, "-preset", "fast",
                "-c:a", "aac", "-b:a", "192k",
                "-ar", "44100", "-ac", "2",
                "-movflags", "+faststart",
                temp_concat,
            ]
            r_concat = subprocess.run(cmd_concat, capture_output=True, timeout=dyn_timeout, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if r_concat.returncode == 0 and os.path.isfile(temp_concat):
                filter_str = (
                    f"[0:a]aresample=44100,volume=1.2,asplit[sc][narr];"
                    f"[1:a]aresample=44100,volume={bgm_volume:.3f}[bgm];"
                    f"[bgm][sc]sidechaincompress=threshold=0.03:ratio=5:level_sc=0.8:attack=20:release=500[bgm_duck];"
                    f"[narr][bgm_duck]amix=inputs=2:duration=first:dropout_transition=2,volume=1.8[aout]"
                )
                cmd = [
                    FFMPEG_EXE, "-y",
                    "-i", temp_concat,
                    "-stream_loop", "-1", "-i", bgm_path,
                    "-filter_complex", filter_str,
                    "-map", "0:v",
                    "-map", "[aout]",
                    "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k",
                    "-ar", "44100", "-ac", "2",
                    "-movflags", "+faststart",
                    output_mp4,
                ]
                log.info(f"[VideoStudio] [L1] Concat {len(clip_paths)} clips + BGM ({bgm_type}) -> {os.path.basename(output_mp4)}")
            else:
                log.error(f"[VideoStudio] [L1] Falló pre-concat: {r_concat.stderr.decode(errors='replace')[-400:]}")
                cmd = None
        else:
            cmd = [
                FFMPEG_EXE, "-y",
                "-f", "concat", "-safe", "0",
                "-i", list_file,
                "-c:v", codec, "-preset", "fast",
                "-c:a", "aac", "-b:a", "192k",
                "-ar", "44100", "-ac", "2",
                "-movflags", "+faststart",
                output_mp4,
            ]
            log.info(f"[VideoStudio] [L1] Concat {len(clip_paths)} clips -> {os.path.basename(output_mp4)}")

        if cmd:
            r1 = subprocess.run(cmd, capture_output=True, timeout=dyn_timeout,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        _cleanup(list_file)
        if has_bgm and 'temp_concat' in locals():
            _cleanup(temp_concat)

        if r1.returncode == 0 and os.path.isfile(output_mp4) and os.path.getsize(output_mp4) > 0:
            log.info(f"[VideoStudio] Video final: {os.path.basename(output_mp4)} ({os.path.getsize(output_mp4)/1048576:.1f} MB)")
            return True

        err1 = r1.stderr.decode(errors="replace")[-600:]
        log.error(f"[VideoStudio] [L1] Falló: {err1}")

    except Exception as e1:
        log.error(f"[VideoStudio] [L1] Excepción: {e1}")
        _cleanup(list_file)

    # ══ CAPA 2: Stream-copy ═════════════════════════════════════════════════
    try:
        _write_list(list_file, clip_paths)
        cmd2 = [
            FFMPEG_EXE, "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            "-movflags", "+faststart",
            output_mp4,
        ]
        log.info("[VideoStudio] [L2] Reintentando con stream-copy...")
        r2 = subprocess.run(cmd2, capture_output=True, timeout=dyn_timeout,
                            creationflags=subprocess.CREATE_NO_WINDOW)
        _cleanup(list_file)

        if r2.returncode == 0 and os.path.isfile(output_mp4) and os.path.getsize(output_mp4) > 0:
            log.info(f"[VideoStudio] Video final (stream-copy): {os.path.basename(output_mp4)} ({os.path.getsize(output_mp4)/1048576:.1f} MB)")
            return True

        err2 = r2.stderr.decode(errors="replace")[-400:]
        log.error(f"[VideoStudio] [L2] Falló: {err2}")

    except Exception as e2:
        log.error(f"[VideoStudio] [L2] Excepción: {e2}")
        _cleanup(list_file)

    # ══ CAPA 3: Pre-normalizar cada clip → luego concat ═════════════════════
    log.info("[VideoStudio] [L3] Pre-normalizando clips individualmente...")
    norm_dir = os.path.join(os.path.dirname(output_mp4), "_norm_tmp")
    os.makedirs(norm_dir, exist_ok=True)
    norm_clips: list[str] = []

    try:
        for idx, cp in enumerate(clip_paths):
            norm_out = os.path.join(norm_dir, f"norm_{idx:03d}.mp4")
            ref_w, ref_h = DEFAULT_IMG_W, DEFAULT_IMG_H
            if "x" in resolution:
                parts = resolution.split("x")
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    ref_w, ref_h = int(parts[0]), int(parts[1])
            cmd_norm = [
                FFMPEG_EXE, "-y",
                "-i", cp,
                "-vf", f"scale={ref_w}:{ref_h}:force_original_aspect_ratio=decrease,pad={ref_w}:{ref_h}:(ow-iw)/2:(oh-ih)/2:black,fps={DEFAULT_FPS}",
                "-af", "aresample=44100",
                "-c:v", codec, "-preset", "fast",
                "-c:a", "aac", "-b:a", "128k",
                "-ar", "44100", "-ac", "2",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                norm_out,
            ]
            rn = subprocess.run(cmd_norm, capture_output=True, timeout=180,
                                creationflags=subprocess.CREATE_NO_WINDOW)
            if rn.returncode == 0 and os.path.isfile(norm_out) and os.path.getsize(norm_out) > 0:
                norm_clips.append(norm_out)
            else:
                log.warning(f"[VideoStudio] [L3] No se pudo normalizar clip {idx}: {os.path.basename(cp)}")
                norm_clips.append(cp)

        if not norm_clips:
            log.error("[VideoStudio] [L3] Sin clips para concatenar tras normalización.")
            return False

        _write_list(list_file, norm_clips)
        cmd3 = [
            FFMPEG_EXE, "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_file,
            "-c:v", codec, "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            "-ar", "44100", "-ac", "2",
            "-movflags", "+faststart",
            output_mp4,
        ]
        log.info(f"[VideoStudio] [L3] Concat post-normalización ({len(norm_clips)} clips)...")
        r3 = subprocess.run(cmd3, capture_output=True, timeout=dyn_timeout,
                            creationflags=subprocess.CREATE_NO_WINDOW)
        _cleanup(list_file)

        if r3.returncode == 0 and os.path.isfile(output_mp4) and os.path.getsize(output_mp4) > 0:
            log.info(f"[VideoStudio] Video final (L3): {os.path.basename(output_mp4)} ({os.path.getsize(output_mp4)/1048576:.1f} MB)")
            return True

        log.error(f"[VideoStudio] [L3] Falló: {r3.stderr.decode(errors='replace')[-400:]}")

    except Exception as e3:
        log.error(f"[VideoStudio] [L3] Excepción: {e3}")
        _cleanup(list_file)
    finally:
        try:
            import shutil as _sh
            _sh.rmtree(norm_dir, ignore_errors=True)
        except Exception:
            pass

    log.error("[VideoStudio] Las 3 capas de concatenación fallaron. Job marcado como fallido.")
    return False
