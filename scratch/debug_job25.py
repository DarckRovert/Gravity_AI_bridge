import sys
sys.path.append(r'F:\Gravity_AI_bridge')
from core.video_pipeline import _process_job
# Job 25 is the failing one. Let's run it synchronously to see the exception or logs
try:
    _process_job(25)
except Exception as e:
    print("FATAL ERROR:", e)
