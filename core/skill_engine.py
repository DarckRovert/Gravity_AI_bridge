import os
import yaml

def load_skill(skill_path: str) -> dict:
    """
    Carga un archivo SKILL.md y extrae su frontmatter (YAML) y su cuerpo (Markdown).
    Retorna un diccionario con 'name', 'description' (del YAML) y 'instructions' (del body).
    """
    if not os.path.exists(skill_path):
        return {"error": f"Skill no encontrada en {skill_path}"}
        
    with open(skill_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    parts = content.split("---")
    
    if len(parts) >= 3 and content.startswith("---"):
        # Tiene frontmatter YAML
        frontmatter_str = parts[1].strip()
        body_str = "---".join(parts[2:]).strip()
        
        try:
            metadata = yaml.safe_load(frontmatter_str) or {}
        except yaml.YAMLError:
            metadata = {}
            
        return {
            "name": metadata.get("name", "Unknown Skill"),
            "description": metadata.get("description", ""),
            "metadata": metadata,
            "instructions": body_str
        }
    else:
        # No tiene frontmatter, todo es body
        return {
            "name": os.path.basename(os.path.dirname(skill_path)) or "Unknown Skill",
            "description": "Sin descripci\u00f3n.",
            "metadata": {},
            "instructions": content.strip()
        }

def get_skill_instructions(skill_name: str) -> str:
    """
    Busca una skill por su nombre de directorio dentro de .agents/skills/ y devuelve sus instrucciones.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    skill_path = os.path.join(base_dir, ".agents", "skills", skill_name, "SKILL.md")
    
    data = load_skill(skill_path)
    if "error" in data:
        return ""
    
    return data.get("instructions", "")
