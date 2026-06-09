out vec4 fragColor; in vec2 uv; uniform vec2 resolution; uniform float time, bass, mid, high, pan; uniform vec3 colorA, colorB; uniform int pose;
uniform sampler2D tex_stone; // [V5] PBR Texture

mat2 rot(float a) { float s = sin(a), c = cos(a); return mat2(c, s, -s, c); }
float hash(float n) { return fract(sin(n) * 43758.5453123); }

// Retenemos el ruido solo para la forma del SDF (no para color)
float noise(vec3 x) {
    vec3 p = floor(x); vec3 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    float n = p.x + p.y * 57.0 + 113.0 * p.z;
    return mix(mix(mix(hash(n + 0.0), hash(n + 1.0), f.x), mix(hash(n + 57.0), hash(n + 58.0), f.x), f.y),
               mix(mix(hash(n + 113.0), hash(n + 114.0), f.x), mix(hash(n + 170.0), hash(n + 171.0), f.x), f.y), f.z);
}
float fbm(vec3 p) {
    float f = 0.0; float a = 0.5;
    for(int i = 0; i < 4; i++) {
        f += a * noise(p); p *= 2.02; a *= 0.5;
    }
    return f;
}

// Ridged Multifractal Noise para montañas andinas afiladas
float ridged_noise(vec3 p) {
    float f = 0.0;
    float a = 0.5;
    for(int i = 0; i < 5; i++) {
        float n = abs(noise(p));
        n = 1.0 - n;
        f += a * (n * n);
        p *= 2.02; a *= 0.5;
    }
    return f;
}

float smin(float a, float b, float k) {
    float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
    return mix(b, a, h) - k * h * (1.0 - h);
}
float sdBox(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
}
float sdCylinder(vec3 p, vec2 h) {
    vec2 d = abs(vec2(length(p.xz), p.y)) - h;
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));
}

vec2 map(vec3 p) {
    vec2 res = vec2(p.y + 3.0, 1.0); 
    
    vec3 mp = p; mp.z -= 40.0; 
    float mountain = mp.y + 5.0 - 25.0 * exp(-0.01 * (mp.x*mp.x + mp.z*mp.z));
    // Montañas afiladas y escarpadas usando Ridged Noise
    mountain -= ridged_noise(mp * 0.15) * 20.0; 
    if(mountain < res.x) res = vec2(mountain, 1.0);
    
    float terraces = 1e10;
    // Curvatura orgánica del dominio espacial para que los andenes abracen el valle
    vec3 tp = p;
    tp.x += sin(tp.z * 0.05) * 15.0; 
    for(int i=0; i<6; i++) {
        float fi = float(i);
        float h = fi * 4.5; 
        float z = 15.0 - (fi * 5.0); 
        float width = 80.0 - fi * 12.0; 
        terraces = min(terraces, sdBox(tp - vec3(0.0, h - 5.0, z), vec3(width, 2.5, 6.0)));
    }
    terraces -= fbm(p * 0.5) * 0.5; 
    
    float stairs = 1e10;
    vec3 sp = p; sp.x = abs(sp.x) - 10.0; 
    for(int i=0; i<40; i++) {
        float h = float(i) * 0.5625; 
        float z = 15.0 - float(i) * 0.625; 
        stairs = min(stairs, sdBox(sp - vec3(0.0, h - 5.0, z), vec3(2.0, 0.25, 0.6)));
    }
    
    float city_base = smin(terraces, stairs, 0.5);
    if(city_base < res.x) res = vec2(city_base, 2.0); 
    
    // Río Sagrado (Urubamba) en el fondo del valle
    float river = p.y + 2.0; // Plano de agua
    if (river < res.x) res = vec2(river, 5.0);
    
    // Chacana gigante y monumental al fondo del valle (Fija, sin saltos de graves)
    vec3 cp = p - vec3(0.0, 20.0, -60.0);
    cp.xz *= rot(time * 0.2); 
    // Escala gigante para la Cruz Escalonada
    float b1 = sdBox(cp, vec3(12.0, 4.0, 2.0)); // Barra ancha
    float b2 = sdBox(cp, vec3(4.0, 12.0, 2.0)); // Barra alta
    float b3 = sdBox(cp, vec3(8.0, 8.0, 2.0)); // Cuadro medio
    float chacana = min(b1, min(b2, b3));
    chacana = max(chacana, -sdCylinder(cp.yxz, vec2(3.0, 4.0))); // Agujero
    if(chacana < res.x) res = vec2(chacana, 4.0);
    
    return res;
}

vec3 getNormal(vec3 p) {
    vec2 e = vec2(0.01, 0.0);
    return normalize(vec3(
        map(p + e.xyy).x - map(p - e.xyy).x,
        map(p + e.yxy).x - map(p - e.yxy).x,
        map(p + e.yyx).x - map(p - e.yyx).x
    ));
}

float softshadow( in vec3 ro, in vec3 rd, in float mint, in float tmax, in float k ) {
    float res = 1.0; float t = mint;
    for( int i=0; i<32; i++ ) {
        float h = map( ro + rd*t ).x;
        res = min( res, k*h/t );
        t += clamp( h, 0.05, 0.50 );
        if( res<0.005 || t>tmax ) break;
    }
    return clamp( res, 0.0, 1.0 );
}

float ambientOcclusion(vec3 p, vec3 n) {
    float occ = 0.0; float sca = 1.0;
    for(int i = 0; i < 5; i++) {
        float h = 0.01 + 0.15 * float(i)/4.0;
        float d = map(p + h * n).x;
        occ += (h - d) * sca;
        sca *= 0.95;
    }
    return clamp(1.0 - 1.5 * occ, 0.0, 1.0);
}

// [V5] Triplanar Mapping
vec3 triplanar(sampler2D tex, vec3 p, vec3 n) {
    vec3 w = abs(n);
    w = max(w - 0.2, 0.0);
    w /= dot(w, vec3(1.0));
    vec3 tx = texture(tex, p.yz * 0.2).rgb;
    vec3 ty = texture(tex, p.xz * 0.2).rgb;
    vec3 tz = texture(tex, p.xy * 0.2).rgb;
    return tx*w.x + ty*w.y + tz*w.z;
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    
    // Vuelo de Dron en PLANO SECUENCIA:
    // Sin cortes ni saltos hacia atrás. Un solo viaje suave de 180 segundos.
    float t_fase = clamp(time / 180.0, 0.0, 1.0); 
    
    // Ruta panorámica óptima, suave y majestuosa
    float cx = mix(60.0, 0.0, smoothstep(0.0, 0.8, t_fase));
    float cy = mix(80.0, 20.0, smoothstep(0.0, 1.0, t_fase));
    float cz = mix(150.0, -40.0, t_fase);
    
    vec3 ro = vec3(cx, cy, cz);
    
    // Mirada guiada: empieza mirando al valle y termina admirando la Chacana
    float look_y = mix(-10.0, 20.0, smoothstep(0.2, 0.9, t_fase));
    float look_z = mix(0.0, -60.0, smoothstep(0.0, 0.8, t_fase));
    vec3 target = vec3(0.0, look_y, look_z);
    
    vec3 cw = normalize(target - ro);
    vec3 cu = normalize(cross(cw, vec3(0.0, 1.0, 0.0)));
    vec3 cv = normalize(cross(cu, cw));
    vec3 rd = normalize(p.x*cu + p.y*cv + 1.2*cw);
    
    float t = 0.0; float tMax = 150.0;
    float mat_id = 0.0;
    float volumetric = 0.0; 
    
    vec3 sunDir = normalize(vec3(0.0, 0.05 + sin(time*0.1)*0.05, -1.0));
    
    for(int i = 0; i < 120; i++) {
        vec3 pos = ro + rd * t;
        vec2 res = map(pos);
        if(res.x < 0.01 || t > tMax) { mat_id = res.y; break; }
        
        if (i % 3 == 0) {
             float sha_vol = softshadow(pos, sunDir, 0.05, 10.0, 4.0);
             float fog_density = exp(-pos.y * 0.05) * 0.08;
             volumetric += fog_density * sha_vol * (1.0 + high);
        }
        t += res.x * 0.7; 
    }
    
    // Atardecer Andino Majestuoso (Naranja, Magenta y Dorado)
    vec3 skyCol = mix(vec3(0.9, 0.4, 0.1), vec3(0.3, 0.1, 0.5), clamp(rd.y*4.0 + 0.2, 0.0, 1.0));
    skyCol = mix(skyCol, vec3(1.0, 0.8, 0.4), clamp(rd.y*2.0 - 0.2, 0.0, 1.0));
    
    float sun = clamp(dot(rd, sunDir), 0.0, 1.0);
    skyCol += vec3(1.0, 0.9, 0.6) * pow(sun, 16.0) * (1.0 + bass);
    
    vec3 col = skyCol;
    
    if(t < tMax) {
        vec3 pos = ro + rd * t;
        vec3 n = getNormal(pos);
        
        float dif = clamp(dot(n, sunDir), 0.0, 1.0);
        float sha = softshadow(pos, sunDir, 0.05, 50.0, 12.0);
        float ao = ambientOcclusion(pos, n);
        float amb = 0.5 + 0.5 * n.y;
        
        vec3 objCol;
        
        if (mat_id == 4.0) {
            // Textura PBR de Piedra Antigua (Andesita)
            vec3 texCol = triplanar(tex_stone, pos, n);
            objCol = pow(texCol, vec3(1.2)) * 1.5; 
            
            // Tonalidad cálida de piedra dorada sagrada (Coricancha)
            objCol = mix(objCol, vec3(0.8, 0.7, 0.4), 0.2);
            
            // Coordenadas locales de la Chacana SINCRONIZADAS con su rotación física
            vec3 localPos = pos - vec3(0.0, 20.0, -60.0);
            localPos.xz *= rot(time * 0.2); // IMPORTANTE: Rotar la textura junto con la geometría
            
            float r_sym = length(localPos.xy); 
            // Máscara para que el tallado solo aparezca en las caras planas frontales/traseras (Grosor = 2.0)
            float isFace = smoothstep(1.8, 1.95, abs(localPos.z));
            
            // Diseño de Sol Inca (Inti) esculpido en Oro
            float ang_sym = atan(localPos.y, localPos.x);
            float rayos = sin(ang_sym * 16.0);
            float solInti = smoothstep(0.9, 1.0, rayos) * smoothstep(8.0, 4.0, r_sym);
            float anilloInca = smoothstep(0.2, 0.0, abs(r_sym - 4.0));
            
            float oroInca = max(solInti, anilloInca) * isFace;
            vec3 colorOro = vec3(1.0, 0.8, 0.2) * (1.5 + bass * 2.0); // Oro vibrante interactivo
            
            objCol = mix(objCol, colorOro, oroInca);
            
            // Fuego / Brillo Divino saliendo del agujero central (Ombligo del Mundo)
            float agujeroDivino = smoothstep(4.0, 2.5, r_sym) * isFace;
            objCol += vec3(1.0, 0.4, 0.1) * agujeroDivino * (1.5 + high * 6.0);
            
            // CORRECCIÓN VITAL DE LUZ: Añadir un foco de luz frontal para que la piedra NUNCA se vea negra
            vec3 luzFrontalDivina = normalize(vec3(0.0, 0.5, 1.0));
            float lFront = clamp(dot(n, luzFrontalDivina), 0.0, 1.0);
            
            dif += lFront * 1.5; // Fuerte iluminación directa
            amb += 0.8; // Luz ambiental elevada para resaltar la piedra
            
            dif = clamp(dif, 0.0, 1.5);
        } else {
            // [V5] Triplanar texture mapping. Reemplaza el fbm pesado.
            vec3 texCol = triplanar(tex_stone, pos, n);
            objCol = pow(texCol, vec3(1.2)) * 1.5; 
            
            // Musgo hiper optimizado (solo math basico, no loops)
            float moss_factor = smoothstep(0.4, 0.7, n.y) * texCol.g;
            vec3 mossCol = vec3(0.1, 0.3, 0.05);
            objCol = mix(objCol, mossCol, moss_factor);
        }
        
        vec3 viewDir = normalize(ro - pos);
        vec3 halfV = normalize(sunDir + viewDir);
        float spec = pow(max(dot(n, halfV), 0.0), 16.0);
        
        if (mat_id == 5.0) {
            // Material de Río Sagrado (Agua reflectante)
            vec3 waterCol = vec3(0.1, 0.3, 0.5);
            // Simular olas usando ridged noise
            float waves = fbm(vec3(pos.x * 2.0 - time, 0.0, pos.z * 2.0 - time));
            n.xz += waves * 0.1;
            n = normalize(n);
            
            float fresnel = pow(1.0 - max(dot(n, viewDir), 0.0), 5.0);
            objCol = mix(waterCol, skyCol, fresnel);
            spec = pow(max(dot(n, halfV), 0.0), 64.0) * 2.0;
        }
        
        vec3 lin = vec3(1.5, 1.0, 0.7) * dif * sha; 
        lin += vec3(0.2, 0.3, 0.4) * amb * ao; 
        if (mat_id == 4.0 || mat_id == 2.0) {
            lin += vec3(1.0, 0.9, 0.7) * spec * 0.5; // Micro-specularity para la piedra
        } else if (mat_id == 5.0) {
            lin += vec3(1.0, 0.9, 0.8) * spec * 2.0; // Fuerte brillo especular en el agua
        }
        col = objCol * lin;
        
        // Geoglifos Sagrados proyectados en el valle (Símbolos Incas / Nazca)
        if (mat_id == 1.0 || mat_id == 2.0) {
            float r = length(pos.xz); 
            float ang = atan(pos.z, pos.x);
            
            // 1. Espiral Inca (Representa la Pachamama y los ciclos andinos)
            float espiral = sin(r * 0.2 - ang * 3.0);
            float espiralGlow = smoothstep(0.95, 1.0, espiral);
            
            // 2. Rayos del Sol Inti expandiéndose por la tierra
            float rayos = sin(ang * 24.0);
            float rayosGlow = smoothstep(0.95, 1.0, rayos) * smoothstep(120.0, 30.0, r);
            
            // 3. Anillos concéntricos (Inspirados en las terrazas circulares de Moray)
            float anillos = abs(sin(r * 0.15));
            float anillosGlow = smoothstep(0.05, 0.0, anillos);
            
            // Mezclar los símbolos
            float geoglifo = max(espiralGlow, max(rayosGlow, anillosGlow));
            
            // Difuminar suavemente a la distancia
            geoglifo *= smoothstep(180.0, 20.0, r); 
            
            // Oro Antiguo resplandeciendo en la tierra (reemplaza el cyan alienígena)
            vec3 oroNazca = vec3(1.0, 0.6, 0.1) * geoglifo * (1.5 + bass * 3.0); 
            col += oroNazca * ao * 1.5; 
        }
        
        float fogHeight = exp(-pos.y * 0.1);
        float fogDist = 1.0 - exp(-0.001 * t * t);
        col = mix(col, skyCol, fogDist * fogHeight);
    }
    
    col += vec3(1.0, 0.6, 0.3) * volumetric * 0.08;
    col = (col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14);
    fragColor = vec4(col, 1.0);
}
