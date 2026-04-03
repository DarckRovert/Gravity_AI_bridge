import sys
import json
import os
from provider_scanner import ProviderScanner

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "_settings.json")
TEMP_BEST_MODEL_TXT = os.path.join(BASE_DIR, "_install_best_model.txt")

try:
    scans = ProviderScanner.scan_all(use_cache=True)
    best_prov, best_mod = ProviderScanner.auto_select_best(scans)

    if best_prov:
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
            
        data["provider"] = best_prov.protocol
        data["api_url"] = best_prov.url
        data["last_model"] = best_mod
        
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        print(f"[OK] Settings V4 actualizados para usar -> {best_prov.name} ({best_mod})")
        
        with open(TEMP_BEST_MODEL_TXT, "w", encoding="utf-8") as f:
            f.write(best_mod)
    else:
        print("[!] Ningun proveedor encontrado. Mantenemos defaults.")
except Exception as e:
    print(f"[X] Fallo al auto-configurar: {e}")
    sys.exit(1)
