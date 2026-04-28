import re

# ─── 1. mixin_get.py — añadir _serve_video_thumbnail ────────────────────────
GET_PATH = r'F:\Gravity_AI_bridge\api\routes\mixin_get.py'
with open(GET_PATH, 'r', encoding='utf-8', errors='replace') as f:
    get_src = f.read()

THUMBNAIL_HANDLER = '''
    def _serve_video_thumbnail(self):
        """GET /v1/video/thumbnail?job_id=N — Sirve el thumbnail JPEG de un job."""
        try:
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            job_id = int(qs.get('job_id', [0])[0])
            BASE_DIR_v = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            thumb_path = os.path.join(BASE_DIR_v, '_videos', 'thumb_' + str(job_id) + '.jpg')
            if not os.path.isfile(thumb_path):
                self.send_response(404); self.end_headers()
                self.wfile.write(b'{}'); return
            with open(thumb_path, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'public, max-age=3600')
            self._send_cors()
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(500); self.end_headers()
            self.wfile.write(('{"error":"' + str(e) + '"}').encode())

'''

# Insertar antes de _serve_pollinations_health
if '_serve_video_thumbnail' not in get_src:
    marker = '    def _serve_pollinations_health(self):'
    get_src = get_src.replace(marker, THUMBNAIL_HANDLER + marker, 1)
    print('OK: _serve_video_thumbnail añadido a mixin_get.py')
else:
    print('INFO: _serve_video_thumbnail ya existe')

with open(GET_PATH, 'w', encoding='utf-8') as f:
    f.write(get_src)

# ─── 2. mixin_post.py — añadir preview_voice y actualizar video/create ──────
POST_PATH = r'F:\Gravity_AI_bridge\api\routes\mixin_post.py'
with open(POST_PATH, 'r', encoding='utf-8', errors='replace') as f:
    post_src = f.read()

PREVIEW_VOICE_HANDLER = '''
        # /v1/video/preview_voice — TTS preview de voz seleccionada
        if self.path == '/v1/video/preview_voice':
            try:
                data     = json.loads(body_bytes.decode('utf-8'))
                voice_id = data.get('voice_id', '')
                text     = data.get('text', 'Prueba de voz para Gravity Studio.')[:200]
                import tempfile, os
                tmp = tempfile.mktemp(suffix='.wav')
                ok  = video_pipeline._generate_audio(text, tmp, rate=150, voice_id=voice_id)
                if ok and os.path.isfile(tmp):
                    with open(tmp, 'rb') as f:
                        wav_data = f.read()
                    try: os.remove(tmp)
                    except: pass
                    self.send_response(200)
                    self.send_header('Content-Type', 'audio/wav')
                    self.send_header('Content-Length', str(len(wav_data)))
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(wav_data)
                else:
                    self.send_response(500)
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(b'{"error":"TTS fallido"}')
            except Exception as e:
                self.send_response(500); self._send_cors(); self.end_headers()
                self.wfile.write(('{"error":"' + str(e) + '"}').encode())
            return

'''

# Insertar antes del bloque video/cancel
if '/v1/video/preview_voice' not in post_src:
    marker = '        # /v1/video/cancel'
    post_src = post_src.replace(marker, PREVIEW_VOICE_HANDLER + '        # /v1/video/cancel', 1)
    print('OK: preview_voice añadido a mixin_post.py')
else:
    print('INFO: preview_voice ya existe')

# ─── 3. Actualizar video/create para pasar ken_burns, intro_card, color_grade ──
OLD_JOB = '''                job_id         = video_pipeline.add_job('''
if 'ken_burns' not in post_src[post_src.find(OLD_JOB):post_src.find(OLD_JOB)+1000]:
    # Encontrar el cierre del add_job call — busca el final del bloque
    # Reemplazar la llamada add_job de forma segura añadiendo los nuevos parámetros al final
    OLD_ADD_END = "                    codec          = body.get('codec', 'libx264'),\n                )"
    NEW_ADD_END = ("                    codec          = body.get('codec', 'libx264'),\n"
                   "                    ken_burns      = bool(body.get('ken_burns', True)),\n"
                   "                    intro_card     = bool(body.get('intro_card', False)),\n"
                   "                    color_grade    = str(body.get('color_grade', 'auto')),\n"
                   "                )")
    if OLD_ADD_END in post_src:
        post_src = post_src.replace(OLD_ADD_END, NEW_ADD_END, 1)
        print('OK: video/create actualizado con ken_burns, intro_card, color_grade')
    else:
        print('WARN: no encontre el cierre de add_job en mixin_post.py')
else:
    print('INFO: ken_burns ya está en video/create')

with open(POST_PATH, 'w', encoding='utf-8') as f:
    f.write(post_src)

# ─── 4. Registrar la ruta en el router (do_GET) ──────────────────────────────
ROUTER_PATH = r'F:\Gravity_AI_bridge\api\server.py'
with open(ROUTER_PATH, 'r', encoding='utf-8', errors='replace') as f:
    router_src = f.read()

OLD_THUMB_ROUTE = "'/v1/video/thumbnail'"
if OLD_THUMB_ROUTE not in router_src:
    # Buscar el bloque de routing video
    old_voices = "'/v1/video/voices':"
    old_voices_line = None
    for line in router_src.split('\n'):
        if "'/v1/video/voices'" in line or '"/v1/video/voices"' in line:
            old_voices_line = line
            break
    
    if old_voices_line:
        new_route_line = old_voices_line.rstrip() + '\n'
        # Añadir después de la ruta de voices
        post_src_r = router_src.replace(
            old_voices_line,
            old_voices_line + '\n            "/v1/video/thumbnail": self._serve_video_thumbnail,'
        )
        if post_src_r != router_src:
            with open(ROUTER_PATH, 'w', encoding='utf-8') as f:
                f.write(post_src_r)
            print('OK: ruta /v1/video/thumbnail registrada en server.py')
        else:
            print('WARN: no pude añadir ruta en server.py')
    else:
        # Buscar el patron de form diferente
        pattern = re.compile(r'(/v1/video/voices["\'])\s*:\s*self\._serve_video_voices')
        match = pattern.search(router_src)
        if match:
            router_src_new = router_src[:match.end()] + ',\n            "/v1/video/thumbnail": self._serve_video_thumbnail' + router_src[match.end():]
            with open(ROUTER_PATH, 'w', encoding='utf-8') as f:
                f.write(router_src_new)
            print('OK: ruta /v1/video/thumbnail registrada (regex)')
        else:
            print('WARN: no encontre patron de voices en server.py — ruta thumbnail NO registrada')
else:
    print('INFO: ruta thumbnail ya registrada')

print('DONE: API actualizada.')
