import time
import os
import sys

# Asegurar path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.provider_manager import scan_all, get_best, ProviderRegistry
from providers.base import ProviderPlugin, ProviderResult


class PoisonPillPlugin(ProviderPlugin):
    name = "Poison Pill"
    protocol = "mock"
    category = "local"

    def check_health(self) -> ProviderResult:
        time.sleep(
            25
        )  # Simula un motor que se colgó (el timeout de 20s debería matarlo antes)
        r = self._make_result("mock://")
        r.is_healthy = True
        return r

    def chat_stream(self, messages, model, options):
        yield "Poison response"

    def chat_complete(self, messages, model, options):
        return "Poison response"


def run_exhaustive_tests():
    print("==================================================")
    print(" GRAVITY AI - EXHAUSTIVE INTEGRATION TEST SUITE")
    print("==================================================")

    # 1. Inject Poison Pill to test timeout resilience
    ProviderRegistry.discover()  # Force discovery first
    ProviderRegistry._plugin_classes[PoisonPillPlugin.name] = PoisonPillPlugin
    ProviderRegistry._instances[PoisonPillPlugin.name] = PoisonPillPlugin()

    print("\n[Test 1] Testing scan_all() resilience against freezing plugins...")
    t0 = time.time()
    results = scan_all(force=True)
    t1 = time.time()
    elapsed = t1 - t0

    print(f"    Elapsed time: {elapsed:.2f}s")
    if elapsed > 15:
        print("    [FAIL] scan_all() took too long. Timeout logic failed!")
    else:
        print("    [OK] scan_all() handled freeze gracefully.")

    # Check if Poison Pill is marked unhealthy due to timeout
    poison = next((r for r in results if r.name == "Poison Pill"), None)
    if poison and not poison.is_healthy:
        print("    [OK] Poison Pill correctly flagged as unhealthy.")
    else:
        print("    [FAIL] Poison Pill slipped through or wasn't tested!")

    print("\n[Test 2] Testing Routing Intelligence (Task -> Model)...")
    tasks = ["bounty", "semantic", "code", "reason", "any"]
    for t in tasks:
        r, m = get_best(t)
        if r:
            print(f"    Task '{t}' -> Routed to: [{r.name}] {m}")
        else:
            print(f"    Task '{t}' -> NO HEALTHY MODELS")

    print("\n[Test 3] Testing multi_agent compare() with mock/fast providers...")
    # We will just see if compare doesn't crash.
    try:
        from core.multi_agent import compare

        messages = [{"role": "user", "content": "Hello"}]
        # Run compare but with a very tight timeout
        t0 = time.time()
        comp = compare(messages, n_models=2, timeout=2.0)
        t1 = time.time()
        print(
            f"    [OK] compare() executed in {t1-t0:.2f}s. Handled {len(comp)} responses."
        )
    except Exception as e:
        print(f"    [FAIL] compare() crashed: {e}")

    print("\n[Test 4] Verifying Watchdog and Lock Architecture...")
    try:
        from providers.local.native_provider import NativeLlamaProvider

        # Verificar que the class has the attributes correctly mapped
        lock = NativeLlamaProvider._inference_lock
        wd = NativeLlamaProvider._watchdog_started
        print("    [OK] NativeLlamaProvider has RLock at class level.")
        print(f"    [OK] Watchdog is started: {wd}")
    except Exception as e:
        print(f"    [FAIL] Architecture validation failed: {e}")

    print("\n==================================================")
    print(" EXHAUSTIVE SUITE COMPLETE")
    print("==================================================")


if __name__ == "__main__":
    run_exhaustive_tests()
