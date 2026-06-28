import os
import sys
import importlib.util
import hashlib
import json
from typing import Dict, Any, List
from core.logger import log

class BaseHook:
    """Clase base para todos los interceptores de Gravity AI."""
    
    # Nombre único del hook
    NAME = "BaseHook"
    # Lista de tipos de nodos a los que aplica. Si está vacío, aplica a todos.
    TARGET_NODES: List[str] = []

    def pre_execute(self, node_id: str, node_type: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecutado antes de que el nodo principal procese la entrada.
        Puede mutar los 'inputs' y debe retornarlos.
        Si se lanza una excepción aquí, la ejecución del nodo se detiene.
        """
        return inputs

    def post_execute(self, node_id: str, node_type: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecutado después de que el nodo principal retorna su resultado.
        Puede auditar o mutar el 'result' y debe retornarlo.
        """
        return result

class HookManager:
    def __init__(self):
        self.hooks: List[BaseHook] = []

    def register(self, hook: BaseHook):
        self.hooks.append(hook)
        log.info(f"[HookEngine] Interceptor cargado: {hook.NAME}")

    def run_pre_hooks(self, node_id: str, node_type: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        mutated_inputs = inputs
        for hook in self.hooks:
            if not hook.TARGET_NODES or node_type in hook.TARGET_NODES:
                try:
                    mutated_inputs = hook.pre_execute(node_id, node_type, mutated_inputs)
                except Exception as e:
                    log.warning(f"[HookEngine] {hook.NAME} falló en pre_execute para {node_id}: {e}. Ignorando error.")
        return mutated_inputs

    def run_post_hooks(self, node_id: str, node_type: str, result: Dict[str, Any]) -> Dict[str, Any]:
        mutated_result = result
        for hook in self.hooks:
            if not hook.TARGET_NODES or node_type in hook.TARGET_NODES:
                try:
                    mutated_result = hook.post_execute(node_id, node_type, mutated_result)
                except Exception as e:
                    log.warning(f"[HookEngine] {hook.NAME} falló en post_execute para {node_id}: {e}. Ignorando error.")
        return mutated_result

# Instancia global
hook_manager = HookManager()

def get_file_hash(filepath: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def autoload_hooks():
    """Importa todos los scripts .py en .agents/hooks/ previa verificación de firma de seguridad."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hooks_dir = os.path.join(base_dir, ".agents", "hooks")
    
    # [AgentShield V16.0] Security fix (CVE-2025-59536): Mover la fuente de confianza fuera del 
    # repositorio local para prevenir la auto-aprobación maliciosa en proyectos clonados.
    local_app = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    gravity_app_dir = os.path.join(local_app, "Gravity")
    os.makedirs(gravity_app_dir, exist_ok=True)
    trust_file = os.path.join(gravity_app_dir, "hooks_trust.json")
    
    if not os.path.isdir(hooks_dir):
        return

    # Cargar registro de confianza
    trusted_hashes = {}
    if os.path.exists(trust_file):
        try:
            with open(trust_file, "r", encoding="utf-8") as f:
                trusted_hashes = json.load(f)
        except Exception as e:
            log.error(f"[HookEngine] Error leyendo hooks_trust.json: {e}")

    sys.path.insert(0, hooks_dir)
    for fname in os.listdir(hooks_dir):
        if fname.endswith(".py") and not fname.startswith("_"):
            filepath = os.path.join(hooks_dir, fname)
            file_hash = get_file_hash(filepath)
            
            # AgentShield: Anti-RCE Verification
            if trusted_hashes.get(fname) != file_hash:
                log.warning(f"[AgentShield] Bloqueo de seguridad: El hook '{fname}' no tiene una firma válida o fue modificado (hash mismatch). Usa un script para firmarlo en hooks_trust.json.")
                continue

            module_name = fname[:-3]
            try:
                importlib.import_module(module_name)
            except Exception as e:
                log.warning(f"[HookEngine] No se pudo cargar el hook {fname}: {e}")
    if hooks_dir in sys.path:
        sys.path.remove(hooks_dir)

# Cargar hooks al iniciar
autoload_hooks()
