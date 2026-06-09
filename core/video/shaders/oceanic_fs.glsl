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
