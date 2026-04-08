import onnxruntime as ort

def list_dml_names():
    print("--- FULL DIRECTML ADAPTER ENUMERATION ---")
    # Using a dummy session to get DML to enumerate
    try:
        # We try to use a session with an invalid device ID to see what ORT reports
        for i in range(5):
            try:
                # We can't directly get the name via Python easily, but we can 
                # try to see if Device 1 is rejected with a specific log message.
                providers = [('DmlExecutionProvider', {'device_id': i})]
                # We won't actually create a session, just check if it's available
                print(f"Checking Device {i}...")
                session = ort.InferenceSession("rag/models/npu_minilm/model.onnx", providers=providers)
                print(f"Device {i} is ACTIVE and ACCEPTED the model.")
            except Exception as e:
                print(f"Device {i} FAILED or REJECTED: {e}")
    except Exception as e:
        print(f"Global Error: {e}")

if __name__ == "__main__":
    list_dml_names()
