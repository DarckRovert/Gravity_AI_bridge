import os
import sys
import moderngl
import numpy as np
import subprocess

# --- SHADERS GLSL V7 ---

VERTEX_SHADER = '''
#version 330
in vec2 in_vert;
out vec2 uv;
void main() {
    uv = in_vert * 0.5 + 0.5;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
'''

# 1. SPACE ODYSSEY V7 (SDF Black Hole Volumétrico)
SPACE_ODYSSEY_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;

uniform vec2 resolution;
uniform float time;
uniform float bass;
uniform float mid;
uniform float high;
uniform float pan;
uniform vec3 colorA;
uniform vec3 colorB;

mat2 rot(float a) {
    float s = sin(a), c = cos(a);
    return mat2(c, -s, s, c);
}

// Rotación 3D para la cámara (Pan influye aquí)
void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); }

float sdTorus( vec3 p, vec2 t ) {
  vec2 q = vec2(length(p.xz)-t.x,p.y);
  return length(q)-t.y;
}

float map(vec3 p) {
    // El horizonte de eventos
    float sphere = length(p) - 1.0;
    // Disco de acreción (warpeado por medios)
    vec3 dp = p;
    pR(dp.xz, time * 0.5);
    pR(dp.xy, mid * 0.5);
    float disk = sdTorus(dp, vec2(1.8 + bass*0.5, 0.05 + mid*0.1));
    
    return min(sphere, disk);
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    
    // Cámara orbital reactiva al paneo (pan)
    vec3 ro = vec3(0.0, 1.0, -4.0);
    pR(ro.xz, time * 0.1 + pan * 1.5);
    
    vec3 target = vec3(0.0);
    vec3 ww = normalize(target - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = normalize(cross(uu, ww));
    vec3 rd = normalize(p.x * uu + p.y * vv + 1.5 * ww);
    
    float t = 0.0;
    float max_d = 20.0;
    vec3 col = vec3(0.0);
    float glow = 0.0;
    
    // Raymarching
    for(int i = 0; i < 64; i++) {
        vec3 pos = ro + rd * t;
        float d = map(pos);
        if(d < 0.001 || t > max_d) break;
        t += d;
        // Acumular brillo para el disco
        if (length(pos) > 1.2) {
            glow += 0.02 / (0.05 + d*d) * (1.0 + bass*2.0);
        }
    }
    
    if(t < max_d) {
        vec3 pos = ro + rd * t;
        if(length(pos) < 1.01) {
            // Hoyo negro puro
            col = vec3(0.0);
        } else {
            // Disco
            col = mix(colorA, colorB, length(pos.xz)/3.0);
        }
    }
    
    // Fondo estrellado basado en altos
    float stars = pow(fract(sin(dot(p, vec2(12.9898,78.233))) * 43758.5453), 100.0) * (high * 5.0);
    col += vec3(stars);
    
    // Añadir Glow
    col += mix(colorA, colorB, 0.5) * glow * 0.05;
    
    fragColor = vec4(col, 1.0);
}
'''

# 2. SYNTHWAVE V7 (Grid 3D infinito con montañas SDF)
SYNTHWAVE_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;

uniform vec2 resolution;
uniform float time;
uniform float bass;
uniform float mid;
uniform float high;
uniform float pan;
uniform vec3 colorA;
uniform vec3 colorB;

void main() {
    vec2 st = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    
    // El pan inclina la cámara como si estuviéramos girando
    float tilt = pan * 0.5;
    mat2 rot = mat2(cos(tilt), -sin(tilt), sin(tilt), cos(tilt));
    st *= rot;
    
    vec3 color = vec3(0.0);
    
    // Sol vibrante
    float sunDist = length(st - vec2(0.0, 0.2));
    float sunRadius = 0.6 + (bass * 0.2);
    float sun = smoothstep(sunRadius, sunRadius - 0.02, sunDist);
    if(st.y < 0.2) {
        float stripes = sin(st.y * 50.0 - time * 5.0);
        sun *= smoothstep(0.0, 0.1, stripes);
    }
    vec3 sunColor = mix(vec3(1.0, 0.9, 0.0), colorA, st.y + 0.5);
    color += sun * sunColor;
    
    // Suelo con perspectiva real
    if (st.y < 0.0) {
        float perspective = 1.0 / abs(st.y);
        vec2 p = st * perspective;
        p.y -= time * (4.0 + mid * 2.0); // Avance
        p.x -= pan * perspective * 2.0; // Desplazamiento lateral por paneo
        
        float grid = sin(p.x * 10.0) * sin(p.y * 10.0);
        float line = smoothstep(0.9 - bass*0.15, 1.0, grid);
        
        vec3 gridColor = colorB * (1.0 + bass * 2.0 + high);
        color = mix(vec3(0.02, 0.0, 0.05), gridColor, line) * min(1.0, perspective * 0.15);
    }
    
    fragColor = vec4(color, 1.0);
}
'''

# 3. JULIA FRACTAL V7 (Quaterniones Raymarching Volumétricos)
JULIA_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;

uniform vec2 resolution;
uniform float time;
uniform float bass;
uniform float mid;
uniform float high;
uniform float pan;
uniform vec3 colorA;
uniform vec3 colorB;

// Distancia SDF a un Quaternión de Julia
float juliaSDF(vec3 p, vec4 c) {
    vec4 z = vec4(p, 0.0);
    float md2 = 1.0;
    float mz2 = dot(z, z);
    for(int i = 0; i < 8; i++) {
        // z^2 + c
        md2 *= 4.0 * mz2;
        vec4 nz;
        nz.x = z.x*z.x - dot(z.yzw, z.yzw);
        nz.yzw = 2.0 * z.x * z.yzw;
        z = nz + c;
        mz2 = dot(z, z);
        if(mz2 > 4.0) break;
    }
    return 0.25 * log(mz2) * sqrt(mz2 / md2);
}

void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); }

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    
    vec3 ro = vec3(0.0, 0.0, -2.5 + bass*0.5); // Bass hace zoom in/out
    pR(ro.xz, time * 0.2 + pan); // Pan rota la vista
    pR(ro.yz, sin(time*0.1)*0.5);
    
    vec3 target = vec3(0.0);
    vec3 ww = normalize(target - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = normalize(cross(uu, ww));
    vec3 rd = normalize(p.x * uu + p.y * vv + 1.0 * ww);
    
    vec4 c = vec4(sin(time*0.5)*0.5, cos(time*0.3)*0.5, mid*0.5, -0.2);
    
    float t = 0.0;
    float max_d = 10.0;
    float iter = 0.0;
    
    for(int i = 0; i < 64; i++) {
        vec3 pos = ro + rd * t;
        float d = juliaSDF(pos, c);
        if(d < 0.002 || t > max_d) break;
        t += d;
        iter++;
    }
    
    vec3 col = vec3(0.05, 0.0, 0.1); // Fondo
    if(t < max_d) {
        float f = iter / 64.0;
        col = mix(colorA, colorB, f * 2.0);
        col *= 1.0 - (t/max_d); // Fake AO
        col += high * 0.5; // Brillo especular
    }
    
    fragColor = vec4(col, 1.0);
}
'''

# --- POST PROCESAMIENTO (Chromatic Aberration, Bloom, Glitch) ---
POST_PROCESS_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;

uniform sampler2D tex;
uniform float bass;
uniform float high;

void main() {
    vec2 st = uv;
    
    // Camera Shake (Vibración) causado por Bajos extremos
    if (bass > 0.8) {
        float shake = (bass - 0.8) * 0.05;
        st.x += sin(st.y * 100.0) * shake;
        st.y += cos(st.x * 100.0) * shake;
    }
    
    // Aberración Cromática Direccional dictada por Bajos
    float aberration = bass * 0.03; 
    
    float r = texture(tex, st + vec2(aberration, 0.0)).r;
    float g = texture(tex, st).g;
    float b = texture(tex, st - vec2(aberration, 0.0)).b;
    
    vec3 col = vec3(r, g, b);
    
    // Bloom muy primitivo / Glow basado en Altos
    vec3 bloom = max(vec3(0.0), col - 0.5) * high * 2.0;
    col += bloom;
    
    fragColor = vec4(col, 1.0);
}
'''


def render_v7_video(timeline: list, multiband: dict, w: int, h: int, fps: int, out_mp4: str, audio_path: str, palette: tuple):
    ctx = moderngl.create_context(standalone=True)
    
    # 1. Shaders de Geometría
    prog_space = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=SPACE_ODYSSEY_FS)
    prog_synth = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=SYNTHWAVE_FS)
    prog_julia = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=JULIA_FS)
    
    engines = {
        "space_odyssey": prog_space,
        "synthwave": prog_synth,
        "julia_fractal": prog_julia
    }
    
    # 2. Shader de Post-Procesado
    prog_post = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=POST_PROCESS_FS)
    
    vertices = np.array([-1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0], dtype='f4')
    vbo = ctx.buffer(vertices)
    
    vaos = {name: ctx.vertex_array(prog, [(vbo, '2f', 'in_vert')]) for name, prog in engines.items()}
    vao_post = ctx.vertex_array(prog_post, [(vbo, '2f', 'in_vert')])
    
    # 3. Pipeline Multi-Pass
    # FBO 1: Geometría
    tex_geom = ctx.texture((w, h), components=3)
    fbo_geom = ctx.framebuffer(color_attachments=[tex_geom])
    
    # FBO 2: Final Post-Procesado
    fbo_final = ctx.framebuffer(color_attachments=[ctx.texture((w, h), components=3)])
    
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ffmpeg_exe = os.path.join(_base, "_integrations", "ffmpeg", "ffmpeg.exe")
    if not os.path.isfile(ffmpeg_exe): ffmpeg_exe = "ffmpeg"
        
    cmd = [
        ffmpeg_exe, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{w}x{h}", "-pix_fmt", "rgb24", "-r", str(fps),
        "-i", "-"
    ]
    if audio_path and os.path.isfile(audio_path):
        cmd.extend(["-i", audio_path, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23", "-c:a", "aac", "-b:a", "192k", "-shortest"])
    else:
        cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23"])
    cmd.append(out_mp4)
    
    colorA = tuple(float(c) for c in palette[0])
    colorB = tuple(float(c) for c in palette[2])
    
    for prog in engines.values():
        if 'resolution' in prog: prog['resolution'].value = (w, h)
        if 'colorA' in prog: prog['colorA'].value = colorA
        if 'colorB' in prog: prog['colorB'].value = colorB

    print(f"\n[🚀 Motor V7 GPU] INICIANDO RAYMARCHING VOLUMÉTRICO Y POST-FX...")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    total_frames = len(multiband['bass'])
    
    try:
        for frame_idx in range(total_frames):
            current_engine = "space_odyssey"
            for scene in timeline:
                if scene["start"] <= frame_idx <= scene["end"]:
                    current_engine = scene["engine"]
                    break
                    
            prog = engines[current_engine]
            vao = vaos[current_engine]
            
            t = frame_idx / float(fps)
            b = float(multiband['bass'][frame_idx])
            m = float(multiband['mid'][frame_idx])
            hg = float(multiband['high'][frame_idx])
            pan = float(multiband.get('pan', np.zeros(total_frames))[frame_idx])
            
            # Update uniforms
            if 'time' in prog: prog['time'].value = t
            if 'bass' in prog: prog['bass'].value = b
            if 'mid' in prog: prog['mid'].value = m
            if 'high' in prog: prog['high'].value = hg
            if 'pan' in prog: prog['pan'].value = pan
            
            # --- PASS 1: Renderizar Geometría ---
            fbo_geom.use()
            ctx.clear(0.0, 0.0, 0.0)
            vao.render(moderngl.TRIANGLE_STRIP)
            
            # --- PASS 2: Post-Procesamiento ---
            fbo_final.use()
            ctx.clear(0.0, 0.0, 0.0)
            tex_geom.use(location=0)
            if 'tex' in prog_post: prog_post['tex'].value = 0
            if 'bass' in prog_post: prog_post['bass'].value = b
            if 'high' in prog_post: prog_post['high'].value = hg
            
            vao_post.render(moderngl.TRIANGLE_STRIP)
            
            # --- EXPORTAR ---
            img_bytes = fbo_final.read(components=3)
            proc.stdin.write(img_bytes)
            
            if frame_idx % (fps*2) == 0:
                print(f"  Frame {frame_idx}/{total_frames} ({(frame_idx/total_frames)*100:.1f}%) [Scene: {current_engine}]", file=sys.stderr)
        
        proc.stdin.close()
        proc.wait()
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error renderizando video V7 GPU: {e}", file=sys.stderr)
    finally:
        if 'proc' in locals() and proc.poll() is None:
            try: proc.stdin.close()
            except Exception: pass
            proc.terminate()
            proc.wait()
            
    # Cleanup
    for v in vaos.values(): v.release()
    vao_post.release()
    for p in engines.values(): p.release()
    prog_post.release()
    vbo.release()
    tex_geom.release()
    fbo_geom.release()
    fbo_final.release()
    ctx.release()
    
    print(f"[✅ Motor V7 GPU] Video volumétrico renderizado en: {out_mp4}", file=sys.stderr)
    return out_mp4
