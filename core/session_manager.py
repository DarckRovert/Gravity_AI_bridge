"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         GRAVITY AI - SESSION MANAGER V15.1 PRO [Diamond-Tier Edition]         ║
║                       Sesiones con Fork/Merge + Export                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import os
import json
import time
import shutil
import copy
import threading
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple

try:
    from . import data_guardian as _guardian
except ImportError:
    _guardian = None


# Subimos un nivel para que la base sea la raíz de F:\Gravity_AI_bridge
BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVES_DIR: str = os.path.join(BASE_DIR, "_saves")
os.makedirs(SAVES_DIR, exist_ok=True)


class SessionManager:
    """
    Manages conversation sessions with branch support.
    The 'main' branch is always the current session.
    All operations are fully thread-safe through a reentrant instance lock.
    """

    def __init__(self, history_ref: List[Dict[str, Any]]) -> None:
        """
        history_ref: reference to the live history list in AuditorCLI.
        This allows SessionManager to read/modify the active history.
        """
        self._lock = threading.RLock()
        with self._lock:
            self._history = history_ref
            self._current_branch = "main"
            # Guardamos una copia aislada en _branches para evitar que clear() vacíe la referencia compartida
            self._branches: Dict[str, List[Dict[str, Any]]] = {"main": copy.deepcopy(history_ref)}

    # ── Save / Load ───────────────────────────────────────────────────────────

    def save(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Saves the current session history and metadata to a JSON file.
        Fully synchronized to prevent file corruption in concurrent environments.
        """
        with self._lock:
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
        """
        Loads session history from a JSON file. Sanitizes and validates the history.
        Returns True if successful, False otherwise.
        """
        with self._lock:
            path = os.path.join(SAVES_DIR, f"{name}.json")
            if not os.path.exists(path):
                return False

            if _guardian:
                # Validación y saneamiento completo con Data Guardian
                history, warnings = _guardian.load_history_file(path)
                if warnings:
                    for w in warnings:
                        print(f"  [Guardian] {w}")
                if not history and os.path.exists(path):
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
            # Sincronizamos la rama activa en memoria con la nueva carga
            self._branches[self._current_branch] = copy.deepcopy(self._history)
            return True

    def list_saves(self) -> List[Dict[str, Any]]:
        """
        Lists all saved sessions with size and modification timestamp.
        """
        with self._lock:
            saves = []
            try:
                for fname in sorted(os.listdir(SAVES_DIR)):
                    if fname.endswith(".json"):
                        path  = os.path.join(SAVES_DIR, fname)
                        size  = os.path.getsize(path)
                        mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
                        saves.append({"name": fname[:-5], "size_kb": size // 1024, "modified": mtime})
            except Exception as e:
                print(f"  [SessionManager] Error listando guardados: {e}")
            return saves

    def delete_save(self, name: str) -> bool:
        """
        Deletes a saved session JSON file from disk.
        """
        with self._lock:
            path = os.path.join(SAVES_DIR, f"{name}.json")
            if os.path.exists(path):
                try:
                    os.unlink(path)
                    return True
                except Exception as e:
                    print(f"  [SessionManager] Error eliminando guardado: {e}")
            return False

    # ── Branch Operations ─────────────────────────────────────────────────────

    def fork(self, branch_name: str) -> str:
        """Creates a new branch from current history. Returns branch name."""
        with self._lock:
            if branch_name in self._branches:
                branch_name = f"{branch_name}_{int(time.time())}"
            self._branches[branch_name] = copy.deepcopy(self._history)
            self.save(f"branch_{branch_name}")
            return branch_name

    def switch(self, branch_name: str) -> bool:
        """Switches to another branch. Returns False if branch not found."""
        with self._lock:
            # 1. Persistir la rama que estamos dejando activa en memoria
            self._branches[self._current_branch] = copy.deepcopy(self._history)

            # 2. Cargar la nueva rama si no está en memoria
            if branch_name not in self._branches:
                if self.load(f"branch_{branch_name}"):
                    self._branches[branch_name] = copy.deepcopy(self._history)
                else:
                    return False
            
            # 3. Hacer el switch atómico actualizando la referencia de historial
            self._current_branch = branch_name
            self._history.clear()
            self._history.extend(copy.deepcopy(self._branches[branch_name]))
            return True

    def list_branches(self) -> List[str]:
        """Lists all memory and disk branches."""
        with self._lock:
            disk = []
            try:
                disk = [f[7:-5] for f in os.listdir(SAVES_DIR) if f.startswith("branch_") and f.endswith(".json")]
            except Exception:
                pass
            return list(set(list(self._branches.keys()) + disk))

    def merge(self, branch_name: str, strategy: str = "append") -> bool:
        """Merges another branch's history into current."""
        with self._lock:
            source = self._branches.get(branch_name)
            if not source:
                return False
            if strategy == "append":
                # Only append messages from the branch that aren't in current
                current_contents = {m.get("content", "") for m in self._history}
                for msg in source:
                    if msg.get("content", "") not in current_contents:
                        self._history.append(copy.deepcopy(msg))
            return True

    # ── MemDir (V15.1 PRO) ────────────────────────────────────────────────────────
    
    def inject_mem_dir(self, workspace_path: str) -> int:
        """
        Escanea el workspace_path buscando un directorio '.gravity_mem' o un archivo 'MEMORY.md'.
        Si los encuentra, inyecta su contenido en el prompt del sistema o como un bloque de contexto
        al inicio del historial, imitando el sistema MemDir de OpenClaude.
        Retorna la cantidad de tokens aproximados inyectados.
        """
        with self._lock:
            mem_file = os.path.join(workspace_path, "MEMORY.md")
            mem_dir = os.path.join(workspace_path, ".gravity_mem")
            
            mem_content: List[str] = []
            if os.path.exists(mem_file):
                try:
                    with open(mem_file, "r", encoding="utf-8") as f:
                        mem_content.append(f"--- MEMORY.md ---\n{f.read()}\n")
                except Exception:
                    pass
                    
            if os.path.exists(mem_dir) and os.path.isdir(mem_dir):
                try:
                    for root, _, files in os.walk(mem_dir):
                        for file in files:
                            if file.endswith(".md") or file.endswith(".txt"):
                                try:
                                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                                        mem_content.append(f"--- {file} ---\n{f.read()}\n")
                                except Exception:
                                    pass
                except Exception:
                    pass
                                
            if not mem_content:
                return 0
                
            full_injection = "\n".join(mem_content)
            
            # Inyectar en el system prompt (primer elemento del historial)
            if self._history and self._history[0].get("role") == "system":
                # Evitar inyección duplicada
                if "--- MEMORY.md ---" not in self._history[0].get("content", ""):
                    self._history[0]["content"] = self._history[0].get("content", "") + f"\n\n[MEMDIR CONTEXT]\n{full_injection}"
            else:
                self._history.insert(0, {"role": "system", "content": f"[MEMDIR CONTEXT]\n{full_injection}"})
                
            return len(full_injection) // 4

    # ── Token Optimization (V15.1 PRO) ─────────────────────────────────────────────

    def trim_history(self, max_tokens: int = 128000) -> int:
        """
        Removes oldest messages when context exceeds max_tokens.
        Preserves the first message (System Prompt).
        Returns number of messages removed.
        """
        with self._lock:
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
        with self._lock:
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

    def export_html(self, path: Optional[str] = None) -> str:
        """Exports current session as formatted HTML."""
        with self._lock:
            if not path:
                ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = os.path.join(BASE_DIR, f"session_{ts}.html")

            rows = ""
            for m in self._history:
                role  = m.get("role", "user")
                color = "#1e3a5f" if role == "user" else "#1e4f2e"
                label = "👤 Tú" if role == "user" else "🤖 Auditor"
                content = m.get("content", "").replace("<", "&lt;").replace(">", "&gt;")
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

    def export_markdown(self, path: Optional[str] = None) -> str:
        """Exports current session as markdown."""
        with self._lock:
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
