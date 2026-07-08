import os
import sys

def main():
    print("================================================================")
    print("GRAVITY AI V2V: Conversor de Modelos a formato ONNX (DirectML)")
    print("================================================================")
    print("Para correr inferencia de Video a Video en AMD iGPU, ")
    print("necesitamos convertir los modelos safetensors a ONNX.")
    print(" ")
    print("OPCION 1 (Recomendada): Descargar modelos ya compilados de HF.")
    print("    Puedes usar el repositorio oficial: runwayml/stable-diffusion-v1-5")
    print("    O mejor aun: lcm-models/lcm-sd15-onnx")
    print(" ")
    print("OPCION 2: Convertir tu modelo local.")
    print("    Si deseas usar un modelo custom (e.g. Juggernaut), necesitas")
    print("    instalar 'optimum' en tu entorno principal y usar optimum-cli:")
    print(" ")
    print("    pip install optimum[onnxruntime]")
    print("    optimum-cli export onnx --model tu_modelo.safetensors models/sd15_turbo_onnx")
    print(" ")
    print("Por favor, pon el resultado en la carpeta: 'models/sd15_turbo_onnx'")
    print("dentro del directorio v2v_engine.")
    
if __name__ == "__main__":
    main()
