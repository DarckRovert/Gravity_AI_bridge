"""
Gravity AI — Parcheador de Base de Datos y Automatización SQL (vMaNGOS CLI-Patch)
Estándar: Diamond-Tier (Tipado formal estricto, evasión de consolas emergentes y tolerancia total a fallas de red).
"""
import urllib.request
import json
import os
import subprocess
import sys
from typing import List, Dict, Any, Optional

# Ruta absoluta del ejecutable de MySQL (según topología del proyecto)
MYSQL_EXE: str = r"F:\Project_Anarchy_Core\MaNGOS\mysql5\bin\mysql.exe"
DB_USER: str = "root"
DB_PASS: str = "root"
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.key_manager import KeyManager
    DB_PASS = KeyManager.get_key("wow_vanilla_db_pass") or "root"
except Exception:
    pass
DB_NAME: str = "mangos"

# Migraciones requeridas extraídas de Server.log
migrations: List[str] = [
    "20230320180317", "20240527204002", "20240602222638",
    "20240611051049", "20240617090632", "20240617091421",
    "20240617091747", "20240617175949", "20240619170801",
    "20240620145249", "20240620151038", "20240620155345",
    "20240620215210", "20240623222319", "20240625223058"
]


def main() -> None:
    """
    Punto de entrada de ejecución del parcheador.
    Descarga recursivamente las migraciones desde GitHub e inyecta el contenido SQL
    directamente a la base de datos local usando mysql.exe de forma segura.
    """
    print("Iniciando inmovilizador de SQL [vMaNGOS CLI-Patch]...")
    
    if not os.path.exists(MYSQL_EXE):
        print(f"ERROR: No se encontró el ejecutable de MySQL en {MYSQL_EXE}")
        return

    print("Obteniendo árbol remoto de migraciones desde GitHub...")
    api_url: str = "https://api.github.com/repos/vmangos/core/contents/sql/migrations?ref=development"
    req: urllib.request.Request = urllib.request.Request(api_url, headers={'User-Agent': 'GravityBridge-v10'})
    
    try:
        # Timeout explícito de 15 segundos para evitar bloqueos por latencia de la red
        with urllib.request.urlopen(req, timeout=15) as resp:
            files: List[Dict[str, Any]] = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print("Fallo obteniendo índice de github:", e)
        return
        
    remote_files: Dict[str, str] = {}
    for f in files:
        if f.get('type') == 'file' and 'name' in f and 'download_url' in f:
            remote_files[f['name']] = f['download_url']
    
    # Impedir la visualización de consolas emergentes en Windows al llamar a mysql.exe
    creationflags: int = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW

    for m_id in migrations:
        target_url: Optional[str] = None
        nombre_archivo: str = ""
        for name, d_url in remote_files.items():
            if m_id in name:
                target_url = d_url
                nombre_archivo = name
                break
                
        if not target_url:
            print(f"[x] No se encontró remotamente archivo para {m_id}")
            continue
            
        print(f"\nDescargando {nombre_archivo}...")
        try:
            rq: urllib.request.Request = urllib.request.Request(target_url, headers={'User-Agent': 'GravityBridge-v10'})
            with urllib.request.urlopen(rq, timeout=15) as rs:
                sql_content: bytes = rs.read() # Leer como bytes
            
            if sql_content:
                print(f"Inyectando {m_id} vía mysql.exe...")
                # Usamos subprocess con input para evitar problemas de DELIMITER en drivers de Python
                cmd: List[str] = [MYSQL_EXE, f"-u{DB_USER}", f"-p{DB_PASS}", DB_NAME]
                process = subprocess.Popen(
                    cmd, 
                    stdin=subprocess.PIPE, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    creationflags=creationflags
                )
                stdout, stderr = process.communicate(input=sql_content, timeout=30)
                
                if process.returncode == 0:
                    print(f"[OK] Migración {m_id} aplicada.")
                else:
                    print(f"[ERROR] Fallo en la inyección de {m_id}:")
                    print(stderr.decode('utf-8', errors='ignore'))
        except subprocess.TimeoutExpired:
            print(f"[ERROR] Excedido el límite de tiempo (30s) al aplicar la migración {m_id}.")
        except Exception as e:
            print(f"Error procesando migración {m_id}: {e}")
            
    print("\nProceso de parcheo finalizado.")


if __name__ == "__main__":
    main()
