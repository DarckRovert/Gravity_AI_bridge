"""
╔══════════════════════════════════════════════════════════════════════════════╗
║    GRAVITY AI — CONTENT SCHEDULER V1.0                                       ║
║    Producción autónoma de videos sin intervención manual                     ║
║                                                                              ║
║  Ciclo:                                                                      ║
║    1. A la hora configurada (time_utc en config.yaml), despierta             ║
║    2. Lee inputs/niches.json y selecciona el tema menos usado                ║
║    3. Encola el job en video_pipeline                                        ║
║    4. Actualiza el registro de uso del tema                                  ║
║    5. Vuelve a dormir hasta el próximo ciclo                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import random
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

from core.logger import log

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NICHES_PATH  = os.path.join(BASE_DIR, "inputs", "niches.json")
CONFIG_PATH  = os.path.join(BASE_DIR, "config.yaml")

_started = False
_lock    = threading.Lock()
_niches_lock = threading.RLock()

# Estado observable desde el dashboard
_state: dict = {
    "enabled":        False,
    "next_run_utc":   None,
    "last_run_utc":   None,
    "jobs_queued":    0,
    "last_topic":     None,
    "last_niche":     None,
}


# ── Config ─────────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    """Carga de forma segura la sección del scheduler del gestor de configuración."""
    try:
        from core.config_manager import config as config_manager
        return config_manager.get("scheduler", {})
    except Exception as e:
        log.error(f"[Scheduler] Error obteniendo config del gestor: {e}")
        return {}


def _load_niches() -> dict:
    """
    Carga el banco de nichos desde inputs/niches.json de forma 100% thread-safe
    utilizando cerrojos reentrantes y retroceso exponencial dinámico.
    """
    with _niches_lock:
        if not os.path.isfile(NICHES_PATH):
            log.warning(f"[Scheduler] niches.json no encontrado en {NICHES_PATH}. Creando banco inicial.")
            _create_default_niches()
        
        backoff = 0.05
        for attempt in range(5):
            try:
                with open(NICHES_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (PermissionError, json.JSONDecodeError) as e:
                if attempt == 4:
                    log.error(f"[Scheduler] Error crítico leyendo niches.json tras 5 intentos: {e}")
                    raise
                log.warning(f"[Scheduler] Colisión en lectura de niches.json, reintentando en {backoff}s... (Intento {attempt+1}/5)")
                time.sleep(backoff)
                backoff *= 2
            except Exception as e:
                log.error(f"[Scheduler] Error inesperado leyendo niches.json: {e}")
                return {"niches": []}
        return {"niches": []}


def _save_niches(data: dict) -> None:
    """
    Persiste el banco de nichos actualizado de manera atómica, previniendo
    corrupciones mediante archivos temporales y bloqueos exclusivos.
    """
    with _niches_lock:
        os.makedirs(os.path.dirname(NICHES_PATH), exist_ok=True)
        backoff = 0.05
        for attempt in range(5):
            try:
                temp_path = NICHES_PATH + ".tmp"
                with open(temp_path, "w", encoding="utf-8", newline="\n") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # Reemplazo atómico — os.replace es seguro en Windows y Linux
                os.replace(temp_path, NICHES_PATH)
                return
            except PermissionError as e:
                if attempt == 4:
                    log.error(f"[Scheduler] No se pudo guardar niches.json tras 5 intentos (PermissionError): {e}")
                    raise
                log.warning(f"[Scheduler] Bloqueo de escritura en niches.json, reintentando en {backoff}s... (Intento {attempt+1}/5)")
                time.sleep(backoff)
                backoff *= 2
            except Exception as e:
                log.error(f"[Scheduler] Error guardando niches.json: {e}")
                break


def _create_default_niches() -> None:
    """Crea el banco de nichos inicial si no existe."""
    os.makedirs(os.path.dirname(NICHES_PATH), exist_ok=True)
    default = {
        "niches": [
            {
                "id": "historia_mundial",
                "topics": [
                    "La caída del Imperio Romano",
                    "La vida de Gengis Kan",
                    "El enigma de las Pirámides de Egipto",
                    "La Revolución Francesa explicada",
                    "El verdadero origen de la Segunda Guerra Mundial",
                    "Alejandro Magno: el conquistador del mundo",
                    "La Inquisición española: mitos y realidades",
                    "El Imperio Azteca antes de la conquista"
                ],
                "style": "historico",
                "lang": "es",
                "bgm_type": "epico",
                "n_scenes": 65,
                "estimated_cpm_usd": 3.5,
                "times_used": 0,
                "last_used": None
            },
            {
                "id": "tecnologia_ia",
                "topics": [
                    "Cómo funciona la inteligencia artificial en 2026",
                    "El futuro de los robots humanoides",
                    "Qué es el AGI y por qué cambiará el mundo",
                    "Cómo ChatGPT genera texto que parece humano",
                    "La carrera espacial entre SpaceX y China",
                    "El chip cuántico de Google explicado fácil",
                    "Cómo la IA está transformando la medicina"
                ],
                "style": "cyberpunk",
                "lang": "es",
                "bgm_type": "synthwave",
                "n_scenes": 62,
                "estimated_cpm_usd": 8.0,
                "times_used": 0,
                "last_used": None
            },
            {
                "id": "finanzas_personales",
                "topics": [
                    "Cómo invertir desde cero con poco dinero",
                    "El error financiero más común que arruina a las personas",
                    "Bitcoin en 2026: invertir o no invertir",
                    "Cómo ahorrar el 30% de tu salario sin sufrimiento",
                    "Los 5 activos que generan ingresos pasivos de verdad",
                    "Por qué los ricos no trabajan por dinero"
                ],
                "style": "publicitario",
                "lang": "es",
                "bgm_type": "corporativo",
                "n_scenes": 64,
                "estimated_cpm_usd": 12.0,
                "times_used": 0,
                "last_used": None
            },
            {
                "id": "misterios_conspiraciones",
                "topics": [
                    "El triángulo de las Bermudas: la verdad científica",
                    "La ciudad perdida de Atlantis: ¿mito o realidad?",
                    "Área 51: lo que el gobierno no quiere que sepas",
                    "Los secretos de la Sociedad Illuminati",
                    "El misterio de las líneas de Nazca en Perú",
                    "Civilizaciones extintas más antiguas que Egipto"
                ],
                "style": "noir",
                "lang": "es",
                "bgm_type": "misterio",
                "n_scenes": 62,
                "estimated_cpm_usd": 4.0,
                "times_used": 0,
                "last_used": None
            },
            {
                "id": "ciencia_naturaleza",
                "topics": [
                    "Los animales más peligrosos del mundo",
                    "Cómo funciona el cerebro humano",
                    "Los 10 lugares más extremos de la Tierra",
                    "La vida en el fondo del océano",
                    "Cómo sobreviven los animales en el Ártico",
                    "Los volcanes más activos del planeta"
                ],
                "style": "naturaleza",
                "lang": "es",
                "bgm_type": "documental",
                "n_scenes": 60,
                "estimated_cpm_usd": 5.0,
                "times_used": 0,
                "last_used": None
            },
            {
                "id": "motivacion_exito",
                "topics": [
                    "Los hábitos de las personas más exitosas del mundo",
                    "Cómo reprogramar tu mente para el éxito",
                    "Por qué la mayoría de las personas nunca triunfan",
                    "El método que usan los millonarios para no perder el tiempo",
                    "Cómo salir de la mediocridad en 90 días"
                ],
                "style": "epico",
                "lang": "es",
                "bgm_type": "heroico",
                "n_scenes": 60,
                "estimated_cpm_usd": 7.0,
                "times_used": 0,
                "last_used": None
            }
        ]
    }
    with open(NICHES_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(default, f, ensure_ascii=False, indent=2)
    log.info(f"[Scheduler] Banco de nichos inicial creado en {NICHES_PATH}")


# ── Selección de tema ───────────────────────────────────────────────────────────

def _select_next_topic(data: dict) -> Optional[tuple[str, str, dict]]:
    """
    Selecciona el próximo tema a producir.
    Estrategia: menor times_used → mayor estimated_cpm_usd (desempate).
    Dentro del niche elegido, selecciona el topic con menor aparición en el lore.
    Retorna (topic_text, niche_id, niche_config) o None si no hay nichos.
    """
    niches = data.get("niches", [])
    if not niches:
        return None

    # Filtrar nichos con topics disponibles
    valid = [n for n in niches if n.get("topics")]
    if not valid:
        return None

    # Ordenar: menos usado primero, mayor CPM como desempate
    valid.sort(key=lambda n: (n.get("times_used", 0), -n.get("estimated_cpm_usd", 0)))
    niche = valid[0]

    topics = niche.get("topics", [])
    # Evitar repetir el último topic del mismo niche
    last_topic = niche.get("last_topic_used", "")
    available  = [t for t in topics if t != last_topic]
    if not available:
        available = topics  # Si solo hay uno, permitir repetición

    topic = random.choice(available)
    return topic, niche["id"], niche


def _mark_topic_used(data: dict, niche_id: str, topic: str) -> None:
    """Incrementa el contador de uso y registra el timestamp."""
    for niche in data.get("niches", []):
        if niche["id"] == niche_id:
            niche["times_used"]      = niche.get("times_used", 0) + 1
            niche["last_used"]       = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            niche["last_topic_used"] = topic
            break


# ── Cálculo de próxima ejecución ────────────────────────────────────────────────

def _next_run_utc(time_utc_str: str) -> datetime:
    """
    Calcula el próximo datetime UTC de ejecución a partir de un string "HH:MM".
    Si la hora ya pasó hoy, devuelve mañana.
    """
    now = datetime.now(timezone.utc)
    try:
        h, m = [int(x) for x in time_utc_str.split(":")]
    except Exception:
        h, m = 3, 0  # Fallback: 03:00 UTC

    target = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


# ── Loop principal ──────────────────────────────────────────────────────────────

def _scheduler_loop() -> None:
    """Loop daemon del scheduler. Duerme hasta la hora configurada y encola jobs."""
    log.info("[Scheduler] Daemon de producción autónoma iniciado.")

    while True:
        try:
            cfg = _load_config()

            if not cfg.get("enabled", False):
                with _lock:
                    _state["enabled"] = False
                time.sleep(60)  # Revisar config cada minuto
                continue

            with _lock:
                _state["enabled"] = True

            time_utc_str = cfg.get("time_utc", "03:00")
            videos_per_day = int(cfg.get("videos_per_day", 2))

            # Calcular cuándo es la próxima ejecución
            next_run = _next_run_utc(time_utc_str)
            with _lock:
                _state["next_run_utc"] = next_run.isoformat().replace("+00:00", "Z")

            now = datetime.now(timezone.utc)
            wait_secs = (next_run - now).total_seconds()
            if wait_secs > 0:
                log.info(f"[Scheduler] Próxima ejecución en {wait_secs/3600:.1f}h ({next_run.strftime('%Y-%m-%d %H:%M UTC')})")
                time.sleep(wait_secs)

            # ── Ejecución: encolar N videos ────────────────────────────────────
            log.info(f"[Scheduler] Despertando. Encolando {videos_per_day} video(s)...")
            data = _load_niches()
            queued = 0

            for _ in range(videos_per_day):
                selection = _select_next_topic(data)
                if not selection:
                    log.warning("[Scheduler] No hay temas disponibles en niches.json.")
                    break

                topic, niche_id, niche = selection

                # Importar aquí para evitar circular import en el startup
                from core import video_pipeline

                job_id = video_pipeline.add_job(
                    topic          = topic,
                    n_scenes       = max(6, min(int(niche.get("n_scenes", 8)), 80)),
                    style          = niche.get("style", "documental"),
                    narration_lang = niche.get("lang", "es"),
                    bgm_type       = niche.get("bgm_type", "ninguna"),
                    bgm_volume     = 0.12,
                    ken_burns      = True,
                    intro_card     = True,
                    use_lore       = True,
                    quality        = "hd",
                    niche_id       = niche_id,
                    color_grade    = "auto",
                    animation_effect = "auto",
                    animation_level  = 1,
                )

                _mark_topic_used(data, niche_id, topic)
                queued += 1

                with _lock:
                    _state["jobs_queued"] += 1
                    _state["last_topic"]   = topic
                    _state["last_niche"]   = niche_id

                log.info(f"[Scheduler] Job #{job_id} encolado: '{topic}' (niche: {niche_id})")

                # Pequeña pausa entre encolas para no saturar
                if _ < videos_per_day - 1:
                    time.sleep(2)

            _save_niches(data)

            with _lock:
                _state["last_run_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

            log.info(f"[Scheduler] Ciclo completado. {queued} video(s) encolados.")

            # Dormir 60s para no re-ejecutar el mismo ciclo inmediatamente
            time.sleep(60)

        except Exception as e:
            log.error(f"[Scheduler] Error en loop: {e}")
            time.sleep(120)


# ── API Pública ─────────────────────────────────────────────────────────────────

def start() -> None:
    """Inicia el daemon scheduler si no estaba corriendo."""
    global _started
    if _started:
        return
    _started = True
    t = threading.Thread(target=_scheduler_loop, name="GravityContentScheduler", daemon=True)
    t.start()
    log.info("[Scheduler] Content Scheduler daemon iniciado.")


def get_state() -> dict:
    """Retorna el estado actual del scheduler para el dashboard."""
    with _lock:
        state = dict(_state)

    cfg = _load_config()
    state["config"] = {
        "enabled":        cfg.get("enabled", False),
        "time_utc":       cfg.get("time_utc", "03:00"),
        "videos_per_day": cfg.get("videos_per_day", 2),
        "niches_file":    NICHES_PATH,
    }
    return state


def get_niches() -> dict:
    """Retorna el banco de nichos completo."""
    data = _load_niches()
    return {
        "ok":     True,
        "niches": data.get("niches", []),
        "count":  len(data.get("niches", [])),
        "file":   NICHES_PATH,
    }


def add_topic(niche_id: str, topic: str) -> dict:
    """Agrega un nuevo topic a un niche existente."""
    data = _load_niches()
    for niche in data.get("niches", []):
        if niche["id"] == niche_id:
            if topic not in niche.get("topics", []):
                niche.setdefault("topics", []).append(topic)
                _save_niches(data)
                return {"ok": True, "niche_id": niche_id, "topic": topic}
            return {"ok": False, "error": "Topic ya existe en ese niche."}
    return {"ok": False, "error": f"Niche '{niche_id}' no encontrado."}


def queue_now(niche_id: Optional[str] = None, topic: Optional[str] = None) -> dict:
    """
    Encola un video inmediatamente (override manual del scheduler).
    Si no se especifica niche_id ni topic, usa la selección automática.
    """
    from core import video_pipeline

    data = _load_niches()

    if topic and niche_id:
        # Búsqueda del niche para obtener parámetros de estilo
        niche = next((n for n in data.get("niches", []) if n["id"] == niche_id), None)
        if not niche:
            return {"ok": False, "error": f"Niche '{niche_id}' no encontrado."}
    else:
        selection = _select_next_topic(data)
        if not selection:
            return {"ok": False, "error": "No hay temas disponibles en niches.json."}
        topic, niche_id, niche = selection

    job_id = video_pipeline.add_job(
        topic          = topic,
        n_scenes       = max(6, min(int(niche.get("n_scenes", 8)), 80)),
        style          = niche.get("style", "documental"),
        narration_lang = niche.get("lang", "es"),
        bgm_type       = niche.get("bgm_type", "ninguna"),
        bgm_volume     = 0.12,
        ken_burns      = True,
        intro_card     = True,
        use_lore       = True,
        quality        = "hd",
        niche_id       = niche_id,
        color_grade    = "auto",
        animation_effect = "auto",
        animation_level  = 1,
    )

    _mark_topic_used(data, niche_id, topic)
    _save_niches(data)

    with _lock:
        _state["jobs_queued"] += 1
        _state["last_topic"]   = topic
        _state["last_niche"]   = niche_id

    log.info(f"[Scheduler] Job #{job_id} encolado manualmente: '{topic}'")
    return {"ok": True, "job_id": job_id, "topic": topic, "niche_id": niche_id}


def load_niches() -> dict:
    """
    Wrapper público y thread-safe para cargar el banco de nichos.
    Garantiza consistencia frente a lecturas concurrentes del sistema.
    """
    return _load_niches()


def save_niches(data: dict) -> None:
    """
    Wrapper público y thread-safe para guardar el banco de nichos.
    Garantiza atomicidad y resiliencia en escrituras concurrentes.
    """
    _save_niches(data)

