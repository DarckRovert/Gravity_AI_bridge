import os
import re

filepath = r"f:\Gravity_AI_bridge\core\video\glsl_renderer_v13.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

pattern = re.compile(r"INCA_MATH_FS\s*=\s*'''#version 330.*?'''\n", re.DOTALL)

NEW_SHADER = """INCA_MATH_FS = '''#version 330
out vec4 fragColor; in vec2 uv; uniform vec2 resolution; uniform float time, bass, mid, high, pan; uniform vec3 colorA, colorB; uniform int pose;

mat2 rot(float a) { float s = sin(a), c = cos(a); return mat2(c, s, -s, c); }
float hash(float n) { return fract(sin(n) * 43758.5453123); }

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

// Retorna vec2(distancia, material_id)
vec2 map(vec3 p) {
    vec2 res = vec2(p.y + 3.0, 1.0); // Terreno base
    
    // Huayna Picchu
    vec3 mp = p; mp.z -= 40.0; 
    float mountain = mp.y + 5.0 - 25.0 * exp(-0.01 * (mp.x*mp.x + mp.z*mp.z));
    mountain -= fbm(mp * 0.1) * 10.0; 
    if(mountain < res.x) res = vec2(mountain, 1.0);
    
    // Andenes y Terrazas (SDF seguro usando loops)
    float terraces = 1e10;
    for(int i=0; i<8; i++) {
        float h = float(i) * 1.0;
        float z = float(i) * -1.5;
        // Cajas largas curvadas por el terreno? No, cajas anchas
        terraces = smin(terraces, sdBox(p - vec3(0.0, h - 2.0, z), vec3(20.0, 0.5, 1.5)), 0.2);
    }
    terraces -= fbm(p * 2.0) * 0.1; 
    
    // Escalinatas (SDF seguro)
    float stairs = 1e10;
    vec3 sp = p; sp.x = abs(sp.x) - 4.0; 
    for(int i=0; i<30; i++) {
        float h = float(i) * 0.25;
        float z = float(i) * -0.375;
        stairs = min(stairs, sdBox(sp - vec3(0.0, h - 2.0, z), vec3(0.8, 0.15, 0.3)));
    }
    
    float city_base = smin(terraces, stairs, 0.1);
    if(city_base < res.x) res = vec2(city_base, 2.0); 
    
    // TORREON (Templo del Sol)
    vec3 bp = p; bp.y -= 2.0; bp.z -= 5.0; 
    float slope_factor = 1.0 - clamp(bp.y * 0.1, 0.0, 0.5);
    float torreon = sdCylinder(bp, vec2(4.0 * slope_factor, 3.0));
    
    vec3 wp = bp; wp.y -= 0.5; 
    float angle = atan(wp.x, wp.z);
    float sector = 0.785398;
    angle = mod(angle + sector/2.0, sector) - sector/2.0;
    vec3 win_p = vec3(length(wp.xz) - 4.0, wp.y, angle * length(wp.xz));
    
    float trap_width = 0.5 - win_p.y * 0.1;
    float windows = sdBox(win_p, vec3(0.6, 0.8, trap_width));
    torreon = max(torreon, -windows);
    
    float torreon_in = sdCylinder(bp + vec3(0,0.5,0), vec2(3.5 * slope_factor, 3.0));
    torreon = max(torreon, -torreon_in);
    
    // Habitaciones adyacentes
    vec3 hp = p; hp.y -= 1.0;
    hp.x = abs(hp.x) - 7.0; 
    
    // Repeticion de dominio segura (espaciado ancho, celdas grandes para no violar SDF cerca de bordes)
    hp.z = mod(hp.z + 3.0, 8.0) - 4.0; 
    
    float house_slope = 1.0 - clamp(hp.y * 0.15, 0.0, 0.5);
    float house = sdBox(hp, vec3(2.5 * house_slope, 1.5, 2.0 * house_slope));
    float house_in = sdBox(hp + vec3(0.0, -0.2, 0.0), vec3(2.1 * house_slope, 1.5, 1.6 * house_slope));
    house = max(house, -house_in);
    float door = sdBox(hp - vec3(0.0, -0.5, 2.0), vec3(0.5 - hp.y*0.1, 1.0, 0.5));
    house = max(house, -door);
    
    float limits = sdBox(p - vec3(0.0, 0.0, -8.0), vec3(12.0, 10.0, 18.0));
    house = max(house, limits);
    
    float ruins = min(torreon, house);
    ruins += fbm(p * 3.0) * 0.1; 
    
    if(ruins < res.x) res = vec2(ruins, 3.0); 
    
    res.x = smin(res.x, mountain, 1.5);
    
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

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    
    float camTime = time * 0.2 + pan;
    float ct = mod(camTime, 20.0); 
    
    vec3 ro, target;
    
    if (ct < 10.0) {
        float t_fase = ct / 10.0;
        ro = vec3(sin(t_fase*3.14)*8.0, 5.0 + t_fase*8.0, 15.0 - t_fase*15.0);
        target = vec3(0.0, 5.0 + t_fase*3.0, -5.0);
    } else {
        float t_fase = (ct - 10.0) / 10.0;
        ro = vec3(0.0 + sin(t_fase*6.28)*3.0, 13.0 - t_fase*4.0, 0.0 - t_fase*10.0);
        target = vec3(0.0, 8.0, -15.0);
    }
    
    ro.y += bass * 0.3;
    
    vec3 cw = normalize(target - ro);
    vec3 cu = normalize(cross(cw, vec3(0.0, 1.0, 0.0)));
    vec3 cv = normalize(cross(cu, cw));
    vec3 rd = normalize(p.x*cu + p.y*cv + 1.2*cw);
    
    float t = 0.0; float tMax = 150.0;
    float mat_id = 0.0;
    float volumetric = 0.0; 
    
    vec3 sunDir = normalize(vec3(0.8, 0.3 + sin(time*0.1)*0.1, -0.5));
    
    for(int i = 0; i < 120; i++) {
        vec3 pos = ro + rd * t;
        vec2 res = map(pos);
        if(res.x < 0.01 || t > tMax) {
            mat_id = res.y;
            break;
        }
        
        if (i % 3 == 0) {
             float sha_vol = softshadow(pos, sunDir, 0.05, 10.0, 4.0);
             float fog_density = exp(-pos.y * 0.1) * 0.05;
             volumetric += fog_density * sha_vol * (1.0 + high);
        }
        
        t += res.x * 0.7; 
    }
    
    vec3 skyCol = mix(vec3(0.2, 0.4, 0.6), vec3(0.8, 0.4, 0.2), clamp(1.0 - rd.y*2.0, 0.0, 1.0));
    skyCol = mix(skyCol, colorB, 0.5); 
    
    float sun = clamp(dot(rd, sunDir), 0.0, 1.0);
    skyCol += vec3(1.0, 0.8, 0.5) * pow(sun, 12.0) * (1.0 + bass*0.5);
    
    vec3 col = skyCol;
    
    if(t < tMax) {
        vec3 pos = ro + rd * t;
        vec3 n = getNormal(pos);
        
        float dif = clamp(dot(n, sunDir), 0.0, 1.0);
        float sha = softshadow(pos, sunDir, 0.05, 50.0, 12.0);
        float ao = ambientOcclusion(pos, n);
        float amb = 0.5 + 0.5 * n.y;
        
        vec3 stoneCol = vec3(0.4, 0.4, 0.35); 
        if (mat_id == 1.0) {
            stoneCol = vec3(0.3, 0.35, 0.25); 
        }
        
        stoneCol *= 0.8 + 0.4 * fbm(pos * 5.0); 
        
        float moss_noise = fbm(pos * 8.0);
        float moss_factor = smoothstep(0.4, 0.7, n.y * moss_noise);
        vec3 mossCol = vec3(0.2, 0.5, 0.1) * (0.5 + 0.5 * noise(pos * 20.0));
        mossCol += vec3(0.1, 0.3, 0.0) * high; 
        
        stoneCol = mix(stoneCol, mossCol, moss_factor);
        
        vec3 lin = vec3(1.5, 1.2, 0.9) * dif * sha; 
        lin += vec3(0.3, 0.4, 0.5) * amb * ao; 
        
        col = stoneCol * lin;
        
        float fogHeight = exp(-pos.y * 0.15);
        float fogDist = 1.0 - exp(-0.0015 * t * t);
        vec3 fogCol = mix(skyCol, vec3(0.5, 0.6, 0.7), 0.5);
        col = mix(col, fogCol, fogDist * fogHeight);
    }
    
    col += vec3(1.0, 0.8, 0.5) * volumetric * 0.05;
    
    col = (col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14);
    fragColor = vec4(col, 1.0);
}
'''
"""

if not pattern.search(content):
    print("Error: Could not find INCA_MATH_FS V2 in file. The regex might be wrong.")
else:
    new_content = pattern.sub(NEW_SHADER, content)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Patch V3 applied successfully with SAFE SDF math.")
