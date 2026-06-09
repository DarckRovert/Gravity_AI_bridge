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
    
    // === CINEMATIC SHOT MACHINE (BLACK HOLE) ===
    float shotDur = 7.0;
    float cycleT  = mod(time, shotDur * 4.0);
    int   shotIdx = int(cycleT / shotDur);
    float shotT   = smoothstep(0.0, 1.0, fract(cycleT / shotDur));
    
    vec3 ro;
    vec3 ta = vec3(0.0, 0.0, 0.0);
    float fov = 1.5;
    
    if (shotIdx == 0) {
        // ESTABLISHING: Órbita media clásica
        float angle = time * 0.1 + pan * 0.5;
        ro = vec3(sin(angle) * 6.0, 1.2 + sin(time*0.2)*0.5, cos(angle) * 6.0);
    } else if (shotIdx == 1) {
        // TOP-DOWN: Picado cenital vertiginoso hacia el horizonte
        float angle = time * 0.15 + pan;
        float height = mix(8.0, 2.5, shotT);
        ro = vec3(sin(angle) * 2.0, height, cos(angle) * 2.0);
        fov = mix(1.2, 1.8, shotT);
    } else if (shotIdx == 2) {
        // CLOSE-UP EXTREMO: Rozando el disco de acreción
        float angle = time * 0.05 + pan * 0.3;
        ro = vec3(sin(angle) * 2.5, 0.1 + sin(time*0.1)*0.2, cos(angle) * 2.5);
        ta = vec3(0.0, -0.2, 0.0);
        fov = 1.6;
    } else {
        // FLYBY: Vuelo rápido ecuatorial
        float flyT = shotT;
        float x = mix(-8.0, 8.0, flyT);
        ro = vec3(x, 0.5 + sin(flyT*3.14)*0.5, -3.0 + sin(flyT*3.14)*-1.5);
        ta = vec3(0.0, 0.0, 0.0) + vec3(sin(flyT*2.0), 0.0, 0.0);
    }
    
    // Temblor de Ondas Gravitacionales
    float shakeAmt = max(0.0, bass - 0.75) * 0.05;
    ro += vec3(sin(time*47.0), cos(time*43.0), sin(time*51.0)) * shakeAmt;
    
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = normalize(cross(uu, ww));
    vec3 rd = normalize(p.x*uu + p.y*vv + fov*ww);
    
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
