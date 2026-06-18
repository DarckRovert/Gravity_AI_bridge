import sys
sys.path.insert(0, 'F:/Gravity_AI_bridge')
from core import provider_manager

print("=== SCAN DE PROVEEDORES ===")
results = provider_manager.scan_all(force=True)
for r in results:
    tag = "OK" if r.is_healthy else "XX"
    print(f"  [{tag}] {r.name:<22} cat={r.category:<8} model={r.active_model} ms={r.response_ms} keys={r.key_configured}")

print()
best_r, best_m = provider_manager.get_best()
if best_r:
    print(f"  MEJOR PROVEEDOR: {best_r.name} / {best_m}")
else:
    print("  ERROR: Ningún proveedor disponible.")
