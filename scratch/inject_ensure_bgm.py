import os

path = r'F:\Gravity_AI_bridge\core\video_pipeline.py'

# Código a insertar — sin triple-comillas anidadas
ensure_bgm_lines = [
    "\n",
    "# -- BGM local: generacion instrumental sin internet -------------------------\n",
    "\n",
    "def _ensure_bgm(bgm_type: str, bgm_path: str) -> bool:\n",
    "    # Genera BGM instrumental con ffmpeg aevalsrc. Sin internet. Cache en inputs/.\n",
    "    if os.path.isfile(bgm_path) and os.path.getsize(bgm_path) > 4096:\n",
    "        return True\n",
    "    if bgm_type not in BGM_GENERATORS:\n",
    "        log.warning('[VideoStudio] BGM tipo desconocido: ' + repr(bgm_type))\n",
    "        return False\n",
    "    if not os.path.isfile(FFMPEG_EXE):\n",
    "        log.error('[VideoStudio] ffmpeg no encontrado para generar BGM.')\n",
    "        return False\n",
    "    os.makedirs(os.path.dirname(bgm_path), exist_ok=True)\n",
    "    dur = 600\n",
    "    expr = BGM_GENERATORS[bgm_type]\n",
    "    aevalsrc_arg = expr + ':c=stereo:s=44100:d=' + str(dur)\n",
    "    fade_out_st = dur - 4\n",
    "    cmd = [\n",
    "        FFMPEG_EXE, '-y',\n",
    "        '-f', 'lavfi', '-i', 'aevalsrc=' + aevalsrc_arg,\n",
    "        '-af', 'volume=0.45,afade=t=in:st=0:d=4,afade=t=out:st=' + str(fade_out_st) + ':d=4',\n",
    "        '-ar', '44100', '-ac', '2',\n",
    "        '-c:a', 'libmp3lame', '-b:a', '128k',\n",
    "        '-t', str(dur),\n",
    "        bgm_path,\n",
    "    ]\n",
    "    try:\n",
    "        result = subprocess.run(\n",
    "            cmd, capture_output=True, timeout=120,\n",
    "            creationflags=subprocess.CREATE_NO_WINDOW\n",
    "        )\n",
    "        if result.returncode == 0 and os.path.isfile(bgm_path) and os.path.getsize(bgm_path) > 4096:\n",
    "            size_kb = os.path.getsize(bgm_path) // 1024\n",
    "            log.info('[VideoStudio] BGM generado localmente (' + str(size_kb) + ' KB): ' + bgm_path)\n",
    "            return True\n",
    "        err = result.stderr.decode(errors='replace')[-400:]\n",
    "        log.error('[VideoStudio] Error generando BGM ' + bgm_type + ': ' + err)\n",
    "        return False\n",
    "    except Exception as e:\n",
    "        log.error('[VideoStudio] Excepcion generando BGM: ' + str(e))\n",
    "        return False\n",
    "\n",
    "\n",
]

ensure_bgm_code = ''.join(ensure_bgm_lines)

with open(path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

if '_ensure_bgm' in content:
    print('_ensure_bgm YA EXISTE — ok')
else:
    marker = 'def _concatenate_clips('
    idx = content.find(marker)
    if idx == -1:
        print('ERROR: _concatenate_clips no encontrado')
    else:
        content = content[:idx] + ensure_bgm_code + content[idx:]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('OK: _ensure_bgm insertada antes de _concatenate_clips (' + str(len(ensure_bgm_lines)) + ' lineas)')
