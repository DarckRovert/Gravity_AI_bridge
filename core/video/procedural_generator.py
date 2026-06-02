import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageMath, ImageChops

def _get_palette(prompt: str):
    """Paletas basadas en coseno (estilo Inigo Quilez) para color continuo avanzado."""
    prompt_lower = prompt.lower()
    
    if any(kw in prompt_lower for kw in ["cyber", "neon", "city", "synthwave"]):
        return (np.array([0.5, 0.5, 0.5]), np.array([0.5, 0.5, 0.5]), 
                np.array([1.0, 1.0, 1.0]), np.array([0.0, 0.33, 0.67]))
    elif any(kw in prompt_lower for kw in ["fire", "gold", "desert"]):
        return (np.array([0.8, 0.5, 0.2]), np.array([0.2, 0.4, 0.2]), 
                np.array([2.0, 1.0, 1.0]), np.array([0.0, 0.25, 0.25]))
    elif any(kw in prompt_lower for kw in ["ocean", "ice", "water"]):
        return (np.array([0.2, 0.4, 0.6]), np.array([0.1, 0.2, 0.4]), 
                np.array([1.0, 1.0, 1.0]), np.array([0.8, 0.9, 0.3]))
    elif any(kw in prompt_lower for kw in ["horror", "dark", "blood"]):
        return (np.array([0.3, 0.0, 0.0]), np.array([0.4, 0.1, 0.1]), 
                np.array([1.0, 1.0, 1.0]), np.array([0.0, 0.5, 0.5]))
    elif any(kw in prompt_lower for kw in ["forest", "nature", "toxic"]):
        return (np.array([0.2, 0.5, 0.2]), np.array([0.2, 0.4, 0.2]), 
                np.array([1.0, 1.0, 1.0]), np.array([0.0, 0.3, 0.6]))
    else:
        return (np.array([0.2, 0.1, 0.4]), np.array([0.4, 0.2, 0.5]), 
                np.array([2.0, 1.0, 1.0]), np.array([0.5, 0.2, 0.25]))

def _apply_vhs_effects(img_arr: np.ndarray) -> np.ndarray:
    """Aplica aberración cromática extrema y scanlines CRT."""
    h, w, _ = img_arr.shape
    res = np.copy(img_arr)
    # Aberración Cromática Direccional
    shift = 6
    res[:, :-shift, 0] = img_arr[:, shift:, 0]
    res[:, shift:, 2] = img_arr[:, :-shift, 2]
    # Scanlines CRT
    scanlines = np.ones((h, w, 3), dtype=np.float32)
    scanlines[::2, :, :] = 0.8  # Oscurecer cada 2da línea
    res = (res * scanlines).astype(np.uint8)
    return res

def _render_julia_fractal_3d(w: int, h: int, seed: int, palette: tuple, t: float = 0.0, energy: float = 0.0) -> Image.Image:
    """Fractal Suprema V5: Sombreado Phong 3D, Reflexión Especular y Animación Audio-Reactiva."""
    rng = np.random.default_rng(seed)
    
    c_base = complex(rng.uniform(-0.8, 0.4), rng.uniform(-0.6, 0.6))
    c = c_base + complex(np.sin(t * 2 * np.pi)*0.01, np.cos(t * 2 * np.pi)*0.01)
    
    start_zoom = rng.uniform(0.8, 1.5)
    # Audio-reactivo: "Saltos" rápidos en el zoom cuando la energía sube
    zoom = start_zoom * (2.0 ** (t * 2.0)) * (1.0 + energy * 0.15)
    
    offset_x = rng.uniform(-0.3, 0.3) + np.sin(t)*0.05
    offset_y = rng.uniform(-0.3, 0.3) + np.cos(t)*0.05
    
    x_min, x_max = -1.5 / zoom + offset_x, 1.5 / zoom + offset_x
    y_min, y_max = -1.5 / (zoom * (w/h)) + offset_y, 1.5 / (zoom * (w/h)) + offset_y
    
    Y, X = np.ogrid[y_min:y_max:h*1j, x_min:x_max:w*1j]
    Z = X + Y*1j
    dZ = np.ones_like(Z)  
    
    max_iter = 128
    div_time = np.zeros(Z.shape, dtype=float)
    m = np.full(Z.shape, True, dtype=bool)
    
    for i in range(max_iter):
        dZ[m] = 2 * Z[m] * dZ[m]
        Z[m] = Z[m]**2 + c
        diverged = np.abs(Z[m]) > 10.0
        
        new_diverged = np.zeros(Z.shape, dtype=bool)
        new_diverged[m] = diverged
        
        smooth_i = i + 1 - np.log(np.log(np.abs(Z[new_diverged]))) / np.log(2.0)
        div_time[new_diverged] = smooth_i
        m[m] = ~diverged
    
    u = Z / dZ
    u_norm = np.abs(u)
    u_norm[u_norm == 0] = 1e-8
    u = u / u_norm
    
    # Audio-reactivo: La luz gira violentamente con la energía
    angle = rng.uniform(0, 2*np.pi) + t * np.pi * 2.0 + (energy * np.pi)
    light = complex(np.cos(angle), np.sin(angle))
    
    reflection = (u.real * light.real + u.imag * light.imag)
    reflection = np.clip(reflection, 0, 1)
    
    # Audio-reactivo: Metales más brillantes con los "kicks"
    spec_power = max(2.0, 16.0 - energy * 10.0)
    specular = np.power(reflection, spec_power) * (1.5 + energy * 1.5)
    diffuse = reflection * 0.7 + 0.3            
    
    div_t = div_time / max_iter
    div_t = np.power(div_t, 0.6) - (t * 0.5) 
    
    pa, pb, pc, pd = palette
    t_rgb = div_t[:, :, np.newaxis]
    color = pa + pb * np.cos(6.28318 * (pc * t_rgb + pd))
    
    color = color * diffuse[:, :, np.newaxis] + specular[:, :, np.newaxis]
    color[m] = np.array([0.0, 0.0, 0.0])  
    
    img_arr = np.clip(color * 255, 0, 255).astype(np.uint8)
    img_arr = _apply_vhs_effects(img_arr)
    return Image.fromarray(img_arr).filter(ImageFilter.SHARPEN)

def _render_synthwave_3d(w: int, h: int, seed: int, palette: tuple, t: float = 0.0, energy: float = 0.0) -> Image.Image:
    """Synthwave Suprema V5: Motor 3D audio-reactivo."""
    rng = np.random.default_rng(seed)
    
    pa, pb, pc, pd = palette
    sky_top = np.clip((pa + pb * np.cos(6.28318 * pd)) * 255, 0, 255).astype(int)
    sky_bot = np.clip((pa + pb * np.cos(6.28318 * (pc*0.5 + pd))) * 255, 0, 255).astype(int)
    neon_col = np.clip((pa + pb * np.cos(6.28318 * (pc*0.8 + pd))) * 255, 0, 255).astype(int)
    
    img = Image.new("RGB", (w, h), color=(5, 5, 10))
    draw = ImageDraw.Draw(img)
    horizon_y = int(h * 0.5)
    
    for y in range(horizon_y):
        grad_t = y / horizon_y
        r = int(sky_top[0] * (1 - grad_t) + sky_bot[0] * grad_t)
        g = int(sky_top[1] * (1 - grad_t) + sky_bot[1] * grad_t)
        b = int(sky_top[2] * (1 - grad_t) + sky_bot[2] * grad_t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    
    for _ in range(400):
        if rng.random() > 0.5:
            px = int((rng.integers(0, w*2) - t*100) % w)
            py = rng.integers(0, horizon_y)
            bright = rng.integers(100, 255)
            draw.point((px, py), fill=(bright, bright, bright))
            
    # Audio-reactivo: El sol pulsa violentamente con la energía (BPM)
    sun_r_base = h * 0.3
    sun_r = int(sun_r_base + np.sin(t * np.pi * 4) * (sun_r_base * 0.02) + (energy * sun_r_base * 0.2))
    sun_x, sun_y = w // 2, horizon_y
    # Audio-reactivo: El neón se satura en los bajos
    sun_glow = tuple(min(255, int(c * (1.5 + energy))) for c in neon_col)
    draw.ellipse([sun_x - sun_r, sun_y - sun_r, sun_x + sun_r, sun_y + sun_r], fill=sun_glow)
    
    cut_offset = int((t * 200) % 20)
    for y in range(sun_y - sun_r + cut_offset, sun_y + sun_r, 12):
        thickness = int(max(1, (y - (sun_y - sun_r)) / (sun_r * 2) * 14))
        if y > horizon_y - 20: thickness *= 2
        draw.line([(sun_x - sun_r - 50, y), (sun_x + sun_r + 50, y)], fill=(5,5,10), width=thickness)
    
    def height_noise(x, z):
        return np.sin(x*0.05)*100 * np.cos(z*0.05)*50 + np.sin(x*0.1)*30
        
    fov = 400.0
    cam_y = 150.0
    spacing = 150
    # Audio-reactivo: Aceleración con la música
    cam_z = -100.0 + (t * spacing * 6.0) + (energy * spacing)
    
    def project(x, y, z):
        factor = fov / (fov + z - cam_z + 1e-5)
        x_p = int(x * factor) + w // 2
        y_p = int(-y * factor) + horizon_y + int(cam_y * factor)
        return x_p, y_p

    grid_size_x = 40
    grid_size_z = 40
    vertices = {}
    
    for gz in range(grid_size_z):
        z = gz * spacing
        if z < cam_z: continue
        
        for gx in range(-grid_size_x//2, grid_size_x//2 + 1):
            x = gx * spacing
            dist_to_center = abs(x)
            if dist_to_center < 600:
                y = -50 
            else:
                y = height_noise(x, z) + (dist_to_center - 600) * 0.5 
            # Audio-reactivo: El terreno vibra verticalmente
            y += energy * rng.uniform(-10, 10)
            vertices[(gx, gz)] = project(x, y, z)
            
    # Audio-reactivo: Parpadeo del grid
    grid_c = tuple(min(255, int(c * (1.0 + energy*2.0))) for c in neon_col)
    for gz in range(grid_size_z - 1):
        z = gz * spacing
        if z < cam_z: continue
        
        for gx in range(-grid_size_x//2, grid_size_x//2):
            if (gx, gz) not in vertices or (gx, gz+1) not in vertices: continue
            
            v1 = vertices[(gx, gz)]
            v2 = vertices[(gx+1, gz)]
            v3 = vertices[(gx+1, gz+1)]
            v4 = vertices[(gx, gz+1)]
            
            if v1[1] > h and v2[1] > h and v3[1] > h and v4[1] > h: continue
            
            draw.polygon([v1, v2, v3, v4], fill=(5, 5, 10))
            thickness = 2 if (z - cam_z) < spacing * 10 else 1
            # Aumentar grosor en los bajos
            if energy > 0.6 and (z - cam_z) < spacing * 5:
                thickness += 1
            draw.line([v1, v2], fill=grid_c, width=thickness)
            draw.line([v1, v4], fill=grid_c, width=thickness)

    img_arr = np.array(img)
    img_arr = _apply_vhs_effects(img_arr)
    img = Image.fromarray(img_arr)
    
    glow_radius = max(5, int(12 + energy * 10))
    glow = img.filter(ImageFilter.GaussianBlur(radius=glow_radius)).point(lambda p: p * (0.6 + energy*0.3))
    img = ImageChops.add(img, glow)
    return img

def _render_space_odyssey(w: int, h: int, seed: int, palette: tuple, t: float = 0.0, energy: float = 0.0) -> Image.Image:
    """Odisea Espacial Suprema V5: Agujero Negro Audio-Reactivo."""
    rng = np.random.default_rng(seed)
    
    def generate_noise(shape, scale, rng_obj):
        noise = rng_obj.uniform(-1, 1, (shape[0] // scale + 2, shape[1] // scale + 2))
        x = np.linspace(0, noise.shape[1] - 1.001, shape[1])
        y = np.linspace(0, noise.shape[0] - 1.001, shape[0])
        x_idx = x.astype(int)
        y_idx = y.astype(int)
        x_t = x - x_idx
        y_t = y - y_idx
        x_t = x_t * x_t * (3 - 2 * x_t)
        y_t = y_t * y_t * (3 - 2 * y_t)
        x_idx0, x_idx1 = np.clip(x_idx, 0, noise.shape[1] - 1), np.clip(x_idx + 1, 0, noise.shape[1] - 1)
        y_idx0, y_idx1 = np.clip(y_idx, 0, noise.shape[0] - 1), np.clip(y_idx + 1, 0, noise.shape[0] - 1)
        n00, n10 = noise[y_idx0[:, None], x_idx0], noise[y_idx1[:, None], x_idx0]
        n01, n11 = noise[y_idx0[:, None], x_idx1], noise[y_idx1[:, None], x_idx1]
        nx0 = n00 * (1 - x_t) + n01 * x_t
        nx1 = n10 * (1 - x_t) + n11 * x_t
        return nx0 * (1 - y_t[:, None]) + nx1 * y_t[:, None]

    def fbm(shape, scale, octaves):
        n = np.zeros(shape)
        w_val = 1.0
        s = scale
        for _ in range(octaves):
            if s < 2: break
            n += generate_noise(shape, s, rng) * w_val
            w_val *= 0.5
            s //= 2
        return n

    # Audio-reactivo: Turbulencia violenta en el gas galáctico
    q_x = fbm((h, w), min(w, h)//2, 5) + (t * 2.0) + energy * 1.5
    q_y = fbm((h, w), min(w, h)//2, 5) + (t * 1.5) - energy * 1.5
    r_x = fbm((h, w), min(w, h)//4, 5) + 3.0 * q_x
    r_y = fbm((h, w), min(w, h)//4, 5) + 3.0 * q_y
    noise = fbm((h, w), min(w, h)//3, 6) + r_x*0.6 + r_y*0.6
    
    noise = (np.sin(noise * 3.0 + t * 4.0) + 1.0) * 0.5
    
    pa, pb, pc, pd = palette
    t_rgb = noise[:, :, np.newaxis]
    color = pa + pb * np.cos(6.28318 * (pc * t_rgb + pd))
    
    for layer in range(3):
        stars = rng.random((h, w)) > (0.999 - layer*0.002)
        star_color = np.array([rng.uniform(0.5, 1.0), rng.uniform(0.5, 1.0), 1.0])
        # Audio-reactivo: Estrellas parpadean con la música
        color[stars] += star_color * (0.3 * (layer+1)) * (1.0 + energy*2.0)
    
    Y, X = np.ogrid[:h, :w]
    cx, cy = w/2, h/2
    dist = np.sqrt((X - cx)**2 + (Y - cy)**2)
    angle = np.arctan2(Y - cy, X - cx)
    
    # Audio-reactivo: El agujero negro palpita (BPM)
    bh_radius = h * 0.15 * (1.0 + t * 0.5) * (1.0 + energy * 0.1)
    disk_radius = h * 0.4 * (1.0 + t * 0.5) * (1.0 + energy * 0.2)
    
    event_horizon = np.clip((dist - bh_radius) / (bh_radius * 0.2), 0, 1)
    event_horizon = event_horizon[:, :, np.newaxis]
    
    gas_warp = generate_noise((h, w), 50, rng)
    disk_intensity = np.exp(-(dist - bh_radius*1.5)**2 / (disk_radius**2 * 0.2))
    
    # Audio-reactivo: Disco de acreción gira con furia temporal
    disk_angle = angle * 6 + dist * 0.05 + gas_warp * 3 + (t * 10.0) + (energy * 5.0)
    disk_pattern = np.abs(np.sin(disk_angle))
    disk_glow = disk_intensity * disk_pattern * (2.0 + energy * 3.0)
    disk_glow_rgb = disk_glow[:, :, np.newaxis] * (pa + pb)
    
    color = color * event_horizon + disk_glow_rgb * event_horizon
    # Lente gravitacional reacciona a los bajos
    grav_lens = np.exp(-(dist - bh_radius)**2 / (bh_radius**2 * (2 + energy)))
    color = color + grav_lens[:, :, np.newaxis] * np.array([0.2, 0.1, 0.4])
    
    img_arr = np.clip(color * 255, 0, 255).astype(np.uint8)
    img_arr = _apply_vhs_effects(img_arr)
    
    img = Image.fromarray(img_arr)
    glow = img.filter(ImageFilter.GaussianBlur(radius=15)).point(lambda p: p * (0.4 + energy*0.2))
    return ImageChops.add(img, glow)

def _render_frame_worker(args):
    """Worker para multiprocessing que genera un frame."""
    frame_idx, total_frames, prompt_lower, w, h, seed, palette, e = args
    t = frame_idx / float(total_frames)
    
    if any(kw in prompt_lower for kw in ["cyber", "neon", "city", "grid", "synthwave"]):
        img = _render_synthwave_3d(w, h, seed, palette, t, e)
    elif any(kw in prompt_lower for kw in ["fractal", "horror", "dark", "complex", "magic", "gold"]):
        img = _render_julia_fractal_3d(w, h, seed, palette, t, e)
    else:
        img = _render_space_odyssey(w, h, seed, palette, t, e)
        
    return frame_idx, img.tobytes()

def generate_procedural_video(prompt: str, seed: int, w: int, h: int, duration_sec: int, fps: int, out_mp4: str, audio_path: str = "") -> str:
    """
    Renderiza un videoclip procedimental matemático frame a frame y lo guarda como MP4
    vía FFmpeg nativo. Utiliza multiprocessing para usar el 100% de la CPU (todos los núcleos).
    """
    import sys
    import os
    import subprocess
    import multiprocessing
    
    palette = _get_palette(prompt)
    prompt_lower = prompt.lower()
    
    total_frames = int(duration_sec * fps)
    
    # ── Módulo Audio-Reactivo ──
    audio_energy = np.zeros(total_frames)
    if audio_path and os.path.isfile(audio_path):
        try:
            from core.video.audio_analyzer import extract_audio_energy
            full_energy = extract_audio_energy(audio_path, fps)
            if len(full_energy) > 0:
                sz = min(total_frames, len(full_energy))
                audio_energy[:sz] = full_energy[:sz]
        except Exception as e:
            print(f"[Motor Matemático V5] Falló el análisis de audio reactivo: {e}")
    
    # Buscar FFMPEG_EXE
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ffmpeg_exe = os.path.join(_base, "_integrations", "ffmpeg", "ffmpeg.exe")
    if not os.path.isfile(ffmpeg_exe):
        ffmpeg_exe = "ffmpeg"
        
    cmd = [
        ffmpeg_exe, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{w}x{h}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-"
    ]
    
    if audio_path and os.path.isfile(audio_path):
        cmd.extend(["-i", audio_path])
        cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23", "-c:a", "aac", "-b:a", "192k", "-shortest"])
    else:
        cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23"])
        
    cmd.append(out_mp4)
    
    n_cores = multiprocessing.cpu_count()
    print(f"\n[Motor Matemático V5] PARALELO: Usando {n_cores} núcleos de CPU.", file=sys.stderr)
    print(f"[Motor Matemático V5] Renderizando {total_frames} frames ({w}x{h}) para {os.path.basename(out_mp4)}...", file=sys.stderr)
    
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        
        args_list = [
            (i, total_frames, prompt_lower, w, h, seed, palette, float(audio_energy[i]))
            for i in range(total_frames)
        ]
        
        with multiprocessing.Pool(processes=n_cores) as pool:
            # imap asegura que recibimos los frames en orden secuencial
            for frame_idx, img_bytes in pool.imap(_render_frame_worker, args_list, chunksize=4):
                proc.stdin.write(img_bytes)
                if frame_idx % 24 == 0:
                    e = audio_energy[frame_idx]
                    print(f"  Frame {frame_idx}/{total_frames} ({(frame_idx/total_frames)*100:.1f}%) [Energy: {e:.3f}]", file=sys.stderr)
                    
        proc.stdin.close()
        proc.wait()

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error renderizando video V5: {e}", file=sys.stderr)
    finally:
        if 'proc' in locals() and proc.poll() is None:
            try:
                proc.stdin.close()
            except Exception:
                pass
            proc.terminate()
            proc.wait()
            
    print(f"[Motor Matemático V5] Video guardado en: {out_mp4}", file=sys.stderr)
    return out_mp4

def generate_art(prompt: str, seed: int, w: int, h: int, out_path: str) -> str:
    palette = _get_palette(prompt)
    prompt_lower = prompt.lower()
    
    try:
        if any(kw in prompt_lower for kw in ["cyber", "neon", "city", "grid", "synthwave"]):
            img = _render_synthwave_3d(w, h, seed, palette)
        elif any(kw in prompt_lower for kw in ["fractal", "horror", "dark", "complex", "magic", "gold"]):
            img = _render_julia_fractal_3d(w, h, seed, palette)
        else:
            img = _render_space_odyssey(w, h, seed, palette)
            
        img.save(out_path, "PNG")
        return out_path
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error en motor generativo procedural V3: {e}")
        img = Image.new("RGB", (w, h), color=(10, 10, 15))
        img.save(out_path, "PNG")
        return out_path
