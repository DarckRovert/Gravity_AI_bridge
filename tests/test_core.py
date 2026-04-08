import os
import pytest
import json
import yaml
from pathlib import Path
from core.config_manager import ConfigManager
from core.audit_log import AuditLogger
from core.logger import sanitize_json

def test_config_migration(tmp_path):
    # Setup legacy JSON
    old_json = tmp_path / "_settings.json"
    new_yaml = tmp_path / "config.yaml"
    
    data = {
        "bridge_port": 9999,
        "provider": "TestProvider",
        "advanced_params": {"num_ctx": 4096}
    }
    old_json.write_text(json.dumps(data))
    
    # Run manager
    manager = ConfigManager(config_path=str(new_yaml), old_settings=str(old_json))
    
    assert manager.get("server.port") == 9999
    assert manager.get("model.default_provider") == "TestProvider"
    assert manager.get("model.ctx_size") == 4096
    assert new_yaml.exists()

def test_audit_logging(tmp_path):
    audit_file = tmp_path / "audit.jsonl"
    logger = AuditLogger(log_path=str(audit_file))
    
    logger.record("session-1", "provider-x", "model-y", 10, 20, 0.05, 100)
    
    content = audit_file.read_text().strip()
    entry = json.loads(content)
    
    assert entry["session_id"] == "session-1"
    assert entry["provider"] == "provider-x"
    assert entry["input_tokens"] == 10

def test_logger_sanitization():
    dirty = {"api_key": "sk-12345", "user": "test"}
    clean = sanitize_json(dirty)
    assert clean["api_key"] == "[REDACTED_KEY]"
    assert clean["user"] == "test"
