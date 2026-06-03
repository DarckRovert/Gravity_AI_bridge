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

// --- Partículas Volumétricas (Beat-Sync V2) ---
vec3 calcVolumetricParticles(vec3 pos, float time, float bass, float mid, float high) {
    vec3 pPos = pos;
    // Movimiento caótico fluido basado en tiempo y medios
    pPos.y += time * (0.5 + mid); 
    pPos.x += sin(time * 2.0 + pPos.z) * 0.5 * mid;
    
    vec3 cell = floor(pPos * 3.0);
    vec3 local = fract(pPos * 3.0) - 0.5;
    
    float h = hash3D(cell);
    
    // Umbral de densidad: aparecen mas con el bajo
    float threshold = 0.95 - (bass * 0.05);
    if (h > threshold) {
        // Posicion aleatoria dentro de la celda
        vec3 offset = vec3(hash3D(cell+1.0), hash3D(cell+2.0), hash3D(cell+3.0)) - 0.5;
        float d = length(local - offset * 0.5);
        float radius = 0.02 + (high * 0.04 * h); // Tamaño reacciona a los altos
        
        if (d < radius * 6.0) { // SSS extendido
            float intensity = 0.005 / (0.001 + d * d);
            // Color: tonos cyan/magenta/dorado según la semilla
            vec3 pColor = mix(vec3(0.1, 0.8, 1.0), vec3(1.0, 0.3, 0.8), h);
            pColor = mix(pColor, vec3(1.0, 0.8, 0.2), fract(h * 10.0));
            return pColor * intensity * (0.2 + high * 2.5);
        }
    }
    return vec3(0.0);
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
    vec3 target = vec3(0.0, 0.0, -5.0);
    
    // === CINEMATIC SHOT MACHINE V1 ===
    // Cada shot dura ~6 segundos. El ciclo completo es 24s.
    float shotDur = 6.0;
    float cycleT  = mod(time, shotDur * 4.0);
    int   shotIdx = int(cycleT / shotDur); // 0,1,2,3
    float shotT   = smoothstep(0.0, 1.0, fract(cycleT / shotDur)); // [0..1] dentro del shot
    
    vec3 ro;
    float focalDist;
    float fov = 1.5;
    float camRoll = 0.0;
    
    if (shotIdx == 0) {
        // ESTABLISHING: Gran angular orbital lento, revelar la escena completa
        float angle = time * 0.08 + pan * 0.5;
        ro = vec3(sin(angle) * 14.0, 3.5 + sin(time * 0.12) * 1.5, cos(angle) * 14.0 - 5.0);
        fov = 1.2; // gran angular
        focalDist = length(target - ro) * 0.7;
        camRoll = sin(time * 0.05) * 0.03; // roll casi imperceptible
    } else if (shotIdx == 1) {
        // ORBIT MEDIUM: Orbital a media altura, nivel del sujeto
        float angle = time * 0.15 + pan * 0.5;
        ro = vec3(sin(angle) * 8.0, sin(time * 0.2) * 1.2 + 0.5, cos(angle) * 8.0 - 5.0);
        fov = 1.5;
        focalDist = length(target - ro) * 0.85;
        camRoll = sin(time * 0.07) * 0.06;
    } else if (shotIdx == 2) {
        // CLOSEUP: Aproximación lenta e intensa al sujeto. Pull-in Beziér.
        float angle = time * 0.06 + pan * 0.3;
        float zoomT = smoothstep(0.0, 1.0, shotT);
        float dist  = mix(9.0, 4.5, zoomT); // se acerca
        ro = vec3(sin(angle) * dist, 0.8 + sin(time*0.1)*0.4, cos(angle) * dist - 5.0);
        fov = mix(1.5, 2.2, zoomT); // focal largo en closeup
        focalDist = mix(length(target - ro) * 0.95, length(target - ro) * 0.6, zoomT);
        camRoll = sin(time * 0.03) * 0.04;
    } else {
        // FLYBY: Paso veloz lateral, añade drama y tensión
        float flyT  = shotT;
        float x     = mix(-12.0, 12.0, flyT);
        ro = vec3(x, 2.0 + sin(flyT * 3.14159) * 1.0, -3.5 + sin(flyT * 3.14159) * -2.0);
        target = vec3(0.0, 0.0, -5.0) + vec3(sin(flyT * 2.0) * 2.0, 0.0, 0.0);
        fov = 1.6;
        focalDist = length(target - ro) * 0.8;
        camRoll = sin(flyT * 6.28318) * 0.1;
    }
    
    // Bass shake CONTROLADO: solo en beats intensos, amortiguado
    float shakeAmt = max(0.0, bass - 0.75) * 0.03;
    ro += vec3(sin(time * 47.0), cos(time * 43.0), sin(time * 51.0)) * shakeAmt;
    
    // Camera basis con roll narrativo
    vec3 ww = normalize(target - ro);
    vec3 up  = vec3(sin(camRoll), cos(camRoll), 0.0);
    vec3 uu = normalize(cross(ww, up));
    vec3 vv = normalize(cross(uu, ww));
    vec3 rd = normalize(p.x * uu + p.y * vv + fov * ww);
    
    float t = 0.0; float max_d = 20.0; vec3 col = vec3(0.0); vec3 particleCol = vec3(0.0);
    float mat_id = 0.0;
    
    for(int i=0; i<64; i++) {
        vec3 pos = ro + rd*t; vec2 res = map(pos);
        if(res.x<0.001 || t>max_d) { mat_id = res.y; break; }
        t += res.x;
        
        // Partículas Volumétricas
        particleCol += calcVolumetricParticles(pos, time, bass, mid, high);
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
    vec3 final_bg = bgCol + vec3(stars);
    
    // Mezcla de la geometría con el fondo según la distancia
    col = mix(col, final_bg, fogFactor);
    
    // Sumar partículas volumétricas
    col += particleCol * mix(1.0, 0.2, fogFactor);
    
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
    
    // === CINEMATIC SHOT MACHINE V1 (JULIA) ===
    float shotDur = 7.0;
    float cycleT  = mod(time, shotDur * 4.0);
    int   shotIdx = int(cycleT / shotDur);
    float shotT   = smoothstep(0.0, 1.0, fract(cycleT / shotDur));
    
    float camZ = forwardTravel() - 3.5;
    vec3 ro; float fov = 1.2;
    
    if (shotIdx == 0) {
        // Plano Maestro: sigue el fractal de lejos con altura variable
        ro = vec3(sin(time*0.08)*2.5, 1.5 + sin(time*0.12)*0.8, camZ);
    } else if (shotIdx == 1) {
        // Zoom de seguimiento suave (dolly-in)
        float zoomT = smoothstep(0.0, 1.0, shotT);
        ro = vec3(sin(time*0.1)*mix(2.0, 0.8, zoomT), mix(1.5, 0.6, zoomT), camZ);
        fov = mix(1.2, 1.8, zoomT);
    } else if (shotIdx == 2) {
        // Lateral (travelling): la cámara se desplaza en X
        ro = vec3(mix(-2.5, 2.5, shotT), 0.8 + sin(time*0.15)*0.5, camZ + 1.0);
    } else {
        // Dutch angle + pull-back
        ro = vec3(cos(time*0.08)*2.0, 2.2, camZ - shotT * 2.0);
        fov = 1.1;
    }
    
    pR(ro.xz, pan * 0.3);
    float shakeAmt = max(0.0, bass - 0.75) * 0.025;
    ro += vec3(sin(time * 47.0) * shakeAmt, cos(time * 43.0) * shakeAmt, 0.0);
    
    vec3 ww = normalize(vec3(0.0, 0.0, 1.0));
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = normalize(cross(uu, ww));
    vec3 rd = normalize(p.x * uu + p.y * vv + fov * ww);
    
    float t = 0.0, max_d = 12.0, iter = 0.0;
    float mat_id = 0.0; vec3 particleCol = vec3(0.0);
    
    for(int i=0; i<64; i++) {
        vec3 pos = ro + rd*t; vec2 res = map(pos);
        if(res.x<0.002 || t>max_d) { mat_id = res.y; break; }
        t += res.x; iter++;
        
        particleCol += calcVolumetricParticles(pos, time, bass, mid, high);
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
    
    // Sumar partículas volumétricas
    col += particleCol * mix(1.0, 0.3, fogFactor);
    
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
    
    // === CINEMATIC SHOT MACHINE V1 (QUANTUM TUNNEL) ===
    float shotDur = 5.0;
    float cycleT  = mod(time, shotDur * 3.0);
    int   shotIdx = int(cycleT / shotDur);
    float shotT   = smoothstep(0.0, 1.0, fract(cycleT / shotDur));
    
    float fwd = forwardTravel();
    vec3 ro; float fov = 1.4;
    
    if (shotIdx == 0) {
        // Centrado en el eje del túnel
        ro = vec3(sin(time*0.05)*0.3 + pan, cos(time*0.07)*0.2, fwd);
    } else if (shotIdx == 1) {
        // Descentrado lateral (tensión visual, como un Steadicam)
        ro = vec3(mix(0.0, 1.2, shotT) + pan, mix(0.0, -0.4, shotT), fwd);
        fov = mix(1.4, 1.7, shotT);
    } else {
        // Pull-back dramático: la cámara se aleja del destino
        ro = vec3(pan * 0.3, 0.0, fwd - shotT * 3.0);
        fov = 1.2;
    }
    
    float shakeAmt = max(0.0, bass - 0.75) * 0.02;
    ro.xy += vec2(sin(time * 47.0), cos(time * 43.0)) * shakeAmt;
    
    vec3 rd = normalize(vec3(p.x, p.y, fov));
    pR(rd.xy, sin(time * 0.04) * 0.04); // roll suave y respirado 
    
    float t = 0.0, max_d = 30.0, glow = 0.0; float mat_id = 0.0;
    vec3 particleCol = vec3(0.0);
    for(int i=0; i<50; i++) {
        vec3 pos = ro + rd*t; vec2 res = map(pos);
        if(res.y == 0.0) glow += 0.01 / (0.01 + res.x*res.x);
        if(res.x<0.01 || t>max_d) { mat_id = res.y; break; }
        t += res.x;
        
        particleCol += calcVolumetricParticles(pos, time, bass, mid, high);
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
    
    // Sumar partículas volumétricas
    col += particleCol * mix(1.0, 0.1, fogFactor);
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
    
    // ── Camera shake CONTROLADO: solo en beat drops intensos ─────────────────
    float shakeStrength = max(0.0, bass - 0.82) * 0.018;
    if (shakeStrength > 0.0) {
        st += vec2(sin(time * 53.0) * shakeStrength, cos(time * 47.0) * shakeStrength);
        // Digital Glitch sutil: desplazamiento de scanlines cada 3-4 beats
        float glitchLine = step(0.92, fract(st.y * 18.0 + time * 12.0));
        st.x += (bass - 0.82) * 0.08 * glitchLine * sin(time * 100.0);
    }
    
    // Inversion de color en momentos pico extremos (solo los mas fuertes)
    float glitchLine2 = step(0.93, fract(st.y * 18.0 + time * 12.0));
    bool doInvert = bass > 0.92 && fract(time * 30.0) > 0.88 && glitchLine2 > 0.0;
    
    // Radial Chromatic Aberration
    vec2 dir = st - 0.5;
    float dist = length(dir);
    float ab = bass * 0.03 * dist;
    
    vec3 col1 = vec3(
        texture(tex1, clamp(st + dir * ab, 0.0, 1.0)).r,
        texture(tex1, clamp(st,            0.0, 1.0)).g,
        texture(tex1, clamp(st - dir * ab, 0.0, 1.0)).b
    );
    vec3 col2 = vec3(
        texture(tex2, clamp(st + dir * ab, 0.0, 1.0)).r,
        texture(tex2, clamp(st,            0.0, 1.0)).g,
        texture(tex2, clamp(st - dir * ab, 0.0, 1.0)).b
    );
    
    if (doInvert) { col1.rgb = 1.0 - col1.rgb; col2.rgb = 1.0 - col2.rgb; }
    
    // Warp transition orgánica
    float luma1 = dot(col1, vec3(0.299, 0.587, 0.114));
    vec2 warp_st = st + (luma1 * 0.1 * transition_t);
    vec3 warped_col2 = texture(tex2, clamp(warp_st, 0.0, 1.0)).rgb;
    vec3 final_col = mix(col1, mix(col2, warped_col2, transition_t), transition_t);
    
    // === DEPTH OF FIELD (Lens Bokeh) ===
    // Efecto sutil, activo siempre. Intensidad surge en Closeup (bass bajo)
    float dofStrength = 0.0035 * (1.0 - bass * 0.5);
    vec3 dofBlur = vec3(0.0);
    float dofWeight = 0.0;
    vec2 texelSize = 1.0 / vec2(1280.0, 720.0);
    // Muestreo tipo Bokeh hexagonal (12 taps)
    for (int i = 0; i < 12; i++) {
        float angle2 = float(i) * 0.5235988; // 30 grados
        float r = dofStrength * 40.0 * dist; // Mayor bokeh en bordes (enfoque central)
        vec2 offset2 = vec2(cos(angle2), sin(angle2)) * r;
        float w = 1.0 - float(i) / 12.0;
        dofBlur += texture(tex1, clamp(st + offset2, 0.0, 1.0)).rgb * w;
        dofWeight += w;
    }
    dofBlur /= dofWeight;
    // Mezcla DoF: centro nítido, bordes desenfocados (similar a lente 85mm f/1.8)
    float focusMask = smoothstep(0.0, 0.55, dist);
    final_col = mix(final_col, mix(final_col, dofBlur, focusMask), dofStrength * 150.0);
    
    // High Quality Bloom Multi-tap
    vec3 bloom = vec3(0.0);
    for(int i=-2; i<=2; i++) {
        for(int j=-2; j<=2; j++) {
            vec3 s = texture(tex1, clamp(st + vec2(float(i), float(j)) * texelSize * 4.0, 0.0, 1.0)).rgb;
            bloom += max(vec3(0.0), s - 0.72);
        }
    }
    bloom *= (high * 0.04);
    final_col += bloom;
    
    // Vignette cinematográfica
    float vig = smoothstep(0.95, 0.2, dist * 1.2);
    final_col *= mix(0.25, 1.0, vig);
    
    // ACES Tone mapping
    final_col = ACESFilm(final_col * 1.2);
    
    // Film Grain reactivo a agudos
    float grain = (hash(st + fract(time * 0.017)) - 0.5) * 0.15 * (0.4 + high * 0.7);
    final_col += grain;
    
    fragColor = vec4(final_col, 1.0);
}
'''

# --- GARGANTUA (RELATIVIDAD GENERAL E INTERESTELAR) ---
INTERSTELLAR_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, pan, beat_hit;
uniform vec3 colorA, colorB; uniform int pose;
uniform sampler2D iChannel0;

mat2 rot(float a) { float s=sin(a), c=cos(a); return mat2(c,-s,s,c); }

float hash(vec3 p) {
    p = fract(p * vec3(127.1, 311.7, 74.7));
    p += dot(p, p + 19.19);
    return fract(p.x * p.y * p.z);
}

float noise(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    f = f*f*(3.0-2.0*f);
    return mix(
        mix(mix(hash(i), hash(i+vec3(1,0,0)), f.x),
            mix(hash(i+vec3(0,1,0)), hash(i+vec3(1,1,0)), f.x), f.y),
        mix(mix(hash(i+vec3(0,0,1)), hash(i+vec3(1,0,1)), f.x),
            mix(hash(i+vec3(0,1,1)), hash(i+vec3(1,1,1)), f.x), f.y), f.z
    );
}

float fbm(vec3 p) {
    float f = 0.0;
    float w = 0.5;
    for(int i=0; i<4; i++) {
        f += w * noise(p);
        p *= 2.0;
        w *= 0.5;
    }
    return f;
}

#define PI 3.14159265359
vec2 envMapEquirect(vec3 dir) {
    float phi = atan(dir.z, dir.x);
    float theta = asin(clamp(dir.y, -1.0, 1.0));
    return vec2(phi / (2.0 * PI) + 0.5, theta / PI + 0.5);
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    
    // Cámara
    vec3 ro = vec3(0.0, 1.2 + sin(time*0.2)*0.5, -6.0 + sin(time*0.1)*1.5);
    ro.xz *= rot(time * 0.1 + pan);
    vec3 ta = vec3(0.0, 0.0, 0.0);
    
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = normalize(cross(uu, ww));
    vec3 rd = normalize(p.x*uu + p.y*vv + 1.5*ww);
    
    // Trazador de Rayos Relativista (Kerr / Schwarzschild aproximado)
    vec3 pos = ro;
    vec3 col = vec3(0.0);
    float dt = 0.08;
    float mass = 1.0; // Singularidad
    float event_horizon = 0.8;
    
    float transmittance = 1.0;
    
    for(int i = 0; i < 150; i++) {
        float r2 = dot(pos, pos);
        float r = sqrt(r2);
        
        // Efecto Lente Gravitacional: Curvatura de la Geodésica
        // La gravedad atrae el fotón hacia el centro (0,0,0)
        vec3 force = -pos * (mass / (r2 * r));
        rd = normalize(rd + force * dt * 1.5);
        
        pos += rd * dt;
        
        // Si cruzamos el horizonte de sucesos, se acabó el rayo (oscuridad)
        if (r < event_horizon) {
            transmittance = 0.0;
            break;
        }
        
        // Disco de Acreción (Volumen plano en y=0)
        if (abs(pos.y) < 0.4 && r > 1.2 && r < 4.5) {
            // Dinámica de fluidos del plasma giratorio
            vec3 dp = pos;
            float angle = atan(dp.z, dp.x);
            float speed = 3.0 / sqrt(r); // Velocidad kepleriana
            dp.xz *= rot(-time * speed);
            
            float plasma = fbm(dp * 4.0 - vec3(0,time*2.0,0));
            plasma *= smoothstep(0.4, 0.0, abs(pos.y));
            plasma *= smoothstep(1.2, 1.5, r) * smoothstep(4.5, 3.5, r); // Bordes difusos
            
            if (plasma > 0.0) {
                // Relativistic Doppler Beaming
                // El plasma acercándose es azul/brillante, alejándose es rojo/oscuro
                vec3 tangent = normalize(vec3(-pos.z, 0.0, pos.x));
                float doppler = dot(rd, tangent) * speed; 
                
                vec3 base_color = mix(colorB, colorA, r/4.5);
                
                // Shift de color basado en la relatividad
                vec3 shiftColor = mix(vec3(1.0, 0.2, 0.0), vec3(0.5, 0.8, 1.0), (doppler + 1.0) * 0.5);
                
                // Pulso de onda gravitacional en el Beat exacto
                float grav_pulse = beat_hit * smoothstep(1.5, 3.0, r);
                vec3 final_glow = base_color * shiftColor * (1.0 + doppler * 0.8) * (1.0 + bass*0.5 + grav_pulse*2.0);
                
                // Absorción y emisión (Volumetric raymarching)
                float alpha = plasma * 0.15;
                col += transmittance * final_glow * alpha * 5.0;
                transmittance *= (1.0 - alpha);
            }
        }
        
        if (transmittance < 0.01) break;
    }
    
    // Fondo Híbrido: Textura Neural (IA) deformada por la Relatividad General
    if (transmittance > 0.01) {
        vec2 uv_env = envMapEquirect(rd);
        vec3 ai_env = texture(iChannel0, uv_env).rgb;
        
        // Mezclamos la IA con la paleta matemática para integración perfecta
        ai_env *= mix(vec3(1.0), colorA, 0.2); 
        
        // Destellos estelares sobre la textura
        float st = fbm(rd * 150.0);
        if (st > 0.65) ai_env += vec3(pow(st, 5.0)) * 2.0;
        
        col += ai_env * transmittance * 1.8;
    }
    
    fragColor = vec4(col, 1.0);
}
'''

# --- JOYA 1: FRACTALES KIFS (INCEPTION) ---
KIFS_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, pan, beat_hit;
uniform vec3 colorA, colorB; uniform int pose;

mat2 rot(float a) { float s=sin(a), c=cos(a); return mat2(c,-s,s,c); }

float map(vec3 p) {
    // KIFS (Kaleidoscopic Iterated Function Systems)
    float scale = 1.0;
    for(int i = 0; i < 5; i++) {
        p.xyz = abs(p.xyz) - vec3(1.2 + bass * 0.8, 0.8 + mid * 0.5, 0.5 + beat_hit * 0.5);
        p.xy *= rot(time * 0.15 + bass * 0.2 + beat_hit * 0.1);
        p.xz *= rot(time * 0.1 + high * 0.2);
        p *= 1.5;
        scale *= 1.5;
    }
    return (length(p) - 1.5) / scale; // Esfera plegada fractalmente
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    vec3 ro = vec3(0.0, 0.0, -8.0 + sin(time*0.5)*2.0);
    vec3 rd = normalize(vec3(p, 1.5));
    
    // Rotar cámara para efecto vértigo
    ro.xy *= rot(sin(time*0.1) * 0.5);
    rd.xy *= rot(sin(time*0.1) * 0.5);
    rd.xz *= rot(time*0.2 + pan);
    
    float t = 0.0;
    vec3 col = vec3(0.0);
    
    // Raymarching
    for(int i = 0; i < 100; i++) {
        vec3 pos = ro + rd * t;
        float d = map(pos);
        if(d < 0.001) {
            // Normales
            vec2 e = vec2(0.001, 0.0);
            vec3 n = normalize(vec3(
                map(pos + e.xyy) - map(pos - e.xyy),
                map(pos + e.yxy) - map(pos - e.yxy),
                map(pos + e.yyx) - map(pos - e.yyx)
            ));
            
            // Iluminación
            vec3 lig = normalize(vec3(sin(time), 1.0, cos(time)));
            float dif = max(dot(n, lig), 0.0);
            float amb = 0.5 + 0.5 * n.y;
            
            // Material basado en posición fractal
            vec3 mat = mix(colorA, colorB, sin(pos.z * 5.0 + time) * 0.5 + 0.5);
            col = mat * (dif * 0.8 + amb * 0.2);
            
            // Glow reactivo
            col += colorA * bass * 2.0 * smoothstep(0.5, 1.0, fract(pos.y * 10.0 + time * 5.0));
            break;
        }
        t += d;
        // Fog volumétrico en cada paso
        col += mix(colorB, vec3(1.0), 0.5) * 0.015 * smoothstep(1.0, 0.0, d) * bass;
        if(t > 20.0) break;
    }
    
    // Fog de profundidad
    col = mix(col, vec3(0.05), 1.0 - exp(-0.05 * t));
    fragColor = vec4(col, 1.0);
}
'''

# --- JOYA 2: FLUIDOS NEON (PSEUDO NAVIER-STOKES) ---
NEON_FLUID_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, beat_hit;
uniform vec3 colorA, colorB;

mat2 rot(float a) { float s=sin(a), c=cos(a); return mat2(c,-s,s,c); }

vec2 hash( vec2 p ) {
    p = vec2( dot(p,vec2(127.1,311.7)), dot(p,vec2(269.5,183.3)) );
    return -1.0 + 2.0*fract(sin(p)*43758.5453123);
}

float noise( in vec2 p ) {
    vec2 i = floor( p );
    vec2 f = fract( p );
    vec2 u = f*f*(3.0-2.0*f);
    return mix( mix( dot( hash( i + vec2(0.0,0.0) ), f - vec2(0.0,0.0) ), 
                     dot( hash( i + vec2(1.0,0.0) ), f - vec2(1.0,0.0) ), u.x),
                mix( dot( hash( i + vec2(0.0,1.0) ), f - vec2(0.0,1.0) ), 
                     dot( hash( i + vec2(1.0,1.0) ), f - vec2(1.0,1.0) ), u.x), u.y);
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    vec2 fluid_uv = p;
    
    // Advección de Curl Noise (Fluido Turbulento)
    float t = time * 0.5;
    for(int i = 0; i < 6; i++) {
        // Empuje del sonido como "viento" físico
        vec2 force = vec2(sin(t + fluid_uv.y * 3.0), cos(t + fluid_uv.x * 3.0)) * bass * 0.2;
        
        float n1 = noise(fluid_uv * 2.0 + t);
        float n2 = noise(fluid_uv * 2.0 - t + vec2(10.0));
        
        // El vector perpendicular al ruido de gradiente da el "Curl" (Navier-Stokes divergence-free)
        vec2 curl = vec2(-n2, n1); 
        
        fluid_uv += (curl * 0.3 + force) * (1.0 + mid);
        fluid_uv *= rot(0.1 * high * sin(time));
    }
    
    // Renderear el humo
    float smoke = noise(fluid_uv * 4.0);
    smoke = smoothstep(0.0, 0.7, smoke);
    
    // Impacto expansivo explosivo de fluido
    float shockwave = beat_hit * smoothstep(0.5, 0.0, abs(length(p) - fract(time*2.0)));
    
    // Colorización basada en la densidad del humo
    vec3 col = mix(vec3(0.0), colorA, smoke + shockwave);
    col = mix(col, colorB, smoothstep(0.4, 1.0, smoke) * bass + beat_hit * 0.5);
    
    // Resaltes especulares de "Líquido de neón"
    float spec = pow(noise(fluid_uv * 10.0 - time*2.0), 4.0);
    col += vec3(1.0) * spec * high * 3.0;
    
    fragColor = vec4(col, 1.0);
}
'''

# --- JOYA 3: NUCLEO ORGANICO (RAYTRACED SUBSURFACE SCATTERING) ---
ORGANIC_CORE_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, pan, beat_hit;
uniform vec3 colorA, colorB;

mat2 rot(float a) { float s=sin(a), c=cos(a); return mat2(c,-s,s,c); }

float smin( float a, float b, float k ) {
    float h = clamp( 0.5+0.5*(b-a)/k, 0.0, 1.0 );
    return mix( b, a, h ) - k*h*(1.0-h);
}

float map(vec3 p) {
    p.xy *= rot(time * 0.2);
    p.xz *= rot(time * 0.3 + pan);
    
    // Estructura orgánica (Corazón o Medusa de luz)
    float d1 = length(p) - 1.5; // Esfera central
    
    // Tentáculos o venas que pulsan con el bajo y el latido
    vec3 q = p;
    q.x += sin(q.y * 5.0 + time * 3.0) * 0.2 * (bass + beat_hit);
    q.z += cos(q.y * 4.0 - time * 2.0) * 0.2 * (bass + beat_hit);
    
    float d2 = length(vec2(length(q.xz) - 0.5, q.y)) - 0.2 - mid*0.2; 
    float d3 = length(vec2(length(q.xy) - 1.0, q.z)) - 0.1 - high*0.1;
    
    float obj = smin(d1, d2, 0.8);
    obj = smin(obj, d3, 0.5);
    
    // Deformación de superficie para parecer tejido/cera
    obj += sin(p.x * 10.0) * sin(p.y * 10.0) * sin(p.z * 10.0) * 0.05;
    return obj;
}

// Monte Carlo Approximation para Subsurface Scattering
float calcSSS(vec3 p, vec3 n, vec3 l) {
    float sss = 0.0;
    float weight = 1.0;
    // Trazamos rayos hacia ADENTRO del objeto
    for(int i = 1; i <= 5; i++) {
        float d = float(i) * 0.15; // Qué tan profundo entra la luz
        float dist = map(p - n * d);
        sss += (d - dist) * weight;
        weight *= 0.5; // Decaimiento exponencial de la luz interna
    }
    return clamp(1.0 - sss * 2.0, 0.0, 1.0); // Transmitancia interna
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    vec3 ro = vec3(0.0, 0.0, -4.0 - bass);
    vec3 rd = normalize(vec3(p, 1.0));
    
    float t = 0.0;
    vec3 col = vec3(0.02); // Fondo oscuro
    
    for(int i = 0; i < 80; i++) {
        vec3 pos = ro + rd * t;
        float d = map(pos);
        if(d < 0.001) {
            vec2 e = vec2(0.001, 0.0);
            vec3 n = normalize(vec3(
                map(pos + e.xyy) - map(pos - e.xyy),
                map(pos + e.yxy) - map(pos - e.yxy),
                map(pos + e.yyx) - map(pos - e.yyx)
            ));
            
            vec3 lig = normalize(vec3(1.0, 1.0, -1.0));
            
            // Difusa clásica
            float dif = max(dot(n, lig), 0.0);
            
            // Subsurface Scattering (Luz que penetra la "piel")
            float sss = calcSSS(pos, n, lig);
            
            // Color de la superficie
            vec3 base = mix(vec3(0.1, 0.05, 0.0), colorA, 0.2); 
            
            // Color de la luz interna (brilla fuerte con el audio)
            vec3 glow = colorB * sss * (1.5 + bass * 2.0 + beat_hit * 3.0);
            
            // Fresnel (Bordes brillantes de tejido)
            float fre = pow(1.0 - max(dot(n, -rd), 0.0), 3.0);
            
            col = base * dif + glow + colorA * fre * (high + beat_hit);
            break;
        }
        t += d;
        if(t > 15.0) break;
    }
    
    fragColor = vec4(col, 1.0);
}
'''

# --- JOYA 4: TURING PATTERNS (REACTION-DIFFUSION BIOLUMINISCENTE) ---
TURING_PATTERNS_FS = '''
#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, beat_hit;
uniform vec3 colorA, colorB;

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    
    // Deformación de espacio celular
    float r = length(p);
    float a = atan(p.y, p.x);
    
    // Simulación pseudo-Reaction-Diffusion usando capas senoidales anidadas
    float v = 0.0;
    vec2 pos = p * (3.0 + mid * 2.0);
    
    for(int i=0; i<6; i++) {
        float t = time * 0.2 + float(i) * 1.5;
        pos.x += sin(pos.y * 2.0 + t) * 0.5 * (1.0 + bass);
        pos.y += cos(pos.x * 2.0 - t) * 0.5 * (1.0 + bass);
        v += sin(pos.x * 4.0) * cos(pos.y * 4.0);
        pos *= 1.3;
    }
    
    // Umbral de Turing (Puntos vs Rayas)
    float pattern = smoothstep(0.0, 0.2, v);
    
    // Contorno Bioluminiscente
    float edge = smoothstep(0.1, 0.0, abs(v));
    
    // Explosión de células en el beat
    float shock = beat_hit * smoothstep(0.8, 0.0, r);
    
    vec3 col = mix(vec3(0.05, 0.0, 0.1), colorA, pattern);
    col += colorB * edge * (2.0 + high * 4.0 + shock * 5.0);
    
    fragColor = vec4(col, 1.0);
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
uniform float breath;            // Lens Breathing: 0.0-1.0 energia acumulada
uniform float beat_hit;          // Sincronización rítmica (1.0 en el golpe exacto, decae suavemente)

// ACES Tone Mapping
vec3 ACESFilm(vec3 x) {
    float a=2.51, b=0.03, c=2.43, d=0.59, e=0.14;
    return clamp((x*(a*x+b))/(x*(c*x+d)+e), 0.0, 1.0);
}
float hash2(vec2 p) { p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }

void main() {
    vec2 st = uv;

    // ── Lens Breathing (micro-zoom organico reactivo al audio) ──────────────────
    // Simula el micro-zoom que produce un lente real al cambiar el plano de enfoque
    float breathZoom = 1.0 + breath * 0.012;
    float zoom = (1.0 + ken_burns_t * 0.08) * breathZoom;
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
    vec3 col = mix(base, base * 0.4 + overlay, alpha_ov);  // Imagen AI visible bajo el overlay
    col += bloom;                                            // Aura luminosa del overlay

    // Tinte global del overlay sobre el fondo (colores del GLSL tiñen sutilmente la imagen)
    col = mix(col, col * (0.6 + overlay * 0.5), 0.3 * alpha_ov);
    
    // ── Hollywood Grade Post-Processing (Bloom + Chromatic Aberration Rítmica) ──
    // Flash de aberración cromática en el golpe del beat
    float beat_aberration = beat_hit * 0.05 * length(dir);
    if (beat_hit > 0.0) {
        vec3 col_ab;
        col_ab.r = mix(base1, base2, transition_t).r; // Fallback simple para el rojo desplazado
        col_ab.g = col.g;
        col_ab.b = texture(tex_base, kb_uv - dir * beat_aberration).b; 
        col = mix(col, col_ab, beat_hit * 0.8);
        
        // Destello de exposición cinematográfica (Flash cut)
        col += vec3(beat_hit * 0.15); 
    }
    
    // Viñeta óptica profunda
    float vignette = 1.0 - dot(dir, dir) * 1.5;
    col *= smoothstep(0.0, 0.5, vignette);

    // ── Camera shake & Cyber Glitch en beat drops ────────────────────────────
    if (bass > 0.85 || beat_hit > 0.8) {
        float shake = max((bass - 0.85) * 0.025, beat_hit * 0.015);
        vec2 shakeUV = kb_uv + vec2(sin(time * 50.0) * shake, cos(time * 47.0) * shake);
        
        // Digital Glitch (Desplazamiento horizontal de scanlines)
        float glitchLine = step(0.9, fract(st.y * 20.0 + time * 15.0));
        float glitchShift = max((bass - 0.85) * 0.15, beat_hit * 0.1) * glitchLine * sin(time * 120.0);
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

    // ── ACES Tone Mapping + Halation (resplandor fotoquímico en halos altos) ──────
    // Halation: zonas de alta luminosidad emiten un halo rojizo-ananaranjado
    float luma_col = dot(col, vec3(0.299, 0.587, 0.114));
    float halation = smoothstep(0.6, 1.0, luma_col) * (0.15 + breath * 0.1);
    col += vec3(halation * 0.9, halation * 0.3, halation * 0.05); // Halo rojo-calido
    
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
    vec3 z = pos; float dr = 1.0; float r = 0.0;
    for (int i = 0; i < 12; i++) {
        r = length(z); if (r > 2.0) break;
        float theta = acos(z.z / r); float phi = atan(z.y, z.x);
        dr = pow(r, 7.0) * 8.0 * dr + 1.0; float zr = pow(r, 8.0);
        theta = theta * 8.0; phi = phi * 8.0;
        z = zr * vec3(sin(theta)*cos(phi), sin(phi)*sin(theta), cos(theta)); z += pos;
    }
    return 0.5 * log(r) * r / dr;
}
vec3 calcNormal(vec3 pos) {
    vec2 e = vec2(1.0,-1.0)*0.5773*0.001;
    return normalize( e.xyy*mandelbulbSDF(pos+e.xyy)+e.yyx*mandelbulbSDF(pos+e.yyx)+e.yxy*mandelbulbSDF(pos+e.yxy)+e.xxx*mandelbulbSDF(pos+e.xxx) );
}
void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    // === SHOT MACHINE (MANDELBULB) ===
    float shotDur = 8.0;
    float cycleT  = mod(time, shotDur * 3.0);
    int   shotIdx = int(cycleT / shotDur);
    float shotT   = smoothstep(0.0, 1.0, fract(cycleT / shotDur));
    vec3 ro; float fov = 1.0;
    if (shotIdx == 0) {
        ro = vec3(0.0, 0.0, -2.5 - sin(time*0.08)*0.4);
        pR(ro.xz, time * 0.08 + pan); pR(ro.xy, time * 0.04);
    } else if (shotIdx == 1) {
        ro = vec3(sin(time*0.1)*0.5, cos(time*0.07)*0.3, mix(-2.5, -1.8, shotT));
        pR(ro.xz, pan * 0.5);
        fov = mix(1.0, 1.3, shotT);
    } else {
        ro = vec3(mix(-0.5, 0.5, shotT), 0.0, -2.2);
        pR(ro.xz, time * 0.05 + pan);
    }
    float shakeAmt = max(0.0, bass - 0.75) * 0.02;
    ro += vec3(sin(time*47.0), cos(time*43.0), 0.0) * shakeAmt;
    vec3 ww = normalize(-ro); vec3 uu = normalize(cross(ww, vec3(0.0,1.0,0.0))); vec3 vv = normalize(cross(uu, ww));
    vec3 rd = normalize(p.x * uu + p.y * vv + fov * ww);
    float t = 0.0; float max_d = 10.0; float trap = 1.0;
    for(int i=0; i<80; i++) {
        vec3 pos = ro + rd*t; float d = mandelbulbSDF(pos); trap = min(trap, d);
        if(d<0.001 || t>max_d) break; t += d;
    }
    vec3 col = colorA * 0.05;
    if(t<max_d) {
        vec3 pos = ro + rd*t; vec3 nor = calcNormal(pos); vec3 lig = normalize(vec3(1.0,1.0,-1.0));
        float dif = clamp(dot(nor, lig), 0.0, 1.0);
        float spe = pow(clamp(dot(reflect(rd,nor), lig), 0.0, 1.0), 32.0);
        float sss = smoothstep(0.0, 1.0, mandelbulbSDF(pos + lig * 0.2)) * 0.5;
        col = mix(colorA, colorB, length(pos)/1.5);
        col *= dif * 0.8 + 0.2; col += spe * (0.5 + high * 2.0); col += colorA * sss;
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
    vec2 uv2 = (i.xy+vec2(37.0,17.0)*i.z) + f.xy;
    vec2 rg = fract(sin((uv2+0.5)*0.014)*292.0); return mix(rg.x, rg.y, f.z);
}
float mapNebula(vec3 p) {
    float f = 0.0; vec3 q = p - vec3(0.0, 0.0, time*2.0);
    f += 0.5000*noise(q); q=q*2.01; f += 0.2500*noise(q); q=q*2.02; f += 0.1250*noise(q); q=q*2.03; f += 0.0625*noise(q);
    return f - 0.5;
}
void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    // === SHOT MACHINE (NEBULA) ===
    float shotDur = 9.0;
    float cycleT  = mod(time, shotDur * 2.0);
    int   shotIdx = int(cycleT / shotDur);
    float shotT   = smoothstep(0.0, 1.0, fract(cycleT / shotDur));
    vec3 ro = vec3(0.0, 0.0, 0.0);
    if (shotIdx == 0) {
        pR(ro.xy, pan * 0.5 + time * 0.02);
    } else {
        ro = vec3(sin(time*0.05)*0.3, cos(time*0.04)*0.2, 0.0);
        pR(ro.xy, pan * 0.3);
    }
    vec3 rd = normalize(vec3(p.x, p.y, 1.0));
    pR(rd.xy, sin(time*0.15)*0.3 + shotT * 0.1);
    float t = 0.0; vec4 sum = vec4(0.0);
    for(int i=0; i<60; i++) {
        vec3 pos = ro + rd*t; float den = mapNebula(pos);
        if(den > 0.01) {
            vec3 col = mix(colorA, colorB, clamp(den*2.0, 0.0, 1.0));
            col *= mix(1.0, 2.5, bass); col += high * colorB * 0.8;
            float sh = clamp(mapNebula(pos + normalize(vec3(1.0,1.0,-1.0))*0.3), 0.0, 1.0);
            col *= 1.0 - sh * 0.5;
            vec4 src = vec4(col * den, den); src.rgb *= src.a; sum = sum + src*(1.0 - sum.a);
        }
        if(sum.a > 0.99) break;
        t += 0.08 + bass*0.05;
    }
    fragColor = vec4(sum.rgb, 1.0);
}'''

GALAXY_SYSTEM_FS = '''#version 330
out vec4 fragColor; in vec2 uv; uniform vec2 resolution; uniform float time, bass, mid, high, pan; uniform vec3 colorA, colorB; uniform int pose;

mat2 rot(float a) { float s = sin(a), c = cos(a); return mat2(c, s, -s, c); }
void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); }

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    
    // Configuración Star Nest inspirada en el legendario shader de Pablo Andrioli (Kali)
    int iterations = 17; // Detalle del fractal
    float formuparam = 0.53; // Constante mágica de pliegue espacial
    int volsteps = 20; // Capas volumétricas de raymarching
    float stepsize = 0.1; // Distancia entre capas
    float zoom = 0.8;
    float tile = 0.85;
    float brightness = 0.0015;
    float darkmatter = 0.3;
    float distfading = 0.73;
    float saturation = 0.85;
    
    // Cinematografía: Vuelo Épico, Suave y Limpio
    float t_time = time * 0.1 + bass * 0.05;
    vec3 ro = vec3(0.0, 0.0, -t_time); // Vuelo incesante por la galaxia
    
    // Shake interactivo de nave muy suave (sin marear)
    float shake = max(0.0, bass - 0.7) * 0.02;
    ro.x += sin(time * 5.0) * shake;
    ro.y += cos(time * 4.0) * shake;
    
    vec3 ww = normalize(vec3(0.0, 0.0, 1.0)); 
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = normalize(cross(uu, ww));
    vec3 rd = normalize(p.x * uu + p.y * vv + zoom * ww);
    
    // Rotación suave e inercial del viaje
    pR(rd.xy, sin(time * 0.05) * 0.3 + pan);
    pR(rd.xz, cos(time * 0.03) * 0.2);
    
    vec3 v = vec3(0.0);
    float s = 0.1;
    float fade = 1.0;
    
    // Raymarching Volumétrico Fractal (La Magia)
    for (int r = 0; r < volsteps; r++) {
        vec3 pos = ro + s * rd * 0.5;
        pos = abs(vec3(tile) - mod(pos, vec3(tile * 2.0))); // Tiling cósmico para infinidad
        
        float a = 0.0, pa = 0.0;
        for (int i = 0; i < iterations; i++) {
            pos = abs(pos) / dot(pos, pos) - formuparam;
            // Damping rítmico para animar el gas con las frecuencias altas
            pos *= 1.0 - (high * 0.015); 
            a += abs(length(pos) - pa);
            pa = length(pos);
        }
        
        float dm = max(0.0, darkmatter - a * a * 0.001); // Materia oscura
        a *= a * a; // Contraste estelar
        
        if (r > 6) fade *= 1.0 - dm;
        
        // Coloreado usando la paleta dinámica de la canción
        vec3 stepCol = mix(colorB, colorA, fract(float(r)*0.1 + time*0.05));
        stepCol = mix(stepCol, vec3(1.0, 0.9, 0.8), 0.2); // Añadir brillo estelar cálido
        
        v += fade;
        v += stepCol * a * brightness * fade * (1.0 + bass * 1.5);
        
        fade *= distfading;
        s += stepsize;
    }
    
    // Ajuste de saturación
    v = mix(vec3(length(v)), v, saturation);
    
    // Añadir un sutil destello volumétrico en el centro de la visión
    float glow = max(0.0, 1.0 - length(p)) * 0.2 * bass;
    v += colorA * glow;
    
    // Tone mapping de cine para retención de reflejos (ACES-like)
    v = (v * (2.51 * v + 0.03)) / (v * (2.43 * v + 0.59) + 0.14);
    
    fragColor = vec4(v, 1.0);
}
'''

OCEANIC_FS = '''#version 330
out vec4 fragColor; in vec2 uv; uniform vec2 resolution; uniform float time, bass, mid, high, pan; uniform vec3 colorA, colorB; uniform int pose;

mat2 rot(float a) { float s = sin(a), c = cos(a); return mat2(c, s, -s, c); }
float hash(vec2 p) { return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453123); }
float noise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    vec2 u = f*f*(3.0-2.0*f);
    return mix(mix(hash(i+vec2(0.,0.)), hash(i+vec2(1.,0.)), u.x),
               mix(hash(i+vec2(0.,1.)), hash(i+vec2(1.,1.)), u.x), u.y);
}
float sea_octave(vec2 uv, float choppy) {
    uv += noise(uv);        
    vec2 wv = 1.0 - abs(sin(uv));
    vec2 swv = abs(cos(uv));    
    wv = mix(wv, swv, wv);
    return pow(1.0 - pow(wv.x * wv.y, 0.65), choppy);
}
float map(vec3 p) {
    float freq = 0.16;
    float amp = 0.6 + bass * 0.4;
    float choppy = 4.0;
    vec2 uv = p.xz; uv.x *= 0.75;
    float d = 0.0, h = 0.0;    
    for(int i = 0; i < 4; i++) {        
        d = sea_octave((uv + time * 0.5)*freq, choppy);
        d += sea_octave((uv - time * 0.5)*freq, choppy);
        h += d * amp;        
        uv *= rot(1.6); freq *= 1.9; amp *= 0.22;
        choppy = mix(choppy, 1.0, 0.2);
    }
    return p.y - h;
}
vec3 getNormal(vec3 p, float eps) {
    vec3 n; n.y = map(p);    
    n.x = map(p + vec3(eps, 0, 0)) - n.y;
    n.z = map(p + vec3(0, 0, eps)) - n.y;
    n.y = eps; return normalize(n);
}
void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    vec3 ro = vec3(0.0, 2.5 + bass*1.5, time * 3.0);
    ro.y += sin(time*0.5)*0.5;
    vec3 rd = normalize(vec3(p.x, p.y - 0.2, 1.0));
    rd.xz *= rot(sin(time*0.1)*0.1 + pan);
    float t = 0.0, tMax = 50.0;
    for(int i = 0; i < 50; i++) {
        vec3 pos = ro + rd * t;
        float h = map(pos);
        if(h < 0.01 || t > tMax) break;
        t += h * 0.9;
    }
    vec3 skyColor = mix(colorB, colorA, clamp(rd.y*1.5, 0.0, 1.0));
    skyColor += vec3(1.0, 0.8, 0.4) * pow(max(0.0, dot(rd, normalize(vec3(0.0, 0.1, 1.0)))), 8.0) * (0.5 + bass*0.5);
    vec3 col = skyColor;
    if(t < tMax) {
        vec3 pos = ro + rd * t;
        vec3 n = getNormal(pos, 0.01);
        vec3 ref = reflect(rd, n);
        vec3 waterCol = mix(colorA * 0.1, colorB * 0.3, clamp(n.y, 0.0, 1.0));
        waterCol *= 1.0 + high * 0.5;
        float fresnel = clamp(1.0 - dot(n, -rd), 0.0, 1.0);
        fresnel = pow(fresnel, 3.0);
        vec3 reflectedSky = mix(colorB, colorA, clamp(ref.y*1.5, 0.0, 1.0));
        col = mix(waterCol, reflectedSky, fresnel);
        col = mix(col, skyColor, smoothstep(15.0, tMax, t));
    }
    col = (col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14);
    fragColor = vec4(col, 1.0);
}
'''


PROTEAN_FS = '''#version 330
out vec4 fragColor; in vec2 uv; uniform vec2 resolution; uniform float time, bass, mid, high, pan; uniform vec3 colorA, colorB; uniform int pose;

mat2 rot(float a) { float s = sin(a), c = cos(a); return mat2(c, s, -s, c); }
float hash(vec3 p) {
    p = fract(p * vec3(127.1, 311.7, 74.7));
    p += dot(p, p + 19.19);
    return fract(p.x * p.y * p.z);
}
float noise(vec3 x) {
    vec3 p = floor(x), f = fract(x);
    f = f*f*(3.0-2.0*f);
    return mix(mix(mix(hash(p+vec3(0,0,0)), hash(p+vec3(1,0,0)),f.x),
                   mix(hash(p+vec3(0,1,0)), hash(p+vec3(1,1,0)),f.x),f.y),
               mix(mix(hash(p+vec3(0,0,1)), hash(p+vec3(1,0,1)),f.x),
                   mix(hash(p+vec3(0,1,1)), hash(p+vec3(1,1,1)),f.x),f.y),f.z);
}

mat3 m3 = mat3(0.33338, 0.56034, -0.71817, -0.87887, 0.32625, -0.15323, 0.15162, 0.69596, 0.69532)*2.0;

float map(vec3 p) {
    vec3 q = p;
    q.z += time * 0.5; // Viento moviendo las nubes hacia adelante
    float f = 0.5000*noise(q); q = m3*q;
    f += 0.2500*noise(q); q = m3*q;
    f += 0.1250*noise(q); q = m3*q;
    f += 0.0625*noise(q); q = m3*q;
    f += 0.03125*noise(q);
    
    // Crear un cañón/cielo de nubes infinito en Y (piso y techo)
    float d = 2.0 - abs(p.y); 
    // Distorsionar el espacio con el ruido FBM rotado
    float den = d - (1.0 - f)*3.0;
    
    // Turbulencia volumétrica reactiva al bajo
    den += (bass * 0.4) * noise(p * 3.0);
    
    return clamp(den, 0.0, 1.0);
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    
    // Vuelo de cámara cinematográfico dentro del cañón de nubes
    vec3 ro = vec3(0.0, 0.0, time * 3.0);
    ro.x += sin(time*0.5)*0.5; // Movimiento de cámara sutil
    ro.y += cos(time*0.3)*0.5;
    
    vec3 rd = normalize(vec3(p.x, p.y, 1.5)); // Lente de 35mm
    rd.xy *= rot(sin(time*0.2)*0.1 + pan);
    rd.xz *= rot(sin(time*0.1)*0.1);
    
    vec3 col = vec3(0.0);
    float t = 0.0, density = 0.0;
    vec3 lightDir = normalize(vec3(1.0, 0.8, 0.5));
    
    for(int i=0; i<80; i++) {
        vec3 pos = ro + rd * t;
        float den = map(pos);
        if(den > 0.01) {
            // Derivada direccional para iluminación "Silver Lining" e iluminacion volumétrica real
            float sh = map(pos + lightDir * 0.15); 
            float dif = clamp((den - sh) / 0.15, 0.0, 1.0);
            
            vec3 cloudColor = mix(colorB, colorA, den);
            
            // Iluminación (Ambiente + Sol interactivo)
            vec3 lin = vec3(0.4, 0.4, 0.5) * 1.0; 
            lin += vec3(1.0, 0.9, 0.7) * dif * (2.0 + high*2.5); // Relámpagos estelares en altos
            
            cloudColor *= lin;
            
            float alpha = den * 0.06 * (1.0 - density);
            col += cloudColor * alpha;
            density += alpha;
        }
        if(density > 0.99) break;
        t += max(0.05, 0.15 - den*0.1); // Dynamic step size
    }
    
    // Cielo de fondo
    vec3 sky = mix(colorB * 0.1, colorA * 0.4, clamp(rd.y*0.5 + 0.5, 0.0, 1.0));
    float sun = clamp(dot(rd, lightDir), 0.0, 1.0);
    sky += colorA * pow(sun, 16.0) * (1.0 + bass);
    
    col += sky * (1.0 - density);
    
    // ACES Tone mapping cinematográfico
    col = (col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14);
    
    // Viñeteado de lente
    col *= 1.0 - 0.4 * dot(p,p);
    
    fragColor = vec4(col, 1.0);
}
'''


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


def render_v13_video(timeline: list, multiband: dict, colorsA: np.ndarray,
                     colorsB: np.ndarray, w: int, h: int, fps: int,
                     out_mp4: str, audio_path: str,
                     speed_multiplier=1.0, turbulence=1.0,
                     background_images: list = None,
                     subtitle_file: str = None):
    """
    Renderiza el video V13 — AI-First Cinematic Pipeline V17.
    Incluye: GALAXY_SYSTEM_FS, Shot Machine, Motion Blur temporal, Lens Breathing, Halation, Subtítulos ASS integrados.
    """
    ctx = moderngl.create_context(standalone=True)

    engines = {
        "space_odyssey": ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=SPACE_ODYSSEY_FS),
        "interstellar":  ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=INTERSTELLAR_FS),
        "inception_kifs": ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=KIFS_FS),
        "neon_fluid":     ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=NEON_FLUID_FS),
        "organic_core":   ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=ORGANIC_CORE_FS),
        "turing_patterns": ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=TURING_PATTERNS_FS),
        "julia_fractal":  ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=JULIA_FS),
        "mandelbulb":     ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=MANDELBULB_FS),
        "nebula":         ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=NEBULA_FS),
        "quantum_tunnel": ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=QUANTUM_TUNNEL_FS),
        "galaxy_system":  ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=GALAXY_SYSTEM_FS),
        "oceanic":        ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=OCEANIC_FS),
        "protean":        ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=PROTEAN_FS),
    }

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
                    "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "18",
                    "-c:a", "aac", "-b:a", "192k", "-shortest"])
    else:
        cmd.extend(["-vf", vf_chain, "-c:v", "libx264", "-pix_fmt", "yuv420p",
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
            accumulated = None

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
                fbo.use(); ctx.clear(0.0, 0.0, 0.0)
                vaos[engine_name].render(moderngl.TRIANGLE_STRIP)

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

                sub = np.frombuffer(fbo_final.read(components=3), dtype=np.uint8).astype(np.float32)
                accumulated = sub if accumulated is None else accumulated + sub

            # Promedio → Motion Blur final
            img_array = np.clip(accumulated / N_BLUR, 0, 255).astype(np.uint8)
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


