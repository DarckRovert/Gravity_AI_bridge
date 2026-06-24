import time

try:
    from optimum.onnxruntime import ORTModelForSpeechSeq2Seq
    from transformers import AutoProcessor, pipeline
    import numpy as np

    print("Librerías cargadas con éxito.")

    # Descargar y compilar el modelo
    model_id = "openai/whisper-tiny"
    processor = AutoProcessor.from_pretrained(model_id)

    print("Probando Device ID 1 (Probablemente NPU Ryzen AI)...")
    provider_options = {"device_id": 1}
    model = ORTModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        export=True,
        provider="DmlExecutionProvider",
        provider_options=provider_options,
    )
    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
    )

    # Inferencia dummy
    dummy_audio = np.zeros(16000, dtype=np.float32)
    print(
        "Ejecutando inferencia en Device ID 1... (Revisa tu administrador de tareas NPU ahora)"
    )
    start = time.time()
    res = pipe(dummy_audio)
    print(f"Inferencia terminada en {time.time()-start:.2f} segundos.")
    print("Si viste actividad en la NPU, Device ID 1 es el correcto!")

except Exception as e:
    print(f"Error fatal: {e}")
