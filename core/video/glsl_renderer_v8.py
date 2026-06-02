import os
import sys
import moderngl
import numpy as np
import subprocess

# --- SHADERS GLSL V8 (MAESTRÍA VISUAL) ---

VERTEX_SHADER = '''
#version 330
in vec2 in_vert;
out vec2 uv;
void main() {
    uv = in_vert * 0.5 + 0.5;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
'''

# 1. SPACE ODYSSEY (Agujero Negro Volumétrico)
SPACE_ODYSSEY_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, pan;
uniform vec3 colorA, colorB;

mat2 rot(float a) { float s = sin(a), c = cos(a); return mat2(c, -s, s, c); }
void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); }

float sdTorus( vec3 p, vec2 t ) { return length(vec2(length(p.xz)-t.x,p.y))-t.y; }

float map(vec3 p) {
    float sphere = length(p) - 1.0;
    vec3 dp = p;
    pR(dp.xz, time * 0.5); pR(dp.xy, mid * 0.5);
    float disk = sdTorus(dp, vec2(1.8 + bass*0.5, 0.05 + mid*0.1));
    return min(sphere, disk);
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    vec3 ro = vec3(0.0, 1.0, -4.0); pR(ro.xz, time * 0.1 + pan * 1.5);
    vec3 ww = normalize(-ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = normalize(cross(uu, ww));
    vec3 rd = normalize(p.x * uu + p.y * vv + 1.5 * ww);
    
    float t = 0.0; float max_d = 20.0; vec3 col = vec3(0.0); float glow = 0.0;
    for(int i=0; i<64; i++) {
        vec3 pos = ro + rd*t; float d = map(pos);
        if(d<0.001 || t>max_d) break;
        t += d;
        if(length(pos)>1.2) glow += 0.02 / (0.05 + d*d) * (1.0 + bass*2.0);
    }
    
    if(t<max_d) {
        vec3 pos = ro + rd*t;
        if(length(pos)<1.01) col = vec3(0.0);
        else col = mix(colorA, colorB, length(pos.xz)/3.0);
    }
    float stars = pow(fract(sin(dot(p, vec2(12.9898,78.233))) * 43758.5453), 100.0) * (high * 5.0);
    col += vec3(stars) + mix(colorA, colorB, 0.5)*glow*0.05;
    fragColor = vec4(col, 1.0);
}
'''

# 2. JULIA FRACTAL (Quaterniones)
JULIA_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, pan;
uniform vec3 colorA, colorB;

float juliaSDF(vec3 p, vec4 c) {
    vec4 z = vec4(p, 0.0); float md2 = 1.0, mz2 = dot(z, z);
    for(int i=0; i<8; i++) {
        md2 *= 4.0 * mz2;
        vec4 nz; nz.x = z.x*z.x - dot(z.yzw, z.yzw); nz.yzw = 2.0 * z.x * z.yzw;
        z = nz + c; mz2 = dot(z, z);
        if(mz2>4.0) break;
    }
    return 0.25 * log(mz2) * sqrt(mz2 / md2);
}
void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); }

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    vec3 ro = vec3(0.0, 0.0, -2.5 + bass*0.5); 
    pR(ro.xz, time * 0.2 + pan); pR(ro.yz, sin(time*0.1)*0.5);
    vec3 ww = normalize(-ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = normalize(cross(uu, ww));
    vec3 rd = normalize(p.x * uu + p.y * vv + 1.0 * ww);
    
    vec4 c = vec4(sin(time*0.5)*0.5, cos(time*0.3)*0.5, mid*0.5, -0.2);
    float t = 0.0, max_d = 10.0, iter = 0.0;
    
    for(int i=0; i<64; i++) {
        vec3 pos = ro + rd*t; float d = juliaSDF(pos, c);
        if(d<0.002 || t>max_d) break;
        t += d; iter++;
    }
    
    vec3 col = colorA * 0.1;
    if(t<max_d) {
        col = mix(colorA, colorB, iter/64.0 * 2.0);
        col *= 1.0 - (t/max_d);
        col += high * 0.5;
    }
    fragColor = vec4(col, 1.0);
}
'''

# 3. MANDELBULB 3D (El monstruo hiperdetallado con normales y PBR falso)
MANDELBULB_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, pan;
uniform vec3 colorA, colorB;

void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); }

float mandelbulbSDF(vec3 pos) {
    vec3 z = pos;
    float dr = 1.0;
    float r = 0.0;
    float Power = 8.0 + sin(time*0.2)*2.0 + bass*4.0; // El bajo deforma el Mandelbulb
    for (int i=0; i<8; i++) {
        r = length(z);
        if (r>2.0) break;
        float theta = acos(z.z/r);
        float phi = atan(z.y, z.x);
        dr =  pow( r, Power-1.0)*Power*dr + 1.0;
        float zr = pow( r,Power);
        theta = theta*Power;
        phi = phi*Power;
        z = zr*vec3(sin(theta)*cos(phi), sin(phi)*sin(theta), cos(theta));
        z+=pos;
    }
    return 0.5*log(r)*r/dr;
}

vec3 calcNormal(vec3 pos) {
    vec2 e = vec2(1.0,-1.0)*0.5773*0.001;
    return normalize( e.xyy*mandelbulbSDF( pos + e.xyy ) + 
					  e.yyx*mandelbulbSDF( pos + e.yyx ) + 
					  e.yxy*mandelbulbSDF( pos + e.yxy ) + 
					  e.xxx*mandelbulbSDF( pos + e.xxx ) );
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    vec3 ro = vec3(0.0, 0.0, -2.5);
    pR(ro.xz, time * 0.1 + pan);
    pR(ro.xy, time * 0.05);
    
    vec3 ww = normalize(-ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = normalize(cross(uu, ww));
    vec3 rd = normalize(p.x * uu + p.y * vv + 1.0 * ww);
    
    float t = 0.0;
    float max_d = 10.0;
    float trap = 1.0;
    for(int i=0; i<80; i++) {
        vec3 pos = ro + rd*t;
        float d = mandelbulbSDF(pos);
        trap = min(trap, d);
        if(d<0.001 || t>max_d) break;
        t += d;
    }
    
    vec3 col = colorA * 0.05; // Fondo
    if(t<max_d) {
        vec3 pos = ro + rd*t;
        vec3 nor = calcNormal(pos);
        
        // PBR falso (Luz direccional + Especularidad por Agudos)
        vec3 lig = normalize(vec3(1.0, 1.0, -1.0));
        float dif = clamp(dot(nor, lig), 0.0, 1.0);
        float spe = pow(clamp(dot(reflect(rd, nor), lig), 0.0, 1.0), 16.0);
        
        col = mix(colorA, colorB, length(pos)/1.5);
        col *= dif + 0.1; // Ambient
        col += spe * (0.5 + high * 2.0) * colorB; // Brillos como cristal/oro
    } else {
        col += mix(colorA, colorB, 0.5) * exp(-trap*5.0) * bass; // Halo exterior
    }
    
    fragColor = vec4(col, 1.0);
}
'''

# 4. NEBULA VOLUMÉTRICA (Raymarching FBM translúcido)
NEBULA_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, pan;
uniform vec3 colorA, colorB;

void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); }

float noise(vec3 p) {
    vec3 i = floor(p); vec3 f = fract(p);
    f = f*f*(3.0-2.0*f);
    vec2 uv = (i.xy+vec2(37.0,17.0)*i.z) + f.xy;
    vec2 rg = fract(sin((uv+0.5)*0.014)*292.0); // fake 3d noise
    return mix(rg.x, rg.y, f.z);
}

float mapNebula(vec3 p) {
    float f = 0.0;
    vec3 q = p - vec3(0.0, 0.0, time*2.0); // Viajar a través de la nebulosa
    f += 0.5000*noise( q ); q = q*2.01;
    f += 0.2500*noise( q ); q = q*2.02;
    f += 0.1250*noise( q ); q = q*2.03;
    f += 0.0625*noise( q );
    return f - 0.5; // Densidad
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    vec3 ro = vec3(0.0, 0.0, 0.0);
    pR(ro.xy, pan); // Paneo estéreo inclina la vista
    
    vec3 rd = normalize(vec3(p.x, p.y, 1.0));
    pR(rd.xy, sin(time*0.2)*0.5);
    
    float t = 0.0;
    vec4 sum = vec4(0.0);
    
    // Raymarching Volumétrico
    for(int i=0; i<50; i++) {
        vec3 pos = ro + rd*t;
        float den = mapNebula(pos);
        if(den > 0.01) {
            // Color de la nube basado en la posición y el audio
            vec3 col = mix(colorA, colorB, clamp(den*2.0, 0.0, 1.0));
            col *= mix(1.0, 3.0, bass); // Destellos internos en el bajo
            col += high * colorB * 0.5; // Chisporroteo agudo
            
            vec4 src = vec4(col * den, den);
            src.rgb *= src.a;
            sum = sum + src*(1.0 - sum.a); // Acumular opacidad (Alpha Blending)
        }
        if(sum.a > 0.99) break;
        t += 0.1;
    }
    
    fragColor = vec4(sum.rgb, 1.0);
}
'''

# 5. QUANTUM TUNNEL (Geometría hiper rápida)
QUANTUM_TUNNEL_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, pan;
uniform vec3 colorA, colorB;

void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); }

float tunnelSDF(vec3 p) {
    // Hexágono invertido
    vec2 q = abs(p.xy);
    float d = max(q.x*0.866025 + q.y*0.5, q.y) - 2.0;
    // Anillos
    float rings = abs(fract(p.z*2.0 - time*(10.0 + bass*20.0)) - 0.5) - 0.1;
    return max(-d, rings);
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    vec3 ro = vec3(0.0, 0.0, time*(5.0 + mid*5.0)); // Avance rápido
    ro.x += sin(time*2.0)*0.5 + pan; // Oscilación
    
    vec3 rd = normalize(vec3(p.x, p.y, 1.0));
    pR(rd.xy, sin(time)*0.2);
    
    float t = 0.0;
    float max_d = 30.0;
    float glow = 0.0;
    
    for(int i=0; i<40; i++) {
        vec3 pos = ro + rd*t;
        float d = tunnelSDF(pos);
        glow += 0.01 / (0.01 + d*d); // Acumular neón
        if(d<0.01 || t>max_d) break;
        t += d;
    }
    
    vec3 col = colorA * 0.1;
    if(t<max_d) {
        col = mix(colorA, colorB, fract(t*0.1));
    }
    col += mix(colorA, colorB, 0.5) * glow * (0.5 + high); // Glow estalla
    
    fragColor = vec4(col, 1.0);
}
'''


# --- POST PROCESAMIENTO V8 (Crossover Volumétrico y Aberración) ---
POST_PROCESS_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;

uniform sampler2D tex1;
uniform sampler2D tex2;
uniform float transition_t; // 0.0 = Solo tex1, 1.0 = Solo tex2
uniform float bass;
uniform float high;

void main() {
    vec2 st = uv;
    
    // Camera Shake
    if (bass > 0.8) {
        float shake = (bass - 0.8) * 0.03;
        st.x += sin(st.y * 100.0) * shake;
        st.y += cos(st.x * 100.0) * shake;
    }
    
    // Aberración cromática Direccional
    float ab = bass * 0.02;
    
    vec3 col1 = vec3(
        texture(tex1, st + vec2(ab, 0.0)).r,
        texture(tex1, st).g,
        texture(tex1, st - vec2(ab, 0.0)).b
    );
    
    vec3 col2 = vec3(
        texture(tex2, st + vec2(ab, 0.0)).r,
        texture(tex2, st).g,
        texture(tex2, st - vec2(ab, 0.0)).b
    );
    
    // Morphing / Crossfade Volumétrico con Distorsión
    // Si estamos en transición, distorsionamos las coordenadas basadas en el ruido (tex1 luminance)
    float luma1 = dot(col1, vec3(0.299, 0.587, 0.114));
    vec2 warp_st = st + (luma1 * 0.1 * transition_t);
    vec3 warped_col2 = texture(tex2, warp_st).rgb;
    
    // Mezcla suave
    vec3 final_col = mix(col1, mix(col2, warped_col2, transition_t), transition_t);
    
    // Bloom
    vec3 bloom = max(vec3(0.0), final_col - 0.6) * high * 1.5;
    final_col += bloom;
    
    fragColor = vec4(final_col, 1.0);
}
'''


def render_v8_video(timeline: list, multiband: dict, colorsA: np.ndarray, colorsB: np.ndarray, w: int, h: int, fps: int, out_mp4: str, audio_path: str):
    ctx = moderngl.create_context(standalone=True)
    
    # 1. Compilar 5 Motores
    engines = {
        "space_odyssey": ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=SPACE_ODYSSEY_FS),
        "julia_fractal": ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=JULIA_FS),
        "mandelbulb": ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=MANDELBULB_FS),
        "nebula": ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=NEBULA_FS),
        "quantum_tunnel": ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=QUANTUM_TUNNEL_FS),
    }
    
    prog_post = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=POST_PROCESS_FS)
    
    vertices = np.array([-1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0], dtype='f4')
    vbo = ctx.buffer(vertices)
    
    vaos = {name: ctx.vertex_array(prog, [(vbo, '2f', 'in_vert')]) for name, prog in engines.items()}
    vao_post = ctx.vertex_array(prog_post, [(vbo, '2f', 'in_vert')])
    
    # 3. Pipeline V8: Doble FBO para Geometría (Para Crossfade)
    tex_geom1 = ctx.texture((w, h), components=3)
    fbo_geom1 = ctx.framebuffer(color_attachments=[tex_geom1])
    
    tex_geom2 = ctx.texture((w, h), components=3)
    fbo_geom2 = ctx.framebuffer(color_attachments=[tex_geom2])
    
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
    
    print(f"\n[🚀 Motor V8] INICIANDO MAESTRÍA VISUAL (CROSSFADES Y PBR)...")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    total_frames = len(multiband['bass'])
    
    try:
        for frame_idx in range(total_frames):
            # Identificar escena actual y si hay transición
            engine_1 = "space_odyssey"
            engine_2 = None
            transition_t = 0.0
            
            for scene in timeline:
                if scene["start"] <= frame_idx <= scene["end"]:
                    engine_1 = scene["engine"]
                    # Chequear si estamos en transición de salida hacia la próxima escena
                    if "transition_start" in scene and frame_idx >= scene["transition_start"]:
                        # Encontrar la próxima escena
                        for next_sc in timeline:
                            if next_sc["start"] == scene["end"]:
                                engine_2 = next_sc["engine"]
                                total_trans_frames = scene["end"] - scene["transition_start"]
                                transition_t = (frame_idx - scene["transition_start"]) / float(total_trans_frames)
                                break
                    break
                    
            t = frame_idx / float(fps)
            b = float(multiband['bass'][frame_idx])
            m = float(multiband['mid'][frame_idx])
            hg = float(multiband['high'][frame_idx])
            pan = float(multiband.get('pan', np.zeros(total_frames))[frame_idx])
            
            cA = tuple(float(x) for x in colorsA[frame_idx])
            cB = tuple(float(x) for x in colorsB[frame_idx])
            
            def render_pass(engine_name, fbo):
                prog = engines[engine_name]
                if 'resolution' in prog: prog['resolution'].value = (w, h)
                if 'time' in prog: prog['time'].value = t
                if 'bass' in prog: prog['bass'].value = b
                if 'mid' in prog: prog['mid'].value = m
                if 'high' in prog: prog['high'].value = hg
                if 'pan' in prog: prog['pan'].value = pan
                if 'colorA' in prog: prog['colorA'].value = cA
                if 'colorB' in prog: prog['colorB'].value = cB
                fbo.use()
                ctx.clear(0.0, 0.0, 0.0)
                vaos[engine_name].render(moderngl.TRIANGLE_STRIP)

            # RENDER ENGINE 1
            render_pass(engine_1, fbo_geom1)
            
            # RENDER ENGINE 2 (Si hay transición)
            if engine_2 is not None:
                render_pass(engine_2, fbo_geom2)
            
            # --- POST-PROCESAMIENTO (CROSSFADE Y FX) ---
            fbo_final.use()
            ctx.clear(0.0, 0.0, 0.0)
            
            tex_geom1.use(location=0)
            if 'tex1' in prog_post: prog_post['tex1'].value = 0
            if engine_2 is not None:
                tex_geom2.use(location=1)
                if 'tex2' in prog_post: prog_post['tex2'].value = 1
            else:
                tex_geom1.use(location=1) # Fallback, tex1 en ambos lados = 0 transición
                if 'tex2' in prog_post: prog_post['tex2'].value = 1
                
            if 'transition_t' in prog_post: prog_post['transition_t'].value = transition_t
            if 'bass' in prog_post: prog_post['bass'].value = b
            if 'high' in prog_post: prog_post['high'].value = hg
            
            vao_post.render(moderngl.TRIANGLE_STRIP)
            
            # EXPORTAR
            img_bytes = fbo_final.read(components=3)
            proc.stdin.write(img_bytes)
            
            if frame_idx % (fps*2) == 0:
                print(f"  Frame {frame_idx}/{total_frames} ({(frame_idx/total_frames)*100:.1f}%) [Sc1: {engine_1} | Trans: {transition_t:.2f}]", file=sys.stderr)
        
        proc.stdin.close()
        proc.wait()
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error renderizando video V8 GPU: {e}", file=sys.stderr)
    finally:
        if 'proc' in locals() and proc.poll() is None:
            try: proc.stdin.close()
            except Exception: pass
            proc.terminate()
            proc.wait()
            
    # Cleanup masivo
    for v in vaos.values(): v.release()
    vao_post.release()
    for p in engines.values(): p.release()
    prog_post.release()
    vbo.release()
    tex_geom1.release()
    tex_geom2.release()
    fbo_geom1.release()
    fbo_geom2.release()
    fbo_final.release()
    ctx.release()
    
    print(f"[✅ Motor V8] Video Maestro renderizado en: {out_mp4}", file=sys.stderr)
    return out_mp4
