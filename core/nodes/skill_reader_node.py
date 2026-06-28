from typing import Dict, Any
from core.workflow_engine import GravityNode, registry
from core.logger import log
from core.skill_engine import get_skill_instructions

@registry.register
class SkillReaderNode(GravityNode):
    NODE_TYPE = "SkillReader"
    DESCRIPTION = "Lee y extrae instrucciones de una skill desde .agents/skills/."
    INPUT_SCHEMA = {
        "skill_name": "TEXT"      # Nombre de la carpeta de la skill
    }
    OUTPUT_SCHEMA = {
        "content": "TEXT"         # Instrucciones de la skill (markdown)
    }

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        skill_name = inputs.get("skill_name", "")
        if not skill_name:
            raise ValueError(f"[{self.node_id}] No se especificó el skill_name.")

        try:
            instructions = get_skill_instructions(skill_name)
            if not instructions:
                log.warning(f"[{self.__class__.__name__}] La skill {skill_name} no existe o está vacía.")
                return {"content": ""}

            log.info(f"[{self.__class__.__name__}] Skill leída: {skill_name} ({len(instructions)} chars)")
            return {"content": instructions}
        except Exception as e:
            log.error(f"[{self.__class__.__name__}] Error leyendo skill {skill_name}: {e}")
            raise
