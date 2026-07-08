import sys
sys.path.insert(0, 'F:/Gravity_AI_bridge')
from core.workflow_engine import run_workflow
import time

print("Generando Noticia 1...")
t0 = time.time()
job = run_workflow('reporter', params={}, blocking=True)
print(f"STATUS 1: {job.status} | Tiempo: {int(time.time() - t0)}s")

print("Generando Noticia 2...")
t0 = time.time()
job = run_workflow('reporter', params={}, blocking=True)
print(f"STATUS 2: {job.status} | Tiempo: {int(time.time() - t0)}s")
