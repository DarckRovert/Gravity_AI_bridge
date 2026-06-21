import os
import sys
import moderngl
import numpy as np
import subprocess
import struct

# --- COMPUTE SHADER (SIMULACIÓN DE MILLONES DE PARTÍCULAS) ---
COMPUTE_PARTICLES = open(os.path.join(os.path.dirname(__file__), "shaders", "compute_particles.glsl"), "r", encoding="utf-8").read()

# --- RENDERIZADO DE PARTÍCULAS SOBRE EL MUNDO V13 ---
PARTICLES_VS = open(os.path.join(os.path.dirname(__file__), "shaders", "particles_vs.glsl"), "r", encoding="utf-8").read()

PARTICLES_FS = open(os.path.join(os.path.dirname(__file__), "shaders", "particles_fs.glsl"), "r", encoding="utf-8").read()

# --- SHADERS GLSL V13 (BIOMECÁNICA Y VIDA) ---

VERTEX_SHADER = open(os.path.join(os.path.dirname(__file__), "shaders", "vertex_shader.glsl"), "r", encoding="utf-8").read()

COSMOS_LIB = open(os.path.join(os.path.dirname(__file__), "shaders", "cosmos_lib.glsl"), "r", encoding="utf-8").read()


# 1. SPACE ODYSSEY V13
SPACE_ODYSSEY_FS = open(os.path.join(os.path.dirname(__file__), "shaders", "space_odyssey_fs.glsl"), "r", encoding="utf-8").read()

# 2. JULIA FRACTAL V13
JULIA_FS = open(os.path.join(os.path.dirname(__file__), "shaders", "julia_fs.glsl"), "r", encoding="utf-8").read()

# 3. QUANTUM TUNNEL V13
QUANTUM_TUNNEL_FS = open(os.path.join(os.path.dirname(__file__), "shaders", "quantum_tunnel_fs.glsl"), "r", encoding="utf-8").read()

# POST PROCESS FS (Cinematic Overhaul)
POST_PROCESS_FS = open(os.path.join(os.path.dirname(__file__), "shaders", "post_process_fs.glsl"), "r", encoding="utf-8").read()

# --- GARGANTUA (RELATIVIDAD GENERAL E INTERESTELAR) ---
INTERSTELLAR_FS = open(os.path.join(os.path.dirname(__file__), "shaders", "interstellar_fs.glsl"), "r", encoding="utf-8").read()

# --- JOYA 1: FRACTALES KIFS (INCEPTION) ---
KIFS_FS = open(os.path.join(os.path.dirname(__file__), "shaders", "kifs_fs.glsl"), "r", encoding="utf-8").read()

# --- JOYA 2: FLUIDOS NEON (PSEUDO NAVIER-STOKES) ---
NEON_FLUID_FS = open(os.path.join(os.path.dirname(__file__), "shaders", "neon_fluid_fs.glsl"), "r", encoding="utf-8").read()

# --- JOYA 3: NUCLEO ORGANICO (RAYTRACED SUBSURFACE SCATTERING) ---
ORGANIC_CORE_FS = open(os.path.join(os.path.dirname(__file__), "shaders", "organic_core_fs.glsl"), "r", encoding="utf-8").read()

# --- JOYA 4: TURING PATTERNS (REACTION-DIFFUSION BIOLUMINISCENTE) ---
TURING_PATTERNS_FS = open(os.path.join(os.path.dirname(__file__), "shaders", "turing_patterns_fs.glsl"), "r", encoding="utf-8").read()

# COMPOSITE SHADER: Mezcla imagen AI de fondo + overlay GLSL + Ken Burns + postproceso
COMPOSITE_FS = open(os.path.join(os.path.dirname(__file__), "shaders", "composite_fs.glsl"), "r", encoding="utf-8").read()

MANDELBULB_FS = open(os.path.join(os.path.dirname(__file__), "shaders", "mandelbulb_fs.glsl"), "r", encoding="utf-8").read()

OCEANIC_FS = open(os.path.join(os.path.dirname(__file__), "shaders", "oceanic_fs.glsl"), "r", encoding="utf-8").read()


PROTEAN_FS = open(os.path.join(os.path.dirname(__file__), "shaders", "protean_fs.glsl"), "r", encoding="utf-8").read()


def _load_image_as_texture(ctx, img_path: str, w: int, h: int):
    """Carga una imagen desde disco como textura moderngl RGB."""
    from PIL import Image
    try:
        img = Image.open(img_path).convert("RGB")
        resample_method = getattr(Image, 'Resampling', Image).LANCZOS
        if img.size != (w, h):
            img = img.resize((w, h), resample_method)
        tex = ctx.texture((w, h), components=3, data=img.tobytes())
        tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        return tex
    except Exception as e:
        print(f"[AIFirst] Warning: no se pudo cargar {img_path}: {e}", file=sys.stderr)
        tex = ctx.texture((w, h), components=3)
        tex.write(bytes(w * h * 3))
        return tex


def _make_gradient_texture(ctx, color1: tuple, color2: tuple, w: int, h: int):
    """Crea una textura de gradiente radial cinematográfico usando numpy."""
    y_g, x_g = np.ogrid[:h, :w]
    cx, cy = w / 2.0, h / 2.0
    dist = np.sqrt(((x_g - cx)**2) / (w*0.7)**2 + ((y_g - cy)**2) / (h*0.7)**2)
    dist = np.clip(dist, 0.0, 1.0)
    vignette = np.maximum(0.15, 1.0 - dist * 1.4)
    c1 = np.array(color1, dtype=np.float32)
    c2 = np.array(color2, dtype=np.float32)
    dist_3d = dist[..., np.newaxis]
    vignette_3d = vignette[..., np.newaxis]
    pixels = (c1 * (1.0 - dist_3d) + c2 * dist_3d) * vignette_3d * 255.0
    pixels = np.clip(pixels, 0, 255).astype(np.uint8)
    tex = ctx.texture((w, h), components=3, data=pixels.tobytes())
    return tex


INCA_MATH_FS = open(os.path.join(os.path.dirname(__file__), "shaders", "inca_math_fs.glsl"), "r", encoding="utf-8").read()


def render_v14_compute_video(timeline: list, multiband: dict, colorsA: np.ndarray,
                     colorsB: np.ndarray, w: int, h: int, fps: int,
                     out_mp4: str, audio_path: str,
                     speed_multiplier=1.0, turbulence=1.0,
                     background_images: list = None,
                     subtitle_file: str = None):
    """
    Renderiza el video V14 — COMPUTE SHADERS SSBO.
    """
    ctx = moderngl.create_context(standalone=True, require=430)
    
    # [V5] Cargar Textura PBR (Inca Stone)
    tex_stone = None
    try:
        from PIL import Image
        tex_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "textures", "inca_stone.png")
        if os.path.exists(tex_path):
            img = Image.open(tex_path).convert("RGB")
            # Flip image top to bottom for OpenGL
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
            tex_stone = ctx.texture(img.size, 3, img.tobytes())
            tex_stone.build_mipmaps()
            tex_stone.use(location=0)
            print("V5: Textura PBR de Andesita cargada exitosamente.")
        else:
            print("V5: No se encontro la textura PBR.")
    except Exception as e:
        print(f"Error cargando textura V5: {e}")


    engines = {
        "space_odyssey": ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=SPACE_ODYSSEY_FS),
        "interstellar":  ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=INTERSTELLAR_FS),
        "inception_kifs": ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=KIFS_FS),
        "neon_fluid":     ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=NEON_FLUID_FS),
        "organic_core":   ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=ORGANIC_CORE_FS),
        "turing_patterns": ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=TURING_PATTERNS_FS),
        "julia_fractal":  ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=JULIA_FS),
        "mandelbulb":     ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=MANDELBULB_FS),
        "nebula":         ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=SPACE_ODYSSEY_FS),
        "quantum_tunnel": ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=QUANTUM_TUNNEL_FS),
        "galaxy_system":  ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=SPACE_ODYSSEY_FS),
        "galactic":       ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=INTERSTELLAR_FS),
        "oceanic":        ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=OCEANIC_FS),
        "protean":        ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=PROTEAN_FS),
        "inca_math":      ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=INCA_MATH_FS),
        "biomechanic_v14":ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=SPACE_ODYSSEY_FS),
    }

    if tex_stone and 'tex_stone' in engines["inca_math"]:
        engines["inca_math"]['tex_stone'].value = 0


    ai_first = background_images is not None
    if ai_first:
        prog_composite = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=COMPOSITE_FS)
        print("\n[🎬 Motor V13] PIPELINE AI-FIRST CINEMATOGRÁFICO V16 ACTIVADO", file=sys.stderr)
    else:
        prog_post = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=POST_PROCESS_FS)
        print("\n[🚀 Motor V13] RENDER CINEMATIC V16 (Shot Machine + Motion Blur)...", file=sys.stderr)

    vertices = np.array([-1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0], dtype='f4')
    vbo = ctx.buffer(vertices)
    vaos = {name: ctx.vertex_array(prog, [(vbo, '2f', 'in_vert')]) for name, prog in engines.items()}

    if ai_first:
        vao_composite = ctx.vertex_array(prog_composite, [(vbo, '2f', 'in_vert')])
    else:
        vao_post = ctx.vertex_array(prog_post, [(vbo, '2f', 'in_vert')])

    tex_geom1 = ctx.texture((w, h), components=3)
    fbo_geom1 = ctx.framebuffer(color_attachments=[tex_geom1])
    tex_geom2 = ctx.texture((w, h), components=3)
    fbo_geom2 = ctx.framebuffer(color_attachments=[tex_geom2])
    fbo_final = ctx.framebuffer(color_attachments=[ctx.texture((w, h), components=3)])

    _black_px = np.zeros((1, 1, 3), dtype=np.uint8)
    tex_black_fallback = ctx.texture((1, 1), components=3, data=_black_px.tobytes())

    scene_bg_textures = {}
    if ai_first:
        for i, scene in enumerate(timeline):
            img_path = background_images[i] if i < len(background_images) else None
            if img_path and os.path.isfile(img_path):
                scene_bg_textures[i] = _load_image_as_texture(ctx, img_path, w, h)
                print(f"  [AIFirst] Escena {i+1}: {os.path.basename(img_path)}", file=sys.stderr)
            else:
                mid_f = min((scene["start"] + scene["end"]) // 2, len(colorsA) - 1)
                c1 = tuple(float(x) for x in colorsA[mid_f])
                c2 = tuple(float(x) for x in colorsB[mid_f])
                scene_bg_textures[i] = _make_gradient_texture(ctx, c1, c2, w, h)

    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ffmpeg_exe = os.path.join(_base, "_integrations", "ffmpeg", "ffmpeg.exe")
    if not os.path.isfile(ffmpeg_exe): ffmpeg_exe = "ffmpeg"

    cmd = [ffmpeg_exe, "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
           "-s", f"{w}x{h}", "-pix_fmt", "rgb24", "-r", str(fps), "-i", "-"]
           
    # Construir filtro de video base
    vf_chain = "vflip"
    if subtitle_file and os.path.isfile(subtitle_file):
        # Escapar la ruta para el filtro de ffmpeg en Windows (ej. C\:/ruta/archivo.ass)
        esc_sub = subtitle_file.replace('\\', '/').replace(':', '\\:')
        vf_chain += f",subtitles='{esc_sub}'"

    if audio_path and os.path.isfile(audio_path):
        cmd.extend(["-i", audio_path, "-vf", vf_chain, "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "ultrafast",
                    "-c:a", "aac", "-b:a", "192k", "-shortest"])
    else:
        cmd.extend(["-vf", vf_chain, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "18", "-preset", "ultrafast"])
    cmd.append(out_mp4)

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    total_frames = len(multiband['bass'])
    _spd_is_arr = isinstance(speed_multiplier, np.ndarray)
    _trb_is_arr = isinstance(turbulence, np.ndarray)

    sub_buffer = bytearray(w * h * 3)
    accumulated = np.zeros(w * h * 3, dtype=np.uint32)

    # --- INICIALIZACIÓN DE COMPUTE SHADER ---
    print("\n[🧠 Motor V14] Compilando Compute Shader (XDNA Simulation)...", file=sys.stderr)
    try:
        compute_prog = ctx.compute_shader(COMPUTE_PARTICLES)
        NUM_PARTICLES = 65536
        # xyz, vida + xyz, size (8 floats = 32 bytes por particula)
        initial_data = np.random.rand(NUM_PARTICLES, 8).astype('f4')
        ssbo_particles = ctx.buffer(initial_data.tobytes())
        ssbo_particles.bind_to_storage_buffer(0)
        compute_active = True
        
        # Vertex y Fragment para dibujarlas
        prog_particles = ctx.program(vertex_shader=PARTICLES_VS, fragment_shader=PARTICLES_FS)
        vao_particles = ctx.vertex_array(prog_particles, [])
        
        print(f"[🧠 Motor V14] SSBO Creado y Render de Partículas ({NUM_PARTICLES}) listo.", file=sys.stderr)
    except Exception as e:
        print(f"[❌ Motor V14] Error al compilar Compute Shader: {e}", file=sys.stderr)
        compute_active = False

    try:
        for frame_idx in range(total_frames):
            engine_1 = "space_odyssey"
            engine_2 = None
            pose_1 = 0; pose_2 = 0
            scene_idx_1 = 0; scene_idx_2 = 0
            transition_t = 0.0; ken_burns_t = 0.0

            for si, scene in enumerate(timeline):
                if scene["start"] <= frame_idx <= scene["end"]:
                    engine_1 = scene["engine"]
                    pose_1 = scene.get("pose", 0)
                    scene_idx_1 = si
                    scene_len = max(1, scene["end"] - scene["start"])
                    ken_burns_t = (frame_idx - scene["start"]) / float(scene_len)
                    if "transition_start" in scene and frame_idx >= scene["transition_start"]:
                        if si + 1 < len(timeline):
                            next_sc = timeline[si + 1]
                            engine_2 = next_sc["engine"]
                            pose_2 = next_sc.get("pose", 0)
                            scene_idx_2 = si + 1
                            total_trans_frames = scene["end"] - scene["transition_start"]
                            transition_t = (frame_idx - scene["transition_start"]) / float(max(1, total_trans_frames))
                    break

            _spd = float(speed_multiplier[frame_idx]) if _spd_is_arr else float(speed_multiplier)
            _trb = float(turbulence[frame_idx]) if _trb_is_arr else float(turbulence)
            t   = (frame_idx / float(fps)) * _spd
            b   = float(multiband['bass'][frame_idx]) * _trb
            m   = float(multiband['mid'][frame_idx]) * _trb
            hg  = float(multiband['high'][frame_idx]) * _trb
            pan = float(multiband.get('pan', np.zeros(total_frames))[frame_idx])
            beat_val = float(multiband.get('beat', np.zeros(total_frames))[frame_idx])
            cA  = tuple(float(x) for x in colorsA[frame_idx])
            cB  = tuple(float(x) for x in colorsB[frame_idx])

            # Lens Breathing: energia acumulada smeared (inercia orgánica)
            _breath_window = 6
            _b_start = max(0, frame_idx - _breath_window)
            _breath = float(np.mean(multiband['bass'][_b_start:frame_idx+1]) * 0.6 +
                           np.mean(multiband['mid'][_b_start:frame_idx+1]) * 0.4)

            # Texturas de fondo (IBL)
            bg_tex1 = None; bg_tex2 = None
            if ai_first and scene_bg_textures:
                bg_tex1 = scene_bg_textures.get(scene_idx_1) or list(scene_bg_textures.values())[0]
                bg_tex2 = scene_bg_textures.get(scene_idx_2) if engine_2 else bg_tex1
                if bg_tex2 is None: bg_tex2 = bg_tex1

            # === TEMPORAL MOTION BLUR ===
            # N sub-frames promediados → suavidad de movimiento cinematográfico real
            N_BLUR = 3 if b > 0.3 else 2
            dt_blur = (1.0 / fps) / float(N_BLUR) * _spd
            accumulated.fill(0)

            def render_pass(engine_name, fbo, pose_val, bg_tex, t_val):
                prog = engines[engine_name]
                if 'resolution' in prog: prog['resolution'].value = (w, h)
                if 'time'       in prog: prog['time'].value = t_val
                if 'bass'       in prog: prog['bass'].value = b
                if 'mid'        in prog: prog['mid'].value = m
                if 'high'       in prog: prog['high'].value = hg
                if 'pan'        in prog: prog['pan'].value = pan
                if 'colorA'     in prog: prog['colorA'].value = cA
                if 'colorB'     in prog: prog['colorB'].value = cB
                if 'pose'       in prog: prog['pose'].value = pose_val
                tex_to_bind = bg_tex if bg_tex else tex_black_fallback
                tex_to_bind.use(location=0)
                if 'iChannel0' in prog: prog['iChannel0'].value = 0
                
                # Ejecutar Compute Shader ANTES de dibujar (simulación de físicas en GPU)
                if compute_active:
                    if 'time' in compute_prog: compute_prog['time'].value = t_val
                    if 'bass' in compute_prog: compute_prog['bass'].value = b
                    if 'mid' in compute_prog: compute_prog['mid'].value = m
                    compute_prog.run(group_x=NUM_PARTICLES // 256)
                
                fbo.use(); ctx.clear(0.0, 0.0, 0.0)
                vaos[engine_name].render(moderngl.TRIANGLE_STRIP)
                
                # Rasterizar las partículas SSBO encima de la escena en TODOS los mundos
                if compute_active:
                    ctx.enable(moderngl.BLEND)
                    ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE # Additive Blending
                    ctx.blend_equation = moderngl.FUNC_ADD
                    
                    if 'time' in prog_particles: prog_particles['time'].value = t_val
                    if 'bass' in prog_particles: prog_particles['bass'].value = b
                    if 'pan' in prog_particles: prog_particles['pan'].value = pan
                    if 'high' in prog_particles: prog_particles['high'].value = hg
                    if 'aspect' in prog_particles: prog_particles['aspect'].value = w / float(h)
                    
                    engine_val = 0
                    if engine_name == "space_odyssey": engine_val = 1
                    elif engine_name == "mandelbulb": engine_val = 2
                    if 'engine_id' in prog_particles: prog_particles['engine_id'].value = engine_val
                    
                    vao_particles.render(moderngl.POINTS, vertices=NUM_PARTICLES)
                    ctx.disable(moderngl.BLEND)

            for blur_i in range(N_BLUR):
                t_sub = t + blur_i * dt_blur

                render_pass(engine_1, fbo_geom1, pose_1, bg_tex1, t_sub)
                if engine_2 is not None:
                    render_pass(engine_2, fbo_geom2, pose_2, bg_tex2, t_sub)
                else:
                    render_pass(engine_1, fbo_geom2, pose_1, bg_tex1, t_sub)

                fbo_final.use()
                ctx.clear(0.0, 0.0, 0.0)

                if ai_first and bg_tex1 is not None:
                    bg_tex1.use(location=0)
                    tex_geom1.use(location=1)
                    tex_geom2.use(location=2)
                    (bg_tex2 or bg_tex1).use(location=3)
                    pc = prog_composite
                    if 'tex_base'     in pc: pc['tex_base'].value = 0
                    if 'tex_overlay'  in pc: pc['tex_overlay'].value = 1
                    if 'tex_overlay2' in pc: pc['tex_overlay2'].value = 2
                    if 'tex_base2'    in pc: pc['tex_base2'].value = 3
                    if 'transition_t' in pc: pc['transition_t'].value = float(transition_t)
                    if 'time'         in pc: pc['time'].value = t_sub
                    if 'bass'         in pc: pc['bass'].value = b
                    if 'mid'          in pc: pc['mid'].value = m
                    if 'high'         in pc: pc['high'].value = hg
                    if 'ken_burns_t'  in pc: pc['ken_burns_t'].value = float(ken_burns_t)
                    if 'breath'       in pc: pc['breath'].value = float(_breath)
                    if 'beat_hit'     in pc: pc['beat_hit'].value = float(beat_val)
                    vao_composite.render(moderngl.TRIANGLE_STRIP)
                else:
                    tex_geom1.use(location=0)
                    tex_geom2.use(location=1)
                    pp = prog_post
                    if 'tex1'         in pp: pp['tex1'].value = 0
                    if 'tex2'         in pp: pp['tex2'].value = 1
                    if 'transition_t' in pp: pp['transition_t'].value = float(transition_t)
                    if 'bass'         in pp: pp['bass'].value = b
                    if 'high'         in pp: pp['high'].value = hg
                    if 'time'         in pp: pp['time'].value = t_sub
                    vao_post.render(moderngl.TRIANGLE_STRIP)

                fbo_final.read_into(sub_buffer, components=3)
                accumulated += np.frombuffer(sub_buffer, dtype=np.uint8)

            # Promedio → Motion Blur final
            img_array = (accumulated / N_BLUR).astype(np.uint8)
            proc.stdin.write(img_array.tobytes())

            if frame_idx % (fps * 2) == 0:
                mode = "AI-FIRST" if ai_first else "GLSL"
                print(f"  Frame {frame_idx}/{total_frames} ({(frame_idx/total_frames)*100:.1f}%) [{mode}:{engine_1}]", file=sys.stderr)

        proc.stdin.close()
        proc.wait()

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error renderizando video V13: {e}", file=sys.stderr)
    finally:
        if 'proc' in locals() and proc.poll() is None:
            try: proc.stdin.close()
            except: pass
            proc.terminate(); proc.wait()

    for v in vaos.values(): v.release()
    if ai_first:
        vao_composite.release()
        prog_composite.release()
        for t_ in scene_bg_textures.values(): t_.release()
    else:
        vao_post.release()
        prog_post.release()
    for p in engines.values(): p.release()
    vbo.release()
    tex_geom1.release(); tex_geom2.release()
    fbo_geom1.release(); fbo_geom2.release(); fbo_final.release()
    ctx.release()

    print(f"[✅ Motor V13] RENDERIZADO EN: {out_mp4}", file=sys.stderr)
    return out_mp4


