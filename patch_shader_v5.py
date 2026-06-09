import os
import re

filepath = r"f:\Gravity_AI_bridge\core\video\glsl_renderer_v13.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Imports
if "from PIL import Image" not in content:
    content = content.replace("import moderngl", "import moderngl\nfrom PIL import Image\n", 1)

# 2. Context & Texture
engine_init_code = """    ctx = moderngl.create_context(standalone=True)
    
    # [V5] Cargar Textura PBR (Inca Stone)
    tex_stone = None
    try:
        tex_path = r"f:\\Gravity_AI_bridge\\assets\\textures\\inca_stone.png"
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
"""
if "# [V5] Cargar Textura PBR" not in content:
    content = content.replace("    ctx = moderngl.create_context(standalone=True)", engine_init_code, 1)

# 3. Bind Uniform
bind_code = """        "inca_math":      ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=INCA_MATH_FS),
    }

    if tex_stone and 'tex_stone' in engines["inca_math"]:
        engines["inca_math"]['tex_stone'].value = 0
"""
if "if tex_stone and 'tex_stone' in engines[\"inca_math\"]" not in content:
    content = content.replace("""        "inca_math":      ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=INCA_MATH_FS),
    }""", bind_code, 1)

# 4. Sustituir el INCA_MATH_FS
NEW_SHADER = """INCA_MATH_FS = '''#version 330
out vec4 fragColor; in vec2 uv; uniform vec2 resolution; uniform float time, bass, mid, high, pan; uniform vec3 colorA, colorB; uniform int pose;
uniform sampler2D tex_stone; // [V5] PBR Texture

mat2 rot(float a) { float s = sin(a), c = cos(a); return mat2(c, s, -s, c); }
float hash(float n) { return fract(sin(n) * 43758.5453123); }

// Retenemos el ruido solo para la forma del SDF (no para color)
float noise(vec3 x) {
    vec3 p = floor(x); vec3 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    float n = p.x + p.y * 57.0 + 113.0 * p.z;
    return mix(mix(mix(hash(n + 0.0), hash(n + 1.0), f.x), mix(hash(n + 57.0), hash(n + 58.0), f.x), f.y),
               mix(mix(hash(n + 113.0), hash(n + 114.0), f.x), mix(hash(n + 170.0), hash(n + 171.0), f.x), f.y), f.z);
}
float fbm(vec3 p) {
    float f = 0.0; float a = 0.5;
    for(int i = 0; i < 4; i++) {
        f += a * noise(p); p *= 2.02; a *= 0.5;
    }
    return f;
}

float smin(float a, float b, float k) {
    float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
    return mix(b, a, h) - k * h * (1.0 - h);
}
float sdBox(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
}
float sdCylinder(vec3 p, vec2 h) {
    vec2 d = abs(vec2(length(p.xz), p.y)) - h;
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));
}

vec2 map(vec3 p) {
    vec2 res = vec2(p.y + 3.0, 1.0); 
    
    vec3 mp = p; mp.z -= 40.0; 
    float mountain = mp.y + 5.0 - 25.0 * exp(-0.01 * (mp.x*mp.x + mp.z*mp.z));
    mountain -= fbm(mp * 0.1) * 10.0; 
    if(mountain < res.x) res = vec2(mountain, 1.0);
    
    float terraces = 1e10;
    for(int i=0; i<8; i++) {
        float h = float(i) * 1.0;
        float z = float(i) * -1.5;
        terraces = smin(terraces, sdBox(p - vec3(0.0, h - 2.0, z), vec3(20.0, 0.5, 1.5)), 0.2);
    }
    terraces -= fbm(p * 2.0) * 0.1; 
    
    float stairs = 1e10;
    vec3 sp = p; sp.x = abs(sp.x) - 4.0; 
    for(int i=0; i<30; i++) {
        float h = float(i) * 0.25;
        float z = float(i) * -0.375;
        stairs = min(stairs, sdBox(sp - vec3(0.0, h - 2.0, z), vec3(0.8, 0.15, 0.3)));
    }
    
    float city_base = smin(terraces, stairs, 0.1);
    if(city_base < res.x) res = vec2(city_base, 2.0); 
    
    vec3 bp = p; bp.y -= 2.0; bp.z -= 5.0; 
    float torreon = sdCylinder(bp, vec2(4.0, 3.0));
    float torreon_in = sdCylinder(bp + vec3(0,0.5,0), vec2(3.5, 3.0));
    torreon = max(torreon, -torreon_in);
    
    vec3 cp = p - vec3(0.0, 10.0 + bass*0.5, -25.0);
    cp.xz *= rot(time * 0.2); 
    cp.xy *= rot(sin(time*0.1)*0.2);
    float b1 = sdBox(cp, vec3(4.0, 1.5, 1.0)); 
    float b2 = sdBox(cp, vec3(1.5, 4.0, 1.0)); 
    float b3 = sdBox(cp, vec3(2.5, 2.5, 1.0)); 
    float chacana = min(b1, min(b2, b3));
    chacana = max(chacana, -sdCylinder(cp.yxz, vec2(0.8, 1.5)));
    if(chacana < res.x) res = vec2(chacana, 4.0);
    
    res.x = smin(res.x, torreon, 0.1);
    return res;
}

vec3 getNormal(vec3 p) {
    vec2 e = vec2(0.01, 0.0);
    return normalize(vec3(
        map(p + e.xyy).x - map(p - e.xyy).x,
        map(p + e.yxy).x - map(p - e.yxy).x,
        map(p + e.yyx).x - map(p - e.yyx).x
    ));
}

float softshadow( in vec3 ro, in vec3 rd, in float mint, in float tmax, in float k ) {
    float res = 1.0; float t = mint;
    for( int i=0; i<32; i++ ) {
        float h = map( ro + rd*t ).x;
        res = min( res, k*h/t );
        t += clamp( h, 0.05, 0.50 );
        if( res<0.005 || t>tmax ) break;
    }
    return clamp( res, 0.0, 1.0 );
}

float ambientOcclusion(vec3 p, vec3 n) {
    float occ = 0.0; float sca = 1.0;
    for(int i = 0; i < 5; i++) {
        float h = 0.01 + 0.15 * float(i)/4.0;
        float d = map(p + h * n).x;
        occ += (h - d) * sca;
        sca *= 0.95;
    }
    return clamp(1.0 - 1.5 * occ, 0.0, 1.0);
}

// [V5] Triplanar Mapping
vec3 triplanar(sampler2D tex, vec3 p, vec3 n) {
    vec3 w = abs(n);
    w = max(w - 0.2, 0.0);
    w /= dot(w, vec3(1.0));
    vec3 tx = texture(tex, p.yz * 0.2).rgb;
    vec3 ty = texture(tex, p.xz * 0.2).rgb;
    vec3 tz = texture(tex, p.xy * 0.2).rgb;
    return tx*w.x + ty*w.y + tz*w.z;
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    
    float ct = mod(time * 0.2 + pan, 20.0); 
    vec3 ro, target;
    
    if (ct < 10.0) {
        float t_fase = ct / 10.0;
        ro = vec3(sin(t_fase*3.14)*8.0, 5.0 + t_fase*8.0, 15.0 - t_fase*25.0);
        target = vec3(0.0, 5.0 + t_fase*5.0, -15.0); 
    } else {
        float t_fase = (ct - 10.0) / 10.0;
        ro = vec3(0.0 + sin(t_fase*6.28)*3.0, 13.0 - t_fase*4.0, -10.0 - t_fase*10.0);
        target = vec3(0.0, 10.0, -25.0);
    }
    ro.y += bass * 0.3;
    
    vec3 cw = normalize(target - ro);
    vec3 cu = normalize(cross(cw, vec3(0.0, 1.0, 0.0)));
    vec3 cv = normalize(cross(cu, cw));
    vec3 rd = normalize(p.x*cu + p.y*cv + 1.2*cw);
    
    float t = 0.0; float tMax = 150.0;
    float mat_id = 0.0;
    float volumetric = 0.0; 
    
    vec3 sunDir = normalize(vec3(0.0, 0.05 + sin(time*0.1)*0.05, -1.0));
    
    for(int i = 0; i < 120; i++) {
        vec3 pos = ro + rd * t;
        vec2 res = map(pos);
        if(res.x < 0.01 || t > tMax) { mat_id = res.y; break; }
        
        if (i % 3 == 0) {
             float sha_vol = softshadow(pos, sunDir, 0.05, 10.0, 4.0);
             float fog_density = exp(-pos.y * 0.05) * 0.08;
             volumetric += fog_density * sha_vol * (1.0 + high);
        }
        t += res.x * 0.7; 
    }
    
    vec3 skyCol = mix(vec3(0.6, 0.1, 0.05), vec3(1.0, 0.8, 0.2), clamp(rd.y*4.0 + 0.2, 0.0, 1.0));
    skyCol = mix(skyCol, vec3(0.9, 0.9, 1.0), clamp(rd.y*2.0 - 0.2, 0.0, 1.0));
    
    float sun = clamp(dot(rd, sunDir), 0.0, 1.0);
    skyCol += vec3(1.0, 0.9, 0.6) * pow(sun, 16.0) * (1.0 + bass);
    
    vec3 col = skyCol;
    
    if(t < tMax) {
        vec3 pos = ro + rd * t;
        vec3 n = getNormal(pos);
        
        float dif = clamp(dot(n, sunDir), 0.0, 1.0);
        float sha = softshadow(pos, sunDir, 0.05, 50.0, 12.0);
        float ao = ambientOcclusion(pos, n);
        float amb = 0.5 + 0.5 * n.y;
        
        vec3 objCol;
        
        if (mat_id == 4.0) {
            objCol = vec3(1.0, 0.8, 0.3);
            dif += pow(clamp(dot(reflect(rd, n), sunDir), 0.0, 1.0), 32.0) * 2.0; 
            amb += 0.5; 
        } else {
            // [V5] Triplanar texture mapping. Reemplaza el fbm pesado.
            vec3 texCol = triplanar(tex_stone, pos, n);
            objCol = pow(texCol, vec3(1.2)) * 1.5; 
            
            // Musgo hiper optimizado (solo math basico, no loops)
            float moss_factor = smoothstep(0.4, 0.7, n.y) * texCol.g;
            vec3 mossCol = vec3(0.1, 0.3, 0.05);
            objCol = mix(objCol, mossCol, moss_factor);
        }
        
        vec3 lin = vec3(1.5, 1.0, 0.7) * dif * sha; 
        lin += vec3(0.2, 0.3, 0.4) * amb * ao; 
        col = objCol * lin;
        
        if (mat_id == 1.0) {
            float r = length(pos.xz); float ang = atan(pos.z, pos.x);
            float spiral = abs(sin(r * 1.5 - ang * 4.0 + time));
            float lines = smoothstep(0.05, 0.02, spiral);
            lines *= smoothstep(40.0, 0.0, r); 
            vec3 nazcaGlow = vec3(1.0, 0.3, 0.1) * lines * (1.0 + bass * 3.0);
            col += nazcaGlow * ao; 
        }
        
        float fogHeight = exp(-pos.y * 0.1);
        float fogDist = 1.0 - exp(-0.001 * t * t);
        col = mix(col, skyCol, fogDist * fogHeight);
    }
    
    col += vec3(1.0, 0.6, 0.3) * volumetric * 0.08;
    col = (col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14);
    fragColor = vec4(col, 1.0);
}
'''
"""
pattern = re.compile(r"INCA_MATH_FS\s*=\s*'''#version 330.*?'''\n", re.DOTALL)

if pattern.search(content):
    content = pattern.sub(NEW_SHADER, content)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("V5 Patch (Triplanar) applied successfully.")
else:
    print("Error: Regex for INCA_MATH_FS failed.")
