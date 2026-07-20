"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — TIKTOK LIVE INTELLIGENCE SUITE (GTLIS) V2.0                   ║
║  Módulo de OSINT White-Hat para monitoreo de canales TikTok en vivo         ║
║                                                                              ║
║  Capacidades:                                                                ║
║    [1] LiveStreamProbe   — Extrae metadata técnica del stream activo         ║
║    [2] ProfileIntelligence — OSINT pasivo del perfil público                 ║
║    [3] NetworkRecon      — CDN fingerprinting y geo-origin estimation         ║
║    [4] BotDetectionEngine — Análisis estadístico de patrones de bots         ║
║    [5] GeoIntelligenceEngine — Inteligencia geográfica máxima (legal)        ║
║        5a. StreamInfraMapper  — Mapeo completo de IPs/nodos CDN              ║
║        5b. StreamerGeoProfiler — Triangulación de ubicación del streamer      ║
║        5c. CommentGeoAnalyzer — Distribución geográfica de audiencia          ║
║        5d. DNSChainMapper    — DNS completo con geo de cada IP               ║
║                                                                              ║
║  LÍMITE TÉCNICO HONESTO: Las IPs de viewers individuales NO son accesibles  ║
║  por ninguna vía legal. Este módulo extrae el máximo posible dentro de la ley║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import os
import sys
import json
import time
import socket
import hashlib
import subprocess
import threading
import urllib.request
import urllib.parse
import urllib.error
import ssl
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from collections import Counter, deque
from dataclasses import dataclass, field, asdict

# ── Path bootstrap ─────────────────────────────────────────────────────────────
_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR = os.path.dirname(_TOOL_DIR)
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

from tools.base_tool import Tool, ToolResult
from core.logger import log

# ── Geo Intelligence Engine (Módulo 5 — v2.0) ─────────────────────────────────
try:
    from tools.tiktok_geo_intelligence import GeoIntelligenceEngine
    _GEO_AVAILABLE = True
except ImportError:
    _GEO_AVAILABLE = False
    GeoIntelligenceEngine = None  # type: ignore

# ── Constants ──────────────────────────────────────────────────────────────────
FFMPEG_DIR = os.path.join(_BASE_DIR, "ffmpeg-master-latest-win64-gpl", "bin")
FFPROBE_EXE = os.path.join(FFMPEG_DIR, "ffprobe.exe")
SCRATCH_DIR = os.path.join(_BASE_DIR, "scratch", "tiktok_osint")
os.makedirs(SCRATCH_DIR, exist_ok=True)

# TikTok URL patterns for public live streams
TIKTOK_LIVE_URL_PATTERNS = [
    "https://www.tiktok.com/@{username}/live",
    "https://www.tiktok.com/live/@{username}",
]

# Known CDN providers mapped by hostname patterns
CDN_FINGERPRINTS: Dict[str, str] = {
    "akamai":       "Akamai",
    "akamaitechnologies": "Akamai",
    "cloudfront":   "AWS CloudFront",
    "fastly":       "Fastly",
    "cloudflare":   "Cloudflare",
    "bytedance":    "ByteDance CDN",
    "tiktokcdn":    "TikTok CDN (ByteDance)",
    "muscdn":       "TikTok CDN (MusCDN)",
    "pull-rtmp":    "TikTok RTMP",
    "pull-flv":     "TikTok FLV",
    "pull-hls":     "TikTok HLS",
    "llnwd":        "Limelight Networks",
    "edgekey":      "Akamai EdgeKey",
    "edgesuite":    "Akamai EdgeSuite",
    "googleusercontent": "Google Cloud CDN",
    "gcdn":         "G-Core Labs",
}

# HTTP request headers that mimic a real browser (white-hat, public data only)
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── Data Models ────────────────────────────────────────────────────────────────


@dataclass
class LiveSnapshot:
    """Snapshot completo de un canal en un instante."""
    username: str
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_live: bool = False
    viewers: int = 0
    title: str = ""
    stream_url: str = ""
    room_id: str = ""
    user_id: str = ""
    codec_video: str = ""
    codec_audio: str = ""
    bitrate_kbps: int = 0
    resolution: str = ""
    fps: float = 0.0
    cdn_provider: str = "unknown"
    cdn_ip: str = ""
    geo_country: str = ""
    geo_city: str = ""
    bot_score: float = 0.0
    engagement: float = 0.0
    raw_meta: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["is_live"] = 1 if self.is_live else 0
        return d


@dataclass
class ProfileReport:
    """Informe OSINT de un perfil público de TikTok."""
    username: str
    display_name: str = ""
    bio: str = ""
    followers: int = 0
    following: int = 0
    likes_total: int = 0
    video_count: int = 0
    verified: bool = False
    profile_pic_url: str = ""
    live_schedule_guess: List[str] = field(default_factory=list)
    cross_platform: Dict[str, str] = field(default_factory=dict)
    top_hashtags: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class NetworkFingerprint:
    """Resultado del reconocimiento de red del stream."""
    stream_url: str
    cdn_provider: str = "unknown"
    cdn_ip: str = ""
    cdn_hostname: str = ""
    geo_country: str = ""
    geo_city: str = ""
    tls_version: str = ""
    hls_variants: List[Dict[str, Any]] = field(default_factory=list)
    response_headers: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None


# ── Module 1: LiveStreamProbe ──────────────────────────────────────────────────


class LiveStreamProbe:
    """
    Técnica white-hat: Extrae metadata pública de streams TikTok Live.
    Usa yt-dlp (modo --skip-download) + ffprobe para análisis técnico.
    """

    def __init__(self) -> None:
        self._ytdlp_lock = threading.Lock()

    def fetch_live_metadata(self, username: str) -> LiveSnapshot:
        """
        Extrae metadata técnica de un canal en vivo.
        Retorna LiveSnapshot con todos los campos disponibles.
        """
        snap = LiveSnapshot(username=username)
        url = f"https://www.tiktok.com/@{username.lstrip('@')}/live"

        try:
            info = self._run_ytdlp(url)
            if not info:
                snap.error = "yt-dlp no pudo extraer metadata (canal offline o privado)"
                snap.raw_meta["error"] = snap.error
                return snap

            snap.is_live = info.get("is_live", False) or info.get("was_live", False)
            snap.title = info.get("title", "") or info.get("fulltitle", "")
            snap.viewers = info.get("concurrent_view_count") or info.get("view_count") or 0
            snap.room_id = info.get("id", "") or info.get("display_id", "")
            snap.user_id = info.get("uploader_id", "") or info.get("channel_id", "")
            snap.raw_meta = {
                k: v for k, v in info.items()
                if k in (
                    "id", "title", "uploader", "upload_date", "duration",
                    "thumbnail", "concurrent_view_count", "view_count",
                    "like_count", "comment_count", "formats", "tags",
                    "description", "webpage_url", "extractor",
                    "display_id", "uploader_id", "creator"
                )
            }

            # Extraer URL del stream HLS/RTMP para análisis técnico
            best_url = self._extract_best_stream_url(info)
            if best_url:
                snap.stream_url = best_url
                try:
                    from urllib.parse import urlparse
                    import socket
                    import json
                    hostname = urlparse(best_url).hostname
                    if hostname:
                        snap.cdn_provider = hostname
                        try:
                            ip = socket.gethostbyname(hostname)
                            snap.cdn_ip = ip
                            # Fast inline GeoIP using free ipinfo API
                            req = urllib.request.Request(
                                f"https://ipinfo.io/{ip}/json",
                                headers={"User-Agent": "curl/7.68.0"}
                            )
                            with urllib.request.urlopen(req, timeout=3.0) as res:
                                geo_data = json.loads(res.read().decode())
                                snap.geo_country = geo_data.get("country", "")
                                snap.geo_city = geo_data.get("city", "")
                        except Exception as e:
                            log.debug(f"[GTLIS·Probe] GeoIP lookup failed: {e}")
                except Exception:
                    pass
                
                tech = self.probe_stream_tech(best_url)
                snap.codec_video = tech.get("codec_video", "")
                snap.codec_audio = tech.get("codec_audio", "")
                snap.bitrate_kbps = tech.get("bitrate_kbps", 0)
                snap.resolution = tech.get("resolution", "")
                snap.fps = tech.get("fps", 0.0)

            # Calcular engagement básico
            if snap.viewers > 0:
                likes = info.get("like_count") or 0
                comments = info.get("comment_count") or 0
                snap.engagement = round(((likes + comments) / snap.viewers) * 100, 2)
                
                # Heurística de Bot Score basada en el stream
                b_score = 0.0
                if snap.engagement < 0.5: b_score += 0.3
                elif snap.engagement < 1.0: b_score += 0.15
                
                if snap.viewers > 1000 and snap.engagement < 0.1: b_score += 0.4
                if not snap.title: b_score += 0.2
                if snap.cdn_provider == "unknown": b_score += 0.1
                
                snap.bot_score = min(b_score, 1.0)

            log.info(f"[GTLIS·Probe] @{username} — live={snap.is_live}, viewers={snap.viewers}")

        except Exception as exc:
            snap.error = str(exc)
            snap.raw_meta["error"] = snap.error
            log.error(f"[GTLIS·Probe] Error analizando @{username}: {exc}")

        return snap

    def _run_ytdlp(self, url: str) -> Optional[Dict[str, Any]]:
        """Ejecuta yt-dlp en subproceso y retorna el JSON de info."""
        with self._ytdlp_lock:
            import random
            uas = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36"
            ]
            cmd = [
                sys.executable, "-m", "yt_dlp",
                "--dump-json",
                "--skip-download",
                "--no-playlist",
                "--quiet",
                "--no-warnings",
                "--user-agent", random.choice(uas)
            ]
            
            # Proxy Config (Rotativo si existe variable de entorno)
            proxy = os.environ.get("GTLIS_PROXY")
            if proxy:
                cmd.extend(["--proxy", proxy])
                
            cookies_path = os.path.join(_BASE_DIR, "cookies.txt")
            if os.path.exists(cookies_path):
                cmd.extend(["--cookies", cookies_path])
                
            cmd.append(url)

            try:
                # Timeout reducido a 15s para failover rápido
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=15,
                    cwd=_BASE_DIR,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return json.loads(result.stdout.strip())
                if result.stderr:
                    log.debug(f"[GTLIS·yt-dlp] stderr: {result.stderr[:300]}")
            except subprocess.TimeoutExpired:
                log.warning("[GTLIS·yt-dlp] Timeout al consultar stream")
            except json.JSONDecodeError as e:
                log.warning(f"[GTLIS·yt-dlp] JSON decode error: {e}")
            except Exception as e:
                log.error(f"[GTLIS·yt-dlp] Error inesperado: {e}")
        return None

    def _extract_best_stream_url(self, info: Dict[str, Any]) -> str:
        """Selecciona la mejor URL de stream de los formatos disponibles."""
        formats = info.get("formats") or []
        # Prefer HLS over RTMP — HLS is easier to probe passively
        hls_formats = [
            f for f in formats
            if f.get("protocol", "") in ("m3u8", "m3u8_native")
            and f.get("url")
        ]
        if hls_formats:
            # Pick highest resolution
            hls_formats.sort(key=lambda f: f.get("height") or 0, reverse=True)
            return hls_formats[0]["url"]

        # Fallback: any URL available
        for f in formats:
            if f.get("url"):
                return f["url"]

        return info.get("url", "")

    def probe_stream_tech(self, stream_url: str) -> Dict[str, Any]:
        """
        Usa ffprobe para extraer parámetros técnicos del stream.
        100% pasivo — solo lee, no modifica nada.
        """
        result: Dict[str, Any] = {
            "codec_video": "",
            "codec_audio": "",
            "bitrate_kbps": 0,
            "resolution": "",
            "fps": 0.0,
        }

        ffprobe = FFPROBE_EXE if os.path.isfile(FFPROBE_EXE) else "ffprobe"

        try:
            cmd = [
                ffprobe,
                "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                "-show_format",
                "-analyzeduration", "5000000",  # 5s max
                "-probesize", "5000000",
                stream_url,
            ]
            out = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
            )
            if out.returncode == 0 and out.stdout:
                data = json.loads(out.stdout)
                streams = data.get("streams", [])
                fmt = data.get("format", {})

                for s in streams:
                    if s.get("codec_type") == "video" and not result["codec_video"]:
                        result["codec_video"] = s.get("codec_name", "")
                        w = s.get("width", 0)
                        h = s.get("height", 0)
                        if w and h:
                            result["resolution"] = f"{w}x{h}"
                        # Parse FPS (may be fraction "30000/1001")
                        fps_str = s.get("r_frame_rate", "0/1")
                        try:
                            num, den = fps_str.split("/")
                            result["fps"] = round(int(num) / max(int(den), 1), 2)
                        except Exception:
                            pass
                    elif s.get("codec_type") == "audio" and not result["codec_audio"]:
                        result["codec_audio"] = s.get("codec_name", "")

                # Bitrate from format
                br = fmt.get("bit_rate")
                if br:
                    result["bitrate_kbps"] = int(int(br) / 1000)

        except subprocess.TimeoutExpired:
            log.warning("[GTLIS·ffprobe] Timeout — stream no accesible en tiempo")
        except Exception as exc:
            log.warning(f"[GTLIS·ffprobe] Error: {exc}")

        return result

    def analyze_engagement(self, info: Dict[str, Any]) -> float:
        """Calcula engagement ratio desde la metadata cruda de yt-dlp."""
        viewers = info.get("concurrent_view_count") or info.get("view_count") or 0
        if viewers == 0:
            return 0.0
        likes = info.get("like_count") or 0
        comments = info.get("comment_count") or 0
        return round(((likes + comments) / viewers) * 100, 2)


# ── Module 2: ProfileIntelligence ─────────────────────────────────────────────


class ProfileIntelligence:
    """
    Técnica white-hat: Scraping pasivo de perfiles públicos de TikTok.
    Solo accede a páginas públicamente accesibles sin autenticación.
    """

    # Regex para extraer datos del JSON embebido en el HTML del perfil público
    _RE_SIGI_STATE = re.compile(
        r'<script[^>]+id="SIGI_STATE"[^>]*>(.*?)</script>', re.DOTALL
    )
    _RE_SCRIPT_DATA = re.compile(
        r'"UserPage":\s*\{[^}]+"userInfo":\s*\{(.*?)\}', re.DOTALL
    )

    def get_public_profile(self, username: str) -> ProfileReport:
        """
        Extrae datos públicos del perfil de un usuario TikTok.
        Emula un navegador normal — datos públicos sin autenticación.
        """
        report = ProfileReport(username=username)
        url = f"https://www.tiktok.com/@{username.lstrip('@')}"

        try:
            req = urllib.request.Request(url, headers=_BROWSER_HEADERS)
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")

            # Intentar extraer JSON embebido (SIGI_STATE — datos públicos del perfil)
            data = self._parse_sigi_state(html)
            if data:
                user = data.get("UserModule", {}).get("users", {})
                stats = data.get("UserModule", {}).get("stats", {})

                # El username puede variar en casing
                user_key = username.lstrip("@").lower()
                user_info = None
                for k, v in user.items():
                    if k.lower() == user_key:
                        user_info = v
                        break
                if not user_info and user:
                    user_info = next(iter(user.values()))

                if user_info:
                    report.display_name = user_info.get("nickname", "")
                    report.bio = user_info.get("signature", "")
                    report.verified = bool(user_info.get("verified", False))
                    report.profile_pic_url = user_info.get("avatarLarger", "")

                stat_key = username.lstrip("@").lower()
                stat_info = None
                for k, v in stats.items():
                    if k.lower() == stat_key:
                        stat_info = v
                        break
                if not stat_info and stats:
                    stat_info = next(iter(stats.values()))

                if stat_info:
                    report.followers = stat_info.get("followerCount", 0)
                    report.following = stat_info.get("followingCount", 0)
                    report.likes_total = stat_info.get("heartCount", 0)
                    report.video_count = stat_info.get("videoCount", 0)

                log.info(
                    f"[GTLIS·Profile] @{username} — "
                    f"followers={report.followers:,}, verified={report.verified}"
                )
            else:
                # Fallback: extraer metadata básica de og: tags del HTML
                report = self._extract_og_fallback(html, report)

        except urllib.error.HTTPError as e:
            report.error = f"HTTP {e.code}: {e.reason}"
            log.warning(f"[GTLIS·Profile] HTTP error para @{username}: {e.code}")
        except Exception as exc:
            report.error = str(exc)
            log.error(f"[GTLIS·Profile] Error OSINT @{username}: {exc}")

        return report

    def _parse_sigi_state(self, html: str) -> Optional[Dict[str, Any]]:
        """Extrae y parsea el JSON SIGI_STATE embebido en el HTML del perfil."""
        m = self._RE_SIGI_STATE.search(html)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass

        # Fallback: buscar __NEXT_DATA__ (variante de Next.js)
        m2 = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if m2:
            try:
                return json.loads(m2.group(1))
            except json.JSONDecodeError:
                pass
        return None

    def _extract_og_fallback(self, html: str, report: ProfileReport) -> ProfileReport:
        """Fallback: extrae datos de Open Graph meta tags."""
        og_title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        og_desc = re.search(r'<meta property="og:description" content="([^"]+)"', html)
        og_image = re.search(r'<meta property="og:image" content="([^"]+)"', html)

        if og_title:
            report.display_name = og_title.group(1).split("(@")[0].strip()
        if og_desc:
            report.bio = og_desc.group(1)
        if og_image:
            report.profile_pic_url = og_image.group(1)
        return report

    def history_fingerprint(self, snapshots: List[Dict[str, Any]]) -> List[str]:
        """
        Analiza snapshots históricos para detectar patrones de horario de streaming.
        Retorna lista de horas habituales de live (ej: ["20:00 UTC", "22:00 UTC"]).
        """
        if not snapshots:
            return []

        live_hours = []
        for snap in snapshots:
            if snap.get("is_live"):
                try:
                    dt = datetime.fromisoformat(snap["ts"].replace("Z", "+00:00"))
                    live_hours.append(dt.hour)
                except Exception:
                    pass

        if not live_hours:
            return []

        # Encontrar horas más frecuentes (top 3)
        counter = Counter(live_hours)
        top = counter.most_common(3)
        return [f"{h:02d}:00 UTC (×{count})" for h, count in top]

    def cross_platform_check(self, username: str) -> Dict[str, str]:
        """
        Búsqueda pasiva del mismo handle en otras plataformas.
        Solo verifica si la URL responde con HTTP 200 (existencia pública).
        """
        clean = username.lstrip("@")
        platforms = {
            "YouTube": f"https://www.youtube.com/@{clean}",
            "Instagram": f"https://www.instagram.com/{clean}/",
            "Twitch": f"https://www.twitch.tv/{clean}",
            "Twitter/X": f"https://x.com/{clean}",
        }
        found: Dict[str, str] = {}
        for platform, url in platforms.items():
            try:
                req = urllib.request.Request(url, headers=_BROWSER_HEADERS, method="HEAD")
                ctx = ssl.create_default_context()
                with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                    if resp.status == 200:
                        found[platform] = url
            except Exception:
                pass  # No responde = no encontrado o bloqueado
        return found


# ── Module 3: NetworkRecon ────────────────────────────────────────────────────


class NetworkRecon:
    """
    Técnica white-hat: Reconocimiento pasivo de la infraestructura de red del stream.
    Analiza headers HTTP públicos, registros DNS y manifests HLS.
    """

    def trace_cdn_path(self, stream_url: str) -> NetworkFingerprint:
        """
        Identifica el proveedor CDN analizando headers HTTP y DNS del stream URL.
        100% pasivo — equivalente a hacer un GET/HEAD normal al URL público.
        """
        fp = NetworkFingerprint(stream_url=stream_url)

        try:
            parsed = urllib.parse.urlparse(stream_url)
            hostname = parsed.hostname or ""

            # DNS resolution para obtener IP
            try:
                fp.cdn_ip = socket.gethostbyname(hostname)
                fp.cdn_hostname = hostname
            except socket.gaierror:
                pass

            # HTTP HEAD request para obtener headers del CDN
            req = urllib.request.Request(
                stream_url,
                headers={**_BROWSER_HEADERS, "Range": "bytes=0-0"},
                method="HEAD",
            )
            ctx = ssl.create_default_context()
            try:
                with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                    headers = dict(resp.headers)
                    fp.response_headers = {k.lower(): v for k, v in headers.items()}

                    # TLS version
                    if hasattr(resp, "fp") and hasattr(resp.fp, "_sock"):
                        try:
                            tls = resp.fp._sock.version()
                            fp.tls_version = tls or ""
                        except Exception:
                            pass
            except Exception:
                pass

            # CDN fingerprinting desde hostname y headers
            fp.cdn_provider = self._identify_cdn(hostname, fp.response_headers)

            # Geo-lookup de la IP (ipinfo.io — API pública, sin key para datos básicos)
            if fp.cdn_ip:
                geo = self._geoip_lookup(fp.cdn_ip)
                fp.geo_country = geo.get("country", "")
                fp.geo_city = geo.get("city", "")

            log.info(
                f"[GTLIS·Recon] CDN={fp.cdn_provider}, IP={fp.cdn_ip}, "
                f"Geo={fp.geo_city},{fp.geo_country}"
            )

        except Exception as exc:
            fp.error = str(exc)
            log.warning(f"[GTLIS·Recon] Error en NetworkRecon: {exc}")

        return fp

    def _identify_cdn(self, hostname: str, headers: Dict[str, str]) -> str:
        """Identifica el CDN por hostname y headers de respuesta."""
        combined = (
            hostname.lower()
            + headers.get("server", "").lower()
            + headers.get("via", "").lower()
            + headers.get("x-cache", "").lower()
            + headers.get("x-served-by", "").lower()
        )
        for pattern, name in CDN_FINGERPRINTS.items():
            if pattern in combined:
                return name
        return "Unknown CDN"

    def _geoip_lookup(self, ip: str) -> Dict[str, str]:
        """Lookup geográfico de IP usando la API pública de ipinfo.io."""
        try:
            url = f"https://ipinfo.io/{ip}/json"
            req = urllib.request.Request(url, headers=_BROWSER_HEADERS)
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                return {
                    "country": data.get("country", ""),
                    "city": data.get("city", ""),
                    "org": data.get("org", ""),
                    "region": data.get("region", ""),
                }
        except Exception:
            return {}

    def extract_hls_variants(self, m3u8_url: str) -> List[Dict[str, Any]]:
        """
        Parsea un manifest HLS maestro para listar todas las calidades disponibles.
        Técnica: lectura pasiva del archivo de playlist público.
        """
        variants: List[Dict[str, Any]] = []
        try:
            req = urllib.request.Request(m3u8_url, headers=_BROWSER_HEADERS)
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                content = resp.read().decode("utf-8", errors="replace")

            current: Dict[str, Any] = {}
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("#EXT-X-STREAM-INF"):
                    # Parse attributes: BANDWIDTH, RESOLUTION, CODECS, FRAME-RATE
                    for attr in ("BANDWIDTH", "RESOLUTION", "CODECS", "FRAME-RATE", "NAME"):
                        m = re.search(rf'{attr}=([^,\n]+)', line)
                        if m:
                            current[attr.lower().replace("-", "_")] = m.group(1).strip('"')
                elif line and not line.startswith("#") and current:
                    current["url"] = (
                        line if line.startswith("http")
                        else urllib.parse.urljoin(m3u8_url, line)
                    )
                    if "bandwidth" in current:
                        try:
                            current["bandwidth_kbps"] = int(int(current["bandwidth"]) / 1000)
                        except Exception:
                            pass
                    variants.append(current)
                    current = {}

        except Exception as exc:
            log.warning(f"[GTLIS·HLS] Error parseando manifest: {exc}")

        return variants


# ── Module 4: BotDetectionEngine ──────────────────────────────────────────────


class BotDetectionEngine:
    """
    Técnica white-hat: Análisis estadístico para detectar actividad de bots.
    Opera sobre datos de comentarios PÚBLICOS — análisis local, no invasivo.
    """

    # Patrones de texto de bots comunes en TikTok Live
    _BOT_TEXT_PATTERNS = [
        re.compile(r"follow\s+me", re.IGNORECASE),
        re.compile(r"f4f\b", re.IGNORECASE),
        re.compile(r"(auto|robot|bot)\s*(like|comment|follow)", re.IGNORECASE),
        re.compile(r"(compra|buy|order)\s*(followers|likes|views)", re.IGNORECASE),
        re.compile(r"(\d{3,})\s*(followers|seguidores)", re.IGNORECASE),
        re.compile(r"(check|visit)\s*(my|mi)\s*(profile|perfil|bio|link)", re.IGNORECASE),
    ]

    def analyze_comment_feed(
        self,
        comments: List[Dict[str, Any]],
        window_seconds: int = 60
    ) -> Dict[str, Any]:
        """
        Analiza una muestra de comentarios para detectar patrones de bots.
        
        Args:
            comments: Lista de dicts con keys: user_id, text, timestamp_ms
            window_seconds: Ventana temporal para analizar velocidad
            
        Returns:
            dict con bot_score (0.0-1.0) y detalle de señales detectadas
        """
        if not comments:
            return {"bot_score": 0.0, "signals": [], "total_analyzed": 0}

        signals = []
        score = 0.0

        # — Signal 1: Velocity check (comentarios por minuto por usuario) —
        user_comment_times: Dict[str, List[float]] = {}
        for c in comments:
            uid = str(c.get("user_id", ""))
            ts = float(c.get("timestamp_ms", 0)) / 1000.0
            user_comment_times.setdefault(uid, []).append(ts)

        high_velocity_users = []
        for uid, times in user_comment_times.items():
            if len(times) < 2:
                continue
            times.sort()
            span = times[-1] - times[0]
            if span > 0:
                rate = len(times) / (span / 60.0)  # comments/min
                if rate > 20:
                    high_velocity_users.append((uid, rate))

        if high_velocity_users:
            velocity_score = min(len(high_velocity_users) / max(len(user_comment_times), 1), 1.0)
            score += velocity_score * 0.35
            signals.append({
                "type": "high_velocity",
                "severity": "warning" if velocity_score < 0.5 else "critical",
                "detail": f"{len(high_velocity_users)} usuario(s) con >20 comentarios/min",
                "contribution": round(velocity_score * 0.35, 3),
            })

        # — Signal 2: Text repetition ratio —
        all_texts = [str(c.get("text", "")).strip().lower() for c in comments]
        unique_texts = set(all_texts)
        if len(all_texts) > 5:
            repetition_ratio = 1.0 - (len(unique_texts) / len(all_texts))
            if repetition_ratio > 0.4:
                score += repetition_ratio * 0.25
                signals.append({
                    "type": "text_repetition",
                    "severity": "warning" if repetition_ratio < 0.7 else "critical",
                    "detail": f"{repetition_ratio:.0%} de comentarios son texto repetido",
                    "contribution": round(repetition_ratio * 0.25, 3),
                })

        # — Signal 3: Bot text pattern matching —
        bot_text_count = sum(
            1 for text in all_texts
            if any(p.search(text) for p in self._BOT_TEXT_PATTERNS)
        )
        if bot_text_count > 0:
            pattern_ratio = bot_text_count / len(all_texts)
            score += pattern_ratio * 0.25
            signals.append({
                "type": "bot_text_pattern",
                "severity": "warning",
                "detail": f"{bot_text_count} comentarios con patrones de bot (spam/promo/f4f)",
                "contribution": round(pattern_ratio * 0.25, 3),
            })

        # — Signal 4: Timestamp clustering (bots comentan en intervalos exactos) —
        timestamps = sorted(
            float(c.get("timestamp_ms", 0)) / 1000.0
            for c in comments
            if c.get("timestamp_ms")
        )
        if len(timestamps) > 10:
            intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            if intervals:
                mean_interval = sum(intervals) / len(intervals)
                near_exact = sum(1 for iv in intervals if abs(iv - mean_interval) < 0.15)
                cluster_ratio = near_exact / len(intervals)
                if cluster_ratio > 0.6:
                    score += cluster_ratio * 0.15
                    signals.append({
                        "type": "timestamp_clustering",
                        "severity": "warning",
                        "detail": f"{cluster_ratio:.0%} de intervalos son casi idénticos (±150ms)",
                        "contribution": round(cluster_ratio * 0.15, 3),
                    })

        bot_score = round(min(score, 1.0), 3)

        return {
            "bot_score": bot_score,
            "risk_level": (
                "critical" if bot_score >= 0.7
                else "high" if bot_score >= 0.4
                else "medium" if bot_score >= 0.2
                else "low"
            ),
            "signals": signals,
            "total_analyzed": len(comments),
            "unique_users": len(user_comment_times),
        }

    def quick_score(self, viewers: int, follower_ratio: float, account_age_days: int) -> float:
        """
        Score rápido de bot basado solo en métricas del canal (sin análisis de comentarios).
        Útil cuando no se tienen datos de chat.
        """
        score = 0.0

        # Ratio following/followers anormalmente alto
        if follower_ratio > 50:
            score += 0.3
        elif follower_ratio > 10:
            score += 0.15

        # Cuenta muy nueva con muchos viewers
        if account_age_days < 30 and viewers > 1000:
            score += 0.4
        elif account_age_days < 90 and viewers > 5000:
            score += 0.2

        return round(min(score, 1.0), 3)


# ── Main Tool Class ────────────────────────────────────────────────────────────


class TikTokLiveMonitor(Tool):
    """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║  GTLIS — TikTok Live Intelligence Suite Tool                            ║
    ║  Herramienta principal de OSINT white-hat para Gravity AI              ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    
    Registrada en el ToolEngine de Gravity. Puede ser invocada por el LLM
    o directamente por el TikTokRadar daemon.
    """

    name = "tiktok_live_monitor"
    description = (
        "Monitoreo OSINT white-hat de canales TikTok Live. "
        "Extrae metadata técnica del stream, perfil público, "
        "CDN fingerprinting y detección estadística de bots."
    )
    requires_confirmation = False

    def __init__(self) -> None:
        self._probe = LiveStreamProbe()
        self._profile = ProfileIntelligence()
        self._recon = NetworkRecon()
        self._bot_engine = BotDetectionEngine()
        self._geo = GeoIntelligenceEngine() if _GEO_AVAILABLE else None

    def execute(self, **kwargs: Any) -> ToolResult:
        """
        Punto de entrada universal para el ToolEngine de Gravity.
        
        Args:
            action (str): Acción a ejecutar — "probe" | "profile" | "recon" | "full"
            username (str): Handle TikTok sin @ (ej: "charlidamelio")
            stream_url (str, opt): URL HLS para recon directo
            comments (list, opt): Lista de comentarios para bot detection
            
        Returns:
            ToolResult con JSON serializado del resultado
        """
        action = kwargs.get("action", "full")
        username = kwargs.get("username", "")
        stream_url = kwargs.get("stream_url", "")
        comments = kwargs.get("comments", [])
        bio = kwargs.get("bio", "")
        live_title = kwargs.get("live_title", "")
        live_history = kwargs.get("live_history", [])

        if not username and not stream_url:
            return ToolResult(
                success=False,
                stderr="Se requiere 'username' o 'stream_url'",
                exit_code=1,
            )

        try:
            result: Dict[str, Any] = {
                "action": action,
                "username": username,
                "ts": datetime.now(timezone.utc).isoformat(),
            }

            if action in ("probe", "full"):
                if username:
                    snap = self._probe.fetch_live_metadata(username)
                    result["live_snapshot"] = snap.to_dict()

            if action in ("profile", "full") and username:
                prof = self._profile.get_public_profile(username)
                result["profile"] = {
                    "display_name": prof.display_name,
                    "bio": prof.bio,
                    "followers": prof.followers,
                    "following": prof.following,
                    "likes_total": prof.likes_total,
                    "video_count": prof.video_count,
                    "verified": prof.verified,
                    "error": prof.error,
                }
                if action == "full":
                    cross = self._profile.cross_platform_check(username)
                    result["profile"]["cross_platform"] = cross

            if action in ("recon", "full"):
                target_url = stream_url
                if not target_url and action == "full":
                    snap_data = result.get("live_snapshot", {})
                    target_url = snap_data.get("stream_url", "")
                if target_url:
                    fp = self._recon.trace_cdn_path(target_url)
                    result["network"] = {
                        "cdn_provider": fp.cdn_provider,
                        "cdn_ip": fp.cdn_ip,
                        "cdn_hostname": fp.cdn_hostname,
                        "geo_country": fp.geo_country,
                        "geo_city": fp.geo_city,
                        "tls_version": fp.tls_version,
                        "response_headers": dict(list(fp.response_headers.items())[:10]),
                        "hls_variants": self._recon.extract_hls_variants(target_url)
                        if target_url.endswith(".m3u8") else [],
                        "error": fp.error,
                    }

            if action in ("bot", "full") and comments:
                bot_result = self._bot_engine.analyze_comment_feed(comments)
                result["bot_detection"] = bot_result

            # ── Acción 'geo': inteligencia geográfica máxima ──────────────────
            if action in ("geo", "full"):
                if self._geo is None:
                    result["geo_intelligence"] = {"error": "GeoIntelligenceEngine no disponible"}
                else:
                    # Obtener datos disponibles de pasos anteriores
                    _stream_url = stream_url
                    _bio = bio
                    _title = live_title
                    if not _stream_url:
                        snap_data = result.get("live_snapshot", {})
                        _stream_url = snap_data.get("stream_url", "")
                    if not _bio or not _title:
                        prof_data = result.get("profile", {})
                        _bio = _bio or prof_data.get("bio", "")
                        _title = _title or result.get("live_snapshot", {}).get("title", "")

                    geo_report = self._geo.full_geo_report(
                        username=username,
                        stream_url=_stream_url,
                        bio=_bio,
                        live_title=_title,
                        comments=comments or None,
                        live_history=live_history or None,
                    )
                    result["geo_intelligence"] = geo_report

            output = json.dumps(result, ensure_ascii=False, indent=2)
            return ToolResult(success=True, stdout=output, data=result)

        except Exception as exc:
            log.error(f"[GTLIS] Error en execute({action}, {username}): {exc}")
            return ToolResult(
                success=False,
                stderr=str(exc),
                exit_code=1,
            )

    def probe(self, username: str) -> LiveSnapshot:
        """Shorthand para LiveStreamProbe.fetch_live_metadata."""
        return self._probe.fetch_live_metadata(username)

    def profile(self, username: str) -> ProfileReport:
        """Shorthand para ProfileIntelligence.get_public_profile."""
        return self._profile.get_public_profile(username)

    def recon(self, stream_url: str) -> NetworkFingerprint:
        """Shorthand para NetworkRecon.trace_cdn_path."""
        return self._recon.trace_cdn_path(stream_url)

    def bot_check(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Shorthand para BotDetectionEngine.analyze_comment_feed."""
        return self._bot_engine.analyze_comment_feed(comments)

    def geo_intel(
        self,
        username: str,
        stream_url: str = "",
        bio: str = "",
        live_title: str = "",
        comments: Optional[List[Dict]] = None,
        live_history: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Shorthand para GeoIntelligenceEngine.full_geo_report."""
        if self._geo is None:
            return {"error": "GeoIntelligenceEngine no disponible"}
        return self._geo.full_geo_report(
            username=username,
            stream_url=stream_url,
            bio=bio,
            live_title=live_title,
            comments=comments,
            live_history=live_history,
        )


# ── Module-level singleton ─────────────────────────────────────────────────────
_monitor_instance: Optional[TikTokLiveMonitor] = None
_monitor_lock = threading.Lock()


def get_monitor() -> TikTokLiveMonitor:
    """Retorna el singleton del monitor (thread-safe)."""
    global _monitor_instance
    if _monitor_instance is None:
        with _monitor_lock:
            if _monitor_instance is None:
                _monitor_instance = TikTokLiveMonitor()
    return _monitor_instance


# ── CLI quick-test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GTLIS — TikTok Live Intelligence Suite")
    parser.add_argument("username", help="Handle TikTok (con o sin @)")
    parser.add_argument(
        "--action",
        choices=["probe", "profile", "recon", "full"],
        default="full",
        help="Acción a ejecutar (default: full)",
    )
    args = parser.parse_args()

    monitor = get_monitor()
    result = monitor.execute(action=args.action, username=args.username)
    print(result.stdout if result.success else f"ERROR: {result.stderr}")
