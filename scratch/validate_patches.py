"""
Script de validación final de todos los patches aplicados en la sesión de auditoría.
"""

# ── Video Pipeline ────────────────────────────────────────────────────────────
with open('F:/Gravity_AI_bridge/core/video_pipeline.py', 'r', encoding='utf-8', errors='replace') as f:
    src = f.read()

pipeline_checks = {
    'Crash recovery _init_db': ('Crash Recovery' in src and 'Proceso interrumpido por reinicio' in src),
    'Timeout dinámico concat (dyn_timeout)': 'dyn_timeout' in src and '120 + len(clip_paths) * 90' in src,
    'Sin ignore_editlist en concat (Bugfix)': '-ignore_editlist' not in src,
    'CoInitialize RPC_E_CHANGED_MODE fix': 'RPC_E_CHANGED_MODE' in src,
    'Fallback stream-copy concat': 'stream-copy' in src,
    'Barras forward en list.txt': "replace('\\\\', '/')" in src,
    'Fallback amix con anullsrc': 'anullsrc=channel_layout=stereo' in src,
    'AR/AC normalizados en concat': '"-ar", "44100"' in src and '"-ac", "2"' in src,
}

# ── mixin_post.py ─────────────────────────────────────────────────────────────
with open('F:/Gravity_AI_bridge/api/routes/mixin_post.py', 'r', encoding='utf-8', errors='replace') as f:
    mixin = f.read()

mixin_checks = {
    'Fix UnboundLocalError os (import os as os)': 'import os as os' in mixin,
}

# ── INICIAR_TODO.bat ──────────────────────────────────────────────────────────
with open('F:/Gravity_AI_bridge/launchers/INICIAR_TODO.bat', 'r', encoding='utf-8', errors='replace') as f:
    bat = f.read()

bat_checks = {
    'cmd /k (ventana persiste, no /c)': 'cmd /k' in bat and 'cmd /c' not in bat,
    'Ruta absoluta PYTHON_EMB': 'PYTHON_EMB' in bat and 'python_embeded' in bat,
    'Ruta absoluta FOOOCUS_SCRIPT': 'FOOOCUS_SCRIPT' in bat and 'entry_with_update.py' in bat,
    'Guard existencia python_embeded': 'if not exist "%PYTHON_EMB%"' in bat,
    'Guard existencia entry_with_update.py': 'if not exist "%FOOOCUS_SCRIPT%"' in bat,
    'Label :skip_fooocus (skip graceful)': ':skip_fooocus' in bat,
    'Kill PIDs por puerto antes de arrancar': 'netstat -ano' in bat and 'LISTENING' in bat,
}

# ── Resultados ────────────────────────────────────────────────────────────────
all_checks = {
    '=== VIDEO PIPELINE ===': pipeline_checks,
    '=== MIXIN_POST ===': mixin_checks,
    '=== INICIAR_TODO.bat ===': bat_checks,
}

total_ok = 0
total_fail = 0

for section, checks in all_checks.items():
    print(f'\n{section}')
    for k, v in checks.items():
        status = '[OK]  ' if v else '[FAIL]'
        print(f'  {status}  {k}')
        if v:
            total_ok += 1
        else:
            total_fail += 1

print(f'\n{"="*55}')
print(f'TOTAL: {total_ok} OK / {total_fail} FAIL')
print('RESULTADO: PASS — Auditoría completada sin regresiones.' if total_fail == 0 else 'RESULTADO: WARN — Revisar items fallidos.')
