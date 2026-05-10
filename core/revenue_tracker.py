"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — REVENUE TRACKER V2.0                                           ║
║  Seguimiento de ingresos estimados por canal, niche y período                ║
║                                                                              ║
║  Fuentes de ingreso rastreadas:                                              ║
║    - YouTube AdSense (CPM × views estimadas, ajustado al niche)              ║
║    - YouTube Shorts (CPM fijo diferenciado × views)                          ║
║    - Afiliados CPA (EPC × clicks registrados por inyección)                  ║
║    - Language Cloner (multiplica ingresos por canal de idioma)               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional

from core.logger import log

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH       = os.path.join(BASE_DIR, "_video_queue.sqlite")
REVENUE_PATH  = os.path.join(BASE_DIR, "_integrations", "revenue_log.json")
CONFIG_PATH   = os.path.join(BASE_DIR, "config.yaml")

# CPM por niche sincronizado con inputs/niches.json → estimated_cpm_usd
# Representa el CPM bruto anunciante; el creator recibe ~55% (RPM real).
NICHE_CPM_MAP: dict[str, float] = {
    "finanzas_personales":      12.0,   # Niche premium — fintech/cripto
    "tecnologia_ia":             8.0,   # Alto en EN, moderado en ES
    "motivacion_exito":          7.0,   # Buen CTR, audiencia amplia
    "ciencia_naturaleza":        5.0,   # Documental, buena retención
    "misterios_conspiraciones":  4.0,   # Viral, CPM medio
    "historia_mundial":          3.5,   # Educativo, estable
    "_default":                  2.5,   # Fallback conservador
}

# CPM por idioma (canal EN tiene 3-5× más CPM que ES)
LANG_CPM_MULTIPLIER: dict[str, float] = {
    "en": 3.5,
    "pt": 1.3,
    "fr": 2.0,
    "de": 2.5,
    "es": 1.0,   # baseline
}

# YouTube se queda 45% → creator recibe 55%
YOUTUBE_REVENUE_SHARE = 0.55

# Shorts: CPM real estimado (mucho menor al long-form)
SHORTS_CPM = 0.12   # $0.12 RPM promedio Shorts — conservador


# ── Revenue log ───────────────────────────────────────────────────────────────

def _load_log() -> list:
    if os.path.isfile(REVENUE_PATH):
        try:
            with open(REVENUE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save_log(records: list) -> None:
    os.makedirs(os.path.dirname(REVENUE_PATH), exist_ok=True)
    with open(REVENUE_PATH, "w", encoding="utf-8") as f:
        json.dump(records[-2000:], f, ensure_ascii=False)


def record_upload(job_id: int, niche_id: str, is_short: bool = False,
                  platform: str = "youtube", lang: str = "es",
                  video_id: str = "") -> None:
    """
    Registra un upload nuevo.
    El revenue se actualizará cuando se llame update_views().
    Incluye multiplicador de idioma para canales clonados.
    """
    records = _load_log()
    records.append({
        "ts":           datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "job_id":       job_id,
        "niche_id":     niche_id,
        "is_short":     is_short,
        "platform":     platform,
        "lang":         lang,
        "video_id":     video_id,
        "views":        0,
        "revenue_usd":  0.0,
        "source":       "upload_registered",
    })
    _save_log(records)
    log.info(f"[Revenue] Upload registrado: job #{job_id} | niche={niche_id} | lang={lang} | short={is_short}")


def update_views(job_id: int, views: int) -> None:
    """
    Actualiza las vistas y recalcula el ingreso estimado de un job.
    Aplica multiplicador de idioma y diferencia Shorts de long-form.
    """
    records = _load_log()
    for rec in records:
        if rec.get("job_id") == job_id:
            niche  = rec.get("niche_id", "_default")
            lang   = rec.get("lang", "es")
            lang_mult = LANG_CPM_MULTIPLIER.get(lang, 1.0)
            if rec.get("is_short"):
                cpm = SHORTS_CPM
            else:
                cpm = NICHE_CPM_MAP.get(niche, NICHE_CPM_MAP["_default"]) * lang_mult
            revenue = (views / 1000) * cpm * YOUTUBE_REVENUE_SHARE
            rec["views"]       = views
            rec["revenue_usd"] = round(revenue, 4)
            rec["cpm_effective"] = round(cpm, 3)
            rec["source"]      = "views_updated"
            break
    _save_log(records)


def record_affiliate_click(job_id: int, program_name: str, epc_usd: float) -> None:
    """Registra un click de afiliado (llamado desde el frontend cuando se puede)."""
    records = _load_log()
    records.append({
        "ts":          datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "job_id":      job_id,
        "program":     program_name,
        "epc_usd":     epc_usd,
        "revenue_usd": epc_usd,
        "source":      "affiliate_click",
        "platform":    "affiliate",
    })
    _save_log(records)


# ── Estadísticas ──────────────────────────────────────────────────────────────

def get_summary(days: int = 30) -> dict:
    """
    Resumen de ingresos de los últimos N días.
    Incluye desglose por fuente (YouTube long-form, Shorts, Afiliados),
    por idioma y proyección mensual realista.
    """
    records  = _load_log()
    cutoff   = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    recent   = [r for r in records if r.get("ts", "") >= cutoff]
    total_r  = sum(r.get("revenue_usd", 0) for r in recent)

    yt_long  = sum(r.get("revenue_usd", 0) for r in recent
                   if r.get("platform") == "youtube" and not r.get("is_short"))
    yt_short = sum(r.get("revenue_usd", 0) for r in recent
                   if r.get("platform") == "youtube" and r.get("is_short"))
    yt_r     = yt_long + yt_short
    aff_r    = sum(r.get("revenue_usd", 0) for r in recent if r.get("platform") == "affiliate")
    total_v  = sum(r.get("views", 0) for r in recent)

    # Por niche
    by_niche: dict[str, float] = {}
    for r in recent:
        n = r.get("niche_id") or "_other"
        by_niche[n] = round(by_niche.get(n, 0) + r.get("revenue_usd", 0), 4)

    # Por idioma
    by_lang: dict[str, float] = {}
    for r in recent:
        lg = r.get("lang", "es")
        by_lang[lg] = round(by_lang.get(lg, 0) + r.get("revenue_usd", 0), 4)

    # Uploads totales del periodo (de DB)
    uploads_total = 0
    uploads_cloned = 0
    try:
        conn = sqlite3.connect(DB_PATH, timeout=15)
        uploads_total = conn.execute(
            "SELECT COUNT(*) FROM video_jobs WHERE upload_status='uploaded' AND uploaded_at >= ?",
            (cutoff,)
        ).fetchone()[0]
        # Contar clones de idioma si la columna existe
        try:
            uploads_cloned = conn.execute(
                "SELECT COUNT(*) FROM video_jobs WHERE upload_status='uploaded' AND cloned_from IS NOT NULL AND uploaded_at >= ?",
                (cutoff,)
            ).fetchone()[0]
        except Exception:
            pass
        conn.close()
    except Exception:
        pass

    # Proyección mensual basada en promedio diario real
    daily_avg    = total_r / max(days, 1)
    monthly_proj = daily_avg * 30

    # Proyección potencial si se activa Language Cloner a EN+PT
    lang_multiplier_potential = 1.0
    enabled_langs = []
    try:
        import yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        enabled_langs = cfg.get("language_cloner", {}).get("languages", [])
        for lg in enabled_langs:
            lang_multiplier_potential += LANG_CPM_MULTIPLIER.get(lg, 1.0) * 0.8
    except Exception:
        pass
    monthly_proj_with_cloner = monthly_proj * lang_multiplier_potential

    return {
        "period_days":                 days,
        "total_revenue_usd":           round(total_r, 2),
        "youtube_usd":                 round(yt_r, 2),
        "youtube_longform_usd":        round(yt_long, 2),
        "youtube_shorts_usd":          round(yt_short, 2),
        "affiliate_usd":               round(aff_r, 2),
        "total_views":                 total_v,
        "uploads":                     uploads_total,
        "uploads_cloned":              uploads_cloned,
        "by_niche":                    by_niche,
        "by_lang":                     by_lang,
        "daily_avg_usd":               round(daily_avg, 4),
        "monthly_proj_usd":            round(monthly_proj, 2),
        "monthly_proj_with_cloner_usd": round(monthly_proj_with_cloner, 2),
        "lang_cloner_enabled_langs":   enabled_langs,
        "disclaimer":                  "Ingresos estimados basados en CPM histórico. No representan pagos reales de AdSense.",
    }


def get_top_jobs(limit: int = 10) -> list[dict]:
    """Retorna los N videos con mayor ingreso estimado."""
    records = _load_log()
    by_job: dict[int, dict] = {}
    for r in records:
        jid = r.get("job_id", 0)
        if jid not in by_job:
            by_job[jid] = {"job_id": jid, "revenue_usd": 0.0, "views": 0,
                           "niche_id": r.get("niche_id", ""), "platform": r.get("platform", "")}
        by_job[jid]["revenue_usd"] += r.get("revenue_usd", 0)
        by_job[jid]["views"]       += r.get("views", 0)

    return sorted(by_job.values(), key=lambda x: x["revenue_usd"], reverse=True)[:limit]


def get_timeline(days: int = 30) -> list[dict]:
    """Retorna ingresos diarios para graficar en el dashboard."""
    records  = _load_log()
    cutoff   = datetime.now(timezone.utc) - timedelta(days=days)
    daily: dict[str, float] = {}

    for r in records:
        try:
            ts  = datetime.fromisoformat(r["ts"].replace("Z", "+00:00"))
            day = ts.strftime("%Y-%m-%d")
        except Exception:
            continue
        if ts < cutoff:
            continue
        daily[day] = round(daily.get(day, 0) + r.get("revenue_usd", 0), 4)

    # Rellenar días vacíos
    result = []
    for i in range(days):
        d = (cutoff + timedelta(days=i+1)).strftime("%Y-%m-%d")
        result.append({"date": d, "revenue_usd": daily.get(d, 0)})

    return result
