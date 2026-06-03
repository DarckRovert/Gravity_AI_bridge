import os
import math
import logging
from core.whisper_engine import WhisperEngine

logger = logging.getLogger("SubtitleEngine")

def get_ass_template(tgt_w: int, tgt_h: int) -> str:
    is_vertical = tgt_h > tgt_w
    play_res_x = 720 if is_vertical else 1280
    play_res_y = 1280 if is_vertical else 720
    margin_l = 60 if is_vertical else 80
    margin_r = 60 if is_vertical else 80
    margin_v = 150 if is_vertical else 50
    font_size = 40 if is_vertical else 52
    
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
WrapStyle: 1

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cinematic,Arial,{font_size},&H0000D7FF,&H88FFFFFF,&H00000000,&H88000000,1,0,0,0,100,100,1,0,1,3,3,2,{margin_l},{margin_r},{margin_v},1

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

def generate_ass_subtitles(audio_path: str, out_ass_path: str, language: str = "es", tgt_w: int = 1280, tgt_h: int = 720) -> str:
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
            
    # Agrupar palabras en frases cortas
    is_vertical = tgt_h > tgt_w
    max_words = 3 if is_vertical else 5
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
            
            # Cortar frase si hay una pausa larga, si alcanza el max_words o si termina en coma/punto
            ends_with_punct = prev_w['word'].strip().endswith(('.', ',', '!', '?', ';'))
            
            if gap > 0.6 or len(current_phrase) >= max_words or ends_with_punct:
                phrases.append(current_phrase)
                current_phrase = [w]
            else:
                current_phrase.append(w)
                
    if current_phrase:
        phrases.append(current_phrase)

    # Escribir archivo ASS
    with open(out_ass_path, "w", encoding="utf-8") as f:
        f.write(get_ass_template(tgt_w, tgt_h))
        
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
            current_time = start_t
            for i, w in enumerate(phrase):
                gap = w['start'] - current_time
                gap_tag = ""
                if gap > 0.01:
                    gap_cs = int(round(gap * 100))
                    # \k minúscula es un retraso invisible para la métrica del karaoke
                    gap_tag = f"{{\\k{gap_cs}}}"
                
                duration_cs = int(round((w['end'] - w['start']) * 100))
                # Espacio inicial
                space = " " if i > 0 else ""
                
                # Inyectar el espacio, luego el gap (silencio), luego el relleno de palabra
                text_line += f"{space}{gap_tag}{{\\K{duration_cs}}}{w['word']}"
                current_time = w['end']
            
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
