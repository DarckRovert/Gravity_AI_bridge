"""
tests/test_subagent_loader.py — Suite de pruebas unitarias para core/subagent_loader.py
Prueba parsing declarativo, manejo de CRLF, validaciones y caching.
"""
import os
import time
import pytest
from core.subagent_loader import (
    load_agent,
    discover_agents,
    get_agent,
    _parse_frontmatter,
    _validate_meta,
    AgentDefinition,
    _CACHE,
    _CACHE_MTIME,
)


def test_parse_frontmatter_standard():
    raw = """---
name: test_agent
description: Un agente de prueba
mode: subagent
model: auto
---
# Mision
Hacer pruebas.
"""
    meta, body = _parse_frontmatter(raw)
    assert meta["name"] == "test_agent"
    assert meta["description"] == "Un agente de prueba"
    assert meta["mode"] == "subagent"
    assert meta["model"] == "auto"
    assert body == "# Mision\nHacer pruebas."


def test_parse_frontmatter_crlf_and_bom():
    # CRLF (\r\n) + UTF-8 BOM (\ufeff)
    raw = "\ufeff---\r\nname: crlf_agent\r\ndescription: Agente con CRLF y BOM\r\nmode: primary\r\n---\r\nBody con salto.\r\n"
    meta, body = _parse_frontmatter(raw)
    assert meta["name"] == "crlf_agent"
    assert meta["mode"] == "primary"
    assert body == "Body con salto."


def test_parse_frontmatter_no_trailing_newline_after_close():
    raw = "---\nname: no_newline\ndescription: Desc\nmode: all\n---Cuerpo inmediato"
    meta, body = _parse_frontmatter(raw)
    assert meta["name"] == "no_newline"
    assert body == "Cuerpo inmediato"


def test_parse_frontmatter_invalid_no_dashes():
    raw = "Este archivo no tiene frontmatter YAML."
    with pytest.raises(ValueError, match="No se encontró frontmatter YAML válido"):
        _parse_frontmatter(raw)


def test_parse_frontmatter_malformed_yaml():
    raw = """---
name: [invalido yaml
---
Body
"""
    with pytest.raises(ValueError, match="YAML inválido"):
        _parse_frontmatter(raw)


def test_validate_meta_missing_fields():
    # Falta name
    with pytest.raises(ValueError, match="Campo requerido 'name' ausente"):
        _validate_meta({"description": "algo", "mode": "subagent"}, "dummy.md")

    # Falta description
    with pytest.raises(ValueError, match="Campo requerido 'description' ausente"):
        _validate_meta({"name": "test", "mode": "subagent"}, "dummy.md")

    # Falta mode
    with pytest.raises(ValueError, match="Campo requerido 'mode' ausente"):
        _validate_meta({"name": "test", "description": "algo"}, "dummy.md")


def test_validate_meta_invalid_mode():
    with pytest.raises(ValueError, match="mode='invalid_mode' inválido"):
        _validate_meta({"name": "test", "description": "algo", "mode": "invalid_mode"}, "dummy.md")


def test_load_agent_caching(tmp_path):
    agent_file = tmp_path / "test_cached.md"
    content = """---
name: cache_agent
description: Agente para probar cache
mode: subagent
model: auto
---
Prompt inicial
"""
    agent_file.write_text(content, encoding="utf-8")
    abs_path = str(agent_file.resolve())

    # Cargar por primera vez
    agent1 = load_agent(abs_path)
    assert agent1.name == "cache_agent"
    assert agent1.system_prompt == "Prompt inicial"

    # Verificar que esta en cache
    assert abs_path in _CACHE

    # Modificar archivo fisicamente
    time.sleep(0.05)
    agent_file.write_text(content.replace("Prompt inicial", "Prompt modificado"), encoding="utf-8")

    # Si no forzamos y el mtime cambia, load_agent recarga
    agent2 = load_agent(abs_path)
    assert agent2.system_prompt == "Prompt modificado"


def test_discover_agents_and_get_agent():
    # Verifica que descubre al menos los 3 agentes creados en .agents/agents/
    agents = discover_agents()
    assert "backend_specialist" in agents
    assert "frontend_specialist" in agents
    assert "qa_tester" in agents

    qa = get_agent("qa_tester")
    assert qa is not None
    assert qa.name == "qa_tester"
    assert qa.mode == "subagent"
    assert qa.model == "openai/gpt-oss-120b"
    assert qa.provider == "Groq"

    none_agent = get_agent("agente_inexistente_xyz")
    assert none_agent is None
