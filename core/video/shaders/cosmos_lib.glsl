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
