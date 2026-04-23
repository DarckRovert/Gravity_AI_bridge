import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('F:/Gravity_AI_bridge/web/dashboard.html', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar exactamente las lineas con el artefacto
for i, line in enumerate(lines):
    if "ncias')" in line:
        print(f"ARTEFACTO en linea {i+1}: {repr(line)}")
        # Imprimir contexto
        for j in range(max(0, i-3), min(len(lines), i+4)):
            marker = ">>>" if j == i else "   "
            print(f"  {marker} {j+1}: {repr(lines[j][:80])}")
        print()
