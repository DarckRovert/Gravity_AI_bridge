import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.provider_manager import stream, ProviderRegistry


def test_autonomous_router():
    print("=====================================================")
    print(" GRAVITY AI - TEST DE ENRUTAMIENTO Y MEMORIA NATIVA")
    print("=====================================================")

    # 1. Check if models are present
    registry = ProviderRegistry
    registry.discover(force=True)
    native = registry.get_by_name("Native Llama")

    if not native:
        print("[FAIL] Native Llama plugin no encontrado.")
        return

    health = native.check_health()
    if not health.is_healthy:
        print(
            "[!] Native Llama no está healthy. Probablemente faltan modelos o llama-cpp-python."
        )
        return

    print(
        f"[OK] Native Llama detectado. Modelos encontrados: {[m['name'] for m in health.models]}"
    )

    print("\n[+] Solicitando Tarea 1: 'bounty'")
    messages = [{"role": "user", "content": "Escribe una frase corta."}]

    time.time()
    res1 = "".join(list(stream(messages, task="bounty")))
    print(f"    Respuesta: {res1.strip()}")
    res2 = "".join(list(stream(messages, task="semantic")))
    print(f"    Respuesta: {res2.strip()}")
    print(f"    Instancias activas en RAM: {list(native._instances.keys())}")

    print("\n[+] Simulación de inactividad (Fast-Forward)...")
    # Forzamos el timeout modificando el last_used
    with native._inference_lock:
        for m in native._instances:
            native._instances[m]["last_used"] -= 400

    print("    Esperando a que el Watchdog detecte la memoria inactiva (max 10s)...")
    for _ in range(12):
        if not native._instances:
            print("    [OK] ¡Watchdog limpió la RAM exitosamente!")
            break
        time.sleep(1)

    if native._instances:
        print("    [FAIL] El Watchdog no limpió la memoria.")

    print("\n=====================================================")
    print(" TEST FINALIZADO")
    print("=====================================================")


if __name__ == "__main__":
    test_autonomous_router()
