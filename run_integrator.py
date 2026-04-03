import sys
from ask_deepseek import IDEIntegrator

if __name__ == "__main__":
    tool = sys.argv[1] if len(sys.argv) > 1 else "todo"
    IDEIntegrator.integrate(tool)
