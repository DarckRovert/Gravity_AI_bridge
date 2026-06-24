import os
import subprocess
import time
from core.logger import log

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FFMPEG_EXE = os.path.join(BASE_DIR, "_integrations", "ffmpeg", "ffmpeg.exe")
TTS_RATE = 150

# Cache de voces SAPI (TTL 300s) — evita enumerar COM en cada polling del dashboard
_voices_cache: list[dict] = []
_voices_cache_ts: float = 0.0
_VOICES_CACHE_TTL: float = 300.0  # segundos

# Generadores de BGM locales (sin internet)
BGM_GENERATORS: dict[str, str] = {
    "epico": "anoisesrc=color=brown:r=44100:a=0.5,lowpass=f=120,chorus=0.5:0.9:50:0.4:0.25:2",
    "documental": "anoisesrc=color=pink:r=44100:a=0.2,lowpass=f=300",
    "synthwave": "anoisesrc=color=brown:r=44100:a=0.4,lowpass=f=400,tremolo=f=4:d=0.5",
    "jazz": "anoisesrc=color=pink:r=44100:a=0.15,lowpass=f=250",
    "cinematic": "anoisesrc=color=brown:r=44100:a=0.6,lowpass=f=80,aecho=0.8:0.88:60:0.4",
    "publicitario": "anoisesrc=color=pink:r=44100:a=0.3,lowpass=f=350,tremolo=f=2:d=0.3",
    "heroico": "anoisesrc=color=brown:r=44100:a=0.5,lowpass=f=100",
    "ambient": "anoisesrc=color=pink:r=44100:a=0.15,lowpass=f=150",
    "tension": "anoisesrc=color=brown:r=44100:a=0.4,lowpass=f=60",
    "triste": "anoisesrc=color=pink:r=44100:a=0.2,lowpass=f=200",
    "misterio": "anoisesrc=color=brown:r=44100:a=0.3,lowpass=f=90",
    "alegre": "anoisesrc=color=pink:r=44100:a=0.25,lowpass=f=400",
    "lofi_beats": "anoisesrc=color=pink:r=44100:a=0.2,lowpass=f=250",
    "corporativo": "anoisesrc=color=pink:r=44100:a=0.15,lowpass=f=300",
    "ninguna": "anullsrc=r=44100:cl=stereo",
}


def _infer_lang(vid: str, name: str) -> str:
    combined = (vid + name).lower()
    if any(t in combined for t in ("es-", "es_", "spanish", "español", "_es", "-es")):
        return "es"
    if any(t in combined for t in ("en-", "en_", "english", "_en", "-en")):
        return "en"
    if any(t in combined for t in ("pt-", "pt_", "portug")):
        return "pt"
    if any(t in combined for t in ("fr-", "fr_", "french", "français")):
        return "fr"
    if any(t in combined for t in ("de-", "de_", "german", "deutsch")):
        return "de"
    return "other"


def get_available_voices() -> list[dict]:
    """
    Lista TODAS las voces instaladas en el sistema mediante win32com + SAPI directo.
    Detecta voces SAPI5 legacy, OneCore, Neural (Windows 11) y voces de terceros.
    Fallback a pyttsx3 si win32com no está disponible.
    Cache con TTL de 300s — evita enumerar COM en cada polling del dashboard.
    """
    global _voices_cache, _voices_cache_ts
    now_ts = time.time()
    if _voices_cache and (now_ts - _voices_cache_ts) < _VOICES_CACHE_TTL:
        return list(_voices_cache)

    v_list: list[dict] = []
    seen_ids: set[str] = set()

    # ── Motor primario: win32com SAPI directo ────────────────────────────────
    if os.name == "nt":
        try:
            import win32com.client
            import pythoncom

            pythoncom.CoInitialize()
            sapi = win32com.client.Dispatch("SAPI.SpVoice")
            voice_tokens = sapi.GetVoices()
            for i in range(voice_tokens.Count):
                token = voice_tokens.Item(i)
                vid = token.Id or ""
                name = token.GetDescription() or vid
                if vid and vid not in seen_ids:
                    seen_ids.add(vid)
                    v_list.append(
                        {
                            "id": vid,
                            "name": name,
                            "lang": _infer_lang(vid, name),
                            "gender": "unknown",
                            "engine": "sapi",
                        }
                    )
            log.info(f"[VideoStudio] win32com SAPI: {len(v_list)} voces detectadas.")
        except Exception as e:
            log.warning(
                f"[VideoStudio] win32com no disponible ({e}), usando pyttsx3 fallback."
            )

    # ── Fallback: pyttsx3 ────────────────────────────────────────────────────
    if not v_list:
        try:
            import pyttsx3

            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            for v in voices:
                vid = v.id or ""
                name = v.name or vid
                if vid and vid not in seen_ids:
                    seen_ids.add(vid)
                    v_list.append(
                        {
                            "id": vid,
                            "name": name,
                            "lang": _infer_lang(vid, name),
                            "gender": v.gender or "unknown",
                            "engine": "pyttsx3",
                        }
                    )
            engine.stop()
            log.info(f"[VideoStudio] pyttsx3 fallback: {len(v_list)} voces detectadas.")
        except Exception as e:
            log.warning(f"[VideoStudio] No se pudo listar voces: {e}")

    # ── Complemento: voces OneCore via SpObjectTokenCategory ────────────────
    if os.name == "nt":
        try:
            import win32com.client
            import pythoncom

            pythoncom.CoInitialize()
            onecore_reg_paths = [
                r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices",
                r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices",
            ]
            for reg_path in onecore_reg_paths:
                try:
                    cat = win32com.client.Dispatch("SAPI.SpObjectTokenCategory")
                    cat.SetId(reg_path, False)
                    extra_tokens = cat.EnumerateTokens()
                    for i in range(extra_tokens.Count):
                        t = extra_tokens.Item(i)
                        vid = t.Id or ""
                        name = t.GetDescription() or vid
                        if vid and vid not in seen_ids:
                            seen_ids.add(vid)
                            source = "OneCore" if "OneCore" in reg_path else "SAPI5"
                            v_list.append(
                                {
                                    "id": vid,
                                    "name": f"{source}: {name}",
                                    "lang": _infer_lang(vid, name),
                                    "gender": "unknown",
                                    "engine": "sapi_cat",
                                }
                            )
                except Exception:
                    pass
        except Exception as e:
            log.warning(
                f"[VideoStudio] Error enumerando voces OneCore via SpObjectTokenCategory: {e}"
            )

    if not v_list:
        log.error("[VideoStudio] No se encontró ninguna voz instalada en el sistema.")
    else:
        log.info(f"[VideoStudio] Total voces disponibles: {len(v_list)}")

    _voices_cache = list(v_list)
    _voices_cache_ts = time.time()
    return v_list


def _generate_audio(
    text: str,
    output_wav: str,
    rate: int = TTS_RATE,
    voice_id: str = "",
) -> bool:
    """
    Convierte texto a audio WAV usando Windows SAPI.
    """
    # ── Intercept: Gemini TTS explícito ──────────────────────────────────────
    if voice_id.startswith("gemini:"):
        gemini_voice = voice_id.split(":", 1)[1]
        try:
            import sys as _sys

            _int_dir = os.path.join(BASE_DIR, "_integrations")
            if _int_dir not in _sys.path:
                _sys.path.insert(0, _int_dir)
            from gemini_tts import synthesize_gemini, get_api_key_from_gravity

            gemini_key = get_api_key_from_gravity()
            if gemini_key:
                log.info(
                    f"[VideoStudio] TTS Gemini: Generando voz premium '{gemini_voice}'."
                )
                ok = synthesize_gemini(
                    text, output_wav, voice=gemini_voice, api_key=gemini_key
                )
                if ok:
                    size_kb = os.path.getsize(output_wav) // 1024
                    log.info(
                        f"[VideoStudio] Audio (Gemini TTS): {os.path.basename(output_wav)} ({size_kb} KB)"
                    )
                    return True
                else:
                    log.warning(
                        "[VideoStudio] Gemini TTS falló. Intentando fallback SAPI."
                    )
            else:
                log.warning(
                    "[VideoStudio] Gemini TTS solicitado pero no hay API key. Intentando fallback SAPI."
                )
        except Exception as e:
            log.warning(f"[VideoStudio] TTS Gemini error: {e}")

    # ── Motor primario: win32com SAPI (SAPI5 + OneCore + Neural) ─────────────
    if os.name == "nt":
        try:
            import win32com.client
            import pythoncom

            _co_initialized_by_us = False
            try:
                pythoncom.CoInitialize()
                _co_initialized_by_us = True
            except Exception as _co_err:
                _co_hresult = (
                    getattr(_co_err, "hresult", None)
                    or (getattr(_co_err, "args", [None]) or [None])[0]
                )
                if _co_hresult not in (0x80010106, -2147417850):
                    raise

            sapi = win32com.client.Dispatch("SAPI.SpVoice")
            file_stream = win32com.client.Dispatch("SAPI.SpFileStream")

            token_list: list = []
            seen_tok_ids: set[str] = set()

            # Standard SAPI5
            voice_tokens = sapi.GetVoices()
            for i in range(voice_tokens.Count):
                t = voice_tokens.Item(i)
                token_list.append(t)
                seen_tok_ids.add((t.Id or "").lower())

            # OneCore/Neural via SpObjectTokenCategory
            _onecore_paths = [
                r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices",
                r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices",
            ]
            for _reg_path in _onecore_paths:
                try:
                    cat = win32com.client.Dispatch("SAPI.SpObjectTokenCategory")
                    cat.SetId(_reg_path, False)
                    extra = cat.EnumerateTokens()
                    for i in range(extra.Count):
                        t = extra.Item(i)
                        if (t.Id or "").lower() not in seen_tok_ids:
                            token_list.append(t)
                            seen_tok_ids.add((t.Id or "").lower())
                except Exception:
                    pass

            selected_token = None

            if voice_id:
                vid_lower = voice_id.lower()
                for tok in token_list:
                    tok_id = (tok.Id or "").lower()
                    tok_name = (tok.GetDescription() or "").lower()
                    if (
                        vid_lower == tok_id
                        or vid_lower in tok_id
                        or tok_id in vid_lower
                        or vid_lower in tok_name
                    ):
                        selected_token = tok
                        log.info(
                            f"[VideoStudio] TTS (win32com) voz seleccionada: {tok.GetDescription()} | ID: {tok.Id}"
                        )
                        break

            if not selected_token:
                es_markers = (
                    "es-",
                    "es_",
                    "spanish",
                    "español",
                    "_es",
                    "-es",
                    "esES",
                    "esMX",
                )
                for tok in token_list:
                    combined = ((tok.Id or "") + (tok.GetDescription() or "")).lower()
                    if any(m.lower() in combined for m in es_markers):
                        selected_token = tok
                        log.info(
                            f"[VideoStudio] TTS (win32com) voz española auto: {tok.GetDescription()}"
                        )
                        break

            if not selected_token and token_list:
                selected_token = token_list[0]
                log.warning(
                    f"[VideoStudio] TTS (win32com) primera voz disponible: {selected_token.GetDescription()}"
                )

            if selected_token:
                sapi.Voice = selected_token
                sapi.Rate = max(-10, min(10, int((rate - 150) / 25)))

                os.makedirs(os.path.dirname(output_wav), exist_ok=True)
                file_stream.Open(output_wav, 3)
                sapi.AudioOutputStream = file_stream
                sapi.Speak(text)
                file_stream.Close()

                ok = os.path.isfile(output_wav) and os.path.getsize(output_wav) > 0
                if ok:
                    size_kb = os.path.getsize(output_wav) // 1024
                    log.info(
                        f"[VideoStudio] Audio (win32com): {os.path.basename(output_wav)} ({size_kb} KB)"
                    )
                    _wav_normalized = output_wav + ".norm.wav"
                    try:
                        _nr = subprocess.run(
                            [
                                FFMPEG_EXE,
                                "-y",
                                "-i",
                                output_wav,
                                "-ar",
                                "44100",
                                "-ac",
                                "2",
                                "-sample_fmt",
                                "s16",
                                _wav_normalized,
                            ],
                            capture_output=True,
                            timeout=30,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                        )
                        if _nr.returncode == 0 and os.path.isfile(_wav_normalized):
                            os.replace(_wav_normalized, output_wav)
                            log.info(
                                f"[VideoStudio] WAV normalizado a 44100Hz: {os.path.basename(output_wav)}"
                            )
                        else:
                            log.warning(
                                "[VideoStudio] Normalización WAV falló, usando WAV nativo de SAPI."
                            )
                            if os.path.isfile(_wav_normalized):
                                os.remove(_wav_normalized)
                    except Exception as _ne:
                        log.warning(f"[VideoStudio] Normalización WAV excepción: {_ne}")
                    if _co_initialized_by_us:
                        pythoncom.CoUninitialize()
                    return True

            if _co_initialized_by_us:
                pythoncom.CoUninitialize()
        except Exception as e:
            log.warning(
                f"[VideoStudio] win32com TTS falló ({e}), usando pyttsx3 fallback."
            )

    # ── Motor secundario: pyttsx3 ────────────────────────────────────────────
    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.setProperty("rate", rate)
        voices = engine.getProperty("voices")

        selected = None

        if voice_id:
            vid_lower = voice_id.lower()
            selected = next(
                (
                    v
                    for v in voices
                    if vid_lower in (v.id or "").lower()
                    or vid_lower in (v.name or "").lower()
                ),
                None,
            )
            if selected:
                log.info(
                    f"[VideoStudio] TTS (pyttsx3) voz seleccionada: {selected.name}"
                )

        if not selected:
            selected = next(
                (
                    v
                    for v in voices
                    if any(
                        t in (v.id or "").lower()
                        for t in ("es-", "es_", "spanish", "español")
                    )
                    or any(
                        t in (v.name or "").lower()
                        for t in (
                            "spanish",
                            "español",
                            "helena",
                            "sabina",
                            "pablo",
                            "laura",
                            "jorge",
                        )
                    )
                ),
                None,
            )
            if selected:
                log.info(
                    f"[VideoStudio] TTS (pyttsx3) voz española auto: {selected.name}"
                )

        if not selected and voices:
            selected = voices[0]
            log.warning(
                f"[VideoStudio] TTS (pyttsx3) primera voz disponible: {selected.name}"
            )

        if not selected:
            log.error("[VideoStudio] No hay voces SAPI disponibles.")
            engine.stop()
            return False

        engine.setProperty("voice", selected.id)
        engine.save_to_file(text, output_wav)
        engine.runAndWait()
        engine.stop()

        ok = os.path.isfile(output_wav) and os.path.getsize(output_wav) > 0
        if ok:
            size_kb = os.path.getsize(output_wav) // 1024
            log.info(
                f"[VideoStudio] Audio (pyttsx3): {os.path.basename(output_wav)} ({size_kb} KB)"
            )
            _wav_normalized = output_wav + ".norm.wav"
            try:
                _nr = subprocess.run(
                    [
                        FFMPEG_EXE,
                        "-y",
                        "-i",
                        output_wav,
                        "-ar",
                        "44100",
                        "-ac",
                        "2",
                        "-sample_fmt",
                        "s16",
                        _wav_normalized,
                    ],
                    capture_output=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                if _nr.returncode == 0 and os.path.isfile(_wav_normalized):
                    os.replace(_wav_normalized, output_wav)
                    log.info(
                        f"[VideoStudio] WAV normalizado a 44100Hz (pyttsx3): {os.path.basename(output_wav)}"
                    )
                else:
                    log.warning(
                        "[VideoStudio] Normalización WAV (pyttsx3) falló, usando WAV nativo."
                    )
                    if os.path.isfile(_wav_normalized):
                        os.remove(_wav_normalized)
            except Exception as _ne:
                log.warning(
                    f"[VideoStudio] Normalización WAV (pyttsx3) excepción: {_ne}"
                )
        return ok
    except Exception as e:
        log.error(f"[VideoStudio] Error TTS pyttsx3: {e}")

    # ── Motor Tier-3: Gemini TTS fallback ─────────────────────────────────────
    try:
        import sys as _sys

        _integrations_dir = os.path.join(BASE_DIR, "_integrations")
        if _integrations_dir not in _sys.path:
            _sys.path.insert(0, _integrations_dir)
        from gemini_tts import synthesize_gemini, get_api_key_from_gravity

        gemini_key = get_api_key_from_gravity()
        if gemini_key:
            log.info(
                "[VideoStudio] TTS Gemini: intentando síntesis premium (motor local no disponible)."
            )
            ok = synthesize_gemini(text, output_wav, api_key=gemini_key)
            if ok:
                size_kb = os.path.getsize(output_wav) // 1024
                log.info(
                    f"[VideoStudio] Audio (Gemini TTS): {os.path.basename(output_wav)} ({size_kb} KB)"
                )
                return True
    except Exception as e:
        log.warning(f"[VideoStudio] TTS Gemini error: {e}")

    return False


def _ensure_bgm(bgm_type: str, bgm_path: str) -> bool:
    """
    Genera BGM instrumental con ffmpeg usando los nuevos generadores de ruido cinemático.
    """
    if os.path.isfile(bgm_path) and os.path.getsize(bgm_path) > 4096:
        return True
    if bgm_type not in BGM_GENERATORS:
        log.warning("[VideoStudio] BGM tipo desconocido: " + bgm_type)
        return False
    if not os.path.isfile(FFMPEG_EXE):
        log.error("[VideoStudio] ffmpeg no encontrado para generar BGM.")
        return False
    parent_dir = os.path.dirname(os.path.abspath(bgm_path))
    os.makedirs(parent_dir, exist_ok=True)
    dur = 600
    expr = BGM_GENERATORS[bgm_type]

    if "anoisesrc" in expr:
        filtergraph = f"{expr},aformat=channel_layouts=stereo"
    else:
        filtergraph = expr

    fade_out_st = dur - 4
    cmd = [
        FFMPEG_EXE,
        "-y",
        "-f",
        "lavfi",
        "-i",
        filtergraph,
        "-af",
        "volume=0.45,afade=t=in:st=0:d=4,afade=t=out:st=" + str(fade_out_st) + ":d=4",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "128k",
        "-t",
        str(dur),
        bgm_path,
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if (
            result.returncode == 0
            and os.path.isfile(bgm_path)
            and os.path.getsize(bgm_path) > 4096
        ):
            size_kb = os.path.getsize(bgm_path) // 1024
            log.info(
                "[VideoStudio] BGM generado localmente ("
                + str(size_kb)
                + " KB): "
                + os.path.basename(bgm_path)
            )
            return True
        err = result.stderr.decode(errors="replace")[-400:]
        log.error("[VideoStudio] Error generando BGM " + bgm_type + ": " + err)
        return False
    except Exception as e:
        log.error("[VideoStudio] Excepcion generando BGM: " + str(e))
        return False
