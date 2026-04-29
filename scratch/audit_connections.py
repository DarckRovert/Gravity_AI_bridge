import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open(r'F:\Gravity_AI_bridge\frontend\src\components\VideoStudio.tsx', 'r', encoding='utf-8', errors='replace') as f:
    tsx = f.read()

checks = {
    'fetchEngines definida':        'fetchEngines' in tsx,
    'fetchEngines en useEffect':    'fetchEngines()' in tsx and 'ivEngines' in tsx,
    'engines.map renderizado':      'engines.map' in tsx,
    'ttsEngines.gemini.available':  'ttsEngines?.gemini?.available' in tsx,
    'useGeminiTts toggle':          'setUseGeminiTts(!useGeminiTts)' in tsx,
    'geminiVoices renderizados':    'Object.entries(geminiVoices)' in tsx,
    'voice_id gemini prefix':       'gemini:' in tsx,
    'geminiVoiceId en state':       'geminiVoiceId' in tsx,
    'Engine Status panel':          'Motor Status' in tsx,
    'Badge IMG/I2V/TTS':            "'IMG'" in tsx and "'I2V'" in tsx and "'TTS'" in tsx,
    'durationMode state':           'setDurationMode' in tsx,
    'engines state declarado':      "useState<any[]>([])" in tsx,
}

for k, v in checks.items():
    status = "OK   " if v else "FALLO"
    print(status + "  " + k)

# Verificar backend
with open(r'F:\Gravity_AI_bridge\bridge_server.py', 'r', encoding='utf-8', errors='replace') as f:
    srv = f.read()
with open(r'F:\Gravity_AI_bridge\api\routes\mixin_get.py', 'r', encoding='utf-8', errors='replace') as f:
    get = f.read()
with open(r'F:\Gravity_AI_bridge\core\video_pipeline.py', 'r', encoding='utf-8', errors='replace') as f:
    pipe = f.read()

print("\n--- BACKEND ---")
back_checks = {
    '/v1/video/engines en router':      '/v1/video/engines' in srv,
    '_serve_video_engines en mixin':    '_serve_video_engines' in get,
    'tts_engines en /voices response':  'tts_engines' in get,
    'gemini_tts importado en pipeline': 'gemini_tts' in pipe,
    'synthesize_gemini en pipeline':    'synthesize_gemini' in pipe,
    'Gemini TTS Tier-3 en _generate_audio': 'Motor Tier-3' in pipe,
    'ComfyUI Tier-2 en _generate_scene': 'comfy_client' in pipe,
}

for k, v in back_checks.items():
    status = "OK   " if v else "FALLO"
    print(status + "  " + k)

# BUG CRITICO: voice_id con prefijo gemini: ¿es manejado en pipeline?
print("\n--- BUG DETECTION ---")
has_gemini_prefix_handler = 'startswith' in pipe and 'gemini' in pipe
print(("OK   " if has_gemini_prefix_handler else "FALLO") + "  pipeline maneja prefijo gemini: en voice_id")
