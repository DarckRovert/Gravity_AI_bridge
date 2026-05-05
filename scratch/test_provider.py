import sys
import os
sys.path.insert(0, r"F:\Gravity_AI_bridge")
from core import provider_manager

print("Buscando el mejor proveedor...")
best, model = provider_manager.get_best()
print(f"Mejor: {best.name} / {model}")

print("Llamando a complete...")
try:
    res = provider_manager.complete(
        [{"role": "user", "content": "Hola, genera 1 frase corta"}],
        model=model,
        provider=best.name,
        options={"temperature": 0.7, "max_tokens": 50}
    )
    print("Respuesta:")
    print(res)
except Exception as e:
    print(f"Excepcion: {e}")
