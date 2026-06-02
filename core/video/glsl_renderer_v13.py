import os
import sys
import moderngl
import numpy as np
import subprocess

# --- SHADERS GLSL V13 (BIOMECÁNICA Y VIDA) ---

VERTEX_SHADER = '''
#version 330
in vec2 in_vert;
out vec2 uv;
void main() {
    uv = in_vert * 0.5 + 0.5;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
'''

COSMOS_LIB = '''
float smin( float a, float b, float k ) {
    float h = clamp( 0.5+0.5*(b-a)/k, 0.0, 1.0 );
    return mix( b, a, h ) - k*h*(1.0-h);
}

mat2 rot(float a) { float s = sin(a), c = cos(a); return mat2(c, -s, s, c); }

float hash3D(vec3 p) {
    p = fract(p * vec3(127.1, 311.7, 74.7));
    p += dot(p, p + 19.19);
    return fract(p.x * p.y * p.z);
}

float cosmicNoise(vec3 p, float scale) {
    vec3 i = floor(p * scale);
    vec3 f = fract(p * scale);
    f = f * f * (3.0 - 2.0 * f);
    return mix(
        mix(mix(hash3D(i), hash3D(i+vec3(1,0,0)), f.x),
            mix(hash3D(i+vec3(0,1,0)), hash3D(i+vec3(1,1,0)), f.x), f.y),
        mix(mix(hash3D(i+vec3(0,0,1)), hash3D(i+vec3(1,0,1)), f.x),
            mix(hash3D(i+vec3(0,1,1)), hash3D(i+vec3(1,1,1)), f.x), f.y), f.z
    ) * 2.0 - 1.0;
}

float sdTorus( vec3 p, vec2 t ) { return length(vec2(length(p.xz)-t.x,p.y))-t.y; }

// --- ESTRUCTURAS CÓSMICAS ---

// 1. Agujero Negro con Lente Gravitacional (Gargantúa)
vec2 sdBlackHole(vec3 p, float t, float bass) {
    float eventHorizon = length(p) - 1.2; // Esfera negra central
    
    // Disco de acreción
    vec3 dp = p;
    dp.yz *= rot(0.2); // Inclinación
    float disk = sdTorus(dp, vec2(3.0 + bass*0.5, 0.05 + bass*0.1));
    float diskNoise = cosmicNoise(dp*2.0 - vec3(0,t*5.0,0), 3.0) * 0.1;
    disk += diskNoise;
    
    if (disk < eventHorizon) return vec2(disk, 4.0); // Material 4: Plasma supercaliente
    return vec2(eventHorizon, 5.0); // Material 5: Vacío absoluto
}

// 2. Planeta Vivo / Supernova
vec2 sdPlanet(vec3 p, float t, float bass) {
    float noise = cosmicNoise(p*1.5 + vec3(t*0.2, 0, t*0.1), 2.0) * 0.4;
    noise += cosmicNoise(p*4.0 - vec3(0, t*0.5, 0), 4.0) * (0.1 + bass*0.2); // Erupciones reactivas
    
    float planet = length(p) - (2.5 + noise);
    
    // Anillos planetarios
    vec3 rp = p; rp.xy *= rot(t*0.2); rp.xz *= rot(0.3);
    float ring = sdTorus(rp, vec2(4.5 + bass*0.5, 0.02));
    
    if (ring < planet) return vec2(ring, 3.0); // Anillos de energía
    return vec2(planet, 6.0); // Magma/Tierra
}

// 3. Megaestructura / StarGate
vec2 sdMegastructure(vec3 p, float t, float bass) {
    vec3 p1 = p; p1.xz *= rot(t * 0.5); p1.yz *= rot(t * 0.3);
    vec3 p2 = p; p2.xz *= rot(-t * 0.7); p2.xy *= rot(t * 0.4);
    vec3 p3 = p; p3.xy *= rot(t * 0.2); p3.yz *= rot(-t * 0.6);
    
    float pulse = sin(t*10.0)*bass*0.2;
    
    float ring1 = sdTorus(p1, vec2(3.0, 0.2 + pulse));
    float ring2 = sdTorus(p2, vec2(2.5, 0.15 + pulse*0.8));
    float ring3 = sdTorus(p3, vec2(2.0, 0.1 + pulse*0.5));
    
    float core = length(p) - (0.5 + bass*1.0); // Núcleo cuántico
    
    float rings = smin(smin(ring1, ring2, 0.2), ring3, 0.2);
    if (core < rings) return vec2(core, 3.0); // Energía
    return vec2(rings, 7.0); // Metal alienígena
}

// Multiplexor de objetos cósmicos basado en `pose` (usaremos pose como tipo de objeto mod 3)
vec2 sdCosmos(vec3 p, float t, float bass, int obj_type) {
    int oType = obj_type % 3;
    if (oType == 1) return sdBlackHole(p, t, bass);
    if (oType == 2) return sdPlanet(p, t, bass);
    return sdMegastructure(p, t, bass);
}

vec3 calcCosmosNormal(vec3 p, float t, float bass, int obj_type) {
    vec2 e = vec2(1.0,-1.0)*0.5773*0.005;
    return normalize( e.xyy*sdCosmos( p + e.xyy, t, bass, obj_type ).x + 
                      e.yyx*sdCosmos( p + e.yyx, t, bass, obj_type ).x + 
                      e.yxy*sdCosmos( p + e.yxy, t, bass, obj_type ).x + 
                      e.xxx*sdCosmos( p + e.xxx, t, bass, obj_type ).x );
}

#define PI 3.14159265359
vec2 envMapEquirect(vec3 dir) {
    float phi = atan(dir.z, dir.x);
    float theta = asin(clamp(dir.y, -1.0, 1.0));
    return vec2(phi / (2.0 * PI) + 0.5, theta / PI + 0.5);
}

// Polvo estelar volumétrico rápido
float starDust(vec3 p) {
    vec3 q = fract(p * 2.0) - 0.5;
    return length(q) - 0.02;
}
'''


# 1. SPACE ODYSSEY V13
SPACE_ODYSSEY_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, pan;
uniform vec3 colorA, colorB; uniform int pose;
uniform sampler2D iChannel0;

''' + COSMOS_LIB + '''

void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); }

vec3 cosmosOffset = vec3(0.0, 0.0, -5.0);

vec2 map(vec3 p) {
    float sphere = length(p) - 1.0;
    vec3 dp = p;
    pR(dp.xz, time * 0.5); pR(dp.xy, mid * 0.5);
    float disk = sdTorus(dp, vec2(1.8 + bass*0.5, 0.05 + mid*0.1));
    float world = min(sphere, disk);
    
    float floorDist = p.y + 1.2; 
    world = min(world, floorDist);
    
    vec3 cp = p - cosmosOffset; 
    // Escalar hacia abajo ligeramente si es muy masivo
    cp *= 0.5;
    vec2 cosmicRes = sdCosmos(cp, time, bass, pose);
    cosmicRes.x *= 2.0; // Deshacer la escala en la distancia
    
    if(cosmicRes.x < world) {
        return cosmicRes;
    }
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
    
    // Cinematografía Bézier 6DOF (Trayectoria orbital)
    float camT = time * 0.2 + pan;
    vec3 ro = vec3(sin(camT)*8.0, sin(camT*0.5)*2.0 + 1.0, cos(camT)*8.0 - 5.0); 
    vec3 target = vec3(0.0, 0.0, -5.0); // Mirar al centro del Cosmos
    
    // Temblor de cámara con bass extremo
    ro += vec3(sin(time*50.0), cos(time*45.0), sin(time*55.0)) * bass * 0.05;
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
        
        // Polvo Estelar acumulativo (gravedad hacia el centro interactiva)
        vec3 dustPos = pos;
        dustPos -= normalize(target - dustPos) * time * (1.0 + bass*5.0); // Atracción al centro
        float dDust = starDust(dustPos);
        if(dDust < 0.1) glow += 0.005 / (0.01 + dDust*dDust) * (1.0 + bass*2.0);
    }
    
    vec3 lig = normalize(vec3(0.0, 1.0, 2.0)); 
    
    if(t<max_d) {
        vec3 pos = ro + rd*t;
        if(mat_id == 1.0 || mat_id >= 4.0) { 
            // Cosmos: Material SSS + Fresnel + IBL
            vec3 cp = pos - cosmosOffset;
            cp *= 0.5;
            vec3 nor = calcCosmosNormal(cp, time, bass, pose);
            float dif = clamp(dot(nor, lig), 0.0, 1.0);
            float spe = pow(clamp(dot(reflect(rd, nor), lig), 0.0, 1.0), 32.0);
            
            // IBL PBR
            vec3 refDir = reflect(rd, nor);
            vec3 envColor = texture(iChannel0, envMapEquirect(refDir)).rgb;
            
            // Fresnel Cinematográfico
            float fresnel = pow(1.0 - max(dot(nor, -rd), 0.0), 3.0);
            float sss = smoothstep(0.0, 1.0, map(pos + lig * 0.2).x) * 0.5;
            
            col = colorB * 0.15 + (colorB * dif) + spe * vec3(1.0) * high;
            col += envColor * fresnel * 2.0; // Reflejo Real-time del arte de IA
            col += colorA * sss;
            
            // Emisión de materiales cósmicos (Plasma/Energía)
            if (mat_id >= 4.0) col += envColor * 0.5 * (1.0 + bass*2.0); 
        } else if(mat_id == 2.0) { 
            col = vec3(1.0) + colorA * (1.0 + bass*4.0);
        } else if(mat_id == 3.0) {
            // Campo de Plasma: superficie emite luz propia con ruido de movimiento
            vec3 plasmaCol = mix(colorA, colorB, 0.5 + 0.5 * sin(time * 3.0 + pos.x * 5.0));
            float pulse = 0.5 + 0.5 * sin(time * 8.0 + length(pos) * 10.0);
            col = plasmaCol * (1.5 + bass * 2.0) * (0.6 + pulse * 0.4);
            col += vec3(1.0) * high * 0.5; // Destello blanco en altos
        } else {
            if(length(pos)<1.01 && pos.y > -1.0) col = vec3(0.0);
            else if(pos.y > -1.0) col = mix(colorA, colorB, length(pos.xz)/3.0);
            else {
                float grid = sin(pos.x*5.0)*sin(pos.z*5.0);
                vec3 floorCol = colorA * 0.1 * smoothstep(0.0, 0.1, grid);
                float sh = softshadow(pos, lig, 0.05, 5.0, 8.0);
                col = floorCol * sh;
            }
        }
    }
    
    // Exponential Distance Fog
    float fogDensity = 0.08;
    float fogFactor = 1.0 - exp(-pow(t * fogDensity, 2.0));
    vec3 bgCol = mix(colorA, vec3(0.0), 0.5); // Color de la niebla en el fondo
    
    float stars = pow(fract(sin(dot(p, vec2(12.9898,78.233))) * 43758.5453), 100.0) * (high * 3.0);
    vec3 final_bg = bgCol + vec3(stars) + mix(colorA, colorB, 0.5)*glow*0.05;
    
    // Mezcla de la geometría con el fondo según la distancia
    col = mix(col, final_bg, fogFactor);
    
    // Lens Flares Anamórficos (JJ Abrams Style)
    // Se dibujan horizontales si la luz o el núcleo son "eclipsados"
    float lfPos = dot(lig, rd);
    if(lfPos > 0.0) {
        float flare = pow(lfPos, 20.0) * 1.5;
        flare += pow(lfPos, 200.0) * 2.0;
        
        // Aberración horizontal anamórfica
        float anamorphic = exp(-pow(abs(p.y), 2.0) * 50.0) * exp(-pow(abs(p.x), 2.0) * 0.5);
        vec3 flareCol = mix(colorA, vec3(1.0), 0.5) * flare * anamorphic * (1.0 + high*3.0);
        
        // Occlusion testing for flare (si hay geometría en frente, atenuar)
        if(t < max_d) flareCol *= 0.1; 
        col += flareCol;
    }
    
    fragColor = vec4(col, 1.0);
}
'''

# 2. JULIA FRACTAL V13
JULIA_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, pan;
uniform vec3 colorA, colorB; uniform int pose;
uniform sampler2D iChannel0;

''' + COSMOS_LIB + '''

// Julia con Orbit Trap: retorna (sdf, orbit_trap_min)
vec2 juliaSDF_OT(vec3 p, vec4 c) {
    vec4 z = vec4(p, 0.0); float md2 = 1.0, mz2 = dot(z, z);
    float trap = 1e10; // Orbit Trap: distancia mínima al origen durante la orbita
    for(int i=0; i<14; i++) {       // 14 iteraciones (era 8)
        md2 *= 4.0 * mz2;
        vec4 nz; nz.x = z.x*z.x - dot(z.yzw, z.yzw); nz.yzw = 2.0 * z.x * z.yzw;
        z = nz + c; mz2 = dot(z, z);
        trap = min(trap, length(z.xy));    // Trampa: plano XY (crea patrones de anillos)
        trap = min(trap, abs(z.x) + abs(z.y)); // Trampa cruzada
        if(mz2 > 4.0) break;
    }
    float sdf = 0.25 * log(mz2) * sqrt(mz2 / md2);
    return vec2(sdf, clamp(trap * 0.5, 0.0, 1.0));
}
void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); }

float forwardTravel() { return time * 3.0; }

// orbit_trap almacenado globalmente para uso en iluminación
float g_orbit_trap = 0.0;

vec2 map(vec3 p) {
    vec3 jp = p;
    jp.y -= 1.0; 
    jp.z = mod(jp.z, 8.0) - 4.0;
    vec2 juliaResult = juliaSDF_OT(jp, vec4(sin(time*0.5)*0.5, cos(time*0.3)*0.5, mid*0.5, -0.2));
    float world = juliaResult.x;
    g_orbit_trap = juliaResult.y;   // Guardamos el trap para colorear
    
    vec3 cosmosPos = vec3(0.0, 0.0, forwardTravel() + 2.0);
    vec3 cp = p - cosmosPos;
    cp *= 0.5; // Escalar
    vec2 cosmicRes = sdCosmos(cp, time*(1.0 + bass*2.0), bass, pose);
    cosmicRes.x *= 2.0;
    
    if(cosmicRes.x < world) {
        return cosmicRes;
    }
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
    
    vec3 lig = normalize(vec3(1.0, 1.5, -1.0)); 
    
    vec3 col = colorA * 0.1;
    if(t<max_d) {
        vec3 pos = ro + rd*t;
        if(mat_id == 1.0) { 
            // Cosmos: SSS y Fresnel intensificado
            vec3 nor = calcCosmosNormal((pos - vec3(0.0, 0.0, forwardTravel() + 2.0)) * 0.5, time*(1.0 + bass*2.0), bass, pose);
            float dif = clamp(dot(nor, lig), 0.0, 1.0);
            float spe = pow(clamp(dot(reflect(rd, nor), lig), 0.0, 1.0), 32.0);
            float sh = softshadow(pos, lig, 0.05, 3.0, 8.0); 
            // IBL en Fractal + Cosmos
            vec3 refDir = reflect(rd, nor);
            vec3 envColor = texture(iChannel0, envMapEquirect(refDir)).rgb;
            float fresnel = pow(1.0 - max(dot(nor, -rd), 0.0), 2.5);
            float sss = smoothstep(0.0, 1.0, map(pos + lig * 0.2).x) * 0.5;
            
            col = colorB * (0.15 + dif*0.8*sh) + spe * high * sh * vec3(1.0);
            col += envColor * fresnel * 2.0; // Rim light PBR
            col += colorA * sss;
        } else if (mat_id == 2.0) { 
            col = vec3(1.0) + colorA * (1.0 + bass*4.0); // Emisivo fuerte
        } else if (mat_id == 3.0) {
            // Campo de Plasma en Julia
            vec3 plasmaCol = mix(colorA, colorB, 0.5 + 0.5 * sin(time * 3.0 + pos.x * 5.0));
            float pulse = 0.5 + 0.5 * sin(time * 8.0 + length(pos) * 10.0);
            col = plasmaCol * (1.5 + bass * 2.0) * (0.6 + pulse * 0.4);
            col += vec3(1.0) * high * 0.5;
        } else { 
            // Fractal: Iluminación mejorada con Orbit Traps y Volumetric SSS
            float sh = softshadow(pos, lig, 0.05, 3.0, 8.0);
            // Orbit Trap coloring: el color base depende de cuán cerca pasó del origen
            vec3 baseCol = mix(colorA, colorB, g_orbit_trap);
            // Patrones espirales/venas adicionales usando el trap
            float veins = smoothstep(0.1, 0.2, fract(g_orbit_trap * 10.0 + time));
            vec3 diffuse = mix(baseCol, vec3(1.0), veins * 0.3 * high);
            
            float ao = clamp(1.0 - iter/64.0, 0.0, 1.0); // Simple AO based on iterations
            
            col = diffuse * sh * ao;
            col += high * 0.5 * sh * g_orbit_trap; // Specular trap-based
        }
    }
    
    // Exponential Distance Fog
    float fogDensity = 0.15;
    float fogFactor = 1.0 - exp(-pow(t * fogDensity, 2.0));
    vec3 bgCol = mix(colorA * 0.2, vec3(0.0), 0.7); 
    
    // Ambient glow from iterations
    vec3 glowCol = colorA * (iter / 64.0) * bass * 0.3;
    
    col = mix(col, bgCol + glowCol, fogFactor);
    
    fragColor = vec4(col, 1.0);
}
'''

# 3. QUANTUM TUNNEL V13
QUANTUM_TUNNEL_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, pan;
uniform vec3 colorA, colorB; uniform int pose;
uniform sampler2D iChannel0;

''' + COSMOS_LIB + '''

void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); }
float tunnelSDF(vec3 p) {
    vec2 q = abs(p.xy); float d = max(q.x*0.866025 + q.y*0.5, q.y) - 2.0;
    float rings = abs(fract(p.z*2.0 - time*(10.0 + bass*20.0)) - 0.5) - 0.1; return max(-d, rings);
}
float forwardTravel() { return time*(10.0 + mid*10.0); }

vec2 map(vec3 p) {
    float world = tunnelSDF(p);
    vec3 cosmosPos = vec3(0.0, 0.0, forwardTravel() + 4.5);
    cosmosPos.x += sin(time*4.0)*0.2; cosmosPos.y += cos(time*3.0)*0.2;
    vec3 cp = p - cosmosPos;
    cp *= 0.5;
    vec2 cosmicRes = sdCosmos(cp, time, bass, pose);
    cosmicRes.x *= 2.0;
    if(cosmicRes.x < world) return cosmicRes;
    return vec2(world, 0.0);
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    vec3 ro = vec3(0.0, 0.0, forwardTravel()); ro.x += sin(time)*0.3 + pan; 
    vec3 rd = normalize(vec3(p.x, p.y, 1.0)); pR(rd.xy, sin(time)*0.1); 
    
    float t = 0.0, max_d = 30.0, glow = 0.0; float mat_id = 0.0;
    for(int i=0; i<50; i++) {
        vec3 pos = ro + rd*t; vec2 res = map(pos);
        if(res.y == 0.0) glow += 0.01 / (0.01 + res.x*res.x);
        if(res.x<0.01 || t>max_d) { mat_id = res.y; break; }
        t += res.x;
    }
    
    vec3 col = colorA * 0.1;
    if(t<max_d) {
        vec3 pos = ro + rd*t;
        if(mat_id == 1.0 || mat_id >= 4.0) { 
            vec3 cosmosPos = vec3(0.0, 0.0, forwardTravel() + 4.5);
            cosmosPos.x += sin(time*4.0)*0.2; cosmosPos.y += cos(time*3.0)*0.2;
            vec3 nor = calcCosmosNormal((pos - cosmosPos) * 0.5, time, bass, pose);
            vec3 lig = normalize(vec3(0.0, 1.0, 1.0));
            float dif = clamp(dot(nor, lig), 0.0, 1.0); 
            float spe = pow(clamp(dot(reflect(rd, nor), lig), 0.0, 1.0), 32.0);
            // IBL Quantum
            vec3 refDir = reflect(rd, nor);
            vec3 envColor = texture(iChannel0, envMapEquirect(refDir)).rgb;
            float fresnel = pow(1.0 - max(dot(nor, -rd), 0.0), 3.0);
            float sss = smoothstep(0.0, 1.0, tunnelSDF(pos + lig * 0.3)) * 0.4;
            col = colorB * dif * 0.3 + spe * vec3(1.0);
            col += envColor * fresnel * 2.5; // PBR Reflection
            col += colorA * sss;
        } else if (mat_id == 2.0) { 
            col = vec3(1.0) + mix(colorA, colorB, 0.5) * (1.0 + bass*4.0);
        } else {
            // Túnel: bandas de color reactivas a la energía del mid
            float band = fract(t * 0.1 + time * 0.05);
            col = mix(colorA, colorB, band);
            col *= 0.8 + mid * 0.5;
        }
    }
    
    // Exponential Tunnel Fog
    float fogDensity = 0.07;
    float fogFactor = 1.0 - exp(-pow(t * fogDensity, 2.0));
    vec3 bgCol = mix(colorA * 0.15, vec3(0.0), 0.6);
    col = mix(col, bgCol, fogFactor);
    
    // Glow de los anillos reactivo al high
    col += mix(colorA, colorB, 0.5) * glow * (0.4 + high * 1.5);
    fragColor = vec4(col, 1.0);
}
'''

# POST PROCESS FS (Cinematic Overhaul)
POST_PROCESS_FS = '''
#version 330
out vec4 fragColor; in vec2 uv; uniform sampler2D tex1; uniform sampler2D tex2; uniform float transition_t; uniform float bass; uniform float high; uniform float time;

// ACES Tone Mapping
vec3 ACESFilm(vec3 x) {
    float a = 2.51; float b = 0.03; float c = 2.43; float d = 0.59; float e = 0.14;
    return clamp((x*(a*x+b))/(x*(c*x+d)+e), 0.0, 1.0);
}

// Pseudo Random for film grain
float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

void main() {
    vec2 st = uv;
    
    // ── Camera shake & Cyber Glitch en beat drops ────────────────────────────
    if (bass > 0.85) {
        float shake = (bass - 0.85) * 0.025;
        vec2 shakeUV = st + vec2(sin(time * 50.0) * shake, cos(time * 47.0) * shake);
        
        // Digital Glitch (Desplazamiento horizontal de scanlines)
        float glitchLine = step(0.9, fract(st.y * 20.0 + time * 15.0));
        float glitchShift = (bass - 0.85) * 0.15 * glitchLine * sin(time * 120.0);
        shakeUV.x += glitchShift;
        
        // Radial Chromatic Aberration impulsada por bass en el shake/glitch
        vec2 dir = shakeUV - 0.5;
        float ab = bass * 0.04 * length(dir);
        
        st = shakeUV; // Apply to base st for later use
    }
    
    // Radial Chromatic Aberration normal + base glitch
    vec2 dir = st - 0.5;
    float dist = length(dir);
    float ab = bass * 0.04 * dist; // La separación RGB aumenta en los bordes
    
    vec3 col1 = vec3(texture(tex1, clamp(st + dir * ab, 0.0, 1.0)).r, texture(tex1, clamp(st, 0.0, 1.0)).g, texture(tex1, clamp(st - dir * ab, 0.0, 1.0)).b);
    vec3 col2 = vec3(texture(tex2, clamp(st + dir * ab, 0.0, 1.0)).r, texture(tex2, clamp(st, 0.0, 1.0)).g, texture(tex2, clamp(st - dir * ab, 0.0, 1.0)).b);
    
    // Invertir colores esporádicamente si hay glitch intenso
    float glitchLine2 = step(0.9, fract(st.y * 20.0 + time * 15.0));
    if (bass > 0.85 && fract(time * 42.0) > 0.85 && glitchLine2 > 0.0) {
        col1.rgb = 1.0 - col1.rgb;
        col2.rgb = 1.0 - col2.rgb;
    }

    
    // Warp transition orgánica (Biomecánica)
    float luma1 = dot(col1, vec3(0.299, 0.587, 0.114)); 
    vec2 warp_st = st + (luma1 * 0.1 * transition_t); 
    vec3 warped_col2 = texture(tex2, warp_st).rgb;
    
    vec3 final_col = mix(col1, mix(col2, warped_col2, transition_t), transition_t);
    
    // High Quality Bloom Multi-tap approximation
    vec3 bloom = vec3(0.0);
    vec2 texel = 1.0 / vec2(1280.0, 720.0);
    for(int i=-2; i<=2; i++) {
        for(int j=-2; j<=2; j++) {
            vec3 s = texture(tex1, st + vec2(i, j) * texel * 4.0).rgb;
            bloom += max(vec3(0.0), s - 0.7);
        }
    }
    bloom *= (high * 0.05);
    final_col += bloom;
    
    // Vignette cinematográfica profunda
    float vig = smoothstep(0.95, 0.2, dist * 1.2);
    final_col *= mix(0.2, 1.0, vig);
    
    // ACES Tone mapping (+20% exposición antes de mapear)
    final_col = ACESFilm(final_col * 1.2);
    
    // Film Grain animado orgánico reactivo a agudos
    float grain = (hash(st + fract(time * 0.017)) - 0.5) * 0.18 * (0.4 + high * 0.8);
    final_col += grain;
    
    fragColor = vec4(final_col, 1.0);
}
'''

# COMPOSITE SHADER: Mezcla imagen AI de fondo + overlay GLSL + Ken Burns + postproceso
COMPOSITE_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;
uniform sampler2D tex_base;      // Imagen fotorrealista de Pollinations/Fooocus
uniform sampler2D tex_overlay;   // GLSL procedural (personaje + efectos)
uniform sampler2D tex_overlay2;  // Segunda escena para crossfade
uniform sampler2D tex_base2;     // Segunda imagen para crossfade de fondos
uniform float transition_t;
uniform float time;
uniform float bass;
uniform float mid;
uniform float high;
uniform float ken_burns_t;       // 0.0-1.0 progreso del zoom Ken Burns en esta escena

// ACES Tone Mapping
vec3 ACESFilm(vec3 x) {
    float a=2.51, b=0.03, c=2.43, d=0.59, e=0.14;
    return clamp((x*(a*x+b))/(x*(c*x+d)+e), 0.0, 1.0);
}
float hash2(vec2 p) { p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }

void main() {
    vec2 st = uv;

    // ── Ken Burns: zoom suave + drift lateral sobre la imagen base ──────────
    float zoom = 1.0 + ken_burns_t * 0.08;   // Zoom del 0% al 8% durante la escena
    float driftX = (ken_burns_t - 0.5) * 0.04;
    float driftY = sin(ken_burns_t * 3.14159) * 0.02;
    vec2 kb_uv = (st - 0.5) / zoom + 0.5 + vec2(driftX, driftY);
    kb_uv = clamp(kb_uv, 0.001, 0.999);

    // ── Leer imagen base con crossfade y Chromatic Aberration reactiva ───────
    vec2 dir = st - 0.5;
    float ab = bass * 0.018 * length(dir);
    
    vec3 base1, base2;
    base1.g = texture(tex_base, kb_uv).g;
    base1.r = texture(tex_base, kb_uv + dir * ab).r;
    base1.b = texture(tex_base, kb_uv - dir * ab).b;
    
    base2.g = texture(tex_base2, kb_uv).g;
    base2.r = texture(tex_base2, kb_uv + dir * ab).r;
    base2.b = texture(tex_base2, kb_uv - dir * ab).b;
    
    vec3 base = mix(base1, base2, transition_t);

    // ── Leer overlay GLSL ────────────────────────────────────────────────────
    vec4 ov1 = texture(tex_overlay, st);
    vec4 ov2 = texture(tex_overlay2, st);

    // Overlay brightness → alpha: pixeles muy oscuros del GLSL se vuelven transparentes
    // Esto hace que el fondo AI "se vea" donde el GLSL no tiene acción
    float luma1 = dot(ov1.rgb, vec3(0.299, 0.587, 0.114));
    float luma2 = dot(ov2.rgb, vec3(0.299, 0.587, 0.114));
    
    // El personaje SDF y el plasma tienen luma alta → opacos
    // El fondo negro del GLSL tiene luma 0 → transparente → muestra la imagen AI
    float alpha1 = smoothstep(0.04, 0.18, luma1);
    float alpha2 = smoothstep(0.04, 0.18, luma2);

    // Crossfade con warp orgánico entre las dos escenas GLSL
    vec2 warp_st = st + dir * luma1 * 0.06 * transition_t;
    vec4 ov2_warped = texture(tex_overlay2, warp_st);
    float alpha2w = smoothstep(0.04, 0.18, dot(ov2_warped.rgb, vec3(0.299, 0.587, 0.114)));
    
    vec3 overlay = mix(ov1.rgb, ov2_warped.rgb, transition_t);
    float alpha_ov = mix(alpha1, alpha2w, transition_t);

    // Bloom del overlay GLSL (aura de luz alrededor del personaje y plasma)
    vec3 bloom = vec3(0.0);
    vec2 texel = vec2(1.0/1280.0, 1.0/720.0);
    for(int i=-3; i<=3; i++) {
        for(int j=-3; j<=3; j++) {
            vec4 s = texture(tex_overlay, st + vec2(float(i),float(j)) * texel * 5.0);
            float sl = dot(s.rgb, vec3(0.299, 0.587, 0.114));
            bloom += max(vec3(0.0), s.rgb - 0.5) * smoothstep(0.05, 0.18, sl);
        }
    }
    bloom *= (0.3 + high * 0.5) * (1.0 / 49.0);

    // ── Composición final ────────────────────────────────────────────────────
    // La imagen AI es el fondo. El GLSL overlay se mezcla SOBRE ella en modo additive/alpha.
    // En zonas donde el overlay es oscuro, el fondo AI domina.
    // En zonas brillantes (personaje, plasma), el overlay domina.
    vec3 col = mix(base, base * 0.4 + overlay, alpha_ov);  // Imagen AI visible bajo el overlay
    col += bloom;                                            // Aura luminosa del overlay

    // Tinte global del overlay sobre el fondo (colores del GLSL tiñen sutilmente la imagen)
    col = mix(col, col * (0.6 + overlay * 0.5), 0.3 * alpha_ov);
    
    // ── Camera shake & Cyber Glitch en beat drops ────────────────────────────
    if (bass > 0.85) {
        float shake = (bass - 0.85) * 0.025;
        vec2 shakeUV = kb_uv + vec2(sin(time * 50.0) * shake, cos(time * 47.0) * shake);
        
        // Digital Glitch (Desplazamiento horizontal de scanlines)
        float glitchLine = step(0.9, fract(st.y * 20.0 + time * 15.0));
        float glitchShift = (bass - 0.85) * 0.15 * glitchLine * sin(time * 120.0);
        shakeUV.x += glitchShift;
        
        // Chromatic Aberration extrema en el Glitch
        vec3 shakeCol;
        shakeCol.r = texture(tex_base, clamp(shakeUV + vec2(shake * 2.5, 0.0), 0.001, 0.999)).r;
        shakeCol.g = texture(tex_base, clamp(shakeUV, 0.001, 0.999)).g;
        shakeCol.b = texture(tex_base, clamp(shakeUV - vec2(shake * 2.5, 0.0), 0.001, 0.999)).b;
        
        col = mix(col, shakeCol + overlay * alpha_ov + bloom, 0.7);
        
        // Invertir colores esporádicamente en la franja del glitch (Flash subliminal)
        if (fract(time * 42.0) > 0.85 && glitchLine > 0.0) {
            col.rgb = 1.0 - col.rgb;
        }
    }

    // ── Vignette cinematográfica profunda ────────────────────────────────────
    float vdist = length(dir * vec2(1.0, 1.2));
    float vig = smoothstep(0.95, 0.2, vdist);
    col *= mix(0.2, 1.0, vig); // Viñeta más agresiva en los bordes

    // ── ACES Tone Mapping + Film Grain procedural ────────────────────────────
    col = ACESFilm(col * 1.15);
    float grain = (hash2(st + fract(time * 0.017)) - 0.5) * 0.18 * (0.4 + high * 0.8);
    col += grain;


    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
'''


MANDELBULB_FS = '''#version 330
out vec4 fragColor; in vec2 uv; uniform vec2 resolution; uniform float time, bass, mid, high, pan; uniform vec3 colorA, colorB; uniform int pose; 
void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); } 
float mandelbulbSDF(vec3 pos) { 
    vec3 z = pos;
    float dr = 1.0;
    float r = 0.0;
    for (int i = 0; i < 12; i++) { // Iteraciones aumentadas a 12
        r = length(z);
        if (r > 2.0) break;
        float theta = acos(z.z / r);
        float phi = atan(z.y, z.x);
        dr = pow(r, 7.0) * 8.0 * dr + 1.0;
        float zr = pow(r, 8.0);
        theta = theta * 8.0;
        phi = phi * 8.0;
        z = zr * vec3(sin(theta)*cos(phi), sin(phi)*sin(theta), cos(theta));
        z += pos;
    }
    return 0.5 * log(r) * r / dr;
} 
vec3 calcNormal(vec3 pos) { 
    vec2 e = vec2(1.0,-1.0)*0.5773*0.001; 
    return normalize( e.xyy*mandelbulbSDF(pos + e.xyy) + e.yyx*mandelbulbSDF(pos + e.yyx) + e.yxy*mandelbulbSDF(pos + e.yxy) + e.xxx*mandelbulbSDF(pos + e.xxx) ); 
} 
void main() { 
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y; 
    vec3 ro = vec3(0.0, 0.0, -2.5); pR(ro.xz, time * 0.1 + pan); pR(ro.xy, time * 0.05); 
    vec3 ww = normalize(-ro); vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0))); vec3 vv = normalize(cross(uu, ww)); 
    vec3 rd = normalize(p.x * uu + p.y * vv + 1.0 * ww); 
    float t = 0.0; float max_d = 10.0; float trap = 1.0; 
    for(int i=0; i<80; i++) { 
        vec3 pos = ro + rd*t; float d = mandelbulbSDF(pos); trap = min(trap, d); 
        if(d<0.001 || t>max_d) break; t += d; 
    } 
    vec3 col = colorA * 0.05; 
    if(t<max_d) { 
        vec3 pos = ro + rd*t; vec3 nor = calcNormal(pos); vec3 lig = normalize(vec3(1.0, 1.0, -1.0)); 
        float dif = clamp(dot(nor, lig), 0.0, 1.0); 
        float spe = pow(clamp(dot(reflect(rd, nor), lig), 0.0, 1.0), 32.0); 
        float sss = smoothstep(0.0, 1.0, mandelbulbSDF(pos + lig * 0.2)) * 0.5;
        col = mix(colorA, colorB, length(pos)/1.5); 
        col *= dif * 0.8 + 0.2; 
        col += spe * (0.5 + high * 2.0) * vec3(1.0); 
        col += colorA * sss;
    } else { 
        col += mix(colorA, colorB, 0.5) * exp(-trap*5.0) * bass; 
    } 
    float fog = 1.0 - exp(-pow(t * 0.15, 2.0));
    col = mix(col, mix(colorA*0.2, vec3(0.0), 0.8), fog);
    fragColor = vec4(col, 1.0); 
}'''

NEBULA_FS = '''#version 330
out vec4 fragColor; in vec2 uv; uniform vec2 resolution; uniform float time, bass, mid, high, pan; uniform vec3 colorA, colorB; uniform int pose; 
void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); } 
float noise(vec3 p) { 
    vec3 i = floor(p); vec3 f = fract(p); f = f*f*(3.0-2.0*f); 
    vec2 uv = (i.xy+vec2(37.0,17.0)*i.z) + f.xy; 
    vec2 rg = fract(sin((uv+0.5)*0.014)*292.0); return mix(rg.x, rg.y, f.z); 
} 
float mapNebula(vec3 p) { 
    float f = 0.0; vec3 q = p - vec3(0.0, 0.0, time*2.0); 
    f += 0.5000*noise(q); q = q*2.01; f += 0.2500*noise(q); q = q*2.02; f += 0.1250*noise(q); q = q*2.03; f += 0.0625*noise(q); 
    return f - 0.5; 
} 
void main() { 
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y; 
    vec3 ro = vec3(0.0, 0.0, 0.0); pR(ro.xy, pan); 
    vec3 rd = normalize(vec3(p.x, p.y, 1.0)); pR(rd.xy, sin(time*0.2)*0.5); 
    float t = 0.0; vec4 sum = vec4(0.0); 
    for(int i=0; i<60; i++) { 
        vec3 pos = ro + rd*t; float den = mapNebula(pos); 
        if(den > 0.01) { 
            vec3 col = mix(colorA, colorB, clamp(den*2.0, 0.0, 1.0)); 
            col *= mix(1.0, 2.5, bass); 
            col += high * colorB * 0.8; 
            // Sombras volumétricas falsas (Auto-sombreado)
            float sh = clamp(mapNebula(pos + normalize(vec3(1.0, 1.0, -1.0))*0.3), 0.0, 1.0);
            col *= 1.0 - sh * 0.5;
            vec4 src = vec4(col * den, den); src.rgb *= src.a; sum = sum + src*(1.0 - sum.a); 
        } 
        if(sum.a > 0.99) break; 
        t += 0.08 + bass*0.05; // Salto de raymarching modulado
    } 
    fragColor = vec4(sum.rgb, 1.0); 
}'''

def _load_image_as_texture(ctx, img_path: str, w: int, h: int):
    """Carga una imagen desde disco como textura moderngl RGB."""
    from PIL import Image
    import io
    try:
        img = Image.open(img_path).convert("RGB")
        resample_method = getattr(Image, 'Resampling', Image).LANCZOS
        if img.size != (w, h):
            img = img.resize((w, h), resample_method)
        data = img.tobytes()
        tex = ctx.texture((w, h), components=3, data=data)
        tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        return tex
    except Exception as e:
        import sys
        print(f"[AIFirst] Warning: no se pudo cargar {img_path}: {e}", file=sys.stderr)
        tex = ctx.texture((w, h), components=3)
        tex.write(bytes(w * h * 3))
        return tex


def _make_gradient_texture(ctx, color1: tuple, color2: tuple, w: int, h: int):
    """Crea una textura de gradiente radial cinematográfico usando numpy."""
    import numpy as np
    y, x = np.ogrid[:h, :w]
    cx, cy = w / 2.0, h / 2.0
    dist = np.sqrt(((x - cx)**2) / (w*0.7)**2 + ((y - cy)**2) / (h*0.7)**2)
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


def render_v13_video(timeline: list, multiband: dict, colorsA: np.ndarray,
                     colorsB: np.ndarray, w: int, h: int, fps: int,
                     out_mp4: str, audio_path: str,
                     speed_multiplier=1.0, turbulence=1.0,
                     background_images: list = None):
    """
    Renderiza el video V13 — AI-First Cinematic Pipeline.

    Si background_images contiene rutas válidas de imágenes (generadas por
    Pollinations/Fooocus), el COMPOSITE_FS las usa como fondo fotorrealista y
    renderiza el GLSL como overlay transparente sobre ellas.

    speed_multiplier y turbulence pueden ser float escalares O np.ndarray.
    background_images: lista de rutas (str|None), una por entrada en timeline.
    """
    ctx = moderngl.create_context(standalone=True)

    engines = {
        "space_odyssey": ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=SPACE_ODYSSEY_FS),
        "julia_fractal":  ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=JULIA_FS),
        "mandelbulb":     ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=MANDELBULB_FS),
        "nebula":         ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=NEBULA_FS),
        "quantum_tunnel": ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=QUANTUM_TUNNEL_FS),
    }

    # Elegir pipeline: AI-First si se provee la lista de fondos (incluso si fallaron)
    ai_first = background_images is not None
    if ai_first:
        prog_composite = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=COMPOSITE_FS)
        print("\n[🎬 Motor V13] PIPELINE AI-FIRST CINEMATOGRÁFICO ACTIVADO", file=sys.stderr)
    else:
        prog_post = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=POST_PROCESS_FS)
        print("\n[🚀 Motor V13] INICIANDO RENDER BIOMECÁNICO (VIDA + INERCIA)...", file=sys.stderr)

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

    # Textura negra de 1x1 como fallback para iChannel0 (evita sampler no inicializado)
    _black_px = np.zeros((1, 1, 3), dtype=np.uint8)
    tex_black_fallback = ctx.texture((1, 1), components=3, data=_black_px.tobytes())

    # Pre-cargar todas las texturas de fondo AI por escena
    scene_bg_textures = {}
    if ai_first:
        for i, scene in enumerate(timeline):
            img_path = background_images[i] if i < len(background_images) else None
            if img_path and os.path.isfile(img_path):
                scene_bg_textures[i] = _load_image_as_texture(ctx, img_path, w, h)
                print(f"  [AIFirst] Escena {i+1}: {os.path.basename(img_path)}", file=sys.stderr)
            else:
                # Fallback: gradiente con los colores de esa escena
                mid_f = (scene["start"] + scene["end"]) // 2
                mid_f = min(mid_f, len(colorsA) - 1)
                c1 = tuple(float(x) for x in colorsA[mid_f])
                c2 = tuple(float(x) for x in colorsB[mid_f])
                scene_bg_textures[i] = _make_gradient_texture(ctx, c1, c2, w, h)

    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ffmpeg_exe = os.path.join(_base, "_integrations", "ffmpeg", "ffmpeg.exe")
    if not os.path.isfile(ffmpeg_exe): ffmpeg_exe = "ffmpeg"

    cmd = [ffmpeg_exe, "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
           "-s", f"{w}x{h}", "-pix_fmt", "rgb24", "-r", str(fps), "-i", "-"]
    if audio_path and os.path.isfile(audio_path):
        cmd.extend(["-i", audio_path, "-vf", "vflip", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "18",
                    "-c:a", "aac", "-b:a", "192k", "-shortest"])
    else:
        cmd.extend(["-vf", "vflip", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-preset", "fast", "-crf", "18"])
    cmd.append(out_mp4)

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    total_frames = len(multiband['bass'])
    _spd_is_arr = isinstance(speed_multiplier, np.ndarray)
    _trb_is_arr = isinstance(turbulence, np.ndarray)

    try:
        for frame_idx in range(total_frames):
            engine_1 = "space_odyssey"
            engine_2 = None
            pose_1 = 0
            pose_2 = 0
            scene_idx_1 = 0
            scene_idx_2 = 0
            transition_t = 0.0
            ken_burns_t = 0.0

            for si, scene in enumerate(timeline):
                if scene["start"] <= frame_idx <= scene["end"]:
                    engine_1 = scene["engine"]
                    pose_1 = scene.get("pose", 0)
                    scene_idx_1 = si
                    # Ken Burns: progreso dentro de la escena (0→1)
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
            cA  = tuple(float(x) for x in colorsA[frame_idx])
            cB  = tuple(float(x) for x in colorsB[frame_idx])

            # Preparar texturas de fondo (IBL)
            bg_tex1 = None; bg_tex2 = None
            if ai_first and len(scene_bg_textures) > 0:
                bg_tex1 = scene_bg_textures.get(scene_idx_1)
                if bg_tex1 is None: bg_tex1 = list(scene_bg_textures.values())[0]
                bg_tex2 = scene_bg_textures.get(scene_idx_2) if engine_2 else bg_tex1
                if bg_tex2 is None: bg_tex2 = bg_tex1

            def render_pass(engine_name, fbo, pose_val, bg_tex):
                prog = engines[engine_name]
                if 'resolution' in prog: prog['resolution'].value = (w, h)
                if 'time'       in prog: prog['time'].value = t
                if 'bass'       in prog: prog['bass'].value = b
                if 'mid'        in prog: prog['mid'].value = m
                if 'high'       in prog: prog['high'].value = hg
                if 'pan'        in prog: prog['pan'].value = pan
                if 'colorA'     in prog: prog['colorA'].value = cA
                if 'colorB'     in prog: prog['colorB'].value = cB
                if 'pose'       in prog: prog['pose'].value = pose_val
                
                # Bindear la imagen fotorealista (IBL) — siempre bindeamos algo a loc 0
                tex_to_bind = bg_tex if bg_tex else tex_black_fallback
                tex_to_bind.use(location=0)
                if 'iChannel0' in prog: prog['iChannel0'].value = 0

                fbo.use(); ctx.clear(0.0, 0.0, 0.0)
                vaos[engine_name].render(moderngl.TRIANGLE_STRIP)

            render_pass(engine_1, fbo_geom1, pose_1, bg_tex1)
            if engine_2 is not None:
                render_pass(engine_2, fbo_geom2, pose_2, bg_tex2)
            else:
                render_pass(engine_1, fbo_geom2, pose_1, bg_tex1)  # Duplicar para evitar artifacts

            fbo_final.use()
            ctx.clear(0.0, 0.0, 0.0)

            if ai_first and bg_tex1 is not None and bg_tex2 is not None:
                # ── AI-First: COMPOSITE_FS con imagen fotorrealista de fondo ──

                bg_tex1.use(location=0)
                tex_geom1.use(location=1)
                tex_geom2.use(location=2)
                bg_tex2.use(location=3)
                
                pc = prog_composite
                if 'tex_base'     in pc: pc['tex_base'].value = 0
                if 'tex_overlay'  in pc: pc['tex_overlay'].value = 1
                if 'tex_overlay2' in pc: pc['tex_overlay2'].value = 2
                if 'tex_base2'    in pc: pc['tex_base2'].value = 3
                if 'transition_t' in pc: pc['transition_t'].value = float(transition_t)
                if 'time'         in pc: pc['time'].value = t
                if 'bass'         in pc: pc['bass'].value = b
                if 'mid'          in pc: pc['mid'].value = m
                if 'high'         in pc: pc['high'].value = hg
                if 'ken_burns_t'  in pc: pc['ken_burns_t'].value = float(ken_burns_t)
                vao_composite.render(moderngl.TRIANGLE_STRIP)
            else:
                # ── Legacy: POST_PROCESS_FS (solo GLSL) ──────────────────────
                tex_geom1.use(location=0)
                tex_geom2.use(location=1)
                pp = prog_post
                if 'tex1'         in pp: pp['tex1'].value = 0
                if 'tex2'         in pp: pp['tex2'].value = 1
                if 'transition_t' in pp: pp['transition_t'].value = float(transition_t)
                if 'bass'         in pp: pp['bass'].value = b
                if 'high'         in pp: pp['high'].value = hg
                if 'time'         in pp: pp['time'].value = t
                vao_post.render(moderngl.TRIANGLE_STRIP)

            img_bytes = fbo_final.read(components=3)
            proc.stdin.write(img_bytes)

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

    # Liberar recursos GPU
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

