import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.autonomy_engine import _execute_low_risk_action

def run_tests():
    print("=== Testing Autonomy Engine Workflow Edge Cases ===")

    cases = [
        {
            "name": "Single Quotes",
            "action": {
                "risk": "BAJA",
                "module": "workflow_engine",
                "description": "run_workflow('investigacion_rapida', {'topic': 'Computación Cuántica'})"
            }
        },
        {
            "name": "No Parameters",
            "action": {
                "risk": "BAJA",
                "module": "workflow_engine",
                "description": "run_workflow('investigacion_rapida')"
            }
        }
    ]

    for case in cases:
        print(f"\n[*] Ejecutando caso: {case['name']}")
        ok, result = _execute_low_risk_action(case["action"])
        print(f"    OK: {ok}")
        print(f"    MSG: {result}")
        if not ok:
            print("[!] Test falló.")
            sys.exit(1)
            
    print("\n[✓] Todos los edge cases completados con éxito.")

if __name__ == "__main__":
    run_tests()
