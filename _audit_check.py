import sys
import os
import json
import sqlite3
import yaml

# Cálculo dinámico del directorio base del proyecto
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

checks = {}

# 1. Provider disponible
try:
    from core import provider_manager
    best_p, best_m = provider_manager.get_best()
    checks['LLM Provider'] = f'OK - {best_p.name}/{best_m}' if best_p else 'FALLO - Sin proveedor'
except Exception as e:
    checks['LLM Provider'] = f'ERROR: {e}'

# 2. YouTube OAuth
try:
    oauth_path = os.path.join(BASE_DIR, "_integrations", "youtube_oauth.json")
    if os.path.isfile(oauth_path):
        with open(oauth_path, "r", encoding="utf-8") as f:
            d = json.load(f)
        has_refresh = bool(d.get('refresh_token'))
        checks['YouTube OAuth'] = f'OK - refresh_token={has_refresh}'
    else:
        checks['YouTube OAuth'] = 'PENDIENTE - Archivo oauth no existe'
except Exception as e:
    checks['YouTube OAuth'] = f'ERROR: {e}'

# 3. DB de videos
try:
    db_path = os.path.join(BASE_DIR, "_video_queue.sqlite")
    conn = sqlite3.connect(db_path)
    total    = conn.execute('SELECT COUNT(*) FROM video_jobs').fetchone()[0]
    done     = conn.execute("SELECT COUNT(*) FROM video_jobs WHERE status='done'").fetchone()[0]
    uploaded = conn.execute("SELECT COUNT(*) FROM video_jobs WHERE upload_status='uploaded'").fetchone()[0]
    checks['Video Queue DB'] = f'OK - {total} jobs, {done} done, {uploaded} subidos a YT'
    conn.close()
except Exception as e:
    checks['Video Queue DB'] = f'ERROR: {e}'

# 4. Config.yaml módulos monetización
try:
    config_path = os.path.join(BASE_DIR, "config.yaml")
    with open(config_path, "r", encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    modules = ['youtube', 'language_cloner', 'affiliates', 'social']
    states = {m: cfg.get(m, {}).get('enabled', False) for m in modules}
    checks['Monetizacion Modulos'] = 'OK - ' + ', '.join([f'{k}={v}' for k,v in states.items()])
except Exception as e:
    checks['Monetizacion Modulos'] = f'ERROR: {e}'

# 5. ToolEngine
try:
    from core.tools_engine import get_tool_engine
    engine = get_tool_engine(BASE_DIR)
    checks['Agentic ToolEngine'] = f'OK - {len(engine.tools)} tools: {list(engine.tools.keys())}'
except Exception as e:
    checks['Agentic ToolEngine'] = f'ERROR: {e}'

# 6. FFmpeg
ffmpeg = os.path.join(BASE_DIR, "_integrations", "ffmpeg", "ffmpeg.exe")
checks['FFmpeg'] = 'OK' if os.path.isfile(ffmpeg) else 'NO ENCONTRADO'

# 7. Afiliados config
try:
    aff = cfg.get('affiliates', {})
    links = aff.get('links', {})
    checks['Affiliates Links'] = f'OK - {len(links)} nichos configurados: {list(links.keys())}'
except Exception as e:
    checks['Affiliates Links'] = f'ERROR: {e}'

# 8. TikTok/Instagram creds
for plat in ['tiktok', 'instagram']:
    path = os.path.join(BASE_DIR, "_integrations", f"{plat}_creds.json")
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        has_key = any(bool(v) for v in data.values() if isinstance(v, str))
        checks[f'{plat.title()} Creds'] = 'OK - credenciales presentes' if has_key else 'PENDIENTE - archivo vacío'
    else:
        checks[f'{plat.title()} Creds'] = 'PENDIENTE - archivo no existe'

# 9. Knowledge base
try:
    from core import data_guardian
    knowledge_path = os.path.join(BASE_DIR, "_knowledge.json")
    kb, _ = data_guardian.load_knowledge(knowledge_path)
    rules = kb.get('persistent_rules', [])
    checks['Knowledge Base'] = f'OK - {len(rules)} reglas persistidas'
except Exception as e:
    checks['Knowledge Base'] = f'ERROR: {e}'

print('=== AUDITORIA SISTEMA GRAVITY V15.2 ===')
for k,v in checks.items():
    icon = 'OK' if v.startswith('OK') else '!!'
    print(f'[{icon}] {k}: {v}')
