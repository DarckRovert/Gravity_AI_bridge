"""
run_integrator.py — Gravity AI Bridge V4.2
Script del instalador para configurar IDEs. Usa ide_integrator.py (sin imports pesados).
"""
import sys
from ide_integrator import IDEIntegrator

if __name__ == "__main__":
    tool = sys.argv[1] if len(sys.argv) > 1 else "todo"
    IDEIntegrator.integrate(tool)
