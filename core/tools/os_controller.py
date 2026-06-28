"""
Módulo 4: Ejecutor del Sistema Operativo (Brazos)
Expone capacidades de control de GUI (Mouse/Keyboard) al entorno de Gravity.
"""

import pyautogui
import subprocess
import os
import time
import json

def open_application(app_name: str) -> str:
    """Abre una aplicación usando el comando de Windows start."""
    try:
        subprocess.Popen(f'start "" "{app_name}"', shell=True)
        return f"Aplicación o archivo '{app_name}' lanzado con éxito."
    except Exception as e:
        return f"Error abriendo la aplicación: {str(e)}"

def type_text(text: str) -> str:
    """Escribe texto simulando pulsaciones de teclado."""
    try:
        pyautogui.write(text, interval=0.01)
        return "Texto escrito con éxito."
    except Exception as e:
        return f"Error escribiendo texto: {str(e)}"

def press_key(key: str) -> str:
    """Presiona una tecla específica o combinación de teclas (separadas por +)."""
    try:
        keys = key.split("+")
        keys = [k.strip() for k in keys]
        if len(keys) > 1:
            pyautogui.hotkey(*keys)
        else:
            pyautogui.press(keys[0])
        return f"Tecla '{key}' presionada con éxito."
    except Exception as e:
        return f"Error presionando tecla: {str(e)}"

def execute_os_action(action_json: str) -> str:
    """
    Punto de entrada unificado para el LLM.
    Ejemplo de action_json:
    {"action": "open_app", "target": "notepad"}
    {"action": "type_text", "target": "Hola mundo"}
    {"action": "press_key", "target": "enter"}
    {"action": "press_key", "target": "ctrl+c"}
    """
    try:
        data = json.loads(action_json)
        action = data.get("action")
        target = data.get("target", "")
        
        if action == "open_app":
            return open_application(target)
        elif action == "type_text":
            return type_text(target)
        elif action == "press_key":
            return press_key(target)
        else:
            return f"Acción desconocida: {action}"
    except Exception as e:
        return f"Error parseando JSON OS Controller: {str(e)}"
