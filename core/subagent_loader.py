"""
core/subagent_loader.py — GRAVITY AI V30.3
Carga y valida definiciones declarativas de subagentes desde .agents/agents/*.md
"""
import os
import re
import yaml
from dataclasses import dataclass
from typing import Dict, Optional, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.join(BASE_DIR, ".agents", "agents")


@dataclass
class AgentDefinition:
    name: str
    description: str
    mode: str           # "primary" | "subagent" | "all"
    model: str
    provider: str
    temperature: float
    max_tokens: int
    permissions: Dict[str, Any]
    system_prompt: str
    source_file: str


_CACHE: Dict[str, AgentDefinition] = {}
_CACHE_MTIME: Dict[str, float] = {}


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """Separa YAML frontmatter del body. Lanza ValueError si malformado.

    FIX #4 (Windows CRLF): normaliza line endings antes de aplicar regex para
    que archivos editados en Windows no fallen silenciosamente.
    FIX #4b: el patrón acepta frontmatter sin newline final tras el cierre '---'.
    """
    # ── Normalización CRLF y UTF-8 BOM (Windows) ─────────────────────────────
    content = content.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    # ── Regex: \n---\s*\n? acepta newline opcional tras el cierre '---' ───────
    pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
    match = pattern.match(content.lstrip())
    if not match:
        raise ValueError("No se encontró frontmatter YAML válido (líneas '---')")
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"YAML inválido: {e}") from e
    return meta, match.group(2).strip()


def _validate_meta(meta: dict, path: str) -> None:
    """Valida campos obligatorios del frontmatter."""
    for f in ["name", "description", "mode"]:
        if f not in meta:
            raise ValueError(f"Campo requerido '{f}' ausente en {path}")
    if meta["mode"] not in {"primary", "subagent", "all"}:
        raise ValueError(f"mode='{meta['mode']}' inválido. Debe ser: primary | subagent | all")


def load_agent(filepath: str, force: bool = False) -> AgentDefinition:
    """Carga y cachea un agente. Re-parsea solo si el archivo cambió (mtime)."""
    abs_path = os.path.abspath(filepath)
    mtime = os.path.getmtime(abs_path)
    if not force and abs_path in _CACHE and _CACHE_MTIME.get(abs_path) == mtime:
        return _CACHE[abs_path]
    with open(abs_path, "r", encoding="utf-8") as f:
        content = f.read()
    meta, body = _parse_frontmatter(content)
    _validate_meta(meta, abs_path)
    defn = AgentDefinition(
        name=str(meta["name"]),
        description=str(meta.get("description", "")).strip(),
        mode=str(meta["mode"]),
        model=str(meta.get("model", "auto")),
        provider=str(meta.get("provider", "auto")),
        temperature=float(meta.get("temperature", 0.3)),
        max_tokens=int(meta.get("max_tokens", 2048)),
        permissions=meta.get("permissions", {}) if isinstance(meta.get("permissions"), dict) else {},
        system_prompt=body,
        source_file=abs_path,
    )
    _CACHE[abs_path] = defn
    _CACHE_MTIME[abs_path] = mtime
    return defn


def discover_agents(agents_dir: str = AGENTS_DIR) -> Dict[str, AgentDefinition]:
    """Escanea el directorio y retorna todos los agentes válidos. Omite los inválidos."""
    from core.logger import log
    result: Dict[str, AgentDefinition] = {}
    if not os.path.isdir(agents_dir):
        return result
    for fname in sorted(os.listdir(agents_dir)):
        if not fname.endswith(".md"):
            continue
        try:
            defn = load_agent(os.path.join(agents_dir, fname))
            result[defn.name] = defn
        except Exception as e:
            log.warning(f"[SubagentLoader] Error en {fname}: {e}")
    return result


def get_agent(name: str) -> Optional[AgentDefinition]:
    return discover_agents().get(name)
