import os
import re

filepath = r"f:\Gravity_AI_bridge\core\video\glsl_renderer_v13.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

pattern = re.compile(r"INCA_MATH_FS\s*=\s*'''#version 330.*?'''", re.DOTALL)

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

float map(vec3 p) {
    // 1. TERRENO BASE Y HUAYNA PICCHU
    float terrain = p.y + 3.0; 
    
    vec3 mp = p; mp.z -= 40.0; 
    float mountain = mp.y + 5.0 - 25.0 * exp(-0.01 * (mp.x*mp.x + mp.z*mp.z));
    mountain -= fbm(mp * 0.1) * 10.0; 
    
    // 2. ANDENES (Terrazas agricolas escalonadas)
    vec3 tp = p;
    float slope = tp.y + tp.z * 0.2; 
    float step_height = 0.8;
    float terrace_slope = floor(slope / step_height) * step_height;
    
    float terrace_hill = sdBox(tp - vec3(0.0, terrace_slope, 0.0), vec3(15.0, step_height * 0.5, 15.0));
    float ground = smin(terrain, mountain, 5.0);
    ground = smin(ground, terrace_hill, 2.0);
    
    // 3. TORREON (Templo del Sol) - Cilíndrico e inclinado
    vec3 bp = p; bp.y -= 2.0; 
    float slope_factor = 1.0 - clamp(bp.y * 0.1, 0.0, 0.5); // Antisismic inca wall slope
    float torreon = sdCylinder(bp, vec2(3.0 * slope_factor, 2.0));
    
    // Ventanas Trapezoidales
    vec3 wp = bp; wp.y -= 0.5; 
    float angle = atan(wp.x, wp.z);
    float sector = 0.785398; // 45 grados de separación
    angle = mod(angle + sector/2.0, sector) - sector/2.0;
    float radius = length(wp.xz);
    vec3 win_p = vec3(radius - 3.0, wp.y, angle * radius);
    
    float trap_width = 0.4 - win_p.y * 0.1;
    float windows = sdBox(win_p, vec3(0.5, 0.6, trap_width));
    torreon = max(torreon, -windows); // Operacion booleana de sustracción
    
    // 4. RUINAS Y CASAS INCAICAS
    vec3 hp = p; hp.y -= 0.0;
    hp.x = abs(hp.x) - 6.0; 
    hp.z = mod(hp.z + 2.0, 4.0) - 2.0; 
    
    float house_slope = 1.0 - clamp(hp.y * 0.15, 0.0, 0.5);
    float house = sdBox(hp, vec3(1.5 * house_slope, 1.2, 1.5 * house_slope));
    
    // Vaciado de la casa
    float house_in = sdBox(hp + vec3(0.0, -0.2, 0.0), vec3(1.2 * house_slope, 1.2, 1.2 * house_slope));
    house = max(house, -house_in);
    
    // Puerta trapezoidal
    float door = sdBox(hp - vec3(0.0, -0.5, 1.5), vec3(0.4 - hp.y*0.1, 0.8, 0.5));
    house = max(house, -door);
    
    // Limitar casas al area central
    float limits = sdBox(p - vec3(0.0, 0.0, -5.0), vec3(10.0, 10.0, 15.0));
    house = max(house, limits);
    
    float ruins = min(torreon, house);
    
    // 5. WEATHERING & DESTRUCTION (Desgaste natural de los siglos)
    float wear = fbm(p * 2.0) * 0.15;
    ruins += wear;
    
    float scene = smin(ground, ruins, 0.2);
    return scene;
}

vec3 getNormal(vec3 p) {
    vec2 e = vec2(0.01, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

float softshadow( in vec3 ro, in vec3 rd, in float mint, in float tmax, in float k ) {
    float res = 1.0; float t = mint;
    for( int i=0; i<32; i++ ) {
        float h = map( ro + rd*t );
        res = min( res, k*h/t );
        t += clamp( h, 0.02, 0.20 );
        if( res<0.005 || t>tmax ) break;
    }
    return clamp( res, 0.0, 1.0 );
}

float ambientOcclusion(vec3 p, vec3 n) {
    float occ = 0.0; float sca = 1.0;
    for(int i = 0; i < 5; i++) {
        float h = 0.01 + 0.12 * float(i)/4.0;
        float d = map(p + h * n);
        occ += (h - d) * sca;
        sca *= 0.95;
    }
    return clamp(1.0 - 1.5 * occ, 0.0, 1.0);
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    
    // Cinematic camera orbital
    float angle = time * 0.1 + pan;
    float radius = 15.0 + sin(time*0.2)*2.0;
    vec3 ro = vec3(sin(angle)*radius, 10.0 + sin(time*0.3)*2.5 + bass*1.0, cos(angle)*radius - 5.0);
    vec3 target = vec3(0.0, 2.0, -5.0);
    
    vec3 cw = normalize(target - ro);
    vec3 cu = normalize(cross(cw, vec3(0.0, 1.0, 0.0)));
    vec3 cv = normalize(cross(cu, cw));
    vec3 rd = normalize(p.x*cu + p.y*cv + 1.2*cw);
    
    float t = 0.0; float tMax = 150.0;
    for(int i = 0; i < 120; i++) {
        vec3 pos = ro + rd * t;
        float h = map(pos);
        if(h < 0.01 || t > tMax) break;
        t += h * 0.7; // Reducido para mayor precision del ruido
    }
    
    vec3 skyCol = mix(colorA, vec3(0.9, 0.6, 0.3), clamp(rd.y, 0.0, 1.0));
    skyCol = mix(skyCol, colorB, clamp(-rd.y, 0.0, 1.0));
    
    vec3 sunDir = normalize(vec3(0.8, 0.4, 0.5));
    float sun = clamp(dot(rd, sunDir), 0.0, 1.0);
    skyCol += vec3(1.0, 0.9, 0.6) * pow(sun, 12.0) * (1.0 + high);
    
    vec3 col = skyCol;
    
    if(t < tMax) {
        vec3 pos = ro + rd * t;
        vec3 n = getNormal(pos);
        
        float dif = clamp(dot(n, sunDir), 0.0, 1.0);
        float sha = softshadow(pos, sunDir, 0.05, 50.0, 12.0);
        float ao = ambientOcclusion(pos, n);
        float amb = 0.5 + 0.5 * n.y;
        
        float height_factor = clamp((pos.y + 3.0) * 0.1, 0.0, 1.0);
        vec3 stoneCol = mix(vec3(0.2, 0.3, 0.25), vec3(0.45, 0.4, 0.35), height_factor); 
        stoneCol *= 0.8 + 0.4 * fbm(pos * 5.0);
        
        float energy = fbm(pos * 2.0 - time) * bass;
        stoneCol += smoothstep(0.6, 1.0, energy) * colorA * 2.0; 
        
        vec3 lin = vec3(1.5, 1.2, 0.9) * dif * sha; 
        lin += vec3(0.2, 0.3, 0.4) * amb * ao; 
        
        col = stoneCol * lin;
        
        float fogHeight = exp(-pos.y * 0.2);
        float fogDist = 1.0 - exp(-0.002 * t * t);
        vec3 fogCol = mix(skyCol, colorB, 0.5) + bass * 0.2 * colorA;
        col = mix(col, fogCol, fogDist * fogHeight);
    }
    
    col = (col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14);
    fragColor = vec4(col, 1.0);
}
'''"""

new_content = pattern.sub(NEW_SHADER, content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Patch applied successfully.")
