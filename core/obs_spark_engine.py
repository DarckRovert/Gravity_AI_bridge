"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY SPARK ENGINE — Generación de Overlays OBS con IA Local            ║
║  Replica la función de Meld Spark usando modelos locales (LM Studio/Ollama) ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import uuid
import re
import threading
import time
import random
import json
from typing import List, Dict, Any, Optional
from core.logger import log

_OVERLAYS_DIR = None  # Se inicializa desde config en primera llamada
_overlays_lock = threading.RLock()

# ── Sistema de registro de overlays activos ───────────────────────────────────
# {overlay_id: {input_name, scene_name, scene_item_id, created_at, prompt, path}}
_active_overlays: Dict[str, Dict[str, Any]] = {}


def _get_overlays_dir() -> str:
    global _OVERLAYS_DIR
    if _OVERLAYS_DIR is None:
        try:
            from core.config_manager import config

            rel = config.get("obs_spark.overlays_dir", "_integrations/obs_overlays")
        except Exception:
            rel = "_integrations/obs_overlays"
        BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _OVERLAYS_DIR = os.path.join(BASE, rel.replace("/", os.sep))
        os.makedirs(_OVERLAYS_DIR, exist_ok=True)
    return _OVERLAYS_DIR


def _get_state_file_path() -> str:
    return os.path.join(_get_overlays_dir(), "active_overlays.json")


def _save_active_overlays():
    path = _get_state_file_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            with _overlays_lock:
                json.dump(_active_overlays, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log.error(f"[GravitySpark] Error saving active overlays state: {e}")


def _load_active_overlays():
    global _active_overlays
    path = _get_state_file_path()
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    with _overlays_lock:
                        _active_overlays.clear()
                        _active_overlays.update(data)
            log.info(
                f"[GravitySpark] Loaded {len(_active_overlays)} active overlays from state cache."
            )
        except Exception as e:
            log.error(f"[GravitySpark] Error loading active overlays state: {e}")


_SYSTEM_PROMPT = """Eres un experto en overlays de streaming para OBS Studio.
Tu tarea es generar código HTML/CSS/JS completo y autocontenido para overlays de stream.

REGLAS OBLIGATORIAS:
1. El body DEBE tener: background-color: rgba(0,0,0,0); margin: 0; padding: 0; overflow: hidden;
2. Todo el CSS va en una etiqueta <style> dentro del <head>
3. Todo el JS va en una etiqueta <script> al final del <body>
4. CERO imports externos (sin CDN, sin Google Fonts, sin URLs externas)
5. Usa solo fuentes del sistema: Arial, Verdana, monospace, sans-serif
6. El overlay debe funcionar en Chromium embebido de OBS (sin acceso a internet)
7. Usa animaciones CSS para que el overlay se vea vivo y profesional
8. Si el usuario pide datos dinámicos (chat, seguidores), simúlalos con JS setInterval
9. Responde ÚNICAMENTE con el código HTML completo. Sin texto adicional, sin explicaciones, sin markdown.
10. El código debe comenzar con <!DOCTYPE html> y terminar con </html>

EXTRAS opcionales si aplican al prompt:
- Para alertas: usa CSS @keyframes con efectos de entrada dramáticos
- Para overlays de chat: simula mensajes con arrays y rotación
- Para contadores: usa CSS grandes y llamativos
- Para "BRB" / pantallas de espera: animaciones de bucle infinito"""


def _call_local_llm(prompt: str, temperature: float = 0.6) -> str:
    """Llama al provider_manager de Gravity para generar el HTML del overlay con robustez y reintentos."""
    from core import provider_manager
    from core.config_manager import config

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    provider = config.get("obs_spark.provider", "")
    model = config.get("obs_spark.model", "")
    options = {"temperature": temperature}


    for attempt in range(3):
        try:
            raw = provider_manager.complete(
                messages,
                provider=provider if provider else None,
                model=model if model else None,
                options=options,
                task="code",
            )
            if raw and raw.strip() != "":
                return raw
            raise RuntimeError("El LLM retornó respuesta vacía")
        except Exception as e:
            if attempt < 2:
                sleep_time = 1.0 * (2**attempt) + random.uniform(0.1, 0.3)
                log.warning(
                    f"[GravitySpark] Intento {attempt+1} fallido llamando a LLM: {e}. Reintentando en {sleep_time:.2f}s..."
                )
                time.sleep(sleep_time)
                continue
            log.error(f"[GravitySpark] Todos los intentos de LLM fallaron: {e}")
            raise

    raise RuntimeError("Fallo irrecuperable llamando al LLM local.")


def _extract_html(raw: str) -> str:
    """Extrae el bloque HTML de la respuesta del LLM."""
    # 1. Buscar bloque markdown ```html ... ``` que contenga <!DOCTYPE ... </html>
    match = re.search(
        r"```(?:html)?\s*(<!DOCTYPE[\s\S]*?</html>)\s*```", raw, re.IGNORECASE
    )
    if match:
        return match.group(1).strip()

    # 1b. Bloque ```html ... ``` genérico si contiene marcas HTML estructuradas
    match = re.search(
        r"```(?:html)?\s*([\s\S]*?)\s*```", raw, re.IGNORECASE
    )
    if match:
        content = match.group(1).strip()
        lower_content = content.lower()
        if any(tag in lower_content for tag in ("<html", "<body", "<div", "<style", "<script")):
            return content

    # 2. Buscar <!DOCTYPE ... </html> directamente en el texto sin markdown blocks
    match = re.search(r"(<!DOCTYPE[\s\S]*?</html>)", raw, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # 2b. Buscar <html ... </html>
    match = re.search(r"(<html[\s\S]*?</html>)", raw, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # 3. Si ya contiene doctype o html de forma suelta
    if "<!DOCTYPE" in raw.upper() or "<html" in raw.lower():
        return raw.strip()

    raise ValueError(f"El LLM no generó HTML válido. Respuesta: {raw[:200]}...")


def generate_overlay(
    prompt: str,
    scene_name: str = "",
    width: int = 400,
    height: int = 300,
    x: int = 0,
    y: int = 0,
    bridge_port: int = 7860,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    Genera un overlay HTML con IA local y lo inyecta en OBS como Browser Source de forma totalmente thread-safe.
    """
    with _overlays_lock:
        from core.obs_client import get_client

        obs = get_client()
        if not obs.is_connected():
            return {
                "ok": False,
                "error": "OBS no conectado. Verifica que OBS esté abierto con WebSocket activo.",
            }

        # Obtener escena activa si no se especifica
        if not scene_name:
            try:
                scene_name = obs.get_current_scene()
            except Exception as e:
                return {
                    "ok": False,
                    "error": f"No se pudo obtener la escena activa: {e}",
                }

        overlay_id = uuid.uuid4().hex[:16]
        input_name = f"Gravity_Spark_{overlay_id[:8]}"
        overlay_file = os.path.join(_get_overlays_dir(), f"{overlay_id}.html")
        url = f"http://127.0.0.1:{bridge_port}/obs-overlay/{overlay_id}"

        log.info(
            f"[GravitySpark] Generando overlay '{input_name}' — prompt: {prompt[:80]}..."
        )

        # ── Instant Premium Template Routing ──────────────────────────────────────
        prompt_norm = prompt.lower().strip()
        html_content = None

        # Mapeo estricto a las plantillas solo si es el prompt exacto o el nombre clave
        TEMPLATE_PROMPTS = {
            "chat_cyberpunk": [
                "chat cyberpunk",
                "chat_cyberpunk",
                "widget de chat cyberpunk con glassmorphism oscuro. bordes neón cian pulsantes. incluye script js que simula recibir mensajes con avatares (imágenes placeholder) y nombres de colores variados cada 2-5 segundos. auto-scroll fluido y un pequeño destello visual en cada nuevo mensaje. tipografía monospace consola.",
            ],
            "dashboard_hud": [
                "dashboard hud",
                "dashboard_hud",
                "panel lateral de estadísticas estilo sci-fi. muestra viewers, subs y bits. usa js para actualizar los números dinámicamente simulando tráfico real. incluye mini gráficos de barras animados con html5 canvas y anillos circulares de progreso. paleta de colores oscuro con acentos en violeta y verde neón.",
            ],
            "alerta_epica": [
                "alerta épica",
                "alerta_epica",
                'alerta de donación que se dispara cada 10 segundos (simulado por js). inicia con una explosión de partículas doradas 2d usando canvas, seguido de un texto central 3d con sombras pronunciadas que dice "nueva donación" y un nombre aleatorio rotando. efecto de entrada con zoom elástico.',
            ],
            "brb_synthwave": [
                "brb synthwave",
                "brb_synthwave",
                'pantalla "vuelvo enseguida" estilo retrowave 80s. fondo animado con un sol de neón y una cuadrícula 3d moviéndose hacia adelante infinitamente (css animations). al centro, un temporizador funcional en js contando hacia atrás desde 5 minutos. si llega a 0, muestra "¡estamos de vuelta!".',
            ],
            "now_playing": [
                "now playing",
                "now_playing",
                "widget flotante de música actual. muestra la rotación de un vinilo con una carátula simulada, barras de ecualizador de audio que saltan aleatoriamente mediante js, y el texto de la canción desplazándose (marquee). diseño limpio, translúcido con bordes muy finos blancos, efecto blur de fondo.",
            ],
            "meta_subs": [
                "meta subs",
                "meta_subs",
                'barra de meta de subs con hitos (25%, 50%, 100%). script js incrementa el progreso constantemente. al alcanzar un hito, la barra cambia de color vibrante y emite con fe ti css/canvas localmente. el texto muestra "meta: x/100" actualizándose fluidamente. estilo moderno, bordes redondeados (pill-shape).',
            ],
            "reloj_scifi": [
                "reloj sci-fi",
                "reloj_scifi",
                "widget hud que muestra la hora real local (hh:mm:ss) actualizándose cada segundo con js. incluye un falso monitor de sistema (cpu/ram en uso) con barras de progreso fluctuantes aleatoriamente, y un pequeño radar rotativo. estética de interfaz de nave espacial, colores verde terminal y negro.",
            ],
            "gravity_core": [
                "cubo núcleo gravity",
                "gravity_core",
                "un cubo wireframe 3d rotando constantemente en el centro de la pantalla, renderizado usando puras matemáticas de proyección de vértices sobre html5 canvas 2d (simulando un motor 3d desde cero). en su centro, un orbe brillante palpitante. hace fetch a la api local de gravity para ajustar su velocidad de rotación según la latencia.",
                "un cubo wireframe 4d rotando constantemente en el centro de la pantalla, renderizado usando puras matemáticas de proyección de vértices sobre html5 canvas 2d (simulando un motor 4d desde cero). en su centro, un orbe brillante palpitante. hace fetch a la api local de gravity para ajustar su velocidad de rotación según la latencia.",
            ],
            "cinematic_start": [
                "pantalla de inicio cinematográfica",
                "cinematic_start",
                'pantalla de inicio cinematográfica starting soon con barras cinematográficas negras. el fondo es una simulación compleja de humo o niebla volumétrica generada procedimentalmente usando perlin noise o algoritmos de fluidos en canvas. cuenta regresiva que al llegar a cero disipa el humo revelando "sistema online".',
            ],
            "matrix_rain": [
                "lluvia matrix de seguridad",
                "matrix_rain",
                "clásica lluvia digital de caracteres verdes cayendo, construida para máximo rendimiento en canvas. se conecta al security monitor local y hace que las gotas formen esporádicamente palabras reales como secure, firewall o gravity cuando detecta monitoreo activo.",
            ],
        }

        selected_template = None
        if use_cache:
            for temp_key, prompts in TEMPLATE_PROMPTS.items():
                if prompt_norm in prompts:
                    selected_template = temp_key
                    break

            if selected_template:
                from core.spark_templates import TEMPLATES

                html_content = TEMPLATES.get(selected_template)
                log.info(
                    f"[GravitySpark] Ruta instantánea: Seleccionada plantilla ultra-premium {selected_template}"
                )
        else:
            log.info(
                "[GravitySpark] Caché desactivada por usuario. Omitiendo plantillas instantáneas para crear variación única."
            )

        # 1. Llamar al LLM local (solo si no coincide con ninguna plantilla instantánea)
        if not html_content:
            try:
                temp = 0.8 if not use_cache else 0.6
                raw_response = _call_local_llm(prompt, temperature=temp)
                html_content = _extract_html(raw_response)
            except Exception as e:
                log.error(f"[GravitySpark] Error LLM: {e}")
                return {
                    "ok": False,
                    "error": f"Error generando overlay con IA local: {e}",
                }

        # 2. Guardar HTML en disco
        try:
            with open(overlay_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            log.info(f"[GravitySpark] HTML guardado: {overlay_file}")
        except Exception as e:
            return {"ok": False, "error": f"Error guardando overlay: {e}"}

        # 3. Crear Browser Source en OBS
        try:
            result = obs.create_browser_source(
                scene_name=scene_name,
                input_name=input_name,
                url=url,
                width=width,
                height=height,
                x=x,
                y=y,
            )
        except Exception as e:
            try:
                os.remove(overlay_file)
            except Exception:
                pass
            return {"ok": False, "error": f"Error creando Browser Source en OBS: {e}"}

        # 4. Registrar overlay activo
        _active_overlays[overlay_id] = {
            "overlay_id": overlay_id,
            "input_name": input_name,
            "scene_name": scene_name,
            "scene_item_id": result.get("scene_item_id"),
            "created_at": time.time(),
            "prompt": prompt,
            "path": overlay_file,
            "url": url,
            "width": width,
            "height": height,
        }
        _save_active_overlays()

        return {
            "ok": True,
            "overlay_id": overlay_id,
            "input_name": input_name,
            "scene_name": scene_name,
            "scene_item_id": result.get("scene_item_id"),
            "preview_url": url,
            "html_path": overlay_file,
            "prompt": prompt,
        }


def edit_overlay(
    overlay_id: str, new_prompt: str, bridge_port: int = 7860
) -> Dict[str, Any]:
    """Regenera un overlay existente de forma totalmente thread-safe y segura en disco y OBS."""
    with _overlays_lock:
        from core.obs_client import get_client

        obs = get_client()

        if overlay_id not in _active_overlays:
            return {"ok": False, "error": f"Overlay {overlay_id} no encontrado"}
        info = _active_overlays[overlay_id]

        # Combinar prompt original con el nuevo para dar contexto
        combined_prompt = f"Overlay existente: {info['prompt']}\nModificación solicitada: {new_prompt}"

        log.info(f"[GravitySpark] Editando overlay {overlay_id}: {new_prompt[:60]}...")
        try:
            raw = _call_local_llm(combined_prompt)
            html = _extract_html(raw)
        except Exception as e:
            return {"ok": False, "error": f"Error LLM: {e}"}

        try:
            with open(info["path"], "w", encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            return {"ok": False, "error": f"Error guardando: {e}"}

        # Forzar refresh del Browser Source en OBS
        try:
            obs.refresh_browser_source(info["input_name"])
        except Exception as e:
            log.warning(f"[GravitySpark] No se pudo refrescar en OBS: {e}")

        _active_overlays[overlay_id]["prompt"] = new_prompt
        _save_active_overlays()

        return {
            "ok": True,
            "overlay_id": overlay_id,
            "input_name": info["input_name"],
            "message": "Overlay actualizado y refrescado en OBS",
        }


def remove_overlay(overlay_id: str) -> Dict[str, Any]:
    """Elimina un overlay de OBS y del disco de forma thread-safe y limpia."""
    with _overlays_lock:
        from core.obs_client import get_client

        obs = get_client()

        if overlay_id not in _active_overlays:
            return {"ok": False, "error": f"Overlay {overlay_id} no encontrado"}
        info = _active_overlays.pop(overlay_id)
        _save_active_overlays()

        errors = []

        # Eliminar de OBS
        try:
            obs.remove_input(info["input_name"])
        except Exception as e:
            errors.append(f"OBS: {e}")

        # Eliminar archivo HTML
        try:
            if os.path.isfile(info["path"]):
                os.remove(info["path"])
        except Exception as e:
            errors.append(f"Disco: {e}")

        if errors:
            return {"ok": False, "overlay_id": overlay_id, "errors": errors}
        return {"ok": True, "overlay_id": overlay_id, "message": "Overlay eliminado"}


def get_overlays() -> List[Dict[str, Any]]:
    """Retorna la lista de overlays activos de forma thread-safe."""
    with _overlays_lock:
        return [
            {
                "overlay_id": v["overlay_id"],
                "input_name": v["input_name"],
                "scene_name": v["scene_name"],
                "scene_item_id": v["scene_item_id"],
                "created_at": v["created_at"],
                "prompt": v["prompt"],
                "url": v["url"],
                "width": v["width"],
                "height": v["height"],
            }
            for v in _active_overlays.values()
        ]


def get_overlay_html(overlay_id: str) -> Optional[str]:
    """Retorna el contenido HTML de un overlay guardado en disco de forma segura."""
    with _overlays_lock:
        overlays_dir = _get_overlays_dir()
        path = os.path.join(overlays_dir, f"{overlay_id}.html")
        if not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            log.error(f"[GravitySpark] Error leyendo HTML de overlay: {e}")
            return None



def _clean_orphaned_overlay_files():
    """Busca y elimina físicamente archivos HTML huérfanos del directorio de overlays."""
    try:
        overlays_dir = _get_overlays_dir()
        if not os.path.isdir(overlays_dir):
            return
        with _overlays_lock:
            active_ids = set(_active_overlays.keys())
        for filename in os.listdir(overlays_dir):
            if filename.endswith(".html"):
                overlay_id = filename[:-5]
                # Verificar que el nombre sea un ID de 16 caracteres hexadecimales
                if len(overlay_id) == 16 and all(c in "0123456789abcdef" for c in overlay_id):
                    if overlay_id not in active_ids:
                        file_path = os.path.join(overlays_dir, filename)
                        try:
                            os.remove(file_path)
                            log.info(f"[GravitySpark] Eliminado archivo de overlay huérfano: {filename}")
                        except Exception as e:
                            log.warning(f"[GravitySpark] No se pudo eliminar el archivo huérfano {filename}: {e}")
    except Exception as e:
        log.error(f"[GravitySpark] Error en la limpieza de archivos huérfanos: {e}")


# ── Cargar estado al importar ────────────────────────────────────────────────
_load_active_overlays()
_clean_orphaned_overlay_files()
