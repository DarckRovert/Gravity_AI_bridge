"""
╔══════════════════════════════════════════════════════════════════════════════╗
║    GRAVITY AI — YOUTUBE UPLOADER V2.0                                        ║
║    Upload autónomo a YouTube Data API v3 con control de quota                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Fixes V2:
  - Lock granular: solo bloquea el refresh de token, NO el upload completo.
  - Quota tracker en _integrations/yt_quota.json (quota diaria de YouTube API).
  - SEO description auto-generada con hashtags y links de branding.
  - Columns migradas en _init_db del pipeline → _init_db_columns() eliminada.
  - Shorts upload helper: clip vertical 9:16 60s para YouTube Shorts.
  - Retry logic: un reintento si el upload falla por error transitorio.
"""

import os
import json
import sqlite3
import threading
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, date, timezone
from typing import Optional

from core.logger import log

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OAUTH_PATH   = os.path.join(BASE_DIR, "_integrations", "youtube_oauth.json")
QUOTA_PATH   = os.path.join(BASE_DIR, "_integrations", "yt_quota.json")
DB_PATH      = os.path.join(BASE_DIR, "_video_queue.sqlite")
CONFIG_PATH  = os.path.join(BASE_DIR, "config.yaml")
FFMPEG_EXE   = os.path.join(BASE_DIR, "_integrations", "ffmpeg", "ffmpeg.exe")

_UPLOAD_URL  = "https://www.googleapis.com/upload/youtube/v3/videos"
_THUMB_URL   = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
_TOKEN_URL   = "https://oauth2.googleapis.com/token"
_AUTH_URL    = "https://accounts.google.com/o/oauth2/v2/auth"
_SCOPE       = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube"

# Lock solo para el refresh del token (operación corta), no para el upload entero.
_token_lock  = threading.Lock()


# ── Config ────────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    try:
        import yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}).get("youtube", {})
    except Exception:
        return {}


# ── Quota diaria (YouTube permite 10 000 unidades/día; upload = ~1600 unidades) ──

def _quota_check() -> bool:
    """Retorna True si aún hay quota disponible hoy."""
    cfg         = _load_config()
    daily_limit = int(cfg.get("quota_daily_limit", 5))
    today       = str(date.today())
    try:
        if os.path.isfile(QUOTA_PATH):
            with open(QUOTA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("date") == today:
                return int(data.get("uploads", 0)) < daily_limit
        return True
    except Exception:
        return True


def _quota_increment() -> None:
    """Registra un upload exitoso en el contador diario."""
    today = str(date.today())
    try:
        data = {"date": today, "uploads": 0}
        if os.path.isfile(QUOTA_PATH):
            with open(QUOTA_PATH, "r", encoding="utf-8") as f:
                stored = json.load(f)
            if stored.get("date") == today:
                data = stored
        data["uploads"] = int(data.get("uploads", 0)) + 1
        os.makedirs(os.path.dirname(QUOTA_PATH), exist_ok=True)
        with open(QUOTA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        log.warning(f"[YouTube] Error actualizando quota: {e}")


def get_quota_status() -> dict:
    """Retorna estado de la quota diaria."""
    cfg         = _load_config()
    daily_limit = int(cfg.get("quota_daily_limit", 5))
    today       = str(date.today())
    uploads     = 0
    try:
        if os.path.isfile(QUOTA_PATH):
            with open(QUOTA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("date") == today:
                uploads = int(data.get("uploads", 0))
    except Exception:
        pass
    return {"date": today, "uploads_today": uploads, "limit": daily_limit, "remaining": max(0, daily_limit - uploads)}


# ── OAuth Token Management ────────────────────────────────────────────────────

def _load_oauth() -> dict:
    if not os.path.isfile(OAUTH_PATH):
        return {}
    try:
        with open(OAUTH_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_oauth(data: dict) -> None:
    os.makedirs(os.path.dirname(OAUTH_PATH), exist_ok=True)
    with open(OAUTH_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _refresh_access_token(oauth: dict) -> Optional[str]:
    """Refresca el access_token. Lock granular solo durante esta operación."""
    with _token_lock:
        refresh_token = oauth.get("refresh_token", "")
        client_id     = oauth.get("client_id", "")
        client_secret = oauth.get("client_secret", "")
        if not all([refresh_token, client_id, client_secret]):
            log.error("[YouTube] Faltan credenciales OAuth (client_id / client_secret / refresh_token).")
            return None
        payload = urllib.parse.urlencode({
            "client_id":     client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type":    "refresh_token",
        }).encode()
        try:
            req = urllib.request.Request(
                _TOKEN_URL, data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                token_data = json.loads(resp.read().decode())
            access_token = token_data.get("access_token")
            if not access_token:
                log.error(f"[YouTube] Token refresh sin access_token: {token_data}")
                return None
            oauth["access_token"] = access_token
            _save_oauth(oauth)
            log.info("[YouTube] Access token refrescado.")
            return access_token
        except Exception as e:
            log.error(f"[YouTube] Error refrescando token: {e}")
            return None


def get_access_token() -> Optional[str]:
    oauth = _load_oauth()
    if not oauth:
        log.warning("[YouTube] Sin credenciales OAuth. Completa el flujo /v1/youtube/auth/url primero.")
        return None
    return _refresh_access_token(oauth)


# ── SEO Description builder ────────────────────────────────────────────────────

def _build_seo_description(title: str, niche_id: str = "", tags: Optional[list] = None,
                           affiliate_block: str = "") -> str:
    """
    Genera una descripción optimizada para SEO con:
    - Resumen del tema en primeras 2 líneas (crítico para buscadores)
    - Timestamps de capítulos estimados
    - CTA de suscripción
    - Bloque de afiliados (si se proporciona)
    - Links de branding
    - Hashtags al final (YouTube los extrae automáticamente)
    """
    tags = tags or []
    hashtags = " ".join(f"#{t.replace(' ', '')}" for t in tags[:5]) if tags else "#IA #Tecnologia #DarckRovert"
    lines = [
        f"{title}",
        "",
        "En este video exploramos uno de los temas más fascinantes del momento.",
        "Contenido generado con Gravity AI Bridge — el pipeline de producción autónoma de DarckRovert.",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "📌 CONTENIDO DEL VIDEO",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "00:00 Introducción",
        "00:30 Desarrollo del tema",
        "04:00 Puntos clave",
        "07:00 Conclusión",
        "",
    ]
    # Insertar bloque de afiliados si existe
    if affiliate_block:
        lines.append(affiliate_block)
        lines.append("")
    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🔔 SÍGUENOS",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "▶ Twitch: https://twitch.tv/darckrovert",
        "▶ GitHub: https://github.com/DarckRovert",
        "",
        "⚠️ Este canal sube contenido nuevo cada día.",
        "Suscríbete y activa la campana para no perderte nada.",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        hashtags,
    ]
    return "\n".join(lines)[:4950]


# ── DB helpers ────────────────────────────────────────────────────────────────

def _update_job_youtube(job_id: int, video_id: str, url: str, status: str,
                         seo_description: str = "") -> None:
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        now  = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        conn.execute(
            "UPDATE video_jobs SET youtube_video_id=?, youtube_url=?, uploaded_at=?, upload_status=?, seo_description=? WHERE id=?",
            (video_id, url, now, status, seo_description, job_id),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log.error(f"[YouTube] Error DB job #{job_id}: {e}")


# ── Thumbnail CTR: overlay de texto con FFmpeg ─────────────────────────────────

def _generate_ctr_thumbnail(video_path: str, title: str, output_jpg: str) -> bool:
    """
    Genera un thumbnail de alta CTR:
    - Extrae frame del segundo 3
    - Aplica vignette oscuro en la mitad inferior
    - Superpone el título con texto blanco grande + sombra
    """
    if not os.path.isfile(FFMPEG_EXE) or not os.path.isfile(video_path):
        return False
    safe_title = title.replace("'", "").replace(":", "").replace("%", "")[:45].upper()
    vf = (
        f"drawtext=text='{safe_title}':fontcolor=white:fontsize=54:"
        f"x=(w-text_w)/2:y=h*0.62:fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
        f"shadowcolor=black:shadowx=3:shadowy=3,"
        f"vignette=angle=PI/4:mode=backward"
    )
    cmd = [
        FFMPEG_EXE, "-y",
        "-ss", "3", "-i", video_path,
        "-vframes", "1",
        "-vf", vf,
        "-q:v", "2",
        output_jpg,
    ]
    try:
        import subprocess
        r = subprocess.run(cmd, capture_output=True, timeout=30,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        return r.returncode == 0 and os.path.isfile(output_jpg)
    except Exception as e:
        log.warning(f"[YouTube] CTR thumbnail error: {e}")
        return False


# ── Shorts: clip vertical 9:16 de 58s ────────────────────────────────────────

def generate_shorts_clip(video_path: str, output_path: str, duration: int = 58) -> bool:
    """
    Corta los primeros `duration` segundos del video y los convierte
    a formato vertical 1080x1920 (9:16) para YouTube Shorts.
    """
    if not os.path.isfile(FFMPEG_EXE) or not os.path.isfile(video_path):
        return False
    try:
        import subprocess
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", video_path,
            "-t", str(duration),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k",
            "-ar", "44100", "-ac", "2",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            output_path,
        ]
        r = subprocess.run(cmd, capture_output=True, timeout=120,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        ok = r.returncode == 0 and os.path.isfile(output_path)
        if ok:
            log.info(f"[YouTube] Short generado: {os.path.basename(output_path)}")
        return ok
    except Exception as e:
        log.warning(f"[YouTube] Error generando Short: {e}")
        return False


# ── Upload core ───────────────────────────────────────────────────────────────

def _build_metadata_bytes(title: str, description: str, tags: list,
                           category_id: str, privacy: str) -> bytes:
    meta = {
        "snippet": {
            "title":       title[:100],
            "description": description[:5000],
            "tags":        tags,
            "categoryId":  category_id,
        },
        "status": {"privacyStatus": privacy},
    }
    return json.dumps(meta, ensure_ascii=False).encode("utf-8")


def _resumable_upload(access_token: str, video_path: str, metadata_bytes: bytes) -> Optional[str]:
    """Upload resumable. Sin lock global — cada thread sube independientemente."""
    file_size = os.path.getsize(video_path)
    url_init  = f"{_UPLOAD_URL}?uploadType=resumable&part=snippet,status"
    try:
        # 1. Iniciar sesión resumable
        req_init = urllib.request.Request(
            url_init, data=metadata_bytes,
            headers={
                "Authorization":           f"Bearer {access_token}",
                "Content-Type":            "application/json; charset=UTF-8",
                "X-Upload-Content-Type":   "video/mp4",
                "X-Upload-Content-Length": str(file_size),
            },
            method="POST",
        )
        with urllib.request.urlopen(req_init, timeout=30) as resp:
            upload_url = resp.headers.get("Location")
        if not upload_url:
            log.error("[YouTube] Sin Location URL en respuesta de inicio.")
            return None

        log.info(f"[YouTube] Subiendo {file_size/(1024*1024):.1f} MB...")
        # 2. Enviar archivo
        with open(video_path, "rb") as vf:
            data = vf.read()
        req_upload = urllib.request.Request(
            upload_url, data=data,
            headers={
                "Authorization":  f"Bearer {access_token}",
                "Content-Type":   "video/mp4",
                "Content-Length": str(file_size),
            },
            method="PUT",
        )
        with urllib.request.urlopen(req_upload, timeout=600) as resp:
            result = json.loads(resp.read().decode())
        video_id = result.get("id")
        if video_id:
            log.info(f"[YouTube] Upload OK. ID: {video_id}")
            return video_id
        log.error(f"[YouTube] Upload sin ID: {result}")
        return None

    except urllib.error.HTTPError as e:
        log.error(f"[YouTube] HTTP {e.code}: {e.read().decode(errors='replace')[:400]}")
        return None
    except Exception as e:
        log.error(f"[YouTube] Upload error: {e}")
        return None


def _upload_thumbnail_api(access_token: str, video_id: str, thumb_path: str) -> bool:
    if not os.path.isfile(thumb_path):
        return False
    try:
        with open(thumb_path, "rb") as f:
            data = f.read()
        req = urllib.request.Request(
            f"{_THUMB_URL}?videoId={video_id}", data=data,
            headers={
                "Authorization":  f"Bearer {access_token}",
                "Content-Type":   "image/jpeg",
                "Content-Length": str(len(data)),
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp.read()
        log.info(f"[YouTube] Thumbnail subido para {video_id}.")
        return True
    except Exception as e:
        log.warning(f"[YouTube] Error thumbnail: {e}")
        return False


# ── API Pública ───────────────────────────────────────────────────────────────

def upload_video(
    job_id:      int,
    video_path:  str,
    title:       str,
    thumb_path:  str = "",
    tags:        Optional[list] = None,
    niche_id:    str = "",
    category_id: str = "28",
    privacy:     str = "public",
    upload_short: bool = True,
    lang:        str = "es",
) -> dict:
    """
    Sube el video principal a YouTube.
    - Inyecta bloque de afiliados en la descripción SEO.
    - Registra el upload en revenue_tracker con niche e idioma.
    - Si upload_short=True, genera y sube un Short de 58s automáticamente.
    """
    cfg = _load_config()
    if not cfg.get("enabled", False):
        return {"ok": False, "error": "YouTube deshabilitado en config.yaml", "skipped": True}

    if not _quota_check():
        msg = f"Quota diaria alcanzada ({cfg.get('quota_daily_limit', 5)} uploads/día)."
        log.warning(f"[YouTube] {msg}")
        _update_job_youtube(job_id, "", "", "quota_exceeded")
        return {"ok": False, "error": msg}

    if not os.path.isfile(video_path):
        return {"ok": False, "error": f"Video no encontrado: {video_path}"}

    tags          = tags or cfg.get("tags_base", ["IA", "DarckRovert"])
    category_id   = cfg.get("default_category", category_id)
    privacy       = cfg.get("default_privacy", privacy)

    # Obtener bloque de afiliados para el niche
    affiliate_block = ""
    try:
        from core.affiliate_manager import build_affiliate_block, log_affiliate_injection, get_affiliate_links
        affiliate_block = build_affiliate_block(niche_id)
        aff_links = get_affiliate_links(niche_id)
        if aff_links:
            log_affiliate_injection(job_id, niche_id, aff_links)
    except Exception as _aff_err:
        log.debug(f"[YouTube] Afiliados no disponibles: {_aff_err}")

    seo_desc       = _build_seo_description(title, niche_id, tags, affiliate_block)
    metadata_bytes = _build_metadata_bytes(title, seo_desc, tags, category_id, privacy)

    # Intentar generar thumbnail CTR mejorado
    ctr_thumb = thumb_path
    if os.path.isfile(video_path):
        ctr_out = video_path.replace(".mp4", "_ctr_thumb.jpg")
        if _generate_ctr_thumbnail(video_path, title, ctr_out):
            ctr_thumb = ctr_out

    access_token = get_access_token()
    if not access_token:
        _update_job_youtube(job_id, "", "", "failed")
        return {"ok": False, "error": "Sin access_token válido."}

    # Primer intento
    video_id = _resumable_upload(access_token, video_path, metadata_bytes)
    if not video_id:
        # Retry único: refrescar token y reintentar
        log.info("[YouTube] Reintentando upload con token fresco...")
        access_token = get_access_token()
        if access_token:
            video_id = _resumable_upload(access_token, video_path, metadata_bytes)

    if not video_id:
        _update_job_youtube(job_id, "", "", "failed")
        return {"ok": False, "error": "Upload fallido tras retry."}

    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    _upload_thumbnail_api(access_token, video_id, ctr_thumb)
    _quota_increment()
    _update_job_youtube(job_id, video_id, youtube_url, "uploaded", seo_desc)
    log.info(f"[YouTube] Job #{job_id} publicado: {youtube_url}")

    # Registrar en revenue tracker
    try:
        from core.revenue_tracker import record_upload
        record_upload(job_id=job_id, niche_id=niche_id, is_short=False,
                      platform="youtube", lang=lang, video_id=video_id)
    except Exception as _rev_err:
        log.debug(f"[YouTube] Revenue tracker error: {_rev_err}")

    # Shorts
    shorts_url = ""
    if upload_short and cfg.get("upload_shorts", True):
        shorts_path = video_path.replace(".mp4", "_short.mp4")
        if generate_shorts_clip(video_path, shorts_path):
            short_title = f"#{title[:80]} #Shorts"
            short_meta  = _build_metadata_bytes(
                short_title, f"{title}\n\n#Shorts #IA #DarckRovert",
                tags + ["Shorts"], category_id, privacy
            )
            short_id = _resumable_upload(access_token, shorts_path, short_meta)
            if short_id:
                shorts_url = f"https://www.youtube.com/shorts/{short_id}"
                try:
                    conn = sqlite3.connect(DB_PATH, timeout=10)
                    conn.execute(
                        "UPDATE video_jobs SET shorts_path=?, shorts_video_id=? WHERE id=?",
                        (shorts_path, short_id, job_id)
                    )
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
                _quota_increment()
                log.info(f"[YouTube] Short publicado: {shorts_url}")
                # Registrar Short en revenue tracker
                try:
                    from core.revenue_tracker import record_upload as _rec_up
                    _rec_up(job_id=-(job_id), niche_id=niche_id, is_short=True,
                            platform="youtube", lang=lang, video_id=short_id)
                except Exception:
                    pass

    return {
        "ok":         True,
        "video_id":   video_id,
        "url":        youtube_url,
        "shorts_url": shorts_url,
    }


def upload_job_async(
    job_id:      int,
    video_path:  str,
    title:       str,
    thumb_path:  str = "",
    tags:        Optional[list] = None,
    niche_id:    str = "",
    lang:        str = "es",
) -> None:
    """Lanza el upload en thread daemon. No bloquea el pipeline."""
    def _run():
        log.info(f"[YouTube] Upload async job #{job_id}: {os.path.basename(video_path)}")
        result = upload_video(
            job_id=job_id, video_path=video_path, title=title,
            thumb_path=thumb_path, tags=tags, niche_id=niche_id, lang=lang,
        )
        if result.get("ok"):
            log.info(f"[YouTube] Job #{job_id} → {result['url']}")
            if result.get("shorts_url"):
                log.info(f"[YouTube] Short #{job_id} → {result['shorts_url']}")
        elif result.get("skipped"):
            log.debug(f"[YouTube] Job #{job_id} upload saltado.")
        else:
            log.error(f"[YouTube] Job #{job_id} falló: {result.get('error')}")

    threading.Thread(target=_run, name=f"GravityYTUpload-{job_id}", daemon=True).start()


def get_upload_status(job_id: int) -> dict:
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, title, youtube_video_id, youtube_url, uploaded_at, upload_status, shorts_video_id FROM video_jobs WHERE id=?",
            (job_id,)
        ).fetchone()
        conn.close()
        if not row:
            return {"ok": False, "error": f"Job #{job_id} no encontrado."}
        return {
            "ok":              True,
            "job_id":          row["id"],
            "title":           row["title"],
            "youtube_video_id": row["youtube_video_id"],
            "youtube_url":     row["youtube_url"],
            "uploaded_at":     row["uploaded_at"],
            "upload_status":   row["upload_status"],
            "shorts_video_id": row["shorts_video_id"],
            "shorts_url":      f"https://www.youtube.com/shorts/{row['shorts_video_id']}" if row["shorts_video_id"] else "",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_oauth_auth_url() -> dict:
    oauth     = _load_oauth()
    client_id = oauth.get("client_id", "")
    if not client_id:
        return {"ok": False, "error": "Sin client_id en _integrations/youtube_oauth.json."}
    params = urllib.parse.urlencode({
        "client_id":     client_id,
        "redirect_uri":  "urn:ietf:wg:oauth:2.0:oob",
        "response_type": "code",
        "scope":         _SCOPE,
        "access_type":   "offline",
        "prompt":        "consent",
    })
    return {
        "ok":           True,
        "auth_url":     f"{_AUTH_URL}?{params}",
        "instructions": "1. Visita auth_url. 2. Aprueba. 3. Copia el código. 4. POST /v1/youtube/auth/exchange {\"code\":\"...\"}",
    }


def exchange_auth_code(code: str) -> dict:
    oauth         = _load_oauth()
    client_id     = oauth.get("client_id", "")
    client_secret = oauth.get("client_secret", "")
    if not all([client_id, client_secret]):
        return {"ok": False, "error": "Faltan client_id / client_secret."}
    payload = urllib.parse.urlencode({
        "client_id":     client_id,
        "client_secret": client_secret,
        "code":          code.strip(),
        "redirect_uri":  "http://localhost",
        "grant_type":    "authorization_code",
    }).encode()
    try:
        req = urllib.request.Request(
            _TOKEN_URL, data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            td = json.loads(resp.read().decode())
        rt = td.get("refresh_token")
        if not rt:
            return {"ok": False, "error": f"Sin refresh_token en respuesta: {td}"}
        oauth["refresh_token"] = rt
        oauth["access_token"]  = td.get("access_token", "")
        _save_oauth(oauth)
        log.info("[YouTube] OAuth completado. Refresh token persistido.")
        return {"ok": True, "message": "Autenticación completada. El sistema puede subir videos de forma autónoma."}
    except Exception as e:
        return {"ok": False, "error": str(e)}
