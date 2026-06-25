"""
Gravity Workflow Node: LLMQuery
Envía un prompt al proveedor de IA activo (local o cloud) y retorna texto.
"""

from core.workflow_engine import GravityNode, registry
from core.logger import log


@registry.register
class LLMQueryNode(GravityNode):
    NODE_TYPE = "LLMQuery"
    DESCRIPTION = "Envía un prompt al LLM activo y retorna texto generado."
    INPUT_SCHEMA = {
        "prompt": "TEXT",
        "system": "TEXT",       # opcional
        "temperature": "FLOAT", # opcional, default 0.7
        "max_tokens": "INT",    # opcional
    }
    OUTPUT_SCHEMA = {
        "text": "TEXT",
    }

    def execute(self, inputs: dict) -> dict:
        from core import provider_manager

        prompt: str = inputs.get("prompt", "")
        system: str = inputs.get("system", "")
        temperature: float = float(inputs.get("temperature") or self.config.get("temperature") or 0.7)
        max_tokens: int = int(inputs.get("max_tokens") or self.config.get("max_tokens") or 2048)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        options = {"temperature": temperature}
        if max_tokens:
            options["max_tokens"] = max_tokens

        try:
            best_provider, best_model = provider_manager.get_best()
            provider_name = best_provider.name if hasattr(best_provider, 'name') else best_provider

            log.info(f"[LLMQueryNode] Usando {provider_name}/{best_model} | temp={temperature}")

            # Generar texto
            full_text = provider_manager.complete(
                messages=messages,
                model=best_model,
                provider=provider_name,
                options=options
            )

            log.info(f"[LLMQueryNode] Resultado ({len(full_text)} chars)")
            return {"text": full_text.strip()}

        except Exception as exc:
            log.error(f"[LLMQueryNode] Error: {exc}")
            raise
