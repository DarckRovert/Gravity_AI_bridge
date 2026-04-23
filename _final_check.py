import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('F:/Gravity_AI_bridge/web/dashboard.html', encoding='utf-8') as f:
    c = f.read()

checks = [
    ('GRAVITY V10.4', 'Logo V10.4 en topbar'),
    ('highlight.min.js"></script>', 'highlight.js cerrado correctamente'),
    ('runCode', 'runCode en script propio'),
    ('runWebSearch', 'runWebSearch en script propio'),
    ('runGit', 'runGit en script propio'),
    ('runGrep', 'runGrep en script propio'),
    ('panel-hitl', 'Panel HITL'),
    ('panel-firecrawl', 'Panel Firecrawl'),
    ('spawn-role', 'Role selector en Sessions'),
    ('fetchHITLPending', 'Polling HITL'),
    ('hitl-badge', 'Badge HITL sidebar'),
    ('ncias\')', 'NO hay artefacto residual'),
]
all_ok = True
for k, label in checks:
    present = k in c
    expected = not k.startswith('NO ') if True else False
    # Para el cheque negativo
    if label.startswith('NO '):
        ok = not present
    else:
        ok = present
    print('  %s: %s' % ('OK' if ok else 'FAIL', label))
    if not ok: all_ok = False

print('\nLineas totales:', c.count('\n'))
print('Tamano:', len(c), 'bytes')
print('\nRESULTADO:', 'TODO OK' if all_ok else 'HAY PROBLEMAS')
