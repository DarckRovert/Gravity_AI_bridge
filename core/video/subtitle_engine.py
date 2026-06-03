import os
import math
import logging
from core.whisper_engine import WhisperEngine

logger = logging.getLogger("SubtitleEngine")

ASS_TEMPLATE = """[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 1

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cinematic,Arial,52,&H0000D7FF,&H88FFFFFF,&H00000000,&H88000000,1,0,0,0,100,100,1,0,1,3,3,2,20,20,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def format_ass_time(seconds: float) -> str:
    """Convierte segundos a formato ASS (H:MM:SS.cc)"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs == 100:
        cs = 99
    return f"{h:01d}:{m:02d}:{s:02d}.{cs:02d}"

def generate_ass_subtitles(audio_path: str, out_ass_path: str, language: str = "es") -> str:
    """
    Genera un archivo de subtítulos .ass cinemáticos a partir del audio usando Whisper.
    """
    if not os.path.isfile(audio_path):
        logger.error(f"Audio no encontrado para subtítulos: {audio_path}")
        return None

    logger.info(f"Generando subtítulos cinematográficos para {os.path.basename(audio_path)}")
    engine = WhisperEngine(model_size="base")
    words = engine.extract_words(audio_path, language=language)

    if not words:
        logger.warning("No se detectaron palabras en el audio.")
        return None

    # --- CORRECCIONES FONÉTICAS ---
    # El modelo Whisper a veces confunde palabras. Aplicamos correcciones directas
    # manteniendo la sincronización de tiempo exacta del karaoke.
    correcciones = {
        "juego": "fuego",
        "juegos": "fuegos",
        "juego,": "fuego,",
        "juegos,": "fuegos,",
        "juego.": "fuego.",
        "juego!": "fuego!",
        "juego?": "fuego?",
        "juego:": "fuego:",
    }
    for w in words:
        clean_word = w['word'].strip()
        lower_word = clean_word.lower()
        if lower_word in correcciones:
            # Preservar los espacios originales si los hubiera, reemplazando la palabra limpia
            w['word'] = w['word'].replace(clean_word, correcciones[lower_word])
            
    # Agrupar palabras en frases cortas (max 4 palabras o pausas > 0.6s)
    phrases = []
    current_phrase = []
    
    for i, w in enumerate(words):
        word_text = w['word'].strip()
        if not word_text:
            continue
            
        if not current_phrase:
            current_phrase.append(w)
        else:
            prev_w = current_phrase[-1]
            gap = w['start'] - prev_w['end']
            
            # Cortar frase si hay una pausa larga, o si la frase ya es muy larga (4 palabras) o si termina en coma/punto
            ends_with_punct = prev_w['word'].strip().endswith(('.', ',', '!', '?', ';'))
            
            if gap > 0.6 or len(current_phrase) >= 4 or ends_with_punct:
                phrases.append(current_phrase)
                current_phrase = [w]
            else:
                current_phrase.append(w)
                
    if current_phrase:
        phrases.append(current_phrase)

    # Escribir archivo ASS
    with open(out_ass_path, "w", encoding="utf-8") as f:
        f.write(ASS_TEMPLATE)
        
        for phrase in phrases:
            start_t = phrase[0]['start']
            end_t = phrase[-1]['end']
            
            # Karaoke effect: color highlighting per word
            # Active word: White. Inactive: Gray.
            # Using ASS {\k} tags to do karaoke fill.
            # Secondary color is grey, Primary is white. \K fills instantly.
            
            ass_start = format_ass_time(start_t)
            # Damos un pequeño fade-out extendiendo el end un poco
            ass_end = format_ass_time(end_t + 0.2)
            
            # Construir texto con tags de karaoke \kf (fill suave) o \K (fill duro)
            text_line = ""
            for i, w in enumerate(phrase):
                duration_cs = int(round((w['end'] - w['start']) * 100))
                # Espacio inicial
                space = " " if i > 0 else ""
                # Usamos \K para relleno duro por palabra
                text_line += f"{space}{{\\K{duration_cs}}}{w['word']}"
            
            # Aplicar fade in/out suave a toda la frase
            dialogue = f"Dialogue: 0,{ass_start},{ass_end},Cinematic,,0,0,0,,{{\\fad(150,200)}}{text_line}\n"
            f.write(dialogue)

    logger.info(f"Subtítulos guardados en {out_ass_path}")
    return out_ass_path

if __name__ == "__main__":
    # Test local
    import sys
    if len(sys.argv) > 1:
        generate_ass_subtitles(sys.argv[1], "test_subs.ass")
