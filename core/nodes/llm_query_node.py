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
        "system": "TEXT",        # alias: system_prompt — ambos aceptados
        "system_prompt": "TEXT", # alias explícito para workflows editoriales
        "role": "TEXT",          # ignorado en runtime (solo documentación)
        "temperature": "FLOAT",  # opcional, default 0.7
        "max_tokens": "INT",     # opcional
        "provider": "TEXT",      # opcional, fuerza un proveedor (ej: openai, nvidia)
        "model": "TEXT",         # opcional, fuerza un modelo específico
    }
    OUTPUT_SCHEMA = {
        "text": "TEXT",
    }

    def execute(self, inputs: dict) -> dict:
        from core import provider_manager

        prompt: str = inputs.get("prompt", "")
        # Aceptar 'system' o 'system_prompt' — prioridad a system_prompt si ambos presentes
        system: str = inputs.get("system_prompt") or inputs.get("system") or ""
        system = system or self.config.get("system", "")
        temperature: float = float(inputs.get("temperature") or self.config.get("temperature") or 0.7)
        max_tokens: int = int(inputs.get("max_tokens") or self.config.get("max_tokens") or 2048)

        if not prompt:
            raise ValueError(f"[{self.node_id}] El campo 'prompt' es obligatorio.")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        options = {"temperature": temperature}
        if max_tokens:
            options["max_tokens"] = max_tokens

        try:
            forced_provider = inputs.get("provider") or self.config.get("provider")
            forced_model = inputs.get("model") or self.config.get("model")

            if forced_provider:
                provider_name = forced_provider
                best_model = forced_model
                log.info(f"[LLMQueryNode] Forzando proveedor: {provider_name} (modelo: {best_model or 'auto'})")
            else:
                best_provider, best_model = provider_manager.get_best()
                provider_name = best_provider.name if hasattr(best_provider, 'name') else best_provider

            if not provider_name:
                raise ValueError("No hay proveedores de IA disponibles o saludables. Revisa tu memoria RAM, inicia un motor local o configura una API Key.")

            log.info(f"[LLMQueryNode] Usando {provider_name}/{best_model} | temp={temperature} | sys={len(system)}c")

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
