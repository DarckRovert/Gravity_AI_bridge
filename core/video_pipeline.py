"""
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘  GRAVITY AI â€” VIDEO STUDIO PIPELINE V10.3 CINEMATIC EDITION                  â•‘
â•‘                                                                              â•‘
â•‘  Motor cinematogrÃ¡fico de Ãºltima generaciÃ³n con:                             â•‘
â•‘    â–¸ Character Consistency Engine â€” ancla visual por escena                  â•‘
â•‘    â–¸ Seed unificada por job â€” coherencia de estilo Pollinations              â•‘
â•‘    â–¸ Selector de voz SAPI â€” elige narrador por ID/nombre                    â•‘
â•‘    â–¸ Estilos cinematogrÃ¡ficos â€” Documental, Anime, Noir, Ã‰pico, etc.        â•‘
â•‘    â–¸ Idioma de narraciÃ³n configurable                                        â•‘
â•‘    â–¸ Transiciones fade entre escenas via ffmpeg                              â•‘
â•‘    â–¸ Soporte de mÃºsica de fondo (pista silenciosa/placeholder)               â•‘
â•‘                                                                              â•‘
â•‘  Flujo completo:                                                             â•‘
â•‘    1. LLM extrae Visual Anchor + genera guiÃ³n con N escenas (JSON)           â•‘
â•‘    2. Pollinations genera imagen por escena (anchor + style + seed/job)      â•‘
â•‘    3. Windows SAPI convierte narraciÃ³n a audio .wav (voz elegida)            â•‘
â•‘    4. ffmpeg ensambla imagen + audio â†’ clip .mp4 por escena (con fade)       â•‘
â•‘    5. ffmpeg concatena todos los clips â†’ video final .mp4                    â•‘
â•‘                                                                              â•‘
â•‘  Prerrequisitos:                                                             â•‘
â•‘    - ffmpeg en _integrations/ffmpeg/ffmpeg.exe                               â•‘
â•‘    - pyttsx3 (pip install pyttsx3)                                           â•‘
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
"""

import os
import json
import time
import sqlite3
import threading
import subprocess
import hashlib
import math
from datetime import datetime, timezone
from typing import Optional

from core.logger import log

# â”€â”€ Rutas absolutas del proyecto â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG_EXE  = os.path.join(BASE_DIR, "_integrations", "ffmpeg", "ffmpeg.exe")
OUTPUT_DIR  = os.path.join(BASE_DIR, "_videos")
DB_PATH     = os.path.join(BASE_DIR, "_video_queue.sqlite")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# â”€â”€ ParÃ¡metros por defecto â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
DEFAULT_SCENES     = 6
DEFAULT_IMG_W      = 1216
DEFAULT_IMG_H      = 832
SECONDS_PER_SCENE  = 8
TTS_RATE           = 150
MAX_HISTORY        = 20
FADE_DURATION      = 0.4    # segundos de fade entre escenas

# â”€â”€ Estilos cinematogrÃ¡ficos â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CINEMA_STYLES: dict[str, dict] = {
    "documental": {
        "label":  "Documental",
        "prefix": "Cinematic documentary, photorealistic, professional lighting, 16:9 landscape, dramatic composition, high detail, award-winning photography",
        "negative": "cartoon, anime, painting, sketch, low quality, blurry",
    },
    "anime": {
        "label":  "Anime",
        "prefix": "Anime style, vibrant colors, high-quality illustration, detailed cel shading, dynamic scene, 16:9 aspect",
        "negative": "photorealistic, 3D render, low quality, blurry, ugly",
    },
    "epico": {
        "label":  "Ã‰pico / Fantasy",
        "prefix": "Epic fantasy artwork, dramatic lighting, cinematic atmosphere, detailed digital painting, heroic composition, 16:9",
        "negative": "modern, mundane, low quality, stock photo",
    },
    "noir": {
        "label":  "Noir / Thriller",
        "prefix": "Film noir, high contrast black and white, moody shadows, 1940s aesthetic, dramatic chiaroscuro, cinematic still, 16:9",
        "negative": "colorful, bright, cheerful, low quality",
    },
    "infantil": {
        "label":  "Infantil / Cuento",
        "prefix": "Children's storybook illustration, cute and colorful, soft warm lighting, friendly characters, Pixar-style, 16:9",
        "negative": "dark, scary, violent, photorealistic, gore",
    },
    "naturaleza": {
        "label":  "Naturaleza / Wildlife",
        "prefix": "National Geographic photography, ultra high resolution, dramatic natural lighting, pristine nature, macro or wide landscape, 16:9",
        "negative": "people, buildings, urban, low quality",
    },
    "cyberpunk": {
        "label":  "Cyberpunk / Sci-Fi",
        "prefix": "Cyberpunk cityscape, neon lights, rain-soaked streets, futuristic dystopia, cinematic composition, ultra-detailed, 16:9",
        "negative": "medieval, nature, low quality, blurry",
    },
    "historico": {
        "label":  "HistÃ³rico / Ã‰pocas",
        "prefix": "Historical epic scene, period-accurate set design, dramatic oil painting style, cinematic lighting, 16:9",
        "negative": "modern, sci-fi, cartoon, low quality",
    },
    "lofi": {
        "label":  "Lo-Fi / Estudiantil",
        "prefix": "Lofi aesthetic, cozy study room, warm pastel colors, rain window, soft grain texture, illustration style, calm atmosphere, 16:9",
        "negative": "dark, scary, violent, photorealistic, high contrast, gore",
    },
    "retro80s": {
        "label":  "Retro 80s / Synth-wave",
        "prefix": "Synthwave retro 1980s aesthetic, neon pink and purple gradients, grid horizon, chrome lettering, vaporwave sunset, cinematic 16:9",
        "negative": "modern minimal, flat design, photography, low quality, blurry",
    },
}
DEFAULT_STYLE = "documental"

# â”€â”€ Estado global â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_lock         = threading.Lock()
_current_job  = None
_started      = False


# â”€â”€ Base de datos â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS video_jobs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            topic           TEXT    NOT NULL,
            n_scenes        INTEGER NOT NULL DEFAULT 6,
            voice_speed     INTEGER NOT NULL DEFAULT 150,
            voice_id        TEXT    NOT NULL DEFAULT '',
            style           TEXT    NOT NULL DEFAULT 'documental',
            narration_lang  TEXT    NOT NULL DEFAULT 'es',
            transitions     INTEGER NOT NULL DEFAULT 1,
            status          TEXT    NOT NULL DEFAULT 'pending',
            progress        INTEGER NOT NULL DEFAULT 0,
            current_step    TEXT,
            output_path     TEXT,
            error           TEXT,
            created_at      TEXT    NOT NULL,
            started_at      TEXT,
            finished_at     TEXT
        )
    """)
    conn.commit()
    # MigraciÃ³n: aÃ±adir columnas nuevas si la tabla ya existÃ­a sin ellas
    existing = {row[1] for row in conn.execute("PRAGMA table_info(video_jobs)").fetchall()}
    migrations = [
        ("voice_id",       "TEXT NOT NULL DEFAULT ''"),
        ("style",          "TEXT NOT NULL DEFAULT 'documental'"),
        ("narration_lang", "TEXT NOT NULL DEFAULT 'es'"),
        ("transitions",    "INTEGER NOT NULL DEFAULT 1"),
        ("resolution",     "TEXT NOT NULL DEFAULT '1024x1024'"),
        ("subtitles",      "INTEGER NOT NULL DEFAULT 1"),
        ("title",          "TEXT NOT NULL DEFAULT ''"),
        ("bgm_type",       "TEXT NOT NULL DEFAULT 'ninguna'"),
        ("quality",        "TEXT NOT NULL DEFAULT 'hd'"),
        ("use_lore",       "INTEGER NOT NULL DEFAULT 1"),
    ]
    for col_name, col_def in migrations:
        if col_name not in existing:
            conn.execute(f"ALTER TABLE video_jobs ADD COLUMN {col_name} {col_def}")
    conn.commit()
    conn.close()


def add_job(
    topic: str,
    n_scenes: int       = DEFAULT_SCENES,
    voice_speed: int    = TTS_RATE,
    voice_id: str       = "",
    style: str          = DEFAULT_STYLE,
    narration_lang: str = "es",
    transitions: bool   = True,
    resolution: str     = "1024x1024",
    subtitles: bool     = True,
    title: str          = "",
    bgm_type: str       = "ninguna",
    quality: str        = "hd",
    use_lore: bool      = True,
) -> int:
    """Encola un nuevo trabajo de video. Retorna el ID generado."""
    _init_db()
    if style not in CINEMA_STYLES:
        style = DEFAULT_STYLE
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.execute(
        "INSERT INTO video_jobs "
        "(topic, n_scenes, voice_speed, voice_id, style, narration_lang, transitions, resolution, subtitles, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (topic, n_scenes, voice_speed, voice_id, style, narration_lang, 1 if transitions else 0, resolution, 1 if subtitles else 0, now)
    )
    job_id = cur.lastrowid
    conn.commit()
    conn.close()
    log.info(f"[VideoStudio] Job #{job_id} encolado: {topic[:60]} | estilo={style} | voz='{voice_id or 'auto'}'")
    return job_id


def get_queue_status() -> dict:
    """Estado completo de la cola de video para el dashboard."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    pending  = [dict(r) for r in conn.execute(
        "SELECT * FROM video_jobs WHERE status='pending' ORDER BY id"
    ).fetchall()]
    
    raw_history = conn.execute(
        "SELECT * FROM video_jobs WHERE status!='pending' ORDER BY id DESC LIMIT ?",
        (MAX_HISTORY,)
    ).fetchall()
    
    history = []
    for r in raw_history:
        job_dict = dict(r)
        if (job_dict.get('status') == 'done' or job_dict.get('status') == 'completed') and job_dict.get('output_path'):
            if not os.path.isfile(job_dict['output_path']):
                job_dict['status'] = 'deleted'
        history.append(job_dict)
        
    conn.close()

    with _lock:
        current = _current_job

    return {
        "pending_count": len(pending),
        "pending_jobs":  pending,
        "current_job":   current,
        "history":       history,
        "ffmpeg_ok":     os.path.isfile(FFMPEG_EXE),
        "styles":        {k: v["label"] for k, v in CINEMA_STYLES.items()},
    }


def cancel_job(job_id: int) -> bool:
    """Cancela un trabajo pendiente. Retorna False si no existe o no estaba pendiente."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    now  = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    rows = conn.execute(
        "UPDATE video_jobs SET status='cancelled', finished_at=? "
        "WHERE id=? AND status='pending'",
        (now, job_id)
    ).rowcount
    conn.commit()
    conn.close()
    return rows > 0


# â”€â”€ Voces SAPI disponibles â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_available_voices() -> list[dict]:
    """
    Lista todas las voces SAPI instaladas en el sistema.
    Retorna lista de dicts con id, name, lang, gender (inferido).
    """
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        result = []
        for v in voices:
            vid  = v.id or ""
            name = v.name or vid
            # Inferir idioma
            lang = "es" if any(t in vid.lower() for t in ("es-", "es_", "spanish", "espaÃ±ol")) else \
                   "en" if any(t in vid.lower() for t in ("en-", "en_", "english")) else \
                   "pt" if any(t in vid.lower() for t in ("pt-", "pt_", "portug")) else "other"
            gender = "female" if any(t in name.lower() for t in (
                "helena", "sabina", "laura", "zira", "hazel", "susan", "linda",
                "maria", "sofia", "female", "mujer"
            )) else "male"
            result.append({"id": vid, "name": name, "lang": lang, "gender": gender})
        engine.stop()
        return result
    except Exception as e:
        log.warning(f"[VideoStudio] No se pudo listar voces SAPI: {e}")
        return []


# â”€â”€ Paso 1: ExtracciÃ³n de Visual Anchor â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _extract_visual_anchor(topic: str) -> str:
    """
    Usa el LLM para extraer un descriptor visual conciso y consistente del tema.
    Si el LLM no estÃ¡ disponible, genera un anchor bÃ¡sico desde el topic.
    El anchor se inyecta como prefijo en TODOS los image_prompts del job.
    """
    system_prompt = (
        "You are a visual descriptor assistant for AI image generation. "
        "Respond ONLY with a single compact English phrase. No bullet points, no JSON."
    )
    user_prompt = (
        f"Given the story/documentary topic: '{topic}'\n"
        "Extract a VISUAL CHARACTER/SUBJECT ANCHOR â€” a compact description of the main "
        "subject's permanent visual attributes (species, breed, color, name label if relevant, "
        "distinctive features). This anchor will be prepended to every scene prompt to maintain "
        "visual consistency across all generated images.\n"
        "Example for 'a siamese kitten named Jamon':\n"
        "  â†’ 'siamese kitten with cream and dark brown fur, blue eyes, named Jamon, small and fluffy'\n"
        "Example for 'the history of Ancient Rome':\n"
        "  â†’ 'ancient Roman setting, marble columns, toga-wearing citizens, Latin inscriptions'\n"
        "Respond ONLY with the anchor phrase, nothing else."
    )
    try:
        from core import provider_manager
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]
        best_result, best_model = provider_manager.get_best()
        if not best_result:
            raise RuntimeError("No LLM disponible")
        anchor = provider_manager.complete(
            messages,
            model=best_model,
            provider=best_result.name,
            options={"temperature": 0.3, "max_tokens": 80},
        )
        anchor = anchor.strip().strip('"').strip("'")
        # Limpiar posibles prefijos explicativos del LLM
        for prefix in ("anchor:", "â†’", "-", "*"):
            if anchor.lower().startswith(prefix):
                anchor = anchor[len(prefix):].strip()
        if len(anchor) > 10:
            log.info(f"[VideoStudio] Visual Anchor extraÃ­do: '{anchor[:80]}'")
            return anchor
    except Exception as e:
        log.warning(f"[VideoStudio] LLM anchor fallback ({e}). Usando topic como anchor.")

    # Fallback: usar el topic directamente como anchor
    return topic[:120]


# â”€â”€ Paso 2: GeneraciÃ³n de guiÃ³n via LLM â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _generate_script(topic: str, n_scenes: int, style: str, narration_lang: str, use_lore: bool = True) -> tuple[list[dict], str]:
    """
    Genera guiÃ³n estructurado AND extrae el visual anchor.
    Retorna (scenes, visual_anchor).
    """
    style_info     = CINEMA_STYLES.get(style, CINEMA_STYLES[DEFAULT_STYLE])
    style_prefix   = style_info["prefix"]

    # ConfiguraciÃ³n de idioma de narraciÃ³n
    lang_names = {
        "es": "espaÃ±ol",
        "en": "English",
        "pt": "portuguÃªs",
        "fr": "franÃ§ais",
        "de": "Deutsch",
        "it": "italiano",
    }
    lang_label = lang_names.get(narration_lang, "espaÃ±ol")

    system_prompt = (
        "Eres un guionista profesional de cine y documentales. "
        "Responde ÃšNICAMENTE con JSON vÃ¡lido, sin texto adicional."
    )
    user_prompt = (
        f"Crea un guiÃ³n de {n_scenes} escenas para un video sobre: '{topic}'.\n"
        f"Estilo visual: {style_info['label']} â€” {style_prefix}\n"
        f"Idioma de narraciÃ³n: {lang_label}\n\n"
        "REGLA CRÃTICA DE CONSISTENCIA VISUAL: El campo 'image_prompt' de CADA escena "
        "DEBE comenzar describiendo al personaje/sujeto principal con los MISMOS atributos visuales "
        "(raza, color, rasgos fÃ­sicos, nombre) en todas las escenas. Nunca omitas estos atributos.\n\n"
        "Responde con este JSON exacto (sin ningÃºn texto antes o despuÃ©s):\n"
        "[\n"
        "  {\n"
        '    "title": "TÃ­tulo corto de la escena",\n'
        '    "character_anchor": "DescripciÃ³n compacta en inglÃ©s del sujeto principal con atributos fÃ­sicos fijos",\n'
        '    "image_prompt": "DescripciÃ³n visual detallada en inglÃ©s. DEBE incluir el character_anchor al inicio.",\n'
        f'    "narration": "Texto de narraciÃ³n en {lang_label} para esta escena (2-4 oraciones)."\n'
        "  }\n"
        "]\n"
        f"Genera exactamente {n_scenes} escenas. Solo JSON, nada mÃ¡s."
    )

    try:
        from core import provider_manager
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]
        best_result, best_model = provider_manager.get_best()
        if not best_result:
            raise RuntimeError("No hay proveedor LLM activo")

        log.info(f"[VideoStudio] Usando '{best_result.name}/{best_model}' para guiÃ³n")
        content = provider_manager.complete(
            messages,
            model=best_model,
            provider=best_result.name,
            options={"temperature": 0.7},
        )

        # Limpiar bloques markdown
        content = content.strip()
        if content.startswith("```"):
            parts = content.split("```")
            content = parts[1] if len(parts) > 1 else parts[0]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        # Extraer primer bloque JSON
        start = content.find("[")
        end   = content.rfind("]") + 1
        if start != -1 and end > start:
            content = content[start:end]

        scenes = json.loads(content)
        if isinstance(scenes, list) and len(scenes) > 0:
            log.info(f"[VideoStudio] GuiÃ³n generado: {len(scenes)} escenas")
            # Extraer anchor del primer character_anchor disponible
            anchor = ""
            for sc in scenes:
                ca = sc.get("character_anchor", "").strip()
                if ca and len(ca) > 5:
                    anchor = ca
                    break
            if not anchor:
                anchor = _extract_visual_anchor(topic)
            return scenes[:n_scenes], anchor

        raise ValueError("LLM no devolviÃ³ lista JSON vÃ¡lida")

    except Exception as e:
        log.warning(f"[VideoStudio] LLM no disponible ({e}). Fallback.")

    # Extraer anchor de forma independiente
    anchor = _extract_visual_anchor(topic)

    # GuiÃ³n de fallback
    scenes = [
        {
            "title":            f"Escena {i+1}: {topic}",
            "character_anchor": anchor,
            "image_prompt": (
                f"{anchor}, cinematic scene {i+1}, "
                f"{style_prefix}, high detail, professional composition"
            ),
            "narration": (
                f"Esta es la escena nÃºmero {i+1} de nuestro video sobre {topic}. "
                "La exploraciÃ³n de este tema nos lleva a descubrir aspectos fascinantes "
                "sobre el mundo que nos rodea."
            ),
        }
        for i in range(n_scenes)
    ]
    return scenes, anchor


# â”€â”€ Paso 3: GeneraciÃ³n de imagen con consistencia â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
    - Usa seed derivada del job_id para coherencia de estilo entre escenas.
    - Aplica el estilo cinematogrÃ¡fico como prefijo.
    Motor primario: Pollinations.ai
    Motor fallback: Fooocus
    """
    job_dir    = os.path.join(OUTPUT_DIR, f"job_{job_id}")
    out_path   = os.path.join(job_dir, f"scene_{scene_idx:02d}_image.png")
    os.makedirs(job_dir, exist_ok=True)

    style_info   = CINEMA_STYLES.get(style, CINEMA_STYLES[DEFAULT_STYLE])
    negative     = style_info.get("negative", "")
    # Seed por escena: base del job + offset de escena â†’ consistencia relativa
    scene_seed   = (job_seed + scene_idx * 7) % 2147483647

    # â”€â”€ Motor 1: Pollinations.ai â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Extraer resolucion
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
            enhance         = False,   # desactivado para mayor fidelidad al prompt exacto
            negative_prompt = negative,
        )
        if result.get("success") and os.path.isfile(out_path):
            log.info(f"[VideoStudio] [Pollinations] Escena {scene_idx}: {os.path.basename(out_path)} (seed={scene_seed})")
            return out_path
        else:
            log.warning(f"[VideoStudio] [Pollinations] FallÃ³ escena {scene_idx}: {result.get('error')}")
    except Exception as e:
        log.warning(f"[VideoStudio] [Pollinations] Exception escena {scene_idx}: {e}")

    # â”€â”€ Motor 2: Fooocus (fallback) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
            log.info("[VideoStudio] Fooocus offline â€” saltando fallback.")
    except Exception as e:
        log.warning(f"[VideoStudio] [Fooocus] Exception escena {scene_idx}: {e}")

    return None


# â”€â”€ Paso 4: Text-to-Speech â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _generate_audio(
    text: str,
    output_wav: str,
    rate: int    = TTS_RATE,
    voice_id: str = "",
) -> bool:
    """
    Convierte texto a audio WAV usando Windows SAPI (pyttsx3).
    Si voice_id estÃ¡ definido, intenta seleccionarla por ID exacto o por nombre parcial.
    Fallback: prioriza voces en espaÃ±ol, luego cualquier voz disponible.
    """
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)
        voices = engine.getProperty("voices")

        selected = None

        # Prioridad 1: voice_id exacto o substring del ID/nombre
        if voice_id:
            vid_lower  = voice_id.lower()
            selected   = next(
                (v for v in voices if
                 vid_lower in (v.id or "").lower() or
                 vid_lower in (v.name or "").lower()),
                None
            )
            if selected:
                log.info(f"[VideoStudio] TTS voz seleccionada por ID: {selected.name}")

        # Prioridad 2: voz espaÃ±ola automÃ¡tica
        if not selected:
            selected = next(
                (v for v in voices if
                 any(t in (v.id or "").lower() for t in ("es-", "es_", "spanish", "espaÃ±ol")) or
                 any(t in (v.name or "").lower() for t in ("spanish", "espaÃ±ol", "helena", "sabina", "pablo", "laura", "jorge"))
                ),
                None
            )
            if selected:
                log.info(f"[VideoStudio] TTS voz espaÃ±ola auto: {selected.name}")

        # Prioridad 3: primera voz disponible
        if not selected and voices:
            selected = voices[0]
            log.warning(f"[VideoStudio] TTS usando primera voz disponible: {selected.name}")

        if not selected:
            log.error("[VideoStudio] No hay voces SAPI disponibles.")
        else:
            engine.setProperty("voice", selected.id)

        engine.save_to_file(text, output_wav)
        engine.runAndWait()
        engine.stop()

        ok = os.path.isfile(output_wav) and os.path.getsize(output_wav) > 0
        if ok:
            size_kb = os.path.getsize(output_wav) // 1024
            log.info(f"[VideoStudio] Audio: {os.path.basename(output_wav)} ({size_kb} KB)")
        return ok
    except Exception as e:
        log.error(f"[VideoStudio] Error TTS: {e}")
        return False


# â”€â”€ Paso 5: Ensamblado por escena con fade â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _assemble_clip(
    image_path: str,
    audio_path: str,
    output_mp4: str,
    fade: bool = True,
    resolution: str = "1024x1024",
    text: str = "",
    subtitles: bool = True,
) -> bool:
    """
    Combina imagen + audio en clip mp4.
    AÃ±ade fade-in / fade-out si fade=True y audio tiene duraciÃ³n detectable.
    """
    if not os.path.isfile(FFMPEG_EXE):
        log.error(f"[VideoStudio] ffmpeg no encontrado en {FFMPEG_EXE}")
        return False

    try:
        has_audio = audio_path and os.path.isfile(audio_path) and os.path.getsize(audio_path) > 0

        # Detectar duraciÃ³n del audio para calcular fade-out offset
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

        clip_dur   = audio_dur + 0.5 if has_audio else float(SECONDS_PER_SCENE)
        fade_d     = min(FADE_DURATION, clip_dur / 3) if fade else 0.0
        fade_out_t = max(0, clip_dur - fade_d)

        # Extraer resolucion
        w_val, h_val = DEFAULT_IMG_W, DEFAULT_IMG_H
        if "x" in resolution:
            parts = resolution.split("x")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                w_val, h_val = int(parts[0]), int(parts[1])

        # Filtro de video con fade
        vf_parts = [
            f"scale={w_val}:{h_val}:force_original_aspect_ratio=decrease",
            f"pad={w_val}:{h_val}:(ow-iw)/2:(oh-ih)/2:black",
            "fps=24",
        ]
        
        if subtitles and text:
            def fmt_time(s):
                ms = int((s % 1) * 1000)
                m, s_int = divmod(int(s), 60)
                _h, _m = divmod(m, 60)
                return f"{_h:02d}:{_m:02d}:{s_int:02d},{ms:03d}"
            
            job_dir = os.path.dirname(image_path)
            scene_name = os.path.splitext(os.path.basename(image_path))[0]
            srt_path = os.path.join(job_dir, f"{scene_name}.srt")
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(f"1\n00:00:00,000 --> {fmt_time(clip_dur)}\n{text}\n")
            
            safe_srt = srt_path.replace('\\', '/').replace(':', '\\:')
            vf_parts.append(f"subtitles='{safe_srt}':force_style='FontSize=20,PrimaryColour=&H00FFFFFF,BorderStyle=3,Outline=2,Shadow=1,Alignment=2,MarginV=20'")
            
        if fade and fade_d > 0:
            vf_parts.append(f"fade=t=in:st=0:d={fade_d}")
            vf_parts.append(f"fade=t=out:st={fade_out_t:.3f}:d={fade_d}")
        vf = ",".join(vf_parts)

        if has_audio:
            cmd = [
                FFMPEG_EXE, "-y",
                "-loop", "1", "-i", image_path,
                "-i",  audio_path,
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac", "-b:a", "128k",
                "-shortest",
                "-vf", vf,
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_mp4,
            ]
        else:
            cmd = [
                FFMPEG_EXE, "-y",
                "-loop", "1", "-i", image_path,
                "-t", str(SECONDS_PER_SCENE),
                "-c:v", "libx264", "-preset", "fast",
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


# â”€â”€ Paso 6: ConcatenaciÃ³n final â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _concatenate_clips(clip_paths: list[str], output_mp4: str, bgm_type: str = "ninguna") -> bool:
    """Concatena todos los clips en el video final."""
    if not clip_paths:
        return False

    if len(clip_paths) == 1:
        import shutil
        shutil.copy2(clip_paths[0], output_mp4)
        return True

    try:
        list_file = output_mp4 + ".list.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            for cp in clip_paths:
                safe = cp.replace("'", "'\\''")
                f.write(f"file '{safe}'\n")

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bgm_path = os.path.join(base_dir, "inputs", "bgm.mp3")
        
        if bgm_type != "ninguna":
            try:
                import urllib.request
                urls = {
                    "epico": "https://archive.org/download/EpicMusic_201708/EpicMusic.mp3",
                    "documental": "https://archive.org/download/chill-out-music/chill-out.mp3",
                    "synthwave": "https://archive.org/download/synthwave_202111/synthwave.mp3",
                    "jazz": "https://archive.org/download/jazzy-lounge/jazzy-lounge.mp3"
                }
                url = urls.get(bgm_type.lower(), urls["documental"])
                os.makedirs(os.path.dirname(bgm_path), exist_ok=True)
                urllib.request.urlretrieve(url, bgm_path)
            except Exception as e:
                log.warning(f"[VideoStudio] Error descargando BGM: {e}")
        has_bgm = bgm_type != "ninguna" and os.path.isfile(bgm_path)
        
        if has_bgm:
            cmd = [
                FFMPEG_EXE, "-y",
                "-f", "concat", "-safe", "0",
                "-i", list_file,
                "-stream_loop", "-1", "-i", bgm_path,
                "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2:weights=1 0.1[a]",
                "-map", "0:v", "-map", "[a]",
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac",
                "-movflags", "+faststart",
                output_mp4,
            ]
            log.info(f"[VideoStudio] Concatenando {len(clip_paths)} clips con MIX MUSICAL -> {os.path.basename(output_mp4)}")
        else:
            cmd = [
                FFMPEG_EXE, "-y",
                "-f", "concat", "-safe", "0",
                "-i", list_file,
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac",
                "-movflags", "+faststart",
                output_mp4,
            ]
            log.info(f"[VideoStudio] Concatenando {len(clip_paths)} clips simples -> {os.path.basename(output_mp4)}")
        
        result = subprocess.run(
            cmd, capture_output=True, timeout=300,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        try:
            os.remove(list_file)
        except Exception:
            pass

        if result.returncode == 0 and os.path.isfile(output_mp4):
            size_mb = os.path.getsize(output_mp4) / 1024 / 1024
            log.info(f"[VideoStudio] Video final: {os.path.basename(output_mp4)} ({size_mb:.1f} MB)")
            return True
        else:
            err = result.stderr.decode(errors="replace")[-400:]
            log.error(f"[VideoStudio] ConcatenaciÃ³n fallida: {err}")
            return False
    except Exception as e:
        log.error(f"[VideoStudio] Error concatenando: {e}")
        return False


# â”€â”€ Actualizador de estado en DB â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _update_job(job_id: int, **kwargs) -> None:
    valid  = {"status", "progress", "current_step", "output_path",
              "error", "started_at", "finished_at"}
    fields = {k: v for k, v in kwargs.items() if k in valid}
    if not fields:
        return
    sql    = "UPDATE video_jobs SET " + ", ".join(f"{k}=?" for k in fields)
    sql   += " WHERE id=?"
    values = list(fields.values()) + [job_id]
    conn   = sqlite3.connect(DB_PATH)
    conn.execute(sql, values)
    conn.commit()
    conn.close()


# â”€â”€ Worker principal â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _process_job(
    job_id: int,
    topic: str,
    n_scenes: int,
    voice_speed: int,
    voice_id: str,
    style: str,
    narration_lang: str,
    transitions: bool,
    resolution: str,
    subtitles: bool,
    title: str = "",
    bgm_type: str = "ninguna",
    quality: str = "hd",
    use_lore: bool = True,
) -> None:
    """
    Pipeline completo con Character Consistency Engine.
    """
    global _current_job

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    _update_job(job_id, status="running", started_at=now, progress=0,
                current_step="Generando guiÃ³n con el LLM...")
    with _lock:
        _current_job = {"id": job_id, "topic": topic, "progress": 0,
                        "step": "Generando guiÃ³n..."}

    job_dir = os.path.join(OUTPUT_DIR, f"job_{job_id}")
    os.makedirs(job_dir, exist_ok=True)

    # Seed base del job: determinista por job_id + topic â†’ coherencia visual
    job_seed = int(hashlib.md5(f"{job_id}:{topic}".encode()).hexdigest()[:8], 16) % 2147483647

    try:
        # â”€â”€ PASO 1: GuiÃ³n + Visual Anchor â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        scenes, visual_anchor = _generate_script(topic, n_scenes, style, narration_lang, use_lore)
        if not scenes:
            raise RuntimeError("El LLM no devolviÃ³ escenas vÃ¡lidas.")

        style_info   = CINEMA_STYLES.get(style, CINEMA_STYLES[DEFAULT_STYLE])
        style_prefix = style_info["prefix"]
        log.info(f"[VideoStudio] Visual Anchor del job #{job_id}: '{visual_anchor[:80]}'")

        total_steps = n_scenes * 3 + 1
        step        = 0
        clip_paths: list[str] = []

        for i, scene in enumerate(scenes):
            scene_num   = i + 1
            scene_title = scene.get("title", f"Escena {scene_num}")
            narration   = scene.get("narration", "")

            # â”€â”€ Construir prompt con anchor garantizado â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            raw_prompt      = scene.get("image_prompt", topic)
            anchored_prompt = (
                f"{visual_anchor}, {raw_prompt}, {style_prefix}"
                if visual_anchor.lower() not in raw_prompt.lower()
                else f"{raw_prompt}, {style_prefix}"
            )
            # Truncar a 450 chars para evitar encode overflows en Pollinations
            anchored_prompt = anchored_prompt[:450]

            # â”€â”€ PASO 2: Imagen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            step += 1
            pct = int(step / total_steps * 100)
            _update_job(job_id, progress=pct,
                        current_step=f"[{scene_num}/{n_scenes}] Generando imagen: {scene_title[:40]}")
            with _lock:
                if _current_job:
                    _current_job["progress"] = pct
                    _current_job["step"]     = f"Escena {scene_num}/{n_scenes}: imagen..."

            img_path = _generate_scene_image(anchored_prompt, scene_num, job_id, job_seed, style, resolution)

            if not img_path:
                placeholder = os.path.join(job_dir, f"scene_{scene_num:02d}_placeholder.png")
                _create_placeholder_image(scene_title, placeholder)
                img_path = placeholder

            # â”€â”€ PASO 3: TTS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            step += 1
            pct = int(step / total_steps * 100)
            _update_job(job_id, progress=pct,
                        current_step=f"[{scene_num}/{n_scenes}] Generando audio: {scene_title[:40]}")
            with _lock:
                if _current_job:
                    _current_job["progress"] = pct
                    _current_job["step"]     = f"Escena {scene_num}/{n_scenes}: audio..."

            audio_path = os.path.join(job_dir, f"scene_{scene_num:02d}_audio.wav")
            audio_ok   = _generate_audio(narration, audio_path, voice_speed, voice_id) if narration else False

            # â”€â”€ PASO 4: Clip â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            step += 1
            pct = int(step / total_steps * 100)
            _update_job(job_id, progress=pct,
                        current_step=f"[{scene_num}/{n_scenes}] Ensamblando clip...")
            with _lock:
                if _current_job:
                    _current_job["progress"] = pct
                    _current_job["step"]     = f"Escena {scene_num}/{n_scenes}: clip..."

            clip_path = os.path.join(job_dir, f"scene_{scene_num:02d}_clip.mp4")
            if _assemble_clip(img_path, audio_path if audio_ok else None, clip_path, fade=transitions, resolution=resolution, text=narration, subtitles=subtitles):
                clip_paths.append(clip_path)

        # â”€â”€ PASO 5: Video final â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        _update_job(job_id, progress=95, current_step="Concatenando clips en video final...")
        with _lock:
            if _current_job:
                _current_job["progress"] = 95
                _current_job["step"]     = "Concatenando video final..."

        ts         = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c for c in topic[:30] if c.isalnum() or c in " _-").strip().replace(" ", "_")
        final_path = os.path.join(OUTPUT_DIR, f"video_{job_id}_{safe_topic}_{ts}.mp4")

        if clip_paths and _concatenate_clips(clip_paths, final_path, bgm_type):
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            _update_job(job_id, status="done", progress=100,
                        current_step="Completado", output_path=final_path,
                        finished_at=now)
            log.info(f"[VideoStudio] Job #{job_id} completado -> {final_path}")
            
            if use_lore:
                try:
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    inputs_dir = os.path.join(base_dir, "inputs")
                    os.makedirs(inputs_dir, exist_ok=True)
                    lore_path = os.path.join(inputs_dir, "cinematic_lore.txt")
                    with open(lore_path, "a", encoding="utf-8") as f:
                        f.write(f"\n\n=== HISTORIA: {title or topic} ===\n")
                        for s in scenes:
                            f.write(f"Escena: {s.get('title', '')}\n")
                            f.write(f"Narración: {s.get('narration', '')}\n")
                except Exception as e:
                    log.warning(f"[VideoStudio] Error guardando lore: {e}")
        else:
            raise RuntimeError("No se pudieron generar clips.")

    except Exception as e:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        _update_job(job_id, status="failed", error=str(e), finished_at=now,
                    current_step="Error")
        log.error(f"[VideoStudio] Job #{job_id} fallÃ³: {e}")
    finally:
        with _lock:
            _current_job = None


# â”€â”€ Imagen de marcador â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


# â”€â”€ Worker daemon â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _worker_loop() -> None:
    """Loop daemon: toma el siguiente job pendiente y lo procesa."""
    _init_db()
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            row  = conn.execute(
                "SELECT * FROM video_jobs WHERE status='pending' ORDER BY id LIMIT 1"
            ).fetchone()
            conn.close()

            if row:
                _process_job(
                    job_id        = row["id"],
                    topic         = row["topic"],
                    n_scenes      = row["n_scenes"],
                    voice_speed   = row["voice_speed"],
                    voice_id      = row["voice_id"]       if "voice_id"       in row.keys() else "",
                    style         = row["style"]          if "style"          in row.keys() else DEFAULT_STYLE,
                    narration_lang= row["narration_lang"] if "narration_lang" in row.keys() else "es",
                    transitions   = bool(row["transitions"] if "transitions" in row.keys() else 1),
                    resolution    = row["resolution"]     if "resolution"     in row.keys() else "1024x1024",
                    subtitles     = bool(row["subtitles"] if "subtitles"      in row.keys() else 1),
                )
            else:
                time.sleep(5)

        except Exception as e:
            log.error(f"[VideoStudio] Error en worker loop: {e}")
            time.sleep(10)


def start() -> None:
    """Inicia el worker daemon de video si no estaba ya corriendo."""
    global _started
    if _started:
        return
    _started = True
    _init_db()
    t = threading.Thread(target=_worker_loop, name="GravityVideoWorker", daemon=True)
    t.start()
    log.info("[VideoStudio] Worker daemon iniciado (Cinematic Edition).")


# â”€â”€ API pÃºblica â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_video_url(output_path: str) -> str:
    """Convierte ruta absoluta en URL relativa para descarga."""
    if not output_path:
        return ""
    fname = os.path.basename(output_path)
    return f"/v1/video/download?file={fname}"

