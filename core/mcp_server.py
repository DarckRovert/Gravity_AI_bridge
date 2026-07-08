import sqlite3
import os
from typing import Dict, Callable, List
from core.logger import log

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class MCPTool:
    def __init__(self, name: str, description: str, parameters: dict, func: Callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func

    def to_dict(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

class MCPServer:
    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}

    def register_tool(self, name: str, description: str, parameters: dict):
        def decorator(func: Callable):
            self.tools[name] = MCPTool(name, description, parameters, func)
            log.info(f"[MCPServer] Herramienta registrada: {name}")
            return func
        return decorator

    def get_tools_schema(self) -> List[dict]:
        return [tool.to_dict() for tool in self.tools.values()]

    def execute_tool(self, name: str, args: dict) -> str:
        if name not in self.tools:
            return f"Error: Tool '{name}' not found."
        try:
            result = self.tools[name].func(**args)
            return str(result)
        except Exception as e:
            return f"Error executing '{name}': {str(e)}"

# Instancia global del servidor MCP
mcp_server = MCPServer()

# ==========================================
# DEFINICIÓN DE HERRAMIENTAS (TOOLS)
# ==========================================

def safe_path_resolve(base_dir: str, target_path: str) -> str:
    """AgentShield: Previene Path Traversal resolviendo rutas absolutas y verificando el prefijo."""
    base_abs = os.path.abspath(base_dir)
    absolute_target = os.path.abspath(os.path.join(base_abs, target_path))
    # Asegurar que termina en sep para evitar bypass de hermanos (ej: data vs database.sqlite)
    if not absolute_target.startswith(base_abs + os.sep) and absolute_target != base_abs:
        raise ValueError("Path traversal attempt blocked by AgentShield.")
    return absolute_target

@mcp_server.register_tool(
    name="list_video_jobs",
    description="Lista los últimos N trabajos de video y sus estados actuales desde la base de datos.",
    parameters={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Número máximo de trabajos a devolver (default: 5)"
            }
        },
        "required": []
    }
)
def list_video_jobs(limit: int = 5) -> str:
    import time
    try:
        from core.db_migrator import _get_db_path
        db_path = _get_db_path("video_queue")
    except ValueError as e:
        return f"AgentShield Security Error: {e}"
        
    if not os.path.exists(db_path):
        return "Error: Database _video_queue.sqlite not found."
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with sqlite3.connect(db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
            cursor.execute("SELECT id, topic, status, created_at FROM video_jobs ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            if not rows:
                return "No hay trabajos de video."
            
            result = "Últimos trabajos de video:\n"
            for r in rows:
                result += f"- ID: {r[0]}, Tema: {r[1]}, Estado: {r[2]}, Creado: {r[3]}\n"
            return result
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                time.sleep(1)
                continue
            return f"DB Error: {e}"
        except Exception as e:
            return f"DB Error: {e}"

@mcp_server.register_tool(
    name="search_duckduckgo",
    description="Realiza una búsqueda web en DuckDuckGo y devuelve un resumen de los resultados.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "El término de búsqueda"
            }
        },
        "required": ["query"]
    }
)
def search_duckduckgo(query: str) -> str:
    # Usaremos duckduckgo_search si está disponible, o un mock si no.
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if not results:
                return "No se encontraron resultados."
            return "\n".join([f"[{r['title']}]({r['href']}): {r['body']}" for r in results])
    except ImportError:
        return "Error: La librería duckduckgo_search no está instalada. Ejecute: pip install duckduckgo-search"
    except Exception as e:
        return f"Error en búsqueda: {e}"
