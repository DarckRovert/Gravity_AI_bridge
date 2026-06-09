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
