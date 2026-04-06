import onnxruntime as ort
import os

# Disables ORT logs that might mess up encoding
os.environ["ORT_LOGGING_LEVEL"] = "3"

def find_active_dml():
    print("Enumerating DirectML Adapters...")
    for i in range(8):
        try:
            providers = [('DmlExecutionProvider', {'device_id': i})]
            session = ort.InferenceSession("rag/models/npu_minilm/model.onnx", providers=providers)
            # If we reach here, it didn't fallback significantly or it worked
            active = session.get_providers()
            if 'DmlExecutionProvider' in active:
                print(f"[SUCCESS] Device {i}: ACTIVE (DmlExecutionProvider)")
                # Test with small data to see if it really works
                import numpy as np
                input_ids = np.zeros((1, 128), dtype=np.int64)
                attn_mask = np.ones((1, 128), dtype=np.int64)
                type_ids = np.zeros((1, 128), dtype=np.int64)
                session.run(None, {"input_ids": input_ids, "attention_mask": attn_mask, "token_type_ids": type_ids})
                print(f"Device {i}: Inference confirmed.")
            else:
                print(f"[FALLBACK] Device {i}: Fell back to CPU")
        except Exception as e:
            print(f"[ERROR] Device {i}: {e}")

if __name__ == "__main__":
    find_active_dml()
