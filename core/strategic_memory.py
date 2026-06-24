"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — STRATEGIC MEMORY V16.0 PRO [Autonomous Edition]               ║
║                                                                              ║
║  Base de datos de decisiones estratégicas y patrones del sistema.           ║
║  Persiste en gravity_brain.db (tabla: strategic_decisions).                 ║
║                                                                              ║
║  Responsabilidades:                                                          ║
║    ▸ Registrar decisiones del AutonomyEngine con contexto completo          ║
║    ▸ Actualizar el resultado de cada decisión (éxito/fallo/neutral)         ║
║    ▸ Detectar patrones recurrentes (módulos que fallan, nichos rentables)   ║
║    ▸ Proyecciones a 7/30/90 días basadas en tendencias reales               ║
║    ▸ API pública thread-safe para lectura/escritura                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import sqlite3
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

try:
    import networkx as nx

    _NX_OK = True
except ImportError:
    nx = None
    _NX_OK = False

from core.logger import log

BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH: str = os.path.join(BASE_DIR, "gravity_brain.db")

_db_lock = threading.RLock()

# ── Outcomes válidos ──────────────────────────────────────────────────────────
OUTCOME_SUCCESS = "success"
OUTCOME_FAILURE = "failure"
OUTCOME_NEUTRAL = "neutral"
OUTCOME_PENDING = "pending"

# ── Categorías de decisión ────────────────────────────────────────────────────
CAT_CONTENT = "content"  # Ajuste de nichos, scheduler
CAT_MONETIZE = "monetize"  # Revenue, afiliados, upload
CAT_SYSTEM = "system"  # Config, provider, hardware
CAT_SECURITY = "security"  # Alertas, parches
CAT_EVOLUTION = "evolution"  # Mejoras de código propuestas
CAT_OPPORTUNITY = "opportunity"  # Bounties, nuevos ingresos


def _get_conn() -> sqlite3.Connection:
    """Conexión SQLite con WAL mode y timeout robusto."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    """Crea las tablas si no existen. Idempotente."""
    with _db_lock:
        conn = _get_conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS strategic_decisions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts          TEXT    NOT NULL,
                    category    TEXT    NOT NULL,
                    title       TEXT    NOT NULL,
                    description TEXT,
                    rationale   TEXT,
                    action_taken TEXT,
                    outcome     TEXT    DEFAULT 'pending',
                    outcome_detail TEXT,
                    outcome_ts  TEXT,
                    impact_score REAL   DEFAULT 0.0,
                    metadata    TEXT    DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS system_patterns (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts          TEXT    NOT NULL,
                    pattern_key TEXT    NOT NULL UNIQUE,
                    pattern_val TEXT    NOT NULL,
                    hits        INTEGER DEFAULT 1,
                    last_seen   TEXT    NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_decisions_ts       ON strategic_decisions(ts);
                CREATE INDEX IF NOT EXISTS idx_decisions_category ON strategic_decisions(category);
                CREATE INDEX IF NOT EXISTS idx_decisions_outcome  ON strategic_decisions(outcome);
                CREATE INDEX IF NOT EXISTS idx_patterns_key       ON system_patterns(pattern_key);
            """)
            conn.commit()
        finally:
            conn.close()


# Inicializar al importar
_init_db()


# ── API de Decisiones ─────────────────────────────────────────────────────────


def record_decision(
    category: str,
    title: str,
    description: str = "",
    rationale: str = "",
    action_taken: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Registra una nueva decisión estratégica.
    Retorna el ID de la decisión creada.
    """
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    meta_str = json.dumps(metadata or {}, ensure_ascii=False)

    with _db_lock:
        for attempt in range(5):
            try:
                conn = _get_conn()
                cur = conn.execute(
                    """
                    INSERT INTO strategic_decisions
                        (ts, category, title, description, rationale, action_taken, outcome, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        now,
                        category,
                        title,
                        description,
                        rationale,
                        action_taken,
                        OUTCOME_PENDING,
                        meta_str,
                    ),
                )
                conn.commit()
                decision_id = cur.lastrowid
                conn.close()
                log.info(
                    f"[StrategicMemory] Decisión #{decision_id} registrada: [{category}] {title}"
                )
                return decision_id
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < 4:
                    time.sleep(0.05 * (2**attempt))
                else:
                    log.error(f"[StrategicMemory] Error registrando decisión: {e}")
                    return -1
    return -1


def update_outcome(
    decision_id: int,
    outcome: str,
    detail: str = "",
    impact_score: float = 0.0,
) -> bool:
    """
    Actualiza el resultado de una decisión pasada.
    outcome: 'success' | 'failure' | 'neutral'
    impact_score: -1.0 a 1.0 (positivo = bueno, negativo = malo)
    """
    if outcome not in (OUTCOME_SUCCESS, OUTCOME_FAILURE, OUTCOME_NEUTRAL):
        log.warning(f"[StrategicMemory] Outcome inválido: {outcome}")
        return False

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with _db_lock:
        for attempt in range(5):
            try:
                conn = _get_conn()
                conn.execute(
                    """
                    UPDATE strategic_decisions
                    SET outcome=?, outcome_detail=?, outcome_ts=?, impact_score=?
                    WHERE id=?
                    """,
                    (outcome, detail, now, impact_score, decision_id),
                )
                conn.commit()
                conn.close()
                log.info(
                    f"[StrategicMemory] Decisión #{decision_id} actualizada: {outcome} (score={impact_score})"
                )
                return True
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < 4:
                    time.sleep(0.05 * (2**attempt))
                else:
                    log.error(f"[StrategicMemory] Error actualizando outcome: {e}")
                    return False
    return False


def get_recent_decisions(
    n: int = 20, category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retorna las N decisiones más recientes, opcionalmente filtradas por categoría."""
    with _db_lock:
        try:
            conn = _get_conn()
            if category:
                rows = conn.execute(
                    "SELECT * FROM strategic_decisions WHERE category=? ORDER BY ts DESC LIMIT ?",
                    (category, n),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM strategic_decisions ORDER BY ts DESC LIMIT ?", (n,)
                ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            log.error(f"[StrategicMemory] Error leyendo decisiones: {e}")
            return []


def get_decision_by_id(decision_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene una decisión por su ID."""
    with _db_lock:
        try:
            conn = _get_conn()
            row = conn.execute(
                "SELECT * FROM strategic_decisions WHERE id=?", (decision_id,)
            ).fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            log.error(
                f"[StrategicMemory] Error obteniendo decisión #{decision_id}: {e}"
            )
            return None


# ── API de Patrones ───────────────────────────────────────────────────────────


def upsert_pattern(pattern_key: str, pattern_val: str) -> None:
    """
    Registra o incrementa un patrón detectado en el sistema.
    Ejemplos de pattern_key: 'module_error:bounty_hunter', 'top_niche:finanzas_personales'
    """
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with _db_lock:
        for attempt in range(5):
            try:
                conn = _get_conn()
                conn.execute(
                    """
                    INSERT INTO system_patterns (ts, pattern_key, pattern_val, hits, last_seen)
                    VALUES (?, ?, ?, 1, ?)
                    ON CONFLICT(pattern_key) DO UPDATE SET
                        hits = hits + 1,
                        last_seen = excluded.last_seen,
                        pattern_val = excluded.pattern_val
                    """,
                    (now, pattern_key, pattern_val, now),
                )
                conn.commit()
                conn.close()
                return
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < 4:
                    time.sleep(0.05 * (2**attempt))
                else:
                    log.error(f"[StrategicMemory] Error en upsert_pattern: {e}")
                    return


def get_patterns(prefix: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Retorna patrones detectados, opcionalmente filtrados por prefijo de key."""
    with _db_lock:
        try:
            conn = _get_conn()
            if prefix:
                rows = conn.execute(
                    "SELECT * FROM system_patterns WHERE pattern_key LIKE ? ORDER BY hits DESC LIMIT ?",
                    (f"{prefix}%", limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM system_patterns ORDER BY hits DESC LIMIT ?", (limit,)
                ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            log.error(f"[StrategicMemory] Error leyendo patrones: {e}")
            return []


# ── Estadísticas y proyecciones ───────────────────────────────────────────────


def get_summary(days: int = 30) -> Dict[str, Any]:
    """
    Resumen estadístico de decisiones y patrones.
    Incluye proyección de éxito/fallo a 7 y 30 días.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    with _db_lock:
        try:
            conn = _get_conn()

            # Total de decisiones en el período
            total = conn.execute(
                "SELECT COUNT(*) FROM strategic_decisions WHERE ts >= ?", (cutoff,)
            ).fetchone()[0]

            # Por outcome
            by_outcome: Dict[str, int] = {}
            for row in conn.execute(
                "SELECT outcome, COUNT(*) as cnt FROM strategic_decisions WHERE ts >= ? GROUP BY outcome",
                (cutoff,),
            ).fetchall():
                by_outcome[row[0]] = row[1]

            # Por categoría
            by_category: Dict[str, int] = {}
            for row in conn.execute(
                "SELECT category, COUNT(*) as cnt FROM strategic_decisions WHERE ts >= ? GROUP BY category",
                (cutoff,),
            ).fetchall():
                by_category[row[0]] = row[1]

            # Impact score promedio
            avg_impact_row = conn.execute(
                """
                SELECT AVG(impact_score) FROM strategic_decisions
                WHERE ts >= ? AND outcome != 'pending'
                """,
                (cutoff,),
            ).fetchone()
            avg_impact = round(avg_impact_row[0] or 0.0, 3)

            # Patrones más frecuentes
            top_patterns = [
                dict(r)
                for r in conn.execute(
                    "SELECT pattern_key, pattern_val, hits FROM system_patterns ORDER BY hits DESC LIMIT 10"
                ).fetchall()
            ]

            conn.close()

            # Tasa de éxito
            successes = by_outcome.get(OUTCOME_SUCCESS, 0)
            failures = by_outcome.get(OUTCOME_FAILURE, 0)
            resolved = successes + failures
            success_rate = (
                round(successes / resolved * 100, 1) if resolved > 0 else None
            )

            return {
                "period_days": days,
                "total_decisions": total,
                "by_outcome": by_outcome,
                "by_category": by_category,
                "avg_impact": avg_impact,
                "success_rate_pct": success_rate,
                "top_patterns": top_patterns,
            }
        except Exception as e:
            log.error(f"[StrategicMemory] Error en get_summary: {e}")
            return {"error": str(e)}


def get_knowledge_graph() -> Dict[str, Any]:
    """
    Construye un Knowledge Graph in-memory a partir de decisiones y patrones,
    usando NetworkX. Identifica los nodos (categorías/patrones) más centrales (PageRank).
    """
    if not _NX_OK:
        return {
            "error": "NetworkX no está instalado. Instala networkx para usar Graph-RAG."
        }

    G = nx.Graph()
    with _db_lock:
        try:
            conn = _get_conn()

            # Nodos y aristas de Decisiones -> Categorías -> Outcomes
            decisions = conn.execute(
                "SELECT id, category, title, outcome FROM strategic_decisions LIMIT 100"
            ).fetchall()
            for d in decisions:
                node_id = f"dec_{d['id']}"
                G.add_node(node_id, type="decision", title=d["title"])
                G.add_node(d["category"], type="category")
                G.add_node(d["outcome"], type="outcome")

                G.add_edge(node_id, d["category"], relation="belongs_to")
                G.add_edge(node_id, d["outcome"], relation="resulted_in")

            # Nodos de Patrones
            patterns = conn.execute(
                "SELECT pattern_key, hits FROM system_patterns LIMIT 100"
            ).fetchall()
            for p in patterns:
                node_id = f"pat_{p['pattern_key']}"
                cat = (
                    p["pattern_key"].split(":")[0]
                    if ":" in p["pattern_key"]
                    else "general"
                )
                G.add_node(node_id, type="pattern", hits=p["hits"])
                G.add_node(cat, type="category")
                G.add_edge(node_id, cat, relation="related_to", weight=p["hits"])

            conn.close()

            # Análisis de centralidad (PageRank)
            pagerank = nx.pagerank(G, weight="weight")
            central_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[
                :5
            ]

            return {
                "nodes_count": G.number_of_nodes(),
                "edges_count": G.number_of_edges(),
                "most_central_nodes": [
                    {"node": str(node), "score": round(score, 4)}
                    for node, score in central_nodes
                ],
            }
        except Exception as e:
            log.error(f"[StrategicMemory] Error en Knowledge Graph: {e}")
            return {"error": str(e)}


def get_brain_snapshot() -> str:
    """
    Retorna un resumen compacto para inyectar en el system prompt de Gravity.
    Muestra las últimas 5 decisiones y métricas clave.
    """
    try:
        recent = get_recent_decisions(5)
        summary = get_summary(7)

        lines = ["=== MEMORIA ESTRATÉGICA (últimos 7 días) ==="]
        lines.append(
            f"Decisiones: {summary.get('total_decisions', 0)} | "
            f"Tasa éxito: {summary.get('success_rate_pct', 'N/A')}% | "
            f"Impact promedio: {summary.get('avg_impact', 0)}"
        )

        if recent:
            lines.append("Últimas decisiones:")
            for d in recent:
                ts = d.get("ts", "")[:19]
                cat = d.get("category", "?")
                ttl = d.get("title", "?")[:60]
                out = d.get("outcome", "?")
                lines.append(f"  [{ts}] [{cat}] {ttl} → {out}")

        patterns = summary.get("top_patterns", [])
        if patterns:
            lines.append("Patrones detectados:")
            for p in patterns[:3]:
                lines.append(
                    f"  {p['pattern_key']} (×{p['hits']}): {str(p['pattern_val'])[:80]}"
                )

        # Inyectar Knowledge Graph Insights si está activo
        graph_data = get_knowledge_graph()
        if "error" not in graph_data:
            lines.append("Insights Graph-RAG (Nodos Críticos):")
            for c in graph_data.get("most_central_nodes", []):
                lines.append(f"  - {c['node']} (centralidad: {c['score']})")

        return "\n".join(lines)
    except Exception as e:
        return f"Memoria estratégica: no disponible ({e})"
