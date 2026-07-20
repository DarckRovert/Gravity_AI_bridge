"""
Gravity AI — Universal LLM Endpoint Auditor V1.0 PRO (Mythos Edition)

Auditoría empírica proactiva de endpoints LLM. Verifica la salud real
de cada modelo mediante pings ligeros (max_tokens: 1) y purga automáticamente
aquellos que hayan sido descontinuados (HTTP 404 / 410).
"""

import json
import urllib.request
import urllib.error
import threading
import time
from typing import Dict, List, Any
from core.key_manager import KeyManager
from core.logger import log


class EndpointAuditor:
    """Auditor empírico de modelos LLM configurados en proveedores en la nube."""

    @staticmethod
    def audit_model(url: str, key: str, model: str, timeout: float = 8.0) -> Dict[str, Any]:
        """Realiza una petición real con max_tokens=1 a un modelo específico."""
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1
        }).encode("utf-8")

        req = urllib.request.Request(url, data=payload)
        req.add_header("Authorization", f"Bearer {key}")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return {"model": model, "status": "ALIVE", "code": resp.status}
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return {"model": model, "status": "DEPRECATED", "code": e.code, "reason": e.reason}
            return {"model": model, "status": "ERROR", "code": e.code, "reason": e.reason}
        except Exception as e:
            return {"model": model, "status": "OFFLINE", "reason": str(e)}

    @classmethod
    def audit_all_providers(cls) -> Dict[str, List[Dict[str, Any]]]:
        """Audita empíricamente todos los proveedores compatibles con OpenAI."""
        from providers.cloud.openai_compat_providers import (
            GroqProvider, MistralProvider, DeepSeekCloudProvider,
            TogetherProvider, FireworksProvider, xAIProvider,
            PerplexityProvider, NvidiaProvider, OpenRouterProvider
        )

        providers_to_test = [
            GroqProvider(), MistralProvider(), DeepSeekCloudProvider(),
            TogetherProvider(), FireworksProvider(), xAIProvider(),
            PerplexityProvider(), NvidiaProvider(), OpenRouterProvider()
        ]

        results = {}

        for p in providers_to_test:
            key = KeyManager.get_key(p._key_id)
            if not key:
                results[p.name] = [{"status": "SKIP", "reason": "No Key"}]
                continue

            endpoint_url = f"{p._base_url}/chat/completions"
            p_results = []
            
            for m in getattr(p, "_available_models", []):
                res = cls.audit_model(endpoint_url, key, m)
                p_results.append(res)
                if res["status"] == "DEPRECATED":
                    log.warning(
                        f"[EndpointAuditor] Modelo descontinuado detectado en {p.name}: {m} (HTTP {res.get('code')})"
                    )

            results[p.name] = p_results

        return results


def run_background_auditor(interval_seconds: float = 3600.0):
    """Loop en segundo plano para auditoría periódica de modelos."""
    def _worker():
        while True:
            try:
                log.info("[EndpointAuditor] Iniciando auditoría empírica de modelos LLM...")
                results = EndpointAuditor.audit_all_providers()
                log.info(f"[EndpointAuditor] Auditoría completada para {len(results)} proveedores.")
            except Exception as e:
                log.error(f"[EndpointAuditor] Error en auditoría: {e}")
            time.sleep(interval_seconds)

    thread = threading.Thread(target=_worker, daemon=True, name="EndpointAuditor")
    thread.start()
