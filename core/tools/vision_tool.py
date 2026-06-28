"""
Módulo 3: Conciencia Contextual de Pantalla (Ojos)
Permite a Gravity "ver" lo que hay en la pantalla tomando una captura y convirtiéndola en Base64.
"""

import pyautogui
import base64
from io import BytesIO
import time

def capture_screen_base64() -> str:
    """
    Toma una captura de pantalla del monitor principal, la reduce si es muy grande,
    y la retorna como un string Base64 JPG listo para inyectarse en un LLM multimodal (ej. Llava/Claude).
    """
    try:
        # Tomar captura
        screenshot = pyautogui.screenshot()
        
        # Opcional: Redimensionar si la resolución es masiva (ej 4K) para ahorrar tokens y tiempo
        # width, height = screenshot.size
        # screenshot = screenshot.resize((int(width/1.5), int(height/1.5)))
        
        # Convertir a RGB (pyautogui a veces devuelve RGBA dependiendo del OS)
        if screenshot.mode != 'RGB':
            screenshot = screenshot.convert('RGB')
            
        # Guardar en memoria como JPEG
        buffer = BytesIO()
        screenshot.save(buffer, format="JPEG", quality=85)
        
        # Convertir a Base64
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        return img_str
    except Exception as e:
        return f"ERROR_VISION: No se pudo capturar la pantalla - {str(e)}"

def analyze_screen(prompt="Describe lo que ves en la pantalla y si hay algún error visible.") -> str:
    """
    Función helper que encapsula la lógica.
    Aquí iría la llamada al modelo LLM multimodal.
    Por ahora retorna la estructura del payload.
    """
    b64_image = capture_screen_base64()
    
    if b64_image.startswith("ERROR"):
        return b64_image
        
    payload = {
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
        ]
    }
    
    # Simulación de respuesta
    return f"Payload visual generado con éxito. Longitud Base64: {len(b64_image)} chars."

if __name__ == "__main__":
    print("[JARVIS-VISION] Iniciando captura de prueba...")
    start_time = time.time()
    result = analyze_screen()
    end_time = time.time()
    print(result)
    print(f"Tiempo de proceso: {end_time - start_time:.2f} segundos.")
