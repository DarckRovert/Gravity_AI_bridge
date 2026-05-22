"""
╔══════════════════════════════════════════════════════════════════════════════╗
║             GRAVITY AI ROUTE HANDLERS — api/routes/handlers/obs_handler.py   ║
║          Modular Controller encapsulating all OBS HTTP actions               ║
╚══════════════════════════════════════════════════════════════════════════════╗
"""

import json
import urllib.parse
from core.logger import log
from integrations.obs.client import get_client

def handle_obs_status(handler):
    """GET /v1/obs/status — Estado de conexion OBS WebSocket."""
    try:
        status = get_client().get_status()
        body = json.dumps(status, indent=2).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"connected": False, "error": str(e)}).encode())

def handle_obs_scenes(handler):
    """GET /v1/obs/scenes — Lista de escenas OBS y escena activa."""
    try:
        cl = get_client()
        if not cl.is_connected():
            handler.send_response(503)
            handler._send_cors()
            handler.end_headers()
            handler.wfile.write(json.dumps({"error": "OBS no conectado"}).encode())
            return
        scenes = cl.get_scenes()
        current = cl.get_current_scene()
        body = json.dumps({"scenes": scenes, "current_scene": current}, indent=2).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())

def handle_obs_scene_items(handler):
    """GET /v1/obs/scene/items?scene=<name> — Fuentes de una escena."""
    try:
        params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(handler.path).query))
        scene_name = params.get("scene", "").strip()
        cl = get_client()
        if not cl.is_connected():
            handler.send_response(503)
            handler._send_cors()
            handler.end_headers()
            handler.wfile.write(json.dumps({"error": "OBS no conectado"}).encode())
            return
        if not scene_name:
            scene_name = cl.get_current_scene()
        items = cl.get_scene_items(scene_name)
        body = json.dumps({"scene_name": scene_name, "items": items, "count": len(items)},
                          indent=2).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())

def handle_obs_inputs(handler):
    """GET /v1/obs/inputs — Todos los inputs/fuentes con estado de audio."""
    try:
        cl = get_client()
        if not cl.is_connected():
            handler.send_response(503)
            handler._send_cors()
            handler.end_headers()
            handler.wfile.write(json.dumps({"error": "OBS no conectado"}).encode())
            return
        inputs = cl.get_inputs()
        body = json.dumps({"inputs": inputs, "count": len(inputs)}, indent=2).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())

def handle_obs_stream_status(handler):
    """GET /v1/obs/stream/status — Estado de stream y grabacion."""
    try:
        cl = get_client()
        if not cl.is_connected():
            handler.send_response(503)
            handler._send_cors()
            handler.end_headers()
            handler.wfile.write(json.dumps({"error": "OBS no conectado"}).encode())
            return
        status = cl.get_stream_status()
        body = json.dumps(status, indent=2).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())

def handle_obs_overlays(handler):
    """GET /v1/obs/overlays — Lista de overlays Gravity Spark activos."""
    try:
        from core.obs_spark_engine import get_overlays
        overlays = get_overlays()
        body = json.dumps({"overlays": overlays, "count": len(overlays)}, indent=2).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())

def handle_obs_overlay_html(handler):
    """
    GET /obs-overlay/<overlay_id> — Sirve el HTML del overlay generado.
    OBS renderiza esta URL en el Browser Source embebido.
    """
    try:
        from core.obs_spark_engine import get_overlay_html
        path_clean = handler.path.split("?")[0]
        overlay_id = path_clean.replace("/obs-overlay/", "").strip("/")
        if not overlay_id or not overlay_id.isalnum():
            handler.send_response(400)
            handler.end_headers()
            handler.wfile.write(b"Invalid overlay ID")
            return
        html = get_overlay_html(overlay_id)
        if html is None:
            handler.send_response(404)
            handler.end_headers()
            handler.wfile.write(b"Overlay not found")
            return
        body = html.encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "text/html; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.send_header("Cache-Control", "no-cache")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(str(e).encode())

def handle_obs_connect(handler):
    """POST /v1/obs/connect"""
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data   = json.loads(handler.rfile.read(length)) if length else {}
        from core.obs_client import get_client
        cl = get_client()
        cfg_host = data.get("host", "127.0.0.1")
        cfg_port = int(data.get("port", 4455))
        cfg_pass = data.get("password", "JZe2JTFSolWLni2i")
        cl.configure(cfg_host, cfg_port, cfg_pass)
        result = cl.connect()
        body = json.dumps(result, indent=2).encode("utf-8")
        handler.send_response(200 if result.get("ok") else 503)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors(); handler.end_headers(); handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500); handler._send_cors(); handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

def handle_obs_scene_switch(handler):
    """POST /v1/obs/scene/switch"""
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data   = json.loads(handler.rfile.read(length)) if length else {}
        scene_name = data.get("scene_name", "").strip()
        if not scene_name:
            handler.send_response(400); handler._send_cors(); handler.end_headers()
            handler.wfile.write(json.dumps({"error": "scene_name requerido"}).encode()); return
        from core.obs_client import get_client
        result = get_client().switch_scene(scene_name)
        body = json.dumps(result).encode("utf-8")
        handler.send_response(200 if result.get("ok") else 400)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors(); handler.end_headers(); handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500); handler._send_cors(); handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

def handle_obs_source_toggle(handler):
    """POST /v1/obs/source/toggle"""
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data   = json.loads(handler.rfile.read(length)) if length else {}
        scene_name   = data.get("scene_name", "").strip()
        scene_item_id = int(data.get("scene_item_id", 0))
        if not scene_name or not scene_item_id:
            handler.send_response(400); handler._send_cors(); handler.end_headers()
            handler.wfile.write(json.dumps({"error": "scene_name y scene_item_id requeridos"}).encode()); return
        from core.obs_client import get_client
        result = get_client().toggle_item_visible(scene_name, scene_item_id)
        body = json.dumps(result).encode("utf-8")
        handler.send_response(200 if result.get("ok") else 400)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors(); handler.end_headers(); handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500); handler._send_cors(); handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

def handle_obs_source_visible(handler):
    """POST /v1/obs/source/visible"""
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data   = json.loads(handler.rfile.read(length)) if length else {}
        scene_name    = data.get("scene_name", "").strip()
        scene_item_id = int(data.get("scene_item_id", 0))
        visible       = bool(data.get("visible", True))
        if not scene_name or not scene_item_id:
            handler.send_response(400); handler._send_cors(); handler.end_headers()
            handler.wfile.write(json.dumps({"error": "scene_name y scene_item_id requeridos"}).encode()); return
        from core.obs_client import get_client
        result = get_client().set_item_visible(scene_name, scene_item_id, visible)
        body = json.dumps(result).encode("utf-8")
        handler.send_response(200 if result.get("ok") else 400)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors(); handler.end_headers(); handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500); handler._send_cors(); handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

def handle_obs_stream_start(handler):
    """POST /v1/obs/stream/start"""
    try:
        from core.obs_client import get_client
        result = get_client().start_stream()
        body = json.dumps(result).encode("utf-8")
        handler.send_response(200 if result.get("ok") else 400)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors(); handler.end_headers(); handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500); handler._send_cors(); handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

def handle_obs_stream_stop(handler):
    """POST /v1/obs/stream/stop"""
    try:
        from core.obs_client import get_client
        result = get_client().stop_stream()
        body = json.dumps(result).encode("utf-8")
        handler.send_response(200 if result.get("ok") else 400)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors(); handler.end_headers(); handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500); handler._send_cors(); handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

def handle_obs_stream_toggle(handler):
    """POST /v1/obs/stream/toggle"""
    try:
        from core.obs_client import get_client
        result = get_client().toggle_stream()
        body = json.dumps(result).encode("utf-8")
        handler.send_response(200 if result.get("ok") else 400)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors(); handler.end_headers(); handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500); handler._send_cors(); handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

def handle_obs_record_start(handler):
    """POST /v1/obs/record/start"""
    try:
        from core.obs_client import get_client
        result = get_client().start_record()
        body = json.dumps(result).encode("utf-8")
        handler.send_response(200 if result.get("ok") else 400)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors(); handler.end_headers(); handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500); handler._send_cors(); handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

def handle_obs_record_stop(handler):
    """POST /v1/obs/record/stop"""
    try:
        from core.obs_client import get_client
        result = get_client().stop_record()
        body = json.dumps(result).encode("utf-8")
        handler.send_response(200 if result.get("ok") else 400)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors(); handler.end_headers(); handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500); handler._send_cors(); handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

def handle_obs_record_toggle(handler):
    """POST /v1/obs/record/toggle"""
    try:
        from core.obs_client import get_client
        result = get_client().toggle_record()
        body = json.dumps(result).encode("utf-8")
        handler.send_response(200 if result.get("ok") else 400)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors(); handler.end_headers(); handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500); handler._send_cors(); handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

def handle_obs_audio_mute(handler):
    """POST /v1/obs/audio/mute"""
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data   = json.loads(handler.rfile.read(length)) if length else {}
        input_name = data.get("input_name", "").strip()
        if not input_name:
            handler.send_response(400); handler._send_cors(); handler.end_headers()
            handler.wfile.write(json.dumps({"error": "input_name requerido"}).encode()); return
        from core.obs_client import get_client
        result = get_client().toggle_mute(input_name)
        body = json.dumps(result).encode("utf-8")
        handler.send_response(200 if result.get("ok") else 400)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors(); handler.end_headers(); handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500); handler._send_cors(); handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

def handle_obs_audio_volume(handler):
    """POST /v1/obs/audio/volume"""
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data   = json.loads(handler.rfile.read(length)) if length else {}
        input_name = data.get("input_name", "").strip()
        volume_db  = float(data.get("volume_db", 0.0))
        if not input_name:
            handler.send_response(400); handler._send_cors(); handler.end_headers()
            handler.wfile.write(json.dumps({"error": "input_name requerido"}).encode()); return
        from core.obs_client import get_client
        result = get_client().set_volume(input_name, volume_db)
        body = json.dumps(result).encode("utf-8")
        handler.send_response(200 if result.get("ok") else 400)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors(); handler.end_headers(); handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500); handler._send_cors(); handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

def handle_obs_spark_generate(handler):
    """POST /v1/obs/spark/generate"""
    import traceback
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data   = json.loads(handler.rfile.read(length)) if length else {}
        prompt = data.get("prompt", "").strip()
        if not prompt:
            handler.send_response(400); handler._send_cors(); handler.end_headers()
            handler.wfile.write(json.dumps({"error": "Campo 'prompt' requerido"}).encode()); return
        from core.obs_spark_engine import generate_overlay
        from core.config_manager import config
        port = config.get("server.port", 7860)
        use_cache = data.get("use_cache", True)
        result = generate_overlay(
            prompt      = prompt,
            scene_name  = data.get("scene_name", ""),
            width       = int(data.get("width",  400)),
            height      = int(data.get("height", 300)),
            x           = int(data.get("x", 0)),
            y           = int(data.get("y", 0)),
            bridge_port = port,
            use_cache   = use_cache,
        )
        body = json.dumps(result, indent=2, ensure_ascii=False).encode("utf-8")
        handler.send_response(200 if result.get("ok") else 500)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors(); handler.end_headers(); handler.wfile.write(body)
    except Exception as e:
        log.error(f"[GravitySpark] /v1/obs/spark/generate error: {traceback.format_exc()}")
        handler.send_response(500); handler._send_cors(); handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

def handle_obs_spark_edit(handler):
    """POST /v1/obs/spark/edit"""
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data   = json.loads(handler.rfile.read(length)) if length else {}
        overlay_id = data.get("overlay_id", "").strip()
        new_prompt = data.get("prompt", "").strip()
        if not overlay_id or not new_prompt:
            handler.send_response(400); handler._send_cors(); handler.end_headers()
            handler.wfile.write(json.dumps({"error": "overlay_id y prompt requeridos"}).encode()); return
        from core.obs_spark_engine import edit_overlay
        result = edit_overlay(overlay_id, new_prompt)
        body = json.dumps(result, indent=2).encode("utf-8")
        handler.send_response(200 if result.get("ok") else 400)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors(); handler.end_headers(); handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500); handler._send_cors(); handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

def handle_obs_spark_remove(handler):
    """POST /v1/obs/spark/remove"""
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data   = json.loads(handler.rfile.read(length)) if length else {}
        overlay_id = data.get("overlay_id", "").strip()
        if not overlay_id:
            handler.send_response(400); handler._send_cors(); handler.end_headers()
            handler.wfile.write(json.dumps({"error": "overlay_id requerido"}).encode()); return
        from core.obs_spark_engine import remove_overlay
        result = remove_overlay(overlay_id)
        body = json.dumps(result, indent=2).encode("utf-8")
        handler.send_response(200 if result.get("ok") else 400)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors(); handler.end_headers(); handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500); handler._send_cors(); handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
