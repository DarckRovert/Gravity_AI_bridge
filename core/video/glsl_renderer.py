import os
import sys
import moderngl
import numpy as np
import subprocess
from PIL import ImageColor

# --- SHADERS GLSL ---

VERTEX_SHADER = '''
#version 330
in vec2 in_vert;
out vec2 uv;
void main() {
    uv = in_vert * 0.5 + 0.5;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
'''

# 1. SPACE ODYSSEY (Agujero Negro / Dominio Espacial)
SPACE_ODYSSEY_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;

uniform vec2 resolution;
uniform float time;
uniform float bass;
uniform float mid;
uniform float high;
uniform vec3 colorA;
uniform vec3 colorB;

// Simple 2D Noise
float random (in vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
}

// 2D Noise based on Morgan McGuire
float noise (in vec2 st) {
    vec2 i = floor(st);
    vec2 f = fract(st);
    float a = random(i);
    float b = random(i + vec2(1.0, 0.0));
    float c = random(i + vec2(0.0, 1.0));
    float d = random(i + vec2(1.0, 1.0));
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(a, b, u.x) + (c - a)* u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}

#define OCTAVES 5
float fbm (in vec2 st) {
    float value = 0.0;
    float amplitude = .5;
    vec2 shift = vec2(100.0);
    mat2 rot = mat2(cos(0.5), sin(0.5), -sin(0.5), cos(0.50));
    for (int i = 0; i < OCTAVES; i++) {
        value += amplitude * noise(st);
        st = rot * st * 2.0 + shift;
        amplitude *= 0.5;
    }
    return value;
}

void main() {
    vec2 st = gl_FragCoord.xy / resolution.xy;
    st.x *= resolution.x / resolution.y;
    
    // Domain Warping dictado por Medios
    vec2 q = vec2(0.);
    q.x = fbm(st + 0.00 * time + mid * 0.2);
    q.y = fbm(st + vec2(1.0));
    
    vec2 r = vec2(0.);
    r.x = fbm(st + 1.0 * q + vec2(1.7,9.2)+ 0.15 * time);
    r.y = fbm(st + 1.0 * q + vec2(8.3,2.8)+ 0.12 * time);
    
    float f = fbm(st + r);
    
    // Color
    vec3 color = mix(vec3(0.101961,0.619608,0.666667),
                     vec3(0.666667,0.666667,0.498039),
                     clamp((f*f)*4.0,0.0,1.0));
                     
    color = mix(color, colorA, clamp(length(q),0.0,1.0));
    color = mix(color, colorB, clamp(length(r.x),0.0,1.0));
    
    // Agujero Negro dictado por Bajos
    vec2 center = vec2(0.5 * (resolution.x/resolution.y), 0.5);
    float dist = distance(st, center);
    float bh_radius = 0.15 + (bass * 0.1);
    float disk = smoothstep(bh_radius, bh_radius + 0.05, dist);
    
    // Estrellas por Altos
    float stars = pow(random(st), 150.0) * (2.0 + high * 5.0);
    
    fragColor = vec4((f * f * f + .6 * f * f + .5 * f) * color * disk + vec3(stars), 1.0);
}
'''

# 2. SYNTHWAVE (Grid Retro)
SYNTHWAVE_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;

uniform vec2 resolution;
uniform float time;
uniform float bass;
uniform float mid;
uniform float high;
uniform vec3 colorA;
uniform vec3 colorB;

void main() {
    vec2 st = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    
    vec3 color = vec3(0.0);
    
    // Sol vibrante (Bass)
    float sunDist = length(st - vec2(0.0, 0.2));
    float sunRadius = 0.6 + (bass * 0.15);
    float sun = smoothstep(sunRadius, sunRadius - 0.02, sunDist);
    if(st.y < 0.2) {
        float stripes = sin(st.y * 50.0 - time * 5.0);
        sun *= smoothstep(0.0, 0.1, stripes);
    }
    vec3 sunColor = mix(vec3(1.0, 0.9, 0.0), colorA, st.y + 0.5);
    color += sun * sunColor;
    
    // Suelo de cuadrícula (Mid mueve cámara, Bass satura)
    if (st.y < 0.0) {
        float perspective = 1.0 / abs(st.y);
        float u = st.x * perspective;
        float v = perspective + time * (2.0 + mid * 2.0);
        
        float grid = sin(u * 10.0) * sin(v * 10.0);
        float thickness = 0.95 - (bass * 0.1);
        float line = smoothstep(thickness, 1.0, grid);
        
        vec3 gridColor = colorB * (1.0 + bass * 2.0);
        color = mix(vec3(0.05, 0.0, 0.1), gridColor, line) * min(1.0, perspective * 0.2);
    }
    
    fragColor = vec4(color, 1.0);
}
'''

# 3. JULIA FRACTAL 3D (Raymarching aproximado / Fractal 2D profundo)
JULIA_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;

uniform vec2 resolution;
uniform float time;
uniform float bass;
uniform float mid;
uniform float high;
uniform vec3 colorA;
uniform vec3 colorB;

vec2 complex_sq(vec2 z) {
    return vec2(z.x * z.x - z.y * z.y, 2.0 * z.x * z.y);
}

void main() {
    vec2 z = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    
    // El warping de medios y el zoom de bajos
    float zoom = 1.0 - (bass * 0.3);
    z *= zoom;
    
    // Constante de Julia animada por el tiempo y los medios
    vec2 c = vec2(sin(time*0.5)*0.5 - 0.2, cos(time*0.3)*0.5 + mid*0.2);
    
    float iter = 0.0;
    const float max_iter = 100.0;
    for(int i = 0; i < int(max_iter); i++) {
        z = complex_sq(z) + c;
        if(length(z) > 4.0) break;
        iter += 1.0;
    }
    
    // Coloreo suave (Highs agregan destellos de fase)
    float smooth_iter = iter - log(log(length(z))) / log(2.0);
    float t = smooth_iter / max_iter;
    t += high * 0.1; 
    
    vec3 color = mix(colorA, colorB, t * 5.0);
    // Oscurecer interiores
    if(iter == max_iter) color = vec3(0.0);
    
    fragColor = vec4(color * (1.0 + bass), 1.0);
}
'''

def render_v6_video(timeline: list, multiband: dict, w: int, h: int, fps: int, out_mp4: str, audio_path: str, palette: tuple):
    """
    Renderiza el video iterando a lo largo del timeline, pasando los valores multi-banda al GPU.
    """
    # 1. Iniciar Contexto Headless GPU
    ctx = moderngl.create_context(standalone=True)
    
    # 2. Compilar Shaders
    prog_space = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=SPACE_ODYSSEY_FS)
    prog_synth = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=SYNTHWAVE_FS)
    prog_julia = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=JULIA_FS)
    
    engines = {
        "space_odyssey": prog_space,
        "synthwave": prog_synth,
        "julia_fractal": prog_julia
    }
    
    # 3. Geometría a pantalla completa (Quad)
    vertices = np.array([
        -1.0, -1.0,
         1.0, -1.0,
        -1.0,  1.0,
         1.0,  1.0
    ], dtype='f4')
    vbo = ctx.buffer(vertices)
    
    vaos = {
        name: ctx.vertex_array(prog, [(vbo, '2f', 'in_vert')])
        for name, prog in engines.items()
    }
    
    # 4. Configurar Framebuffer
    fbo = ctx.framebuffer(
        color_attachments=[ctx.texture((w, h), components=3)]
    )
    
    # 5. Pipeline FFmpeg
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ffmpeg_exe = os.path.join(_base, "_integrations", "ffmpeg", "ffmpeg.exe")
    if not os.path.isfile(ffmpeg_exe):
        ffmpeg_exe = "ffmpeg"
        
    cmd = [
        ffmpeg_exe, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{w}x{h}", "-pix_fmt", "rgb24", "-r", str(fps),
        "-i", "-"
    ]
    if audio_path and os.path.isfile(audio_path):
        cmd.extend(["-i", audio_path])
        cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23", "-c:a", "aac", "-b:a", "192k", "-shortest"])
    else:
        cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23"])
    cmd.append(out_mp4)
    
    colorA = tuple(float(c) for c in palette[0])
    colorB = tuple(float(c) for c in palette[2])
    
    # Init uniform base values
    for prog in engines.values():
        if 'resolution' in prog: prog['resolution'].value = (w, h)
        if 'colorA' in prog: prog['colorA'].value = colorA
        if 'colorB' in prog: prog['colorB'].value = colorB

    print(f"\n[🚀 Motor V6 GPU] RENDERIZANDO A TIEMPO REAL EN LA TARJETA GRÁFICA...")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    total_frames = len(multiband['bass'])
    
    try:
        fbo.use()
        for frame_idx in range(total_frames):
            # Obtener motor según timeline
            current_engine = "space_odyssey"
            for scene in timeline:
                if scene["start"] <= frame_idx <= scene["end"]:
                    current_engine = scene["engine"]
                    break
                    
            prog = engines[current_engine]
            vao = vaos[current_engine]
            
            # Pasar uniforms de audio y tiempo
            t = frame_idx / float(fps)
            if 'time' in prog: prog['time'].value = t
            if 'bass' in prog: prog['bass'].value = float(multiband['bass'][frame_idx])
            if 'mid' in prog: prog['mid'].value = float(multiband['mid'][frame_idx])
            if 'high' in prog: prog['high'].value = float(multiband['high'][frame_idx])
            
            # Render GPU Frame
            ctx.clear(0.0, 0.0, 0.0)
            vao.render(moderngl.TRIANGLE_STRIP)
            
            # Descargar GPU RAM a CPU RAM (muy rápido)
            img_bytes = fbo.read(components=3)
            proc.stdin.write(img_bytes)
            
            if frame_idx % (fps*2) == 0:
                print(f"  Frame {frame_idx}/{total_frames} ({(frame_idx/total_frames)*100:.1f}%) [Scene: {current_engine}]", file=sys.stderr)
        
        # [CORRECCIÓN CRÍTICA]: Cerrar el stdin para avisar a ffmpeg que terminamos de enviar frames.
        # Luego esperar a que FFmpeg termine de codificar y escriba la cabecera (MOOV atom) del MP4.
        proc.stdin.close()
        proc.wait()
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error renderizando video V6 GPU: {e}", file=sys.stderr)
    finally:
        if 'proc' in locals() and proc.poll() is None:
            try:
                proc.stdin.close()
            except Exception: pass
            proc.terminate()
            proc.wait()
            
    # Liberar recursos GPU
    for v in vaos.values(): v.release()
    for p in engines.values(): p.release()
    vbo.release()
    fbo.release()
    ctx.release()
    
    print(f"[✅ Motor V6 GPU] Video maestro renderizado en: {out_mp4}", file=sys.stderr)
    return out_mp4
