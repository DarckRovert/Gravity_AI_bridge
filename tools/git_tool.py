"""
Gravity AI — Git Tool + File Ops Tool V7.0
"""
import os
import re
import shutil
import subprocess
import difflib
from tools.base_tool import Tool, ToolResult


# ── Git Tool ──────────────────────────────────────────────────────────────────

class GitTool(Tool):
    name        = "git_tool"
    description = "Git operations: status, log, diff, branch"

    def execute(self, operation: str = "status", **kwargs) -> ToolResult:
        ops = {
            "status":   ["git", "status", "--short"],
            "log":      ["git", "log", "--oneline", "-15"],
            "diff":     ["git", "diff", "HEAD"],
            "branch":   ["git", "branch", "-a"],
            "stash":    ["git", "stash"],
        }
        cmd = ops.get(operation)
        if not cmd:
            return ToolResult(success=False, stderr=f"Operación '{operation}' no soportada.")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return ToolResult(
                success=(result.returncode == 0),
                stdout=result.stdout[:6000],
                stderr=result.stderr[:2000],
                exit_code=result.returncode,
            )
        except Exception as e:
            return ToolResult(success=False, stderr=str(e))


# ── File Ops Tool ─────────────────────────────────────────────────────────────

class FileOpsTool(Tool):
    name                  = "file_ops"
    description           = "Apply patches, create diffs, backup files"
    requires_confirmation = True

    def backup(self, path: str) -> ToolResult:
        """Creates a .bak copy of a file before modifying it."""
        if not os.path.exists(path):
            return ToolResult(success=False, stderr=f"Archivo no existe: {path}")
        bak = path + ".gravity.bak"
        try:
            shutil.copy2(path, bak)
            return ToolResult(success=True, stdout=f"Backup creado: {bak}")
        except Exception as e:
            return ToolResult(success=False, stderr=str(e))

    def diff(self, original_path: str, new_content: str) -> ToolResult:
        """Shows diff between existing file content and new_content string."""
        try:
            with open(original_path, "r", encoding="utf-8") as f:
                orig = f.readlines()
            new  = new_content.splitlines(keepends=True)
            diff = list(difflib.unified_diff(orig, new, fromfile=original_path, tofile="[nuevo]"))
            return ToolResult(success=True, stdout="".join(diff[:200]), language="diff")
        except Exception as e:
            return ToolResult(success=False, stderr=str(e))

    def apply_patch(self, ai_response: str) -> ToolResult:
        """
        Attempts to extract a code block from an AI response and apply it.
        Looks for patterns like:
          # Archivo: path/to/file.py
          ```python
          ... code ...
          ```
        or standard diff blocks.
        """
        # Pattern 1: "# Archivo: <path>" + code block
        match = re.search(
            r"#\s*[Aa]rchivo:\s*(.+?)\n```\w*\n(.*?)```",
            ai_response, re.DOTALL
        )
        if match:
            path, code = match.group(1).strip(), match.group(2)
            self.backup(path)
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(code)
                return ToolResult(success=True, stdout=f"✓ Aplicado a {path}")
            except Exception as e:
                return ToolResult(success=False, stderr=str(e))

        # Pattern 2: unified diff block
        diff_match = re.search(r"```diff\n(.*?)```", ai_response, re.DOTALL)
        if diff_match:
            return ToolResult(
                success=False,
                stderr="Patch diff detectado pero aplicación automática de unified diff "
                       "requiere 'patch' binary. Por ahora copia manualmente el bloque diff.",
            )

        return ToolResult(
            success=False,
            stderr="No se encontró un bloque aplicable. "
                   "Formato esperado: '# Archivo: <ruta>' seguido de bloque de código.",
        )

    def execute(self, action: str = "diff", **kwargs) -> ToolResult:
        if action == "backup":
            return self.backup(kwargs.get("path", ""))
        elif action == "diff":
            return self.diff(kwargs.get("path", ""), kwargs.get("content", ""))
        elif action == "apply":
            return self.apply_patch(kwargs.get("response", ""))
        return ToolResult(success=False, stderr=f"Acción '{action}' no reconocida.")
