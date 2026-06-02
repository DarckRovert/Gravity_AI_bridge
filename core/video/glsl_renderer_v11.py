import os
import sys
import moderngl
import numpy as np
import subprocess

# --- SHADERS GLSL V11 (ANATOMÍA Y SOFT SHADOWS) ---

VERTEX_SHADER = '''
#version 330
in vec2 in_vert;
out vec2 uv;
void main() {
    uv = in_vert * 0.5 + 0.5;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
'''

CHARACTER_LIB = '''
float smin( float a, float b, float k ) {
    float h = clamp( 0.5+0.5*(b-a)/k, 0.0, 1.0 );
    return mix( b, a, h ) - k*h*(1.0-h);
}

float sdCapsule( vec3 p, vec3 a, vec3 b, float r ) {
  vec3 pa = p - a, ba = b - a;
  float h = clamp( dot(pa,ba)/dot(ba,ba), 0.0, 1.0 );
  return length( pa - ba*h ) - r;
}

vec2 sdCharacter(vec3 p, float t, int pose) {
    p *= 1.5; // Escala
    
    float walk_cycle = (pose == 1) ? t * 5.0 : 0.0;
    
    // Cabeza & Cuello
    vec3 headPos = vec3(0.0, 1.6, 0.0);
    vec3 neckBot = vec3(0.0, 1.35, 0.0);
    if(pose == 2) { headPos = vec3(0.0, 0.2, 1.3); neckBot = vec3(0.0, 0.1, 0.9); }
    
    float head = length(p - headPos) - 0.22; 
    float neck = sdCapsule(p, headPos, neckBot, 0.1);
    
    // Torso Heroico 
    vec3 torsoTop = vec3(0.0, 1.3, 0.0);
    vec3 torsoBot = vec3(0.0, 0.6, 0.0);
    if(pose == 2) { torsoTop = vec3(0.0, 0.0, 0.8); torsoBot = vec3(0.0, 0.0, -0.2); }
    
    vec3 chestMid = mix(torsoTop, torsoBot, 0.4);
    float chest = sdCapsule(p, torsoTop, chestMid, 0.35); 
    float abdomen = sdCapsule(p, chestMid, torsoBot, 0.25); 
    
    // Core (Corazón/Reactor)
    vec3 corePos = mix(torsoTop, chestMid, 0.5);
    corePos.z -= (pose == 2) ? -0.3 : 0.35;
    float coreDist = length(p - corePos) - 0.15;
    
    // Piernas 
    vec3 leftHip = torsoBot + vec3(-0.18, 0.0, 0.0);
    vec3 rightHip = vec3(0.18, 0.0, 0.0) + torsoBot;
    
    vec3 leftKnee = leftHip + vec3(0.0, -0.5, sin(walk_cycle)*0.4);
    vec3 rightKnee = rightHip + vec3(0.0, -0.5, -sin(walk_cycle)*0.4);
    vec3 leftFoot = leftKnee + vec3(0.0, -0.55, sin(walk_cycle+0.5)*0.3);
    vec3 rightFoot = rightKnee + vec3(0.0, -0.55, -sin(walk_cycle+0.5)*0.3);
    
    if(pose == 2) { // Volando
        leftKnee = leftHip + vec3(-0.1, -0.1, -0.5); leftFoot = leftKnee + vec3(-0.1, 0.1, -0.5);
        rightKnee = rightHip + vec3(0.1, -0.1, -0.5); rightFoot = rightKnee + vec3(0.1, 0.1, -0.5);
    }
    
    float thighL = sdCapsule(p, leftHip, leftKnee, 0.16); 
    float calfL = sdCapsule(p, leftKnee, leftFoot, 0.11); 
    float thighR = sdCapsule(p, rightHip, rightKnee, 0.16);
    float calfR = sdCapsule(p, rightKnee, rightFoot, 0.11);
    
    // Brazos 
    vec3 leftShoulder = torsoTop + vec3(-0.45, -0.1, 0.0);
    vec3 rightShoulder = torsoTop + vec3(0.45, -0.1, 0.0);
    
    vec3 leftElbow = leftShoulder + vec3(-0.1, -0.4, -sin(walk_cycle)*0.4);
    vec3 rightElbow = rightShoulder + vec3(0.1, -0.4, sin(walk_cycle)*0.4);
    vec3 leftHand = leftElbow + vec3(-0.05, -0.4, -sin(walk_cycle+0.5)*0.4);
    vec3 rightHand = rightElbow + vec3(0.05, -0.4, sin(walk_cycle+0.5)*0.4);
    
    if(pose == 2) { // Superman
        leftElbow = leftShoulder + vec3(-0.2, 0.0, 0.6); leftHand = leftElbow + vec3(-0.1, 0.0, 0.5);
        rightElbow = rightShoulder + vec3(0.2, 0.0, 0.6); rightHand = rightElbow + vec3(0.1, 0.0, 0.5);
    }
    
    float bicepL = sdCapsule(p, leftShoulder, leftElbow, 0.12);
    float forearmL = sdCapsule(p, leftElbow, leftHand, 0.08);
    float bicepR = sdCapsule(p, rightShoulder, rightElbow, 0.12);
    float forearmR = sdCapsule(p, rightElbow, rightHand, 0.08);
    
    // Unión Orgánica
    float body = smin(head, neck, 0.05);
    body = smin(body, chest, 0.15);
    body = smin(body, abdomen, 0.15);
    body = smin(body, smin(thighL, calfL, 0.1), 0.1);
    body = smin(body, smin(thighR, calfR, 0.1), 0.1);
    body = smin(body, smin(bicepL, forearmL, 0.1), 0.1);
    body = smin(body, smin(bicepR, forearmR, 0.1), 0.1);
    
    body /= 1.5;
    coreDist /= 1.5;
    
    if (coreDist < body) return vec2(coreDist, 2.0); // Material 2.0 = Core Brillante
    return vec2(body, 1.0); // Material 1.0 = Armadura
}

vec3 calcCharNormal(vec3 p, float t, int pose) {
    vec2 e = vec2(1.0,-1.0)*0.5773*0.005;
    return normalize( e.xyy*sdCharacter( p + e.xyy, t, pose ).x + 
					  e.yyx*sdCharacter( p + e.yyx, t, pose ).x + 
					  e.yxy*sdCharacter( p + e.yxy, t, pose ).x + 
					  e.xxx*sdCharacter( p + e.xxx, t, pose ).x );
}
'''

# 1. SPACE ODYSSEY V11 (Soft Shadows)
SPACE_ODYSSEY_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, pan;
uniform vec3 colorA, colorB;

''' + CHARACTER_LIB + '''

mat2 rot(float a) { float s = sin(a), c = cos(a); return mat2(c, -s, s, c); }
void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); }
float sdTorus( vec3 p, vec2 t ) { return length(vec2(length(p.xz)-t.x,p.y))-t.y; }

vec3 charOffset = vec3(0.0, 0.0, -3.0);

vec2 map(vec3 p) {
    // Agujero Negro en el Origen 0,0,0
    float sphere = length(p) - 1.0;
    vec3 dp = p;
    pR(dp.xz, time * 0.5); pR(dp.xy, mid * 0.5);
    float disk = sdTorus(dp, vec2(1.8 + bass*0.5, 0.05 + mid*0.1));
    float world = min(sphere, disk);
    
    // Suelo
    float floorDist = p.y + 1.2; 
    world = min(world, floorDist);
    
    // Personaje 
    vec3 cp = p - charOffset; 
    cp.y += 0.2; 
    vec2 charRes = sdCharacter(cp, time, 0);
    
    if(charRes.x < world) return charRes;
    return vec2(world, 0.0);
}

float softshadow( in vec3 ro, in vec3 rd, in float mint, in float tmax, in float k ) {
    float res = 1.0;
    float t = mint;
    for( int i=0; i<24; i++ ) {
        float h = map( ro + rd*t ).x;
        res = min( res, k*h/t );
        t += clamp( h, 0.02, 0.2 );
        if( res<0.005 || t>tmax ) break;
    }
    return clamp( res, 0.0, 1.0 );
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    // CÁMARA OVER THE SHOULDER
    vec3 ro = vec3(-1.0, 1.0, -6.5); 
    pR(ro.xz, pan * 0.5); 
    
    vec3 target = vec3(0.0, 0.0, 0.0);
    vec3 ww = normalize(target - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = normalize(cross(uu, ww));
    vec3 rd = normalize(p.x * uu + p.y * vv + 1.5 * ww);
    
    float t = 0.0; float max_d = 20.0; vec3 col = vec3(0.0); float glow = 0.0;
    float mat_id = 0.0;
    
    for(int i=0; i<64; i++) {
        vec3 pos = ro + rd*t; vec2 res = map(pos);
        if(res.x<0.001 || t>max_d) { mat_id = res.y; break; }
        t += res.x;
        if(res.y == 0.0 && length(pos)>1.2 && pos.y > -1.0) glow += 0.02 / (0.05 + res.x*res.x) * (1.0 + bass*2.0);
    }
    
    vec3 lig = normalize(vec3(0.0, 1.0, 2.0)); // Luz del disco
    
    if(t<max_d) {
        vec3 pos = ro + rd*t;
        if(mat_id == 1.0) { // Armadura
            vec3 nor = calcCharNormal(pos - charOffset + vec3(0.0, 0.2, 0.0), time, 0);
            float dif = clamp(dot(nor, lig), 0.0, 1.0);
            float spe = pow(clamp(dot(reflect(rd, nor), lig), 0.0, 1.0), 16.0);
            col = colorB * 0.2 + (colorB * dif) + spe * colorB * high;
            col += colorB * clamp(1.0 - dot(nor, -rd), 0.0, 1.0) * 0.5; // Contraluz
        } else if(mat_id == 2.0) { // Núcleo
            col = vec3(1.0) + colorA * (1.0 + bass*2.0); // Brillo puro
        } else {
            if(length(pos)<1.01 && pos.y > -1.0) col = vec3(0.0);
            else if(pos.y > -1.0) col = mix(colorA, colorB, length(pos.xz)/3.0);
            else {
                // Suelo con SOMBRA PROYECTADA
                float grid = sin(pos.x*5.0)*sin(pos.z*5.0);
                vec3 floorCol = colorA * 0.1 * smoothstep(0.0, 0.1, grid);
                float sh = softshadow(pos, lig, 0.05, 5.0, 8.0);
                col = floorCol * sh;
            }
        }
    }
    
    float stars = pow(fract(sin(dot(p, vec2(12.9898,78.233))) * 43758.5453), 100.0) * (high * 5.0);
    col += vec3(stars) + mix(colorA, colorB, 0.5)*glow*0.05;
    fragColor = vec4(col, 1.0);
}
'''

# 2. JULIA FRACTAL V11 (Soft Shadows & PBR Completo)
JULIA_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, pan;
uniform vec3 colorA, colorB;

''' + CHARACTER_LIB + '''

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

float forwardTravel() { return time * 3.0; }

vec2 map(vec3 p) {
    vec3 jp = p;
    jp.y -= 1.0; 
    jp.z = mod(jp.z, 8.0) - 4.0;
    float world = juliaSDF(jp, vec4(sin(time*0.5)*0.5, cos(time*0.3)*0.5, mid*0.5, -0.2));
    
    vec3 charPos = vec3(0.0, 0.0, forwardTravel());
    vec3 cp = p - charPos;
    cp.y += 0.5; 
    vec2 charRes = sdCharacter(cp, time*(1.0 + bass*2.0), 1);
    
    if(charRes.x < world) return charRes;
    return vec2(world, 0.0);
}

float softshadow( in vec3 ro, in vec3 rd, in float mint, in float tmax, in float k ) {
    float res = 1.0; float t = mint;
    for( int i=0; i<24; i++ ) {
        float h = map( ro + rd*t ).x;
        res = min( res, k*h/t ); t += clamp( h, 0.02, 0.2 );
        if( res<0.005 || t>tmax ) break;
    }
    return clamp( res, 0.0, 1.0 );
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    float camZ = forwardTravel() - 3.5;
    vec3 ro = vec3(0.0, 0.5, camZ); 
    pR(ro.xz, pan * 0.5); pR(ro.yz, sin(time*0.5)*0.05); 
    
    vec3 ww = normalize(vec3(0.0, 0.0, 1.0));
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = normalize(cross(uu, ww));
    vec3 rd = normalize(p.x * uu + p.y * vv + 1.2 * ww);
    
    float t = 0.0, max_d = 12.0, iter = 0.0;
    float mat_id = 0.0;
    
    for(int i=0; i<64; i++) {
        vec3 pos = ro + rd*t; vec2 res = map(pos);
        if(res.x<0.002 || t>max_d) { mat_id = res.y; break; }
        t += res.x; iter++;
    }
    
    vec3 lig = normalize(vec3(1.0, 1.5, -1.0)); // Sol 
    
    vec3 col = colorA * 0.1;
    if(t<max_d) {
        vec3 pos = ro + rd*t;
        if(mat_id == 1.0) { // Armadura
            vec3 nor = calcCharNormal(pos - vec3(0.0, -0.5, forwardTravel()), time*(1.0 + bass*2.0), 1);
            float dif = clamp(dot(nor, lig), 0.0, 1.0);
            float spe = pow(clamp(dot(reflect(rd, nor), lig), 0.0, 1.0), 16.0);
            float sh = softshadow(pos, lig, 0.05, 3.0, 8.0); // El personaje se ensombrece por el fractal
            col = colorB * (0.2 + dif*0.8*sh) + spe * high * sh;
            col += mix(colorA, colorB, 0.5) * clamp(1.0 - dot(nor, -rd), 0.0, 1.0);
        } else if (mat_id == 2.0) { // Nucleo
            col = vec3(1.0) + colorA * (1.0 + bass*2.0);
        } else { // Fractal
            // Sombras proyectadas del personaje en el fractal
            float sh = softshadow(pos, lig, 0.05, 3.0, 8.0);
            col = mix(colorA, colorB, iter/64.0 * 2.0);
            col *= sh; // Aplicar sombra
            col *= 1.0 - (t/max_d);
            col += high * 0.5 * sh;
        }
    }
    
    fragColor = vec4(col, 1.0);
}
'''

# 3. QUANTUM TUNNEL V11 (Núcleo Emisivo y Armadura Hiper-Reflectante)
QUANTUM_TUNNEL_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, pan;
uniform vec3 colorA, colorB;

''' + CHARACTER_LIB + '''

void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); }
float tunnelSDF(vec3 p) {
    vec2 q = abs(p.xy); float d = max(q.x*0.866025 + q.y*0.5, q.y) - 2.0;
    float rings = abs(fract(p.z*2.0 - time*(10.0 + bass*20.0)) - 0.5) - 0.1; return max(-d, rings);
}
float forwardTravel() { return time*(10.0 + mid*10.0); }

vec2 map(vec3 p) {
    float world = tunnelSDF(p);
    vec3 charPos = vec3(0.0, 0.0, forwardTravel() + 2.5);
    charPos.x += sin(time*4.0)*0.2; charPos.y += cos(time*3.0)*0.2;
    vec3 cp = p - charPos;
    vec2 charRes = sdCharacter(cp, time, 2);
    if(charRes.x < world) return charRes;
    return vec2(world, 0.0);
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    vec3 ro = vec3(0.0, 0.0, forwardTravel()); ro.x += sin(time)*0.3 + pan; 
    vec3 rd = normalize(vec3(p.x, p.y, 1.0)); pR(rd.xy, sin(time)*0.1); 
    
    float t = 0.0, max_d = 30.0, glow = 0.0, char_glow = 0.0; float mat_id = 0.0;
    for(int i=0; i<50; i++) {
        vec3 pos = ro + rd*t; vec2 res = map(pos);
        if(res.y == 0.0) glow += 0.01 / (0.01 + res.x*res.x);
        if(res.x<0.01 || t>max_d) { mat_id = res.y; break; }
        t += res.x;
    }
    
    vec3 col = colorA * 0.1;
    if(t<max_d) {
        vec3 pos = ro + rd*t;
        if(mat_id == 1.0) { // Armadura Cromo
            vec3 charPos = vec3(0.0, 0.0, forwardTravel() + 2.5);
            charPos.x += sin(time*4.0)*0.2; charPos.y += cos(time*3.0)*0.2;
            vec3 nor = calcCharNormal(pos - charPos, time, 2);
            vec3 lig = normalize(vec3(0.0, 1.0, 1.0));
            float dif = clamp(dot(nor, lig), 0.0, 1.0); float spe = pow(clamp(dot(reflect(rd, nor), lig), 0.0, 1.0), 32.0);
            float fresnel = clamp(1.0 - dot(nor, -rd), 0.0, 1.0);
            col = colorB * dif * 0.3 + mix(colorA, colorB, 0.5) * fresnel * 1.5 + spe * vec3(1.0);
        } else if (mat_id == 2.0) { // Núcleo Pecho
            col = vec3(1.0) + mix(colorA, colorB, 0.5) * (1.0 + bass*3.0);
        } else {
            col = mix(colorA, colorB, fract(t*0.1));
        }
    }
    col += mix(colorA, colorB, 0.5) * glow * (0.5 + high);
    fragColor = vec4(col, 1.0);
}
'''

# Motores Auxiliares Intactos (B-Roll)
MANDELBULB_FS = '''
#version 330
out vec4 fragColor; in vec2 uv; uniform vec2 resolution; uniform float time, bass, mid, high, pan; uniform vec3 colorA, colorB;
void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); }
float mandelbulbSDF(vec3 pos) {
    vec3 z = pos; float dr = 1.0; float r = 0.0; float Power = 8.0 + sin(time*0.2)*2.0 + bass*4.0; 
    for (int i=0; i<8; i++) { r = length(z); if (r>2.0) break;
        float theta = acos(z.z/r); float phi = atan(z.y, z.x); dr =  pow( r, Power-1.0)*Power*dr + 1.0;
        float zr = pow( r,Power); theta = theta*Power; phi = phi*Power;
        z = zr*vec3(sin(theta)*cos(phi), sin(phi)*sin(theta), cos(theta)); z+=pos; } return 0.5*log(r)*r/dr; }
vec3 calcNormal(vec3 pos) { vec2 e = vec2(1.0,-1.0)*0.5773*0.001;
    return normalize( e.xyy*mandelbulbSDF( pos + e.xyy ) + e.yyx*mandelbulbSDF( pos + e.yyx ) + e.yxy*mandelbulbSDF( pos + e.yxy ) + e.xxx*mandelbulbSDF( pos + e.xxx ) ); }
void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y; vec3 ro = vec3(0.0, 0.0, -2.5); pR(ro.xz, time * 0.1 + pan); pR(ro.xy, time * 0.05);
    vec3 ww = normalize(-ro); vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0))); vec3 vv = normalize(cross(uu, ww)); vec3 rd = normalize(p.x * uu + p.y * vv + 1.0 * ww);
    float t = 0.0; float max_d = 10.0; float trap = 1.0;
    for(int i=0; i<80; i++) { vec3 pos = ro + rd*t; float d = mandelbulbSDF(pos); trap = min(trap, d); if(d<0.001 || t>max_d) break; t += d; }
    vec3 col = colorA * 0.05; 
    if(t<max_d) { vec3 pos = ro + rd*t; vec3 nor = calcNormal(pos); vec3 lig = normalize(vec3(1.0, 1.0, -1.0)); float dif = clamp(dot(nor, lig), 0.0, 1.0); float spe = pow(clamp(dot(reflect(rd, nor), lig), 0.0, 1.0), 16.0); col = mix(colorA, colorB, length(pos)/1.5); col *= dif + 0.1; col += spe * (0.5 + high * 2.0) * colorB; } else { col += mix(colorA, colorB, 0.5) * exp(-trap*5.0) * bass; }
    fragColor = vec4(col, 1.0);
}
'''
NEBULA_FS = '''
#version 330
out vec4 fragColor; in vec2 uv; uniform vec2 resolution; uniform float time, bass, mid, high, pan; uniform vec3 colorA, colorB;
void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); }
float noise(vec3 p) { vec3 i = floor(p); vec3 f = fract(p); f = f*f*(3.0-2.0*f); vec2 uv = (i.xy+vec2(37.0,17.0)*i.z) + f.xy; vec2 rg = fract(sin((uv+0.5)*0.014)*292.0); return mix(rg.x, rg.y, f.z); }
float mapNebula(vec3 p) { float f = 0.0; vec3 q = p - vec3(0.0, 0.0, time*2.0); f += 0.5000*noise( q ); q = q*2.01; f += 0.2500*noise( q ); q = q*2.02; f += 0.1250*noise( q ); q = q*2.03; f += 0.0625*noise( q ); return f - 0.5; }
void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y; vec3 ro = vec3(0.0, 0.0, 0.0); pR(ro.xy, pan); vec3 rd = normalize(vec3(p.x, p.y, 1.0)); pR(rd.xy, sin(time*0.2)*0.5);
    float t = 0.0; vec4 sum = vec4(0.0);
    for(int i=0; i<50; i++) { vec3 pos = ro + rd*t; float den = mapNebula(pos); if(den > 0.01) { vec3 col = mix(colorA, colorB, clamp(den*2.0, 0.0, 1.0)); col *= mix(1.0, 3.0, bass); col += high * colorB * 0.5; vec4 src = vec4(col * den, den); src.rgb *= src.a; sum = sum + src*(1.0 - sum.a); } if(sum.a > 0.99) break; t += 0.1; }
    fragColor = vec4(sum.rgb, 1.0);
}
'''

POST_PROCESS_FS = '''
#version 330
out vec4 fragColor; in vec2 uv; uniform sampler2D tex1; uniform sampler2D tex2; uniform float transition_t; uniform float bass; uniform float high;
void main() {
    vec2 st = uv;
    if (bass > 0.8) { float shake = (bass - 0.8) * 0.03; st.x += sin(st.y * 100.0) * shake; st.y += cos(st.x * 100.0) * shake; }
    float ab = bass * 0.02;
    vec3 col1 = vec3(texture(tex1, st + vec2(ab, 0.0)).r, texture(tex1, st).g, texture(tex1, st - vec2(ab, 0.0)).b);
    vec3 col2 = vec3(texture(tex2, st + vec2(ab, 0.0)).r, texture(tex2, st).g, texture(tex2, st - vec2(ab, 0.0)).b);
    float luma1 = dot(col1, vec3(0.299, 0.587, 0.114)); vec2 warp_st = st + (luma1 * 0.1 * transition_t); vec3 warped_col2 = texture(tex2, warp_st).rgb;
    vec3 final_col = mix(col1, mix(col2, warped_col2, transition_t), transition_t);
    vec3 bloom = max(vec3(0.0), final_col - 0.6) * high * 1.5; final_col += bloom;
    fragColor = vec4(final_col, 1.0);
}
'''

def render_v11_video(timeline: list, multiband: dict, colorsA: np.ndarray, colorsB: np.ndarray, w: int, h: int, fps: int, out_mp4: str, audio_path: str):
    ctx = moderngl.create_context(standalone=True)
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
    
    tex_geom1 = ctx.texture((w, h), components=3)
    fbo_geom1 = ctx.framebuffer(color_attachments=[tex_geom1])
    tex_geom2 = ctx.texture((w, h), components=3)
    fbo_geom2 = ctx.framebuffer(color_attachments=[tex_geom2])
    fbo_final = ctx.framebuffer(color_attachments=[ctx.texture((w, h), components=3)])
    
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ffmpeg_exe = os.path.join(_base, "_integrations", "ffmpeg", "ffmpeg.exe")
    if not os.path.isfile(ffmpeg_exe): ffmpeg_exe = "ffmpeg"
        
    # V11: Flip (-vf vflip) arregla el mundo invertido
    cmd = [
        ffmpeg_exe, "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{w}x{h}", "-pix_fmt", "rgb24", "-r", str(fps), "-i", "-"
    ]
    if audio_path and os.path.isfile(audio_path):
        cmd.extend(["-i", audio_path, "-vf", "vflip", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23", "-c:a", "aac", "-b:a", "192k", "-shortest"])
    else:
        cmd.extend(["-vf", "vflip", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23"])
    cmd.append(out_mp4)
    
    print(f"\n[🚀 Motor V11] INICIANDO OBRA MAESTRA (ANATOMÍA Y SOFT SHADOWS)...")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    total_frames = len(multiband['bass'])
    
    try:
        for frame_idx in range(total_frames):
            engine_1 = "space_odyssey"
            engine_2 = None
            transition_t = 0.0
            
            for scene in timeline:
                if scene["start"] <= frame_idx <= scene["end"]:
                    engine_1 = scene["engine"]
                    if "transition_start" in scene and frame_idx >= scene["transition_start"]:
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

            render_pass(engine_1, fbo_geom1)
            if engine_2 is not None: render_pass(engine_2, fbo_geom2)
            
            fbo_final.use()
            ctx.clear(0.0, 0.0, 0.0)
            tex_geom1.use(location=0)
            if 'tex1' in prog_post: prog_post['tex1'].value = 0
            if engine_2 is not None:
                tex_geom2.use(location=1)
                if 'tex2' in prog_post: prog_post['tex2'].value = 1
            else:
                tex_geom1.use(location=1) 
                if 'tex2' in prog_post: prog_post['tex2'].value = 1
                
            if 'transition_t' in prog_post: prog_post['transition_t'].value = transition_t
            if 'bass' in prog_post: prog_post['bass'].value = b
            if 'high' in prog_post: prog_post['high'].value = hg
            
            vao_post.render(moderngl.TRIANGLE_STRIP)
            img_bytes = fbo_final.read(components=3)
            proc.stdin.write(img_bytes)
            
            if frame_idx % (fps*2) == 0:
                print(f"  Frame {frame_idx}/{total_frames} ({(frame_idx/total_frames)*100:.1f}%) [Actor in: {engine_1}]", file=sys.stderr)
        
        proc.stdin.close()
        proc.wait()
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error renderizando video V11 GPU: {e}", file=sys.stderr)
    finally:
        if 'proc' in locals() and proc.poll() is None:
            try: proc.stdin.close()
            except Exception: pass
            proc.terminate()
            proc.wait()
            
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
    
    print(f"[✅ Motor V11] OBRA MAESTRA RENDERIZADA EN: {out_mp4}", file=sys.stderr)
    return out_mp4
