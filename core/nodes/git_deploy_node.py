import os
import subprocess
from typing import Dict, Any

from core.workflow_engine import GravityNode, registry
from core.logger import log

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@registry.register

class GitDeployNode(GravityNode):
    """
    Ejecuta comandos de Git para desplegar cambios automáticamente.
    Inputs requeridos:
      - repository_path: Ruta absoluta al repositorio local de git.
      - commit_message: Mensaje del commit.
    Inputs opcionales:
      - files_to_add: Qué archivos añadir (default: "." para todo).
      - push: Boolean si debe hacer git push (default: True).
    """
    
    NODE_TYPE = "GitDeploy"
    DESCRIPTION = "Ejecuta comandos de Git para desplegar cambios automáticamente."
    INPUT_SCHEMA = {
        "repository_path": "TEXT",
        "commit_message": "TEXT",
        "files_to_add": "TEXT",
        "push": "BOOL"
    }
    OUTPUT_SCHEMA = {
        "status": "TEXT",
        "commit_message": "TEXT",
        "output": "TEXT"
    }
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        repo_path = inputs.get("repository_path")
        msg = inputs.get("commit_message", "Automated deploy by Gravity")
        files = inputs.get("files_to_add", ".")
        do_push = inputs.get("push", True)

        if not repo_path or not os.path.exists(repo_path):
            raise ValueError(f"[{self.node_id}] Ruta de repositorio invalida: {repo_path}")

        try:
            # git add
            subprocess.run(
                ["git", "add", files],
                cwd=repo_path,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # git commit
            # (If no changes, it will fail, we handle it)
            commit_res = subprocess.run(
                ["git", "commit", "-m", msg],
                cwd=repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            commit_output = commit_res.stdout.decode("utf-8", errors="ignore")
            if commit_res.returncode != 0:
                if "nothing to commit" in commit_output or "working tree clean" in commit_output:
                    log.info(f"[{self.__class__.__name__}] Nada que commitear en {repo_path}.")
                    return {"status": "no_changes", "commit_message": msg, "output": "nothing to commit"}
                else:
                    err = commit_res.stderr.decode("utf-8", errors="ignore")
                    raise RuntimeError(f"Git commit failed: {err}")

            log.info(f"[{self.__class__.__name__}] Commit realizado: {msg}")

            # git push
            if do_push:
                # Primero intentamos un pull --rebase para evitar conflictos
                subprocess.run(
                    ["git", "pull", "--rebase"],
                    cwd=repo_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                push_res = subprocess.run(
                    ["git", "push"],
                    cwd=repo_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                if push_res.returncode != 0:
                    push_err = push_res.stderr.decode("utf-8", errors="ignore").strip()
                    log.warning(
                        f"[{self.__class__.__name__}] Git push falló (¿sin internet o conflicto?): {push_err}. "
                        "El artículo fue guardado localmente. Se reintentará en el próximo deploy."
                    )
                    return {"status": "push_failed", "commit_message": msg, "output": push_err}
                log.info(f"[{self.__class__.__name__}] Push realizado exitosamente.")

            return {"status": "deployed", "commit_message": msg, "output": commit_output}

        except subprocess.CalledProcessError as e:
            err = e.stderr.decode("utf-8", errors="ignore") if e.stderr else str(e)
            log.error(f"[{self.__class__.__name__}] Error Git: {err}")
            raise RuntimeError(f"Error en GitDeployNode: {err}")
