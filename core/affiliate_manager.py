"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — AFFILIATE MANAGER V1.0                                         ║
║  Inyección automática de enlaces CPA en descripciones de YouTube por nicho   ║
║                                                                              ║
║  Flujo:                                                                      ║
║    1. Clasifica el nicho del video                                           ║
║    2. Selecciona los top-3 programas de afiliados con mayor EPC              ║
║    3. Inyecta los enlaces en la descripción de YouTube antes de subir        ║
║    4. Registra el uso para rotación equitativa de productos                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
from datetime import datetime, timezone
from typing import Optional

from core.logger import log

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH    = os.path.join(BASE_DIR, "_integrations", "affiliate_db.json")
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")

# ── Base de datos de programas de afiliados por nicho ─────────────────────────
# EPC = Earnings Per Click estimado (USD). Ordenados de mayor a menor.
_DEFAULT_AFFILIATES: dict = {
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


# ── Config ────────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    try:
        import yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}).get("affiliates", {})
    except Exception:
        return {}


def _get_aff_ids() -> dict[str, str]:
    """Retorna el mapa provider_name -> affiliate_id desde config.yaml."""
    return _load_config().get("ids", {})


# ── Banco de afiliados ────────────────────────────────────────────────────────

def _load_affiliate_db() -> dict:
    """Carga el banco de afiliados desde disco (fallback al default hardcoded)."""
    if os.path.isfile(DB_PATH):
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge con defaults: añadir nichos nuevos sin borrar los del usuario
            for k, v in _DEFAULT_AFFILIATES.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return dict(_DEFAULT_AFFILIATES)


def save_affiliate_db(data: dict) -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Lógica de selección y formateo ───────────────────────────────────────────

def get_affiliate_links(niche_id: str, max_links: int = 3) -> list[dict]:
    """
    Retorna los mejores programas de afiliados para el nicho dado.
    Ordena por EPC descendente.
    """
    cfg = _load_config()
    if not cfg.get("enabled", False):
        return []

    db    = _load_affiliate_db()
    progs = db.get(niche_id, db.get("_default", []))
    aff_ids = _get_aff_ids()

    # Substituir placeholder {aff_id} con el ID real si existe
    result = []
    for prog in sorted(progs, key=lambda x: x.get("epc_usd", 0), reverse=True)[:max_links]:
        aff_id = aff_ids.get(prog["name"], aff_ids.get("_default", "gravity_ai"))
        url    = prog["url_template"].replace("{aff_id}", str(aff_id))
        result.append({**prog, "url": url, "aff_id_used": aff_id})

    return result


def build_affiliate_block(niche_id: str) -> str:
    """
    Genera el bloque de texto de afiliados listo para insertar en la descripción de YouTube.
    Retorna string vacío si no hay afiliados configurados.
    """
    links = get_affiliate_links(niche_id)
    if not links:
        return ""

    lines = [
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


# ── Revenue tracking ──────────────────────────────────────────────────────────

AFFILIATE_LOG = os.path.join(BASE_DIR, "_integrations", "affiliate_log.json")

def log_affiliate_injection(job_id: int, niche_id: str, links_used: list[dict]) -> None:
    """
    Registra qué afiliados se inyectaron en qué job para auditoría.
    También proyecta el ingreso CPA en revenue_tracker (EPC × CTR 0.5% × 500 views).
    """
    try:
        records = []
        if os.path.isfile(AFFILIATE_LOG):
            with open(AFFILIATE_LOG, "r", encoding="utf-8") as f:
                records = json.load(f)
        records.append({
            "ts":         datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "job_id":     job_id,
            "niche_id":   niche_id,
            "links_used": [l["name"] for l in links_used],
        })
        records = records[-500:]
        os.makedirs(os.path.dirname(AFFILIATE_LOG), exist_ok=True)
        with open(AFFILIATE_LOG, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False)
    except Exception as e:
        log.warning(f"[Affiliates] Error logging: {e}")

    # Proyección conservadora de ingresos CPA: EPC × CTR 0.5% × 500 views iniciales
    try:
        from core.revenue_tracker import _load_log, _save_log
        n_links = max(len(links_used), 1)
        avg_epc = sum(l.get("epc_usd", 0.5) for l in links_used) / n_links
        estimated_clicks = 500 * 0.005  # 0.5% CTR sobre 500 views
        affiliate_rev = round(avg_epc * estimated_clicks, 4)

        aff_record_id = f"aff_{job_id}"
        rev_records = _load_log()
        # Solo registrar si no existe ya para este job
        existing = [r for r in rev_records if r.get("video_id") == aff_record_id]
        if not existing:
            rev_records.append({
                "ts":          datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "job_id":      -(job_id + 100000),
                "niche_id":    niche_id,
                "is_short":    False,
                "platform":    "affiliate",
                "lang":        "es",
                "video_id":    aff_record_id,
                "views":       0,
                "revenue_usd": affiliate_rev,
                "source":      "affiliate_projection",
            })
            _save_log(rev_records)
    except Exception as _rev_e:
        log.debug(f"[Affiliates] Revenue projection skip: {_rev_e}")


# ── API Pública ───────────────────────────────────────────────────────────────

def get_status() -> dict:
    cfg   = _load_config()
    db    = _load_affiliate_db()
    total = sum(len(v) for v in db.values())
    return {
        "enabled":        cfg.get("enabled", False),
        "niches_covered": len([k for k in db if k != "_default"]),
        "total_programs": total,
        "ids_configured": list(_get_aff_ids().keys()),
    }


def get_programs_by_niche() -> dict:
    """Retorna el banco completo de afiliados agrupado por niche."""
    return _load_affiliate_db()


def add_program(niche_id: str, program: dict) -> dict:
    """Agrega o actualiza un programa de afiliados vía API."""
    required = {"name", "url_template", "cta", "epc_usd"}
    if not required.issubset(program.keys()):
        return {"ok": False, "error": f"Faltan campos: {required - set(program.keys())}"}
    db = _load_affiliate_db()
    db.setdefault(niche_id, [])
    # Remover si ya existe (upsert por nombre)
    db[niche_id] = [p for p in db[niche_id] if p["name"] != program["name"]]
    db[niche_id].append(program)
    save_affiliate_db(db)
    return {"ok": True, "niche_id": niche_id, "program": program["name"]}
