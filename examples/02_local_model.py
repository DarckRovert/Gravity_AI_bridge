"""
Ejemplo de uso de un modelo local (ej: Ollama o LM Studio) con ProviderManager.
"""
from provider_manager import ProviderManager

def main():
    pm = ProviderManager()
    pm.scan_all()  # Detectar proveedores locales automáticamente
    mensajes = [
        {"role": "system", "content": "Eres un asistente Python experto."},
        {"role": "user", "content": "Genera una función para invertir una lista en Python"}
    ]
    # Realizar inferencia en modelo Mistral local via Ollama
    for chunk in pm.stream(mensajes, model="mistral", provider="Ollama"):
        print(chunk, end="", flush=True)

if __name__ == "__main__":
    main()