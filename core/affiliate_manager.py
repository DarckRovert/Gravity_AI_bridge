"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — AFFILIATE MANAGER V16.0 PRO                                    ║
║  Inyección automática de enlaces CPA en descripciones de YouTube por nicho   ║
║                                                                              ║
║  Garantiza seguridad multihilo absoluta, exclusión mutua y atomicidad en     ║
║  disco bajo entornos altamente concurrentes en Windows.                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import threading
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from core.logger import log
from core.config_manager import config

BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH: str = os.path.join(BASE_DIR, "_integrations", "affiliate_db.json")
AFFILIATE_LOG: str = os.path.join(BASE_DIR, "_integrations", "affiliate_log.json")

# Cerrojo reentrante a nivel de módulo para sincronizar I/O y mutaciones
_affiliate_io_lock = threading.RLock()

# ── Base de datos de programas de afiliados por nicho ─────────────────────────
# EPC = Earnings Per Click estimado (USD). Ordenados de mayor a menor.
_DEFAULT_AFFILIATES: Dict[str, List[Dict[str, Any]]] = {
    "tecnologia_ia": [
        {
            "name": "NordVPN",
            "program": "NordVPN Affiliates",
            "url_template": "https://go.nordvpn.net/aff_c?offer_id=15&aff_id={aff_id}",
            "cta": "🔒 Protege tu privacidad online con 70% de descuento",
            "epc_usd": 12.50,
            "category": "vpn",
        },
        {
            "name": "Hostinger",
            "program": "Hostinger Affiliates",
            "url_template": "https://www.hostinger.com?ref={aff_id}",
            "cta": "🌐 Crea tu sitio web desde $2.99/mes",
            "epc_usd": 8.00,
            "category": "hosting",
        },
        {
            "name": "Coursera",
            "program": "Coursera Affiliates (Impact)",
            "url_template": "https://coursera.org/?siteID={aff_id}",
            "cta": "📚 Aprende IA con certificados de Google y Meta",
            "epc_usd": 5.50,
            "category": "education",
        },
    ],
    "finanzas_personales": [
        {
            "name": "Binance",
            "program": "Binance Affiliate Program",
            "url_template": "https://accounts.binance.com/register?ref={aff_id}",
            "cta": "📈 Opera cripto con 20% de descuento en comisiones",
            "epc_usd": 22.00,
            "category": "crypto",
        },
        {
            "name": "eToro",
            "program": "eToro Partners",
            "url_template": "https://etoro.tw/partner?affp={aff_id}",
            "cta": "💹 Invierte en acciones y cripto sin comisiones",
            "epc_usd": 18.00,
            "category": "trading",
        },
        {
            "name": "Wise",
            "program": "Wise Affiliates",
            "url_template": "https://wise.com/invite/{aff_id}",
            "cta": "💸 Envía dinero al extranjero sin tarifas ocultas",
            "epc_usd": 7.50,
            "category": "fintech",
        },
    ],
    "motivacion_exito": [
        {
            "name": "Audible",
            "program": "Amazon Associates",
            "url_template": "https://amzn.to/audible?tag={aff_id}",
            "cta": "🎧 30 días gratis de audiolibros en Audible",
            "epc_usd": 6.00,
            "category": "books",
        },
        {
            "name": "Skillshare",
            "program": "Skillshare Affiliates",
            "url_template": "https://skl.sh/partner?ref={aff_id}",
            "cta": "🎨 1 mes gratis de Skillshare — miles de cursos",
            "epc_usd": 7.00,
            "category": "education",
        },
    ],
    "historia_mundial": [
        {
            "name": "Curiosity Stream",
            "program": "Curiosity Stream Affiliates",
            "url_template": "https://curiositystream.com/?couponCode={aff_id}",
            "cta": "🎬 Miles de documentales históricos — 26 días gratis",
            "epc_usd": 9.00,
            "category": "streaming",
        },
        {
            "name": "Audible",
            "program": "Amazon Associates",
            "url_template": "https://amzn.to/audible?tag={aff_id}",
            "cta": "🎧 30 días gratis de audiolibros históricos",
            "epc_usd": 6.00,
            "category": "books",
        },
    ],
    "misterios_conspiraciones": [
        {
            "name": "Curiosity Stream",
            "program": "Curiosity Stream Affiliates",
            "url_template": "https://curiositystream.com/?couponCode={aff_id}",
            "cta": "🔍 Documentales de misterio sin censura — 26 días gratis",
            "epc_usd": 9.00,
            "category": "streaming",
        },
        {
            "name": "ExpressVPN",
            "program": "ExpressVPN Affiliates",
            "url_template": "https://www.expressvpn.com/refer-a-friend/{aff_id}",
            "cta": "🔐 Navega sin restricciones — 3 meses gratis",
            "epc_usd": 13.00,
            "category": "vpn",
        },
    ],
    "ciencia_naturaleza": [
        {
            "name": "Curiosity Stream",
            "program": "Curiosity Stream Affiliates",
            "url_template": "https://curiositystream.com/?couponCode={aff_id}",
            "cta": "🌿 Documentales de naturaleza en 4K — 26 días gratis",
            "epc_usd": 9.00,
            "category": "streaming",
        },
        {
            "name": "iNaturalist",
            "program": "Amazon Associates (libros naturaleza)",
            "url_template": "https://amzn.to/naturaleza?tag={aff_id}",
            "cta": "📖 Los mejores libros de naturaleza — envío gratis",
            "epc_usd": 4.00,
            "category": "books",
        },
    ],
    "_default": [
        {
            "name": "NordVPN",
            "program": "NordVPN Affiliates",
            "url_template": "https://go.nordvpn.net/aff_c?offer_id=15&aff_id={aff_id}",
            "cta": "🔒 Protege tu privacidad con 70% de descuento",
            "epc_usd": 12.50,
            "category": "vpn",
        },
    ],
}


def _load_config() -> Dict[str, Any]:
    """Carga de forma thread-safe la configuración delegando en ConfigManager."""
    return config.get("affiliates", {})


def _get_aff_ids() -> Dict[str, str]:
    """Retorna el mapa provider_name -> affiliate_id desde la configuración."""
    return _load_config().get("ids", {})


def _atomic_write_json(file_path: str, data: Any) -> None:
    """
    Escribe datos JSON de manera atómica con reintentos y retroceso exponencial.
    Protege el disco contra cortes bruscos de energía o PermissionError en Windows.
    """
    temp_path = f"{file_path}.tmp"
    dir_name = os.path.dirname(file_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
        
    last_err: Optional[Exception] = None
    for i in range(5):
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # Operación atómica en Windows/Unix
            os.replace(temp_path, file_path)
            return
        except PermissionError as e:
            last_err = e
            wait = 0.05 * (2 ** i)
            time.sleep(wait)
        except Exception as e:
            last_err = e
            # Errores graves (disco lleno, etc.) se lanzan
            raise e
            
    if last_err:
        log.error(f"[Affiliates] Atomic write failed to {file_path} after 5 attempts: {last_err}")
        raise last_err


def _load_affiliate_db() -> Dict[str, List[Dict[str, Any]]]:
    """Carga de forma sincronizada el banco de afiliados de nichos desde disco."""
    with _affiliate_io_lock:
        if os.path.isfile(DB_PATH):
            for i in range(5):
                try:
                    with open(DB_PATH, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # Sincronizar y complementar con valores por defecto
                    for k, v in _DEFAULT_AFFILIATES.items():
                        data.setdefault(k, v)
                    return data
                except (PermissionError, json.JSONDecodeError) as e:
                    time.sleep(0.02 * (2 ** i))
                except Exception as e:
                    log.warning(f"[Affiliates] Failed to load db: {e}")
                    break
        return dict(_DEFAULT_AFFILIATES)


def save_affiliate_db(data: Dict[str, List[Dict[str, Any]]]) -> None:
    """Guarda de forma atómica y thread-safe el banco de afiliados en disco."""
    with _affiliate_io_lock:
        _atomic_write_json(DB_PATH, data)


def get_affiliate_links(niche_id: str, max_links: int = 3) -> List[Dict[str, Any]]:
    """
    Retorna los mejores programas de afiliados para el nicho dado.
    Ordena por EPC descendente bajo exclusión mutua absoluta.
    """
    with _affiliate_io_lock:
        cfg = _load_config()
        if not cfg.get("enabled", False):
            return []

        db = _load_affiliate_db()
        progs = db.get(niche_id, db.get("_default", []))
        aff_ids = _get_aff_ids()

        result: List[Dict[str, Any]] = []
        # Ordenar por EPC descendente
        sorted_progs = sorted(progs, key=lambda x: x.get("epc_usd", 0.0), reverse=True)[:max_links]
        
        for prog in sorted_progs:
            aff_id = aff_ids.get(prog["name"], aff_ids.get("_default", "gravity_ai"))
            url = prog["url_template"].replace("{aff_id}", str(aff_id))
            result.append({**prog, "url": url, "aff_id_used": aff_id})

        return result


def build_affiliate_block(niche_id: str) -> str:
    """
    Genera el bloque de texto de afiliados listo para insertar en la descripción de YouTube.
    Retorna string vacío si no hay afiliados habilitados.
    """
    links = get_affiliate_links(niche_id)
    if not links:
        return ""

    lines: List[str] = [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🤝 PATROCINADORES Y HERRAMIENTAS RECOMENDADAS",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    for link in links:
        lines.append(f"▶ {link['cta']}")
        lines.append(f"   {link['url']}")
        lines.append("")

    lines.append("⚠️ Algunos links son de afiliados. Al usarlos apoyas el canal sin costo extra.")
    return "\n".join(lines)


def log_affiliate_injection(job_id: int, niche_id: str, links_used: List[Dict[str, Any]]) -> None:
    """
    Registra de forma sincronizada y atómica la inyección en affiliate_log.json.
    Proyecta de forma thread-safe los ingresos estimados en revenue_tracker.
    """
    with _affiliate_io_lock:
        try:
            records: List[Dict[str, Any]] = []
            if os.path.isfile(AFFILIATE_LOG):
                for i in range(5):
                    try:
                        with open(AFFILIATE_LOG, "r", encoding="utf-8") as f:
                            records = json.load(f)
                        break
                    except (PermissionError, json.JSONDecodeError):
                        time.sleep(0.02 * (2 ** i))
                        
            records.append({
                "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "job_id": job_id,
                "niche_id": niche_id,
                "links_used": [l["name"] for l in links_used],
            })
            # Mantener histórico limitado a 500 registros
            records = records[-500:]
            _atomic_write_json(AFFILIATE_LOG, records)
        except Exception as e:
            log.warning(f"[Affiliates] Error logging affiliate injection: {e}")

    # Proyección conservadora de ingresos CPA: EPC × CTR 0.5% × 500 views iniciales
    try:
        from core.revenue_tracker import _load_log, _save_log
        n_links = max(len(links_used), 1)
        avg_epc = sum(l.get("epc_usd", 0.5) for l in links_used) / n_links
        estimated_clicks = 500 * 0.005  # 0.5% CTR sobre 500 views
        affiliate_rev = round(avg_epc * estimated_clicks, 4)

        aff_record_id = f"aff_{job_id}"
        
        # Sincronizar el acceso y guardado en revenue_tracker
        from core.revenue_tracker import _revenue_io_lock
        with _revenue_io_lock:
            rev_records = _load_log()
            existing = [r for r in rev_records if r.get("video_id") == aff_record_id]
            if not existing:
                rev_records.append({
                    "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "job_id": -(job_id + 100000),
                    "niche_id": niche_id,
                    "is_short": False,
                    "platform": "affiliate",
                    "lang": "es",
                    "video_id": aff_record_id,
                    "views": 0,
                    "revenue_usd": affiliate_rev,
                    "source": "affiliate_projection",
                })
                _save_log(rev_records)
    except Exception as _rev_e:
        log.debug(f"[Affiliates] Revenue projection skipped or failed: {_rev_e}")


def get_status() -> Dict[str, Any]:
    """Retorna las estadísticas operativas del gestor de afiliados de forma segura."""
    with _affiliate_io_lock:
        cfg = _load_config()
        db = _load_affiliate_db()
        total = sum(len(v) for v in db.values())
        return {
            "enabled": cfg.get("enabled", False),
            "niches_covered": len([k for k in db if k != "_default"]),
            "total_programs": total,
            "ids_configured": list(_get_aff_ids().keys()),
        }


def get_programs_by_niche() -> Dict[str, List[Dict[str, Any]]]:
    """Retorna el banco completo de afiliados agrupado por niche de forma sincronizada."""
    with _affiliate_io_lock:
        return _load_affiliate_db()


def add_program(niche_id: str, program: Dict[str, Any]) -> Dict[str, Any]:
    """Agrega o actualiza un programa de afiliados de forma thread-safe."""
    required = {"name", "url_template", "cta", "epc_usd"}
    if not required.issubset(program.keys()):
        return {"ok": False, "error": f"Faltan campos requeridos: {required - set(program.keys())}"}
        
    with _affiliate_io_lock:
        db = _load_affiliate_db()
        db.setdefault(niche_id, [])
        # Upsert por nombre del programa
        db[niche_id] = [p for p in db[niche_id] if p["name"] != program["name"]]
        db[niche_id].append(program)
        save_affiliate_db(db)
        return {"ok": True, "niche_id": niche_id, "program": program["name"]}

