"""
Gravity Workflow Node: ScriptBuilder
Transforma texto libre en un guión estructurado de N escenas para el Video Studio.
"""

from core.workflow_engine import GravityNode, registry
from core.logger import log


@registry.register
class ScriptBuilderNode(GravityNode):
    NODE_TYPE = "ScriptBuilder"
    DESCRIPTION = "Convierte un texto/topic en un guión de N escenas con visual, narración y emoción."
    INPUT_SCHEMA = {
        "topic": "TEXT",
        "n_scenes": "INT",   # default 6
        "style": "TEXT",     # default "documental"
        "lang": "TEXT",      # default "es"
        "use_lore": "BOOL",  # default True
    }
    OUTPUT_SCHEMA = {
        "scenes": "JSON_LIST",  # lista de {narration, visual, emotion, title}
        "title": "TEXT",
        "style": "TEXT",
        "n_scenes": "INT",
    }

    def execute(self, inputs: dict) -> dict:
        from core.video.script_builder import _generate_script, DEFAULT_STYLE

        topic: str = inputs.get("topic", "")
        n_scenes: int = int(inputs.get("n_scenes") or self.config.get("n_scenes") or 6)
        style: str = inputs.get("style") or self.config.get("style") or DEFAULT_STYLE
        lang: str = inputs.get("lang") or self.config.get("lang") or "es"
        use_lore: bool = bool(inputs.get("use_lore") if "use_lore" in inputs else True)

        log.info(f"[ScriptBuilderNode] Generando guión: '{topic[:60]}' | escenas={n_scenes} | estilo={style}")

        try:
            script_data = _generate_script(
                topic=topic,
                n_scenes=n_scenes,
                style=style,
                narration_lang=lang,
                use_lore=use_lore,
            )

            scenes = script_data.get("scenes", [])
            title = script_data.get("title", topic[:60])

            return {
                "scenes": scenes,
                "title": title,
                "style": style,
                "n_scenes": len(scenes),
            }

        except Exception as exc:
            log.error(f"[ScriptBuilderNode] Error: {exc}")
            raise
