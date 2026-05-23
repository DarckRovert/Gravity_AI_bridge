"""
Gravity AI — Tool Base Classes V15.0 PRO
All tools implement Tool and return ToolResult.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class ToolResult:
    """
    Representa el resultado estandarizado de la ejecución de cualquier herramienta.
    """
    success:   bool
    stdout:    str   = ""
    stderr:    str   = ""
    exit_code: int   = 0
    data:      Dict[str, Any] = field(default_factory=dict)
    language:  str   = ""

    def __str__(self) -> str:
        if self.success:
            return self.stdout or "✓ Ejecutado sin output"
        return f"✗ Error (exit {self.exit_code}):\n{self.stderr or self.stdout}"


class Tool(ABC):
    """
    Clase base abstracta para todas las herramientas del ecosistema Gravity AI.
    """
    name:                  str  = ""
    description:           str  = ""
    requires_confirmation: bool = False

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """
        Ejecuta la herramienta con los argumentos provistos y devuelve un ToolResult.
        """

