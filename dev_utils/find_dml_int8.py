import onnxruntime as ort
import os
import numpy as np

os.environ["ORT_LOGGING_LEVEL"] = "3"

def find_active_dml_int8():
    print("Enumerating DirectML Adapters (INT8 MODEL)...")
    for i in range(8):
        try:
            providers = [('DmlExecutionProvider', {'device_id': i})]
            session = ort.InferenceSession("rag/models/npu_minilm/model_int8.onnx", providers=providers)
            active = session.get_providers()
            if 'DmlExecutionProvider' in active:
                print(f"[SUCCESS] Device {i}: ACTIVE (DML)")
                # Inference test
                ids = np.zeros((1, 128), dtype=np.int64)
                attn = np.ones((1, 128), dtype=np.int64)
                # Note: INT8 models might have slightly different input shapes, 
                # but most keep the same for BERT.
                inputs = {"input_ids": ids, "attention_mask": attn}
                # Check actual input names
                actual_inputs = [x.name for x in session.get_inputs()]
                feed = {name: ids for name in actual_inputs}
                session.run(None, feed)
                print(f"Device {i}: INT8 Inference SUCCESS.")
            else:
                print(f"[FALLBACK] Device {i}: Fell back to CPU")
        except Exception as e:
            print(f"[ERROR] Device {i}: {e}")

if __name__ == "__main__":
    find_active_dml_int8()
