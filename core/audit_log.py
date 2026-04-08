import json
import os
import time
from datetime import datetime

class AuditLogger:
    """
    Immutable audit log for all inference calls (append-only JSONL).
    Records: timestamp, session_id, provider, model, tokens, latency, cost.
    """
    def __init__(self, log_path: str = "_audit_log.jsonl"):
        self.log_path = log_path

    def record(self, session_id: str, provider: str, model: str, 
               input_tokens: int, output_tokens: int, cost_usd: float, latency_ms: float):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "latency_ms": latency_ms,
            "cost_usd": cost_usd
        }
        
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            # Fallback a stdout si no puede escribir (poco probable pero posible)
            print(f"[AUDIT ERROR] No se pudo escribir al log: {e}")

    def get_recent(self, limit: int = 50) -> list[dict]:
        """Devuelve las últimas N entradas del audit log."""
        if not os.path.exists(self.log_path):
            return []
            
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # Tomar las últimas 'limit' líneas
            recent_lines = lines[-limit:] if limit > 0 else lines
            
            return [json.loads(line) for line in recent_lines if line.strip()]
        except Exception:
            return []

# Singleton instance
audit_logger = AuditLogger()
