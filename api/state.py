import json
import time
import urllib.request
import threading

# ── Rate Limiter State ────────────────────────────────────────────────────────
RATE_LIMIT_MAX = 120
RATE_LIMIT_WINDOW = 60

from core.rate_limiter import ip_limiter


def check_rate_limit(ip: str) -> bool:
    """Retorna True si la IP puede hacer la request. False si está bloqueada."""
    return ip_limiter.is_allowed(ip, RATE_LIMIT_MAX, RATE_LIMIT_WINDOW)


# ── GeoIP Tracker State ───────────────────────────────────────────────────────
geoip_cache = {}
recent_ips = []
geoip_lock = threading.Lock()


def track_geoip(ip: str):
    if not ip or ip in geoip_cache:
        return
    if (
        ip in ("127.0.0.1", "localhost", "0.0.0.0", "::1")
        or ip.startswith("192.168.")
        or ip.startswith("10.")
    ):
        geoip_cache[ip] = {
            "status": "success",
            "country": "LocalNet",
            "city": "Gravity Core",
            "isp": "Localhost",
        }
        return

    geoip_cache[ip] = {
        "status": "pending",
        "country": "Resolviendo...",
        "city": "...",
        "isp": "...",
    }

    def fetch():
        try:
            req = urllib.request.Request(
                f"http://ip-api.com/json/{ip}",
                headers={"User-Agent": "Gravity_GeoIP_Watch/10.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as res:
                geoip_cache[ip] = json.loads(res.read().decode())
        except Exception:
            geoip_cache[ip] = {
                "status": "fail",
                "country": "Unknown",
                "city": "Unknown",
                "isp": "Error de Red",
            }

    threading.Thread(target=fetch, daemon=True, name=f"GeoIP-{ip}").start()


def register_ip_hit(ip: str):
    with geoip_lock:
        for i, x in enumerate(recent_ips):
            if x["ip"] == ip:
                recent_ips.pop(i)
                break
        recent_ips.insert(0, {"ip": ip, "timestamp": time.time()})
        if len(recent_ips) > 30:
            recent_ips.pop()
    track_geoip(ip)
