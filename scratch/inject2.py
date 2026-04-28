import os

path = r'F:\Gravity_AI_bridge\core\video_pipeline.py'
body_path = r'F:\Gravity_AI_bridge\scratch\ensure_bgm_body.txt'

with open(path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Check si ya existe la definicion
if 'def _ensure_bgm(' in content:
    print('def _ensure_bgm( YA EXISTE — OK')
else:
    print('Insertando definicion de _ensure_bgm...')
    with open(body_path, 'r', encoding='utf-8') as f:
        body = f.read()

    func_def = '\n\n# -- BGM local: generacion instrumental sin internet -------------------------\n\ndef _ensure_bgm(bgm_type: str, bgm_path: str) -> bool:\n    # Genera BGM instrumental con ffmpeg aevalsrc. Sin internet. Cache en inputs/.\n' + body + '\n\n'

    marker = 'def _concatenate_clips('
    idx = content.find(marker)
    if idx == -1:
        print('ERROR: _concatenate_clips no encontrado')
    else:
        content = content[:idx] + func_def + content[idx:]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('OK: def _ensure_bgm( insertada')
