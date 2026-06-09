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
