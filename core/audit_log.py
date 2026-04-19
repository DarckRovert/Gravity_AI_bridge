import json
import os
import time
from datetime import datetime

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_BYTES = 5 * 1024 * 1024   # 5 MB — archivo de rotación


class AuditLogger:
    """
    Immutable audit log for all inference calls (append-only JSONL).
    Records: timestamp, session_id, provider, model, tokens, latency, cost.
    V2: Rotación automática cuando el archivo supera MAX_BYTES (5 MB).
    """

    def __init__(self, log_path: str = "_audit_log.jsonl"):
        # Soportar rutas relativas y absolutas
        if not os.path.isabs(log_path):
            self.log_path = os.path.join(BASE_DIR, log_path)
        else:
            self.log_path = log_path

    def _rotate_if_needed(self) -> None:
        """Rota el log si supera MAX_BYTES. Crea una copia .bak y empieza uno nuevo."""
        try:
            if os.path.isfile(self.log_path) and os.path.getsize(self.log_path) >= MAX_BYTES:
                bak = self.log_path.replace(".jsonl", f".bak.{int(time.time())}.jsonl")
                os.rename(self.log_path, bak)
                # Eliminar backups viejos si hay más de 3
                base_dir  = os.path.dirname(self.log_path)
                base_name = os.path.basename(self.log_path).replace(".jsonl", "")
                baks = sorted([
                    f for f in os.listdir(base_dir)
                    if f.startswith(base_name + ".bak.")
                ])
                while len(baks) > 3:
                    os.remove(os.path.join(base_dir, baks.pop(0)))
        except Exception:
            pass

    def record(self, session_id: str, provider: str, model: str,
               input_tokens: int, output_tokens: int, cost_usd: float, latency_ms: float):
        entry = {
            "timestamp":    datetime.utcnow().isoformat() + "Z",
            "session_id":   session_id,
            "provider":     provider,
            "model":        model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "latency_ms":   latency_ms,
            "cost_usd":     cost_usd,
        }

        self._rotate_if_needed()

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass  # Silencioso en frozen build — stdout puede no estar disponible

    def get_recent(self, limit: int = 50) -> list:
        """Devuelve las últimas N entradas del audit log."""
        if not os.path.exists(self.log_path):
            return []

        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            recent_lines = lines[-limit:] if limit > 0 else lines
            return [json.loads(line) for line in recent_lines if line.strip()]
        except Exception:
            return []


# Singleton instance
audit_logger = AuditLogger()
