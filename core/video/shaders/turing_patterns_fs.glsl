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
