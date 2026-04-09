"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         GRAVITY AI - SESSION MANAGER V9.0 PRO [Diamond-Tier Edition]         ║
║                       Sesiones con Fork/Merge + Export                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import os
import json
import time
import shutil
import copy
from datetime import datetime

try:
    from . import data_guardian as _guardian
except ImportError:
    _guardian = None


# Subimos un nivel para que la base sea la raíz de F:\Gravity_AI_bridge
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVES_DIR  = os.path.join(BASE_DIR, "_saves")
os.makedirs(SAVES_DIR, exist_ok=True)


class SessionManager:
    """
    Manages conversation sessions with branch support.
    The 'main' branch is always the current session.
    """

    def __init__(self, history_ref: list):
        """
        history_ref: reference to the live history list in AuditorCLI.
        This allows SessionManager to read/modify the active history.
        """
        self._history = history_ref
        self._current_branch = "main"
        self._branches: dict[str, list] = {"main": history_ref}

    # ── Save / Load ───────────────────────────────────────────────────────────

    def save(self, name: str, metadata: dict = None) -> str:
        path = os.path.join(SAVES_DIR, f"{name}.json")
        data = {
            "name":        name,
            "branch":      self._current_branch,
            "saved_at":    datetime.now().isoformat(),
            "metadata":    metadata or {},
            "history":     copy.deepcopy(self._history),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    def load(self, name: str) -> bool:
        path = os.path.join(SAVES_DIR, f"{name}.json")
        if not os.path.exists(path):
            return False

        if _guardian:
            # Validación y saneamiento completo
            history, warnings = _guardian.load_history_file(path)
            if warnings:
                # Imprimir advertencias sin depender de Rich (puede no estar cargado)
                for w in warnings:
                    print(f"  [Guardian] {w}")
            if not history and os.path.exists(path):
                # Si el archivo existía pero no se pudo cargar, reportar error
                print(f"  [Guardian] WARN: No se pudo recuperar la sesión '{name}'. Archivo posiblemente vacío o corrupto.")
                return False
            self._history.clear()
            self._history.extend(history)
        else:
            # Fallback sin guardian
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._history.clear()
                self._history.extend(data.get("history", []))
            except Exception as e:
                print(f"  [Guardian] Error cargando sesión: {e}")
                return False
        return True


    def list_saves(self) -> list[dict]:
        saves = []
        for fname in sorted(os.listdir(SAVES_DIR)):
            if fname.endswith(".json"):
                path  = os.path.join(SAVES_DIR, fname)
                size  = os.path.getsize(path)
                mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
                saves.append({"name": fname[:-5], "size_kb": size//1024, "modified": mtime})
        return saves

    def delete_save(self, name: str) -> bool:
        path = os.path.join(SAVES_DIR, f"{name}.json")
        if os.path.exists(path):
            os.unlink(path)
            return True
        return False

    # ── Branch Operations ─────────────────────────────────────────────────────

    def fork(self, branch_name: str) -> str:
        """Creates a new branch from current history. Returns branch name."""
        if branch_name in self._branches:
            branch_name = f"{branch_name}_{int(time.time())}"
        self._branches[branch_name] = copy.deepcopy(self._history)
        self.save(f"branch_{branch_name}")
        return branch_name

    def switch(self, branch_name: str) -> bool:
        """Switches to another branch. Returns False if branch not found."""
        # Try loading from disk if not in memory
        if branch_name not in self._branches:
            if self.load(f"branch_{branch_name}"):
                self._branches[branch_name] = copy.deepcopy(self._history)
            else:
                return False
        self._current_branch = branch_name
        self._history.clear()
        self._history.extend(self._branches[branch_name])
        return True

    def list_branches(self) -> list[str]:
        disk = [f[7:-5] for f in os.listdir(SAVES_DIR) if f.startswith("branch_") and f.endswith(".json")]
        return list(set(list(self._branches.keys()) + disk))

    def merge(self, branch_name: str, strategy: str = "append") -> bool:
        """Merges another branch's history into current."""
        source = self._branches.get(branch_name)
        if not source:
            return False
        if strategy == "append":
            # Only append messages from the branch that aren't in current
            current_contents = {m["content"] for m in self._history}
            for msg in source:
                if msg["content"] not in current_contents:
                    self._history.append(msg)
        return True

    # ── Token Optimization (V7.1) ─────────────────────────────────────────────

    def trim_history(self, max_tokens: int = 128000) -> int:
        """
        Removes oldest messages when context exceeds max_tokens.
        Preserves the first message (System Prompt).
        Returns number of messages removed.
        """
        if len(self._history) <= 2:
            return 0

        removed_count = 0
        while len(self._history) > 1:
            # Simple heuristic: chars / 4
            total_tokens = sum(len(m.get("content", "")) // 4 for m in self._history)
            if total_tokens <= max_tokens:
                break
            
            # Remove the second message (index 1), keeping index 0 (system)
            self._history.pop(1)
            removed_count += 1
            
        return removed_count

    def cleanup_reasoning(self) -> int:
        """
        Permanently removes <think> blocks and internal metadata from history.
        Used before final save or session exit.
        """
        import re
        removed_chars = 0
        # Tags to strip: <think>...</think>, <|canal>pensamiento...<channel|>
        patterns = [
            r"<think>.*?</think>",
            r"<\|canal\|>pensamiento.*?<channel\|>",
            r"<\|canal\|>pensamiento.*" # Greedy fallback if not closed
        ]
        
        for msg in self._history:
            original_len = len(msg.get("content", ""))
            content = msg.get("content", "")
            for pattern in patterns:
                content = re.sub(pattern, "", content, flags=re.DOTALL)
            
            msg["content"] = content.strip()
            removed_chars += (original_len - len(msg["content"]))
            
        return removed_chars // 4 # return approx tokens saved

    # ── Export ────────────────────────────────────────────────────────────────

    def export_html(self, path: str = None) -> str:
        """Exports current session as formatted HTML."""
        if not path:
            ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(BASE_DIR, f"session_{ts}.html")

        rows = ""
        for m in self._history:
            role  = m.get("role", "user")
            color = "#1e3a5f" if role == "user" else "#1e4f2e"
            label = "👤 Tú" if role == "user" else "🤖 Auditor"
            content = m.get("content", "").replace("<","&lt;").replace(">","&gt;")
            rows += f"""
            <div style="background:{color};border-radius:8px;padding:12px;margin:8px 0;">
                <strong style="color:#adf;">{label}</strong>
                <pre style="white-space:pre-wrap;color:#eee;font-family:monospace;margin:8px 0 0 0">{content}</pre>
            </div>"""

        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Gravity AI Session Export</title></head>
<body style="background:#111;color:#eee;font-family:sans-serif;max-width:900px;margin:auto;padding:20px">
<h1 style="color:#4af">🔗 Gravity AI Session Export</h1>
<p style="color:#888">Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Mensajes: {len(self._history)}</p>
{rows}
</body></html>"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        return path

    def export_markdown(self, path: str = None) -> str:
        if not path:
            ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(BASE_DIR, f"session_{ts}.md")
        lines = [f"# Gravity AI Session — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]
        for m in self._history:
            role  = m.get("role", "user")
            label = "**👤 Usuario**" if role == "user" else "**🤖 Auditor**"
            lines.append(f"\n---\n{label}\n\n{m.get('content','')}\n")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return path
