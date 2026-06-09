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
