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
