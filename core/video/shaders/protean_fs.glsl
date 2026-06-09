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
