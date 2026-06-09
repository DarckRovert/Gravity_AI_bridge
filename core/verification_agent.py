"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — VERIFICATION AGENT V15.2 PRO [Diamond Edition]                 ║
║  Servicio de auditoría doble para cambios críticos e integridad de código.  ║
╚══════════════════════════════════════════════════════════════════════════════╝

Agente adversarial encargado de validar propuestas de cambio y planes de ejecución
antes de su aplicación definitiva en el codebase de forma thread-safe y ultra robusta.
"""

import os
import json
import re
from typing import List, Dict, Any, Optional, Tuple


class VerificationAgent:
    """
    Agente adversarial encargado de validar propuestas de cambio 
    antes de su aplicación definitiva en el codebase.
    """

    def __init__(self, bridge_config: Dict[str, Any]) -> None:
        self.config: Dict[str, Any] = bridge_config
        self.risk_patterns: List[Tuple[str, str]] = [
            (r"os\.remove", "Riesgo de borrado de archivos"),
            (r"subprocess\.run.*shell=True", "Posible inyección de comandos"),
            (r"eval\(", "Ejecución de código dinámico inseguro"),
            (r"base64\.b64decode", "Inyección de binarios potenciales"),
            (r"chmod 777", "Permisos excesivos detectados")
        ]

    def audit_edit(self, file_path: str, old_content: str, new_content: str) -> Dict[str, Any]:
        """Realiza un escaneo de seguridad y lógica sobre una edición propuesta."""
        findings: List[Dict[str, Any]] = []
        
        # 1. Escaneo de patrones de riesgo (Regex simple)
        for pattern, description in self.risk_patterns:
            if re.search(pattern, new_content) and not re.search(pattern, old_content):
                findings.append({
                    "level": "CRITICAL",
                    "category": "security",
                    "message": f"Nuevo patrón de riesgo detectado: {description}"
                })

        # 2. Análisis de integridad (Sintaxis básica según extensión)
        integrity_check = self._check_syntax(file_path, new_content)
        if not integrity_check["success"]:
            findings.append({
                "level": "WARNING",
                "category": "syntax",
                "message": f"Posible error de sintaxis: {integrity_check['error']}"
            })

        # 3. Verificación de tamaño
        size_diff: int = len(new_content) - len(old_content)
        if size_diff > 5000:
            findings.append({
                "level": "INFO",
                "category": "volume",
                "message": f"Cambio masivo detectado (+{size_diff} caracteres)."
            })

        return {
            "is_safe": not any(f["level"] == "CRITICAL" for f in findings),
            "findings": findings,
            "score": max(0, 100 - (len(findings) * 20))
        }

    def _check_syntax(self, file_path: str, content: str) -> Dict[str, Any]:
        """Intenta validar la sintaxis del contenido según la extensión del archivo."""
        ext: str = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == ".py":
                compile(content, '<string>', 'exec')
            elif ext == ".json":
                json.loads(content)
            elif ext == ".lua":
                # Validación de Lua robusta: remover comentarios antes de evaluar balanceo
                # Remueve comentarios de línea única y comentarios multilínea de Lua
                clean_content: str = re.sub(r"--.*$", "", content, flags=re.MULTILINE)
                clean_content = re.sub(r"--\[\[.*?\]\]", "", clean_content, flags=re.DOTALL)
                
                # Contar palabras clave exactas con límites de palabra (\b)
                ifs: int = len(re.findall(r"\bif\b", clean_content))
                functions: int = len(re.findall(r"\bfunction\b", clean_content))
                dos: int = len(re.findall(r"\bdo\b", clean_content))
                ends: int = len(re.findall(r"\bend\b", clean_content))
                
                if ifs + functions + dos != ends:
                    return {
                        "success": False,
                        "error": f"Desbalance de bloques Lua (if: {ifs}, function: {functions}, do: {dos} vs end: {ends})"
                    }
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        return {"success": True}

    def analyze_plan(self, steps: List[str]) -> Dict[str, Any]:
        """Audita los pasos de un plan antes de entrar en fase de ejecución."""
        risky_steps: List[str] = [
            s for s in steps 
            if "delete" in s.lower() or "remove" in s.lower() or "overwrite" in s.lower()
        ]
        return {
            "total_steps": len(steps),
            "risky_steps": len(risky_steps),
            "recommendation": "Proceder con precaución" if risky_steps else "Seguro para ejecución automática"
        }

