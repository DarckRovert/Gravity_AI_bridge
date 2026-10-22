"""
=============================================================================
        GRAVITY AI — PROGRESSION GOVERNOR DAEMON V1.0 PRO
        Orquestador Autónomo de Eras y Progresión Temporal de Reinos
=============================================================================
Gobernador temporal para Project JAIna (AzerothCore 3.3.5a):
  - Administra el ciclo evolutivo de eras (Vanilla -> TBC -> WotLK -> Beyond)
  - Coordina cambios de fase en caliente sin downtime vía SOAP y Eluna
  - Emite proclamas y crónicas narrativas de Lady Jaina
  - Mantiene sincronizado el Single Source of Truth con el portal web
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.logger import log
from core import game_server_manager
from core.soap_client import AzerothCoreSOAPClient
from core.config_manager import config

WEB_SSOT_PATH = r"E:\ProjectJaina_Web\data\progression.json"
AUDIT_FILE = os.path.join(BASE_DIR, "_audit_log.jsonl")

class ProgressionGovernor:
    """
    Gobernador Autónomo de Progresión Temporal para Project JAIna.
    """

    def __init__(self, server_id: str = "project_jaina"):
        self.server_id = server_id
        self._load_config()

    def _load_config(self):
        cfg = config.get("game_servers", {}).get(self.server_id, {})
        self.soap_host = cfg.get("soap_host", "127.0.0.1")
        self.soap_port = int(cfg.get("soap_port", 7878))
        self.soap_user = cfg.get("soap_user", "DARCK")
        self.soap_pass = cfg.get("soap_pass", "darck")
        self.soap_ns = cfg.get("soap_namespace", "urn:AC")

    def _get_soap_client(self) -> AzerothCoreSOAPClient:
        return AzerothCoreSOAPClient(
            host=self.soap_host,
            port=self.soap_port,
            username=self.soap_user,
            password=self.soap_pass,
            namespace=self.soap_ns
        )

    def _append_audit(self, entry: Dict[str, Any]) -> None:
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        entry["agent"] = "ProgressionGovernor"
        try:
            with open(AUDIT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def get_progression_data(self) -> Dict[str, Any]:
        """Lee el archivo Single Source of Truth de la web."""
        if os.path.exists(WEB_SSOT_PATH):
            try:
                with open(WEB_SSOT_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                log.warning(f"[ProgressionGovernor] Error leyendo {WEB_SSOT_PATH}: {e}")
        return {"active_phase_id": "tbc", "phases": []}

    def set_phase(self, new_phase_id: str, changed_by: str = "Gravity AI Governor") -> Dict[str, Any]:
        """
        Ejecuta la ceremonia integral de transición de fase:
        1. Valida existencia de la fase en SSOT
        2. Actualiza SSOT en disco
        3. Inyecta comando GM vía SOAP (.phase set <id>)
        4. Inyecta anuncio de lore de Lady Jaina
        5. Recarga Eluna (.reload eluna)
        6. Audita la acción
        """
        data = self.get_progression_data()
        phases = data.get("phases", [])
        target_phase = None
        target_idx = -1

        for idx, p in enumerate(phases):
            if p.get("id", "").lower() == new_phase_id.lower():
                target_phase = p
                target_idx = idx
                break

        if not target_phase:
            return {"ok": False, "error": f"Fase '{new_phase_id}' no encontrada en el catálogo."}

        # 1. Actualizar estados en SSOT
        for idx, p in enumerate(phases):
            if idx < target_idx:
                p["status"] = "completed"
                p["status_label"] = "COMPLETADA"
            elif idx == target_idx:
                p["status"] = "active"
                p["status_label"] = "FASE ACTUAL"
            else:
                p["status"] = "upcoming"
                p["status_label"] = "LÍNEA DE FASES"

        data["active_phase_id"] = target_phase["id"]
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        data["last_changed_by"] = changed_by

        try:
            with open(WEB_SSOT_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log.info(f"[ProgressionGovernor] SSOT web actualizado a '{new_phase_id}'.")
        except Exception as e:
            log.warning(f"[ProgressionGovernor] No se pudo escribir SSOT: {e}")

        # 2. Despacho SOAP al servidor de juego
        soap = self._get_soap_client()
        soap_results = []

        # A. Actualizar fase en Eluna
        res_cmd = soap.execute_command(f".phase set {target_phase['id']}")
        soap_results.append({"cmd": f".phase set {target_phase['id']}", "res": res_cmd})

        # B. Proclama de Lady Jaina
        lore = target_phase.get("jaina_lore", "")
        if lore:
            clean_lore = lore.replace('«', '').replace('»', '').replace('"', '')
            res_lore = soap.execute_command(f".announce [Lady Jaina] {clean_lore}")
            soap_results.append({"cmd": "announce lore", "res": res_lore})

        # C. Recarga en caliente de Eluna
        res_reload = soap.execute_command(".reload eluna")
        soap_results.append({"cmd": ".reload eluna", "res": res_reload})

        self._append_audit({
            "action": "phase_transition",
            "from_phase": data.get("active_phase_id"),
            "to_phase": target_phase["id"],
            "phase_name": target_phase.get("name"),
            "level_cap": target_phase.get("level_cap"),
            "changed_by": changed_by,
            "soap_results": soap_results
        })

        return {
            "ok": True,
            "active_phase": target_phase["id"],
            "phase_name": target_phase.get("name"),
            "level_cap": target_phase.get("level_cap"),
            "soap_results": soap_results
        }

governor = ProgressionGovernor()
