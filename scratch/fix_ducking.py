import sys
sys.stdout.reconfigure(encoding='utf-8')
TARGET = r'F:\Gravity_AI_bridge\core\video_pipeline.py'
with open(TARGET, 'rb') as f:
    raw = f.read()

start_str = b'f"anullsrc=channel_layout=stereo'
end_str = b'[a]"'
start_idx = raw.find(start_str)
end_idx = raw.find(end_str, start_idx) + len(end_str)

if start_idx > 0 and end_idx > start_idx:
    indent = b'                '
    sep = raw[end_idx:end_idx+6]
    if b'\n' in sep or b'\r' in sep:
        sep = b'\n' if b'\r' not in raw else (b'\r\r\r\n' if b'\r\r\r\n' in raw else b'\r\n')
    else:
        sep = b'\n'
        
    replacement = (
        b'f"anullsrc=channel_layout=stereo:sample_rate=44100[silence];"' + sep +
        indent + b'f"[0:a][silence]amix=inputs=2:duration=longest[narr_mixed];"' + sep +
        indent + b'f"[narr_mixed]asplit[narr_main][narr_side];"' + sep +
        indent + b'f"[1:a][narr_side]sidechaincompress=threshold=0.1:ratio=5:attack=200:release=1000[bgm_ducked];"' + sep +
        indent + b'f"[bgm_ducked]volume={bgm_volume}[bgm_final];"' + sep +
        indent + b'f"[narr_main][bgm_final]amix=inputs=2:duration=first:dropout_transition=3[a]"'
    )
    raw_new = raw[:start_idx] + replacement + raw[end_idx:]
    with open(TARGET, 'wb') as f:
        f.write(raw_new)
    print('Filter_str corregido exitosamente (con busqueda indexada)')
else:
    print('Error fatal: no se pudo encontrar el filter_complex')
