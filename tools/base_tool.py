"""
Gravity AI — Tool Base Classes V7.1
All tools implement Tool and return ToolResult.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ToolResult:
    success:   bool
    stdout:    str   = ""
    stderr:    str   = ""
    exit_code: int   = 0
    data:      dict  = field(default_factory=dict)
    language:  str   = ""

    def __str__(self):
        if self.success:
            return self.stdout or "✓ Ejecutado sin output"
        return f"✗ Error (exit {self.exit_code}):\n{self.stderr or self.stdout}"


class Tool(ABC):
    name:                  str  = ""
    description:           str  = ""
    requires_confirmation: bool = False

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool and return a ToolResult."""
