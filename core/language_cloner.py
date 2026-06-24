"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — LANGUAGE CLONER V2.0                                           ║
║  Multiplica un video a EN / PT / FR reutilizando los assets ya renderizados  ║
║                                                                              ║
║  Flujo:                                                                      ║
║    1. Lee el guion JSON generado por el pipeline (guardado en job_dir)       ║
║    2. Llama al LLM para traducir el guion a cada idioma objetivo             ║
║    3. Genera narración TTS en el idioma nuevo (SAPI o pyttsx3)               ║
║    4. Recompone el video usando las imágenes ya renderizadas + nuevo audio   ║
║    5. Encola el upload YouTube con el idioma correcto                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import subprocess
import threading
import sqlite3
import time
import random
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from core.logger import log
from core.config_manager import config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG_EXE = os.path.join(BASE_DIR, "_integrations", "ffmpeg", "ffmpeg.exe")
OUTPUT_DIR = os.path.join(BASE_DIR, "_videos")
DB_PATH = os.path.join(BASE_DIR, "_video_queue.sqlite")
REMOTION_FPS = 30  # Debe coincidir con fps en remotion_workspace/src/Root.tsx
CREATION_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

# Idiomas soportados: código IETF -> config TTS voz + código YouTube
LANG_CONFIG: Dict[str, Dict[str, str]] = {
    "en": {
        "voice_hint": "english",
        "yt_title_suffix": "",
        "description_lang": "English",
    },
    "pt": {
        "voice_hint": "portuguese",
        "yt_title_suffix": " [PT]",
        "description_lang": "Português",
    },
    "fr": {
        "voice_hint": "french",
        "yt_title_suffix": " [FR]",
        "description_lang": "Français",
    },
    "de": {
        "voice_hint": "german",
        "yt_title_suffix": " [DE]",
        "description_lang": "Deutsch",
    },
}

_cloner_lock = threading.RLock()
_tts_lock = threading.Lock()


# ── Config ────────────────────────────────────────────────────────────────────


def _load_config() -> Dict[str, Any]:
    """Carga de forma segura la configuración de clonación mediante ConfigManager."""
    try:
        return config.get("language_cloner", {})
    except Exception as e:
        log.error(f"[LangCloner] Error cargando config: {e}")
        return {}


def get_enabled_languages() -> List[str]:
    """Retorna la lista de idiomas habilitados para clonación en la configuración."""
    cfg = _load_config()
    return [l for l in cfg.get("languages", ["en"]) if l in LANG_CONFIG]


# ── LLM translation ───────────────────────────────────────────────────────────


def _translate_script(
    scenes: List[Dict[str, Any]], target_lang: str, original_lang: str = "es"
) -> List[Dict[str, Any]]:
    """
    Traduce el guion de escenas usando el LLM del bridge con reintentos.
    """
    lang_name = {
        "en": "English",
        "pt": "Portuguese (Brazil)",
        "fr": "French",
        "de": "German",
    }.get(target_lang, target_lang)

    from core import provider_manager

    chunk_size = 5
    all_translated = []

    for i in range(0, len(scenes), chunk_size):
        chunk = scenes[i : i + chunk_size]
        script_text = json.dumps(chunk, ensure_ascii=False, indent=2)
        prompt = (
            f"Translate the following JSON array of video scenes from {original_lang} to {lang_name}.\n"
            f"Rules:\n"
            f"- Preserve EXACTLY the JSON structure and all keys.\n"
            f"- Only translate the values of: title, narration, image_prompt keys.\n"
            f"- Keep image_prompt values visual and descriptive.\n"
            f"- Return ONLY the valid JSON array, no extra text.\n\n"
            f"JSON:\n{script_text}"
        )

        success = False
        for attempt in range(3):
            try:
                messages = [{"role": "user", "content": prompt}]
                best_result, best_model = provider_manager.get_best()
                if not best_result:
                    raise RuntimeError("No LLM disponible para traducción")

                raw = provider_manager.complete(
                    messages,
                    model=best_model,
                    provider=best_result.name,
                    options={"temperature": 0.3, "max_tokens": 4096},
                )

                # Extraer JSON del response
                start = raw.find("[")
                end = raw.rfind("]") + 1
                if start >= 0 and end > start:
                    translated_chunk = json.loads(raw[start:end])
                    if isinstance(translated_chunk, list) and len(
                        translated_chunk
                    ) == len(chunk):
                        all_translated.extend(translated_chunk)
                        success = True
                        break

                log.warning(
                    f"[LangCloner] Intento {attempt+1}: Traducción a {target_lang} retornó JSON inválido."
                )
                time.sleep(2)
            except Exception as e:
                log.error(
                    f"[LangCloner] Intento {attempt+1}: Error traduciendo a {target_lang}: {e}"
                )
                time.sleep(2)

        if not success:
            log.error(
                f"[LangCloner] Fallaron los 3 intentos de traducción para el chunk {i//chunk_size}. Usando original."
            )
            all_translated.extend(chunk)

    log.info(
        f"[LangCloner] Guion traducido a {target_lang} ({len(all_translated)} escenas)."
    )
    return all_translated


def _translate_title(title: str, target_lang: str, original_lang: str = "es") -> str:
    """Traduce el título del video al idioma objetivo usando LLM."""
    if not title:
        return ""
    lang_name = {
        "en": "English",
        "pt": "Portuguese (Brazil)",
        "fr": "French",
        "de": "German",
    }.get(target_lang, target_lang)
    prompt = f"Translate the following video title from {original_lang} to {lang_name}. Respond ONLY with the translated text, nothing else. Title: {title}"

    from core import provider_manager

    for attempt in range(2):
        try:
            messages = [{"role": "user", "content": prompt}]
            best_result, best_model = provider_manager.get_best()
            if best_result:
                raw = provider_manager.complete(
                    messages,
                    model=best_model,
                    provider=best_result.name,
                    options={"temperature": 0.3, "max_tokens": 100},
                )
                return raw.strip().replace('"', "").replace("\n", "")
        except Exception as e:
            log.error(f"[LangCloner] Error traduciendo título a {target_lang}: {e}")
    return title


# ── TTS en el nuevo idioma ────────────────────────────────────────────────────


def _generate_audio_for_lang(text: str, output_wav: str, lang_code: str) -> bool:
    """Genera narración TTS en el idioma dado usando pyttsx3 (SAPI en Windows) de forma segura y exclusiva."""
    with _tts_lock:
        try:
            import pyttsx3

            # CoInitialize es obligatorio en CADA thread que use COM en Windows.
            _com_initialized = False
            try:
                import pythoncom

                pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
                _com_initialized = True
            except Exception:
                try:
                    import pythoncom  # type: ignore

                    pythoncom.CoInitialize()
                    _com_initialized = True
                except Exception:
                    pass

            try:
                engine = pyttsx3.init()
                voices = engine.getProperty("voices")
                lang_hint = (
                    LANG_CONFIG.get(lang_code, {}).get("voice_hint", "english").lower()
                )

                selected = None
                for v in voices:
                    name_lower = (v.name or "").lower()
                    lang_lower = (
                        (v.languages[0] if v.languages else b"").lower()
                        if isinstance((v.languages[0] if v.languages else ""), bytes)
                        else (v.languages[0] if v.languages else "").lower()
                    )
                    if lang_hint in name_lower or lang_hint in str(lang_lower):
                        selected = v.id
                        break

                if selected:
                    engine.setProperty("voice", selected)
                else:
                    log.warning(
                        f"[LangCloner] No se encontró voz para '{lang_hint}'. Usando voz por defecto."
                    )

                engine.setProperty("rate", 155)
                engine.save_to_file(text, output_wav)
                engine.runAndWait()

                # Desvincular motor para asegurar recolección COM exitosa
                del engine

                return os.path.isfile(output_wav)
            finally:
                if _com_initialized:
                    try:
                        import pythoncom

                        pythoncom.CoUninitialize()
                    except Exception:
                        pass

        except Exception as e:
            log.error(f"[LangCloner] Error TTS {lang_code}: {e}")
            return False


# ── Recomposición del clip con nuevo audio ────────────────────────────────────


def _recompose_clip(
    image_path: str,
    audio_wav: str,
    output_mp4: str,
    duration: float,
    text: str = "",
    scene_idx: int = 0,
    codec: str = "libx264",
) -> bool:
    """Recompone un clip heredando el motor visual de video_pipeline (animación y subtítulos)."""
    try:
        from core.video_pipeline import _assemble_clip

        return _assemble_clip(
            image_path=image_path,
            audio_path=audio_wav,
            output_mp4=output_mp4,
            fade=True,
            text=text,
            subtitles=True,
            duration_mode="manual",
            scene_duration=duration,
            codec=codec,
            scene_idx=scene_idx,
            ken_burns=True,
        )
    except Exception as e:
        log.error(f"[LangCloner] Error recomponiendo clip: {e}")
        return False


def _concat_clips(clip_list: List[str], output_mp4: str) -> bool:
    """Concatena clips con FFmpeg concat demuxer de forma portable."""
    try:
        list_path = output_mp4.replace(".mp4", "_list.txt")
        with open(list_path, "w", encoding="utf-8") as f:
            for c in clip_list:
                f.write(f"file '{c.replace(chr(92), '/')}'\n")
        cmd = [
            FFMPEG_EXE,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            list_path,
            "-c",
            "copy",
            output_mp4,
        ]
        r = subprocess.run(
            cmd, capture_output=True, timeout=300, creationflags=CREATION_FLAGS
        )
        try:
            os.remove(list_path)
        except Exception:
            pass
        return r.returncode == 0 and os.path.isfile(output_mp4)
    except Exception as e:
        log.error(f"[LangCloner] Error concatenando: {e}")
        return False


# ── DB con robustez concurrente ─────────────────────────────────────────────────


def _execute_db_query(
    query: str, params: tuple = (), is_write: bool = False
) -> Optional[List[Any]]:
    """Ejecuta una consulta SQL en DB_PATH con reintentos exponenciales y retroceso aleatorizado."""
    for attempt in range(5):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30.0)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(query, params)
            if is_write:
                conn.commit()
                res = cur.lastrowid
            else:
                res = cur.fetchall()
            conn.close()
            return res
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < 4:
                sleep_time = 0.1 * (2**attempt) + random.uniform(0.05, 0.15)
                time.sleep(sleep_time)
                continue
            log.error(
                f"[LangCloner] DB locked error in query '{query}' (attempt {attempt+1}): {e}"
            )
            raise
        except Exception as e:
            log.error(f"[LangCloner] DB query error: {e}")
            raise


def _get_job_data(source_job_id: int) -> Optional[Dict[str, Any]]:
    """Retorna los datos del job origen con tolerancia a bloqueos concurrentes."""
    try:
        rows = _execute_db_query(
            "SELECT topic, title, style, output_path, thumbnail_path, niche_id FROM video_jobs WHERE id=?",
            (source_job_id,),
            is_write=False,
        )
        if not rows:
            return None
        row = rows[0]
        return {
            "topic": row["topic"],
            "title": row["title"],
            "style": row["style"],
            "output_path": row["output_path"],
            "thumbnail_path": row["thumbnail_path"],
            "niche_id": row["niche_id"] if "niche_id" in row.keys() else "",
        }
    except Exception as e:
        log.error(f"[LangCloner] _get_job_data DB error: {e}")
        return None


def _register_clone_job(
    source_job_id: int, lang: str, output_path: str, title: str, niche_id: str = ""
) -> int:
    """Registra el video clonado como un nuevo job en la DB de forma segura."""
    try:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        last_id = _execute_db_query(
            "INSERT INTO video_jobs (topic, title, n_scenes, style, narration_lang, status, progress, "
            "current_step, output_path, created_at, finished_at, upload_status, niche_id, cloned_from, clone_lang) "
            "VALUES (?, ?, 0, 'cloned', ?, 'done', 100, 'Clon de idioma listo', ?, ?, ?, 'pending', ?, ?, ?)",
            (
                f"[CLONE:{lang}] {title}",
                title,
                lang,
                output_path,
                now,
                now,
                niche_id,
                source_job_id,
                lang,
            ),
            is_write=True,
        )
        return last_id or 0
    except Exception as e:
        log.error(f"[LangCloner] Error registrando clon: {e}")
        return 0


# ── API Pública ───────────────────────────────────────────────────────────────


def clone_job(
    source_job_id: int, target_langs: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Clona el video de un job existente a los idiomas especificados.
    Si target_langs es None, usa los habilitados en la configuración.
    """
    with _cloner_lock:
        if target_langs is None:
            target_langs = get_enabled_languages()

        if not target_langs:
            return {
                "ok": False,
                "error": "Sin idiomas habilitados. Configura language_cloner.languages en config.yaml",
            }

        job_data = _get_job_data(source_job_id)
        if not job_data:
            return {"ok": False, "error": f"Job #{source_job_id} no encontrado."}

        # El job_dir contiene las imágenes originales
        job_dir = os.path.join(OUTPUT_DIR, f"job_{source_job_id}")
        if not os.path.isdir(job_dir):
            return {"ok": False, "error": f"Directorio de job no encontrado: {job_dir}"}

        # Leer el guion JSON guardado durante el render
        script_path = os.path.join(job_dir, "script.json")
        if not os.path.isfile(script_path):
            return {
                "ok": False,
                "error": f"script.json no encontrado en {job_dir}. El pipeline debe guardarlo.",
            }

        with open(script_path, "r", encoding="utf-8") as f:
            original_scenes = json.load(f)

        results = []
        for lang in target_langs:
            log.info(f"[LangCloner] Clonando job #{source_job_id} a idioma: {lang}")
            lang_conf = LANG_CONFIG.get(lang, {})

            # 1. Traducir guion
            translated_scenes = _translate_script(original_scenes, lang)

            # 2. Generar audio y clips por escena
            lang_dir = os.path.join(job_dir, f"lang_{lang}")
            os.makedirs(lang_dir, exist_ok=True)

            clip_paths = []
            for i, scene in enumerate(translated_scenes):
                narration = scene.get("narration", "")
                image_path = os.path.join(job_dir, f"scene_{i+1:02d}_image.jpg")
                if not os.path.isfile(image_path):
                    image_path = os.path.join(job_dir, f"scene_{i+1:02d}_image.png")
                if not os.path.isfile(image_path):
                    log.warning(
                        f"[LangCloner] Imagen scene_{i+1:03d} no encontrada, saltando."
                    )
                    continue

                audio_wav = os.path.join(lang_dir, f"audio_{i+1:03d}.wav")
                clip_mp4 = os.path.join(lang_dir, f"clip_{i+1:03d}.mp4")

                if _generate_audio_for_lang(narration, audio_wav, lang):
                    # Estimar duración del audio
                    try:
                        r = subprocess.run(
                            [FFMPEG_EXE, "-i", audio_wav],
                            capture_output=True,
                            timeout=10,
                            creationflags=CREATION_FLAGS,
                        )
                        import re

                        m = re.search(
                            r"Duration: (\d+):(\d+):(\d+\.?\d*)",
                            r.stderr.decode(errors="replace"),
                        )
                        dur = (
                            float(m.group(3))
                            + int(m.group(2)) * 60
                            + int(m.group(1)) * 3600
                            if m
                            else 8.0
                        )
                        dur = max(dur + 0.5, 6.0)
                    except Exception:
                        dur = 8.0

                    if _recompose_clip(
                        image_path,
                        audio_wav,
                        clip_mp4,
                        dur,
                        text=narration,
                        scene_idx=i,
                    ):
                        clip_paths.append(clip_mp4)

            if not clip_paths:
                log.error(f"[LangCloner] Sin clips generados para {lang}.")
                results.append({"lang": lang, "ok": False, "error": "Sin clips"})
                continue

            # 3. Concatenar
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            final_path = os.path.join(
                OUTPUT_DIR, f"clone_{source_job_id}_{lang}_{ts}.mp4"
            )
            suffix = lang_conf.get("yt_title_suffix", f" [{lang.upper()}]")

            base_title = job_data.get("title") or job_data.get("topic", "Video")
            translated_title = _translate_title(base_title, lang)
            clone_title = translated_title[:95] + suffix

            if not _concat_clips(clip_paths, final_path):
                results.append(
                    {"lang": lang, "ok": False, "error": "Concatenación fallida"}
                )
                continue

            # 4. Registrar en DB y disparar upload con idioma
            clone_job_id = _register_clone_job(
                source_job_id,
                lang,
                final_path,
                clone_title,
                niche_id=job_data.get("niche_id", ""),
            )

            from core.youtube_uploader import upload_job_async

            upload_job_async(
                job_id=clone_job_id,
                video_path=final_path,
                title=clone_title,
                niche_id=job_data.get("niche_id", ""),
                lang=lang,
            )

            # --- START REMOTION SHORTS CLONER ---
            _shorts_path = final_path.replace(".mp4", "_short.mp4")
            try:
                log.info(
                    f"[LangCloner] Generando versión Short para {lang} con Remotion..."
                )
                from core.whisper_engine import WhisperEngine
                from core.remotion_engine import RemotionEngine

                # Recortar a máximo 59s (límite YouTube Shorts)
                temp_short_src = final_path.replace(".mp4", "_temp_short.mp4")
                subprocess.run(
                    [
                        FFMPEG_EXE,
                        "-y",
                        "-i",
                        final_path,
                        "-t",
                        "59",
                        "-c:v",
                        "copy",
                        "-c:a",
                        "copy",
                        temp_short_src,
                    ],
                    capture_output=True,
                    creationflags=CREATION_FLAGS,
                )

                probe = subprocess.run(
                    [FFMPEG_EXE, "-i", temp_short_src],
                    capture_output=True,
                    text=True,
                    errors="replace",
                    creationflags=CREATION_FLAGS,
                )
                dur = 59
                for l in probe.stderr.splitlines():
                    if "Duration:" in l:
                        t = l.split("Duration:")[1].split(",")[0].strip()
                        h, m, s = t.strip().split(":")
                        dur = int(h) * 3600 + int(m) * 60 + float(s)
                        break
                duration_frames = int(dur * REMOTION_FPS)

                w_engine = WhisperEngine(model_size="base")
                words_data = w_engine.extract_words(
                    temp_short_src, language=lang[:2].lower()
                )

                r_engine = RemotionEngine()
                props = {
                    "videoPath": temp_short_src,
                    "words": words_data,
                    "durationInFrames": duration_frames,
                }

                output_name = os.path.basename(_shorts_path).replace(".mp4", "")
                rendered_mp4 = r_engine.render_composition(
                    "ShortTemplate", output_name, props
                )

                if os.path.isfile(rendered_mp4):
                    import shutil

                    shutil.move(rendered_mp4, _shorts_path)
                    log.info(
                        f"[LangCloner] Short {lang} generado exitosamente: {_shorts_path}"
                    )

                    try:
                        from core.tiktok_uploader import distribute_short_async

                        distribute_short_async(
                            job_id=clone_job_id,
                            shorts_path=_shorts_path,
                            title=clone_title,
                        )
                    except Exception as _tt_e:
                        log.warning(f"[LangCloner] Social distribution error: {_tt_e}")

                try:
                    os.remove(temp_short_src)
                except Exception:
                    pass

            except Exception as rem_e:
                log.error(f"[LangCloner] Error generando Short con Remotion: {rem_e}")
            # --- END REMOTION SHORTS CLONER ---
            results.append(
                {
                    "lang": lang,
                    "ok": True,
                    "clone_job_id": clone_job_id,
                    "title": clone_title,
                    "path": final_path,
                }
            )
            log.info(f"[LangCloner] Clon {lang} listo: {clone_title}")

        return {"ok": True, "source_job_id": source_job_id, "clones": results}


def clone_job_async(
    source_job_id: int, target_langs: Optional[List[str]] = None
) -> None:
    """Dispara la clonación multi-idioma en un thread daemon."""

    def _run():
        result = clone_job(source_job_id, target_langs)
        ok_langs = [c["lang"] for c in result.get("clones", []) if c.get("ok")]
        log.info(f"[LangCloner] Job #{source_job_id} clonado a: {ok_langs}")

    threading.Thread(
        target=_run, name=f"GravityLangClone-{source_job_id}", daemon=True
    ).start()


def get_status() -> Dict[str, Any]:
    """Retorna el estado y configuración actual de la clonación."""
    return {
        "enabled_languages": get_enabled_languages(),
        "supported_languages": list(LANG_CONFIG.keys()),
        "config": _load_config(),
    }
