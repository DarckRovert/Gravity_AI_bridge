"""
Gravity AI — Tool Base Classes V16.0 PRO
All tools implement Tool and return ToolResult.
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any


def safe_path_resolve(base_dir: str, target_path: str, is_write: bool = False) -> str:
    """AgentShield Ring 0 protection para tools."""
    base_abs = os.path.abspath(base_dir)
    absolute_target = os.path.abspath(os.path.join(base_abs, target_path))
    
    # Prevenir Path Traversal
    if not absolute_target.startswith(base_abs + os.sep):
        raise Exception("AgentShield blocked Path Traversal attempt.")
        
    # Prevenir escritura en archivos críticos (Ring 0)
    if is_write:
        protected_paths = [
            os.path.join(base_abs, "core"),
            os.path.join(base_abs, ".agents"),
            os.path.join(base_abs, "bridge_server.py"),
            os.path.join(base_abs, "mcp_server.py"),
        ]
        for prot in protected_paths:
            if absolute_target.startswith(prot) or absolute_target == prot:
                raise Exception("AgentShield Core Protection blocked write attempt to system critical path.")
                
    return absolute_target


@dataclass
class ToolResult:
    """
    Representa el resultado estandarizado de la ejecución de cualquier herramienta.
    """

    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    data: Dict[str, Any] = field(default_factory=dict)
    language: str = ""

    def __str__(self) -> str:
        if self.success:
            return self.stdout or "✓ Ejecutado sin output"
        return f"✗ Error (exit {self.exit_code}):\n{self.stderr or self.stdout}"


class Tool(ABC):
    """
    Clase base abstracta para todas las herramientas del ecosistema Gravity AI.
    """

    name: str = ""
    description: str = ""
    requires_confirmation: bool = False

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """
        Ejecuta la herramienta con los argumentos provistos y devuelve un ToolResult.
        """
