import urllib.request
import json
import os
import subprocess
import sys

# Ruta del ejecutable de MySQL (según tu estructura)
MYSQL_EXE = r"F:\Project_Anarchy_Core\MaNGOS\mysql5\bin\mysql.exe"
DB_USER = "root"
DB_PASS = "root"
DB_NAME = "mangos"

# Migraciones requeridas extraidas de Server.log
migrations = [
    "20230320180317", "20240527204002", "20240602222638",
    "20240611051049", "20240617090632", "20240617091421",
    "20240617091747", "20240617175949", "20240619170801",
    "20240620145249", "20240620151038", "20240620155345",
    "20240620215210", "20240623222319", "20240625223058"
]

def main():
    print("Iniciando inmovilizador de SQL [vMaNGOS CLI-Patch]...")
    
    if not os.path.exists(MYSQL_EXE):
        print(f"ERROR: No se encontro el ejecutable de MySQL en {MYSQL_EXE}")
        return

    print("Obteniendo arbol remoto de migraciones desde GitHub...")
    api_url = "https://api.github.com/repos/vmangos/core/contents/sql/migrations?ref=development"
    req = urllib.request.Request(api_url, headers={'User-Agent': 'GravityBridge-v10'})
    try:
        resp = urllib.request.urlopen(req)
        files = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print("Fallo obteniendo indice de github:", e)
        return
        
    remote_files = {}
    for f in files:
        if f['type'] == 'file':
            remote_files[f['name']] = f['download_url']
    
    for m_id in migrations:
        target_url = None
        for name, d_url in remote_files.items():
            if m_id in name:
                target_url = d_url
                nombre_archivo = name
                break
                
        if not target_url:
            print(f"[x] No se encontro remotamente archivo para {m_id}")
            continue
            
        print(f"\nDescargando {nombre_archivo}...")
        try:
            rq = urllib.request.Request(target_url, headers={'User-Agent': 'GravityBridge-v10'})
            rs = urllib.request.urlopen(rq)
            sql_content = rs.read() # Read as bytes
            
            if sql_content:
                print(f"Inyectando {m_id} via mysql.exe...")
                # Usamos subprocess con input para evitar problemas de DELIMITER en drivers de Python
                cmd = [MYSQL_EXE, f"-u{DB_USER}", f"-p{DB_PASS}", DB_NAME]
                process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate(input=sql_content)
                
                if process.returncode == 0:
                    print(f"[OK] Migracion {m_id} aplicada.")
                else:
                    print(f"[ERROR] Fallo en la inyeccion de {m_id}:")
                    print(stderr.decode('utf-8', errors='ignore'))
        except Exception as e:
            print(f"Error procesando migracion {m_id}: {e}")
            
    print("\nProceso de parcheo finalizado.")

if __name__ == "__main__":
    main()
