"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — TIKTOK / INSTAGRAM REELS UPLOADER V1.0                        ║
║  Distribución omnicanal del clip Short ya generado por youtube_uploader      ║
║                                                                              ║
║  Backends soportados:                                                        ║
║    - TikTok: Content Posting API v2 (requiere developer.tiktok.com)          ║
║    - Instagram: Graph API v19 (requiere Facebook Developer App)              ║
║                                                                              ║
║  Si las API keys no están configuradas, opera en modo DRY-RUN                ║
║  y registra los intentos en _integrations/social_log.json                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import threading
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

from core.logger import log
from core.config_manager import config as config_manager

BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH: str = os.path.join(BASE_DIR, "config.yaml")
SOCIAL_LOG: str = os.path.join(BASE_DIR, "_integrations", "social_log.json")
OAUTH_DIR: str = os.path.join(BASE_DIR, "_integrations")

# Cerrojo reentrante a nivel de módulo para la E/S de credenciales y registros sociales
_social_io_lock: threading.RLock = threading.RLock()


# ── Config ────────────────────────────────────────────────────────────────────

def _load_config() -> Dict[str, Any]:
    """
    Retorna la sección de configuración social de manera segura usando ConfigManager.
    """
    try:
        cfg = config_manager.get("social", {})
        return cfg if isinstance(cfg, dict) else {}
    except Exception as e:
        log.error(f"[Social] Error cargando configuración centralizada: {e}")
        return {}


def _load_tiktok_creds() -> Dict[str, Any]:
    """
    Carga de manera segura y sincronizada las credenciales de TikTok.
    """
    path: str = os.path.join(OAUTH_DIR, "tiktok_creds.json")
    with _social_io_lock:
        if os.path.isfile(path):
            for attempt in range(5):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except (PermissionError, json.JSONDecodeError):
                    if attempt == 4:
                        return {}
                    time.sleep(0.05 * (2 ** attempt))
                except Exception:
                    return {}
        return {}


def _load_instagram_creds() -> Dict[str, Any]:
    """
    Carga de manera segura y sincronizada las credenciales de Instagram.
    """
    path: str = os.path.join(OAUTH_DIR, "instagram_creds.json")
    with _social_io_lock:
        if os.path.isfile(path):
            for attempt in range(5):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except (PermissionError, json.JSONDecodeError):
                    if attempt == 4:
                        return {}
                    time.sleep(0.05 * (2 ** attempt))
                except Exception:
                    return {}
        return {}


# ── Social log ────────────────────────────────────────────────────────────────

def _log_attempt(platform: str, job_id: int, status: str,
                 video_id: str = "", error: str = "") -> None:
    """
    Registra de manera atómica, thread-safe y persistente el intento de publicación.
    """
    with _social_io_lock:
        for attempt in range(5):
            try:
                records: List[Dict[str, Any]] = []
                if os.path.isfile(SOCIAL_LOG):
                    try:
                        with open(SOCIAL_LOG, "r", encoding="utf-8") as f:
                            records = json.load(f)
                            if not isinstance(records, list):
                                records = []
                    except Exception:
                        records = []
                
                records.append({
                    "ts":        datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "platform":  platform,
                    "job_id":    job_id,
                    "status":    status,
                    "video_id":  video_id,
                    "error":     error,
                })
                
                os.makedirs(OAUTH_DIR, exist_ok=True)
                tmp_path: str = SOCIAL_LOG + ".tmp"
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(records[-1000:], f, ensure_ascii=False)
                os.replace(tmp_path, SOCIAL_LOG)
                return
            except (PermissionError, IOError) as e:
                if attempt == 4:
                    log.error(f"[Social] Colisión persistente guardando log en disco: {e}")
                time.sleep(0.05 * (2 ** attempt))
            except Exception as e:
                log.error(f"[Social] Error guardando log: {e}")
                return



# ── TikTok Content Posting API v2 ─────────────────────────────────────────────

def upload_to_tiktok(job_id: int, video_path: str, title: str,
                     tags: Optional[list[str]] = None) -> dict:
    """
    Sube un video a TikTok usando la Content Posting API v2.
    Requiere: access_token en _integrations/tiktok_creds.json
    Docs: https://developers.tiktok.com/doc/content-posting-api-get-started
    """
    cfg   = _load_config()
    tt_cfg = cfg.get("tiktok", {})

    if not tt_cfg.get("enabled", False):
        return {"ok": False, "skipped": True, "error": "TikTok deshabilitado (social.tiktok.enabled: false)"}

    creds        = _load_tiktok_creds()
    access_token = creds.get("access_token", "")

    if not access_token:
        _log_attempt("tiktok", job_id, "dry_run")
        return {
            "ok": False, "dry_run": True,
            "error": "Sin access_token en tiktok_creds.json. Configura la TikTok Developer App.",
            "setup_url": "https://developers.tiktok.com/doc/content-posting-api-get-started",
        }

    if not os.path.isfile(video_path):
        return {"ok": False, "error": f"Archivo no encontrado: {video_path}"}

    tags     = tags or ["IA", "DarckRovert", "Shorts"]
    hashtags = " ".join(f"#{t.replace(' ', '')}" for t in tags[:5])
    caption  = f"{title[:100]}\n\n{hashtags}"

    try:
        file_size = os.path.getsize(video_path)

        # 1. Iniciar upload
        init_payload = json.dumps({
            "post_info": {
                "title":        caption,
                "privacy_level": tt_cfg.get("privacy_level", "SELF_ONLY"),  # empieza privado, luego se publica
                "disable_duet":  False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000,
            },
            "source_info": {
                "source":          "FILE_UPLOAD",
                "video_size":      file_size,
                "chunk_size":      file_size,
                "total_chunk_count": 1,
            },
        }).encode("utf-8")

        init_req = urllib.request.Request(
            "https://open.tiktokapis.com/v2/post/publish/video/init/",
            data=init_payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type":  "application/json; charset=UTF-8",
            },
            method="POST",
        )
        with urllib.request.urlopen(init_req, timeout=30) as resp:
            init_data = json.loads(resp.read().decode())

        publish_id  = init_data.get("data", {}).get("publish_id", "")
        upload_url  = init_data.get("data", {}).get("upload_url", "")

        if not upload_url:
            err = f"Sin upload_url en respuesta TikTok: {init_data}"
            _log_attempt("tiktok", job_id, "failed", error=err)
            return {"ok": False, "error": err}

        # 2. Subir bytes
        with open(video_path, "rb") as vf:
            video_bytes = vf.read()

        upload_req = urllib.request.Request(
            upload_url,
            data=video_bytes,
            headers={
                "Content-Type":           "video/mp4",
                "Content-Length":         str(file_size),
                "Content-Range":          f"bytes 0-{file_size-1}/{file_size}",
            },
            method="PUT",
        )
        with urllib.request.urlopen(upload_req, timeout=300) as resp:
            resp.read()

        log.info(f"[TikTok] Job #{job_id} subido. publish_id: {publish_id}")
        _log_attempt("tiktok", job_id, "uploaded", video_id=publish_id)
        return {"ok": True, "publish_id": publish_id, "platform": "tiktok"}

    except urllib.error.HTTPError as e:
        err = f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}"
        log.error(f"[TikTok] {err}")
        _log_attempt("tiktok", job_id, "failed", error=err)
        return {"ok": False, "error": err}
    except Exception as e:
        log.error(f"[TikTok] Error: {e}")
        _log_attempt("tiktok", job_id, "failed", error=str(e))
        return {"ok": False, "error": str(e)}


# ── Instagram Graph API (Reels) ───────────────────────────────────────────────

def upload_to_instagram(job_id: int, video_path: str, title: str,
                        tags: Optional[list[str]] = None) -> dict:
    """
    Sube un Reel a Instagram usando Graph API v19.
    Requiere: access_token e ig_user_id en _integrations/instagram_creds.json
    El video debe ser accesible públicamente via URL (se sube a un servidor temporal).
    
    NOTA: Instagram Graph API NO permite uploads directos de archivo; el video
    debe estar en una URL HTTPS pública. En producción, sube el archivo a un
    bucket S3/R2/Cloudflare y usa esa URL. Esta implementación soporta un 
    campo video_url en instagram_creds.json como CDN personalizado.
    """
    cfg    = _load_config()
    ig_cfg = cfg.get("instagram", {})

    if not ig_cfg.get("enabled", False):
        return {"ok": False, "skipped": True, "error": "Instagram deshabilitado (social.instagram.enabled: false)"}

    creds        = _load_instagram_creds()
    access_token = creds.get("access_token", "")
    ig_user_id   = creds.get("ig_user_id", "")
    cdn_base_url = creds.get("cdn_base_url", "")  # URL pública donde está el video

    if not all([access_token, ig_user_id]):
        _log_attempt("instagram", job_id, "dry_run")
        return {
            "ok": False, "dry_run": True,
            "error": "Sin credenciales en instagram_creds.json.",
            "setup_url": "https://developers.facebook.com/docs/instagram-api/guides/content-publishing",
        }

    tags     = tags or ["IA", "DarckRovert"]
    hashtags = " ".join(f"#{t.replace(' ', '')}" for t in tags[:15])
    caption  = f"{title[:200]}\n\n{hashtags}"

    if not cdn_base_url:
        return {
            "ok": False,
            "error": "instagram_creds.json requiere 'cdn_base_url' con la URL base de tu CDN. "
                     "Instagram no permite uploads directos de archivo.",
        }

    video_url = f"{cdn_base_url.rstrip('/')}/{os.path.basename(video_path)}"

    try:
        # 1. Crear contenedor de media
        create_params = urllib.parse.urlencode({
            "media_type":   "REELS",
            "video_url":    video_url,
            "caption":      caption,
            "share_to_feed": "true",
            "access_token": access_token,
        })
        req1 = urllib.request.Request(
            f"https://graph.instagram.com/v19.0/{ig_user_id}/media",
            data=create_params.encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(req1, timeout=60) as resp:
            media_data = json.loads(resp.read().decode())

        creation_id = media_data.get("id", "")
        if not creation_id:
            err = f"Sin creation_id: {media_data}"
            _log_attempt("instagram", job_id, "failed", error=err)
            return {"ok": False, "error": err}

        # 2. Publicar
        publish_params = urllib.parse.urlencode({
            "creation_id":  creation_id,
            "access_token": access_token,
        })
        req2 = urllib.request.Request(
            f"https://graph.instagram.com/v19.0/{ig_user_id}/media_publish",
            data=publish_params.encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(req2, timeout=60) as resp:
            pub_data = json.loads(resp.read().decode())

        media_id = pub_data.get("id", "")
        log.info(f"[Instagram] Job #{job_id} publicado. media_id: {media_id}")
        _log_attempt("instagram", job_id, "uploaded", video_id=media_id)
        return {"ok": True, "media_id": media_id, "platform": "instagram"}

    except urllib.error.HTTPError as e:
        err = f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}"
        log.error(f"[Instagram] {err}")
        _log_attempt("instagram", job_id, "failed", error=err)
        return {"ok": False, "error": err}
    except Exception as e:
        log.error(f"[Instagram] Error: {e}")
        _log_attempt("instagram", job_id, "failed", error=str(e))
        return {"ok": False, "error": str(e)}


# ── Distribuidor omnicanal ────────────────────────────────────────────────────

def distribute_short(job_id: int, shorts_path: str, title: str,
                     tags: Optional[list[str]] = None) -> dict:
    """
    Distribuye el Short a todos los canales sociales habilitados.
    Retorna un dict con el resultado por plataforma.
    """
    if not os.path.isfile(shorts_path):
        return {"ok": False, "error": f"Short no encontrado: {shorts_path}"}

    results = {}
    cfg     = _load_config()

    if cfg.get("tiktok", {}).get("enabled", False):
        results["tiktok"] = upload_to_tiktok(job_id, shorts_path, title, tags)

    if cfg.get("instagram", {}).get("enabled", False):
        results["instagram"] = upload_to_instagram(job_id, shorts_path, title, tags)

    ok_count = sum(1 for r in results.values() if r.get("ok"))
    log.info(f"[Social] Job #{job_id} distribuido a {ok_count}/{len(results)} plataformas.")
    return {"ok": ok_count > 0, "results": results, "job_id": job_id}


def distribute_short_async(job_id: int, shorts_path: str, title: str,
                           tags: Optional[list[str]] = None) -> None:
    """Distribuye en background sin bloquear el pipeline."""
    def _run():
        distribute_short(job_id, shorts_path, title, tags)
    threading.Thread(target=_run, name=f"GravitySocial-{job_id}", daemon=True).start()


# ── Estado y configuración ────────────────────────────────────────────────────

def get_status() -> dict:
    cfg    = _load_config()
    tt_ok  = bool(_load_tiktok_creds().get("access_token"))
    ig_ok  = bool(_load_instagram_creds().get("access_token") and _load_instagram_creds().get("ig_user_id"))

    records = []
    if os.path.isfile(SOCIAL_LOG):
        try:
            with open(SOCIAL_LOG, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            pass

    last_24h = [r for r in records if r.get("ts", "") >= (
        datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    )]

    return {
        "tiktok": {
            "enabled":     cfg.get("tiktok", {}).get("enabled", False),
            "configured":  tt_ok,
            "uploads_24h": sum(1 for r in last_24h if r.get("platform") == "tiktok" and r.get("status") == "uploaded"),
            "setup_url":   "https://developers.tiktok.com/doc/content-posting-api-get-started",
        },
        "instagram": {
            "enabled":     cfg.get("instagram", {}).get("enabled", False),
            "configured":  ig_ok,
            "uploads_24h": sum(1 for r in last_24h if r.get("platform") == "instagram" and r.get("status") == "uploaded"),
            "setup_url":   "https://developers.facebook.com/docs/instagram-api/guides/content-publishing",
        },
        "recent_log": records[-20:],
    }


def get_credential_templates() -> dict:
    """Retorna los templates de JSON para configurar las credenciales."""
    return {
        "tiktok": {
            "file": "_integrations/tiktok_creds.json",
            "template": {
                "access_token": "",
                "client_key":   "",
                "client_secret": "",
                "_instrucciones": [
                    "1. Ve a developers.tiktok.com y crea una App",
                    "2. Solicita el permiso 'video.publish'",
                    "3. Completa el proceso OAuth y pega el access_token aqui",
                ]
            }
        },
        "instagram": {
            "file": "_integrations/instagram_creds.json",
            "template": {
                "access_token": "",
                "ig_user_id":   "",
                "cdn_base_url": "",
                "_instrucciones": [
                    "1. Ve a developers.facebook.com y crea una App de tipo 'Business'",
                    "2. Agrega el producto 'Instagram Graph API'",
                    "3. Genera un Long-Lived User Access Token",
                    "4. cdn_base_url es la URL pública donde subes los videos (S3, R2, etc.)",
                ]
            }
        }
    }
