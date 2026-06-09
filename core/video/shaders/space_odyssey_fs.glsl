#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, pan;
uniform vec3 colorA, colorB; uniform int pose;
uniform sampler2D iChannel0;

''' + COSMOS_LIB + '''

void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); }

vec3 cosmosOffset = vec3(0.0, 0.0, -5.0);

vec2 map(vec3 p) {
    float sphere = length(p) - 1.0;
    vec3 dp = p;
    pR(dp.xz, time * 0.5); pR(dp.xy, mid * 0.5);
    float disk = sdTorus(dp, vec2(1.8 + bass*0.5, 0.05 + mid*0.1));
    float world = min(sphere, disk);
    
    float floorDist = p.y + 1.2; 
    world = min(world, floorDist);
    
    vec3 cp = p - cosmosOffset; 
    // Escalar hacia abajo ligeramente si es muy masivo
    cp *= 0.5;
    vec2 cosmicRes = sdCosmos(cp, time, bass, pose);
    cosmicRes.x *= 2.0; // Deshacer la escala en la distancia
    
    if(cosmicRes.x < world) {
        return cosmicRes;
    }
    return vec2(world, 0.0);
}

float softshadow( in vec3 ro, in vec3 rd, in float mint, in float tmax, in float k ) {
    float res = 1.0; float t = mint;
    for( int i=0; i<24; i++ ) {
        float h = map( ro + rd*t ).x;
        res = min( res, k*h/t ); t += clamp( h, 0.02, 0.2 );
        if( res<0.005 || t>tmax ) break;
    }
    return clamp( res, 0.0, 1.0 );
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    vec3 target = vec3(0.0, 0.0, -5.0);
    
    // === SMOOTH CINEMATIC FLIGHT V2 ===
    // Órbita fluida y majestuosa alrededor del cosmos sin cortes abruptos.
    float angle = time * 0.15;
    
    vec3 ro = vec3(
        sin(angle) * 12.0, 
        2.5 + sin(time * 0.08) * 2.0, // Oscilación suave de altura
        cos(angle) * 12.0 - 5.0
    );
    
    float fov = 1.3 + sin(time * 0.1) * 0.2; // Zoom dinámico muy suave
    float focalDist = length(target - ro) * 0.8;
    float camRoll = sin(time * 0.05) * 0.05;
    
    // Bass shake CONTROLADO: solo en beats intensos, amortiguado
    float shakeAmt = max(0.0, bass - 0.75) * 0.03;
    ro += vec3(sin(time * 47.0), cos(time * 43.0), sin(time * 51.0)) * shakeAmt;
    
    // Camera basis con roll narrativo
    vec3 ww = normalize(target - ro);
    vec3 up  = vec3(sin(camRoll), cos(camRoll), 0.0);
    vec3 uu = normalize(cross(ww, up));
    vec3 vv = normalize(cross(uu, ww));
    vec3 rd = normalize(p.x * uu + p.y * vv + fov * ww);
    
    float t = 0.0; float max_d = 20.0; vec3 col = vec3(0.0); vec3 particleCol = vec3(0.0);
    float mat_id = 0.0;
    
    for(int i=0; i<64; i++) {
        vec3 pos = ro + rd*t; vec2 res = map(pos);
        if(res.x<0.001 || t>max_d) { mat_id = res.y; break; }
        t += res.x;
        
        // Partículas Volumétricas
        particleCol += calcVolumetricParticles(pos, time, bass, mid, high);
    }
    
    vec3 lig = normalize(vec3(0.0, 1.0, 2.0)); 
    
    if(t<max_d) {
        vec3 pos = ro + rd*t;
        if(mat_id == 1.0 || mat_id >= 4.0) { 
            // Cosmos: Material SSS + Fresnel + IBL
            vec3 cp = pos - cosmosOffset;
            cp *= 0.5;
            vec3 nor = calcCosmosNormal(cp, time, bass, pose);
            float dif = clamp(dot(nor, lig), 0.0, 1.0);
            float spe = pow(clamp(dot(reflect(rd, nor), lig), 0.0, 1.0), 32.0);
            
            // IBL PBR
            vec3 refDir = reflect(rd, nor);
            vec3 envColor = texture(iChannel0, envMapEquirect(refDir)).rgb;
            
            // Fresnel Cinematográfico
            float fresnel = pow(1.0 - max(dot(nor, -rd), 0.0), 3.0);
            float sss = smoothstep(0.0, 1.0, map(pos + lig * 0.2).x) * 0.5;
            
            col = colorB * 0.15 + (colorB * dif) + spe * vec3(1.0) * high;
            col += envColor * fresnel * 2.0; // Reflejo Real-time del arte de IA
            col += colorA * sss;
            
            // Emisión de materiales cósmicos (Plasma/Energía)
            if (mat_id >= 4.0) col += envColor * 0.5 * (1.0 + bass*2.0); 
        } else if(mat_id == 2.0) { 
            col = vec3(1.0) + colorA * (1.0 + bass*4.0);
        } else if(mat_id == 3.0) {
            // Campo de Plasma: superficie emite luz propia con ruido de movimiento
            vec3 plasmaCol = mix(colorA, colorB, 0.5 + 0.5 * sin(time * 3.0 + pos.x * 5.0));
            float pulse = 0.5 + 0.5 * sin(time * 8.0 + length(pos) * 10.0);
            col = plasmaCol * (1.5 + bass * 2.0) * (0.6 + pulse * 0.4);
            col += vec3(1.0) * high * 0.5; // Destello blanco en altos
        } else {
            if(length(pos)<1.01 && pos.y > -1.0) col = vec3(0.0);
            else if(pos.y > -1.0) col = mix(colorA, colorB, length(pos.xz)/3.0);
            else {
                float grid = sin(pos.x*5.0)*sin(pos.z*5.0);
                vec3 floorCol = colorA * 0.1 * smoothstep(0.0, 0.1, grid);
                float sh = softshadow(pos, lig, 0.05, 5.0, 8.0);
                col = floorCol * sh;
            }
        }
    }
    
    // Exponential Distance Fog
    float fogDensity = 0.08;
    float fogFactor = 1.0 - exp(-pow(t * fogDensity, 2.0));
    vec3 bgCol = mix(colorA, vec3(0.0), 0.5); // Color de la niebla en el fondo
    
    float stars = pow(fract(sin(dot(p, vec2(12.9898,78.233))) * 43758.5453), 100.0) * (high * 3.0);
    vec3 final_bg = bgCol + vec3(stars);
    
    // Mezcla de la geometría con el fondo según la distancia
    col = mix(col, final_bg, fogFactor);
    
    // Sumar partículas volumétricas
    col += particleCol * mix(1.0, 0.2, fogFactor);
    
    // Lens Flares Anamórficos (JJ Abrams Style)
    // Se dibujan horizontales si la luz o el núcleo son "eclipsados"
    float lfPos = dot(lig, rd);
    if(lfPos > 0.0) {
        float flare = pow(lfPos, 20.0) * 1.5;
        flare += pow(lfPos, 200.0) * 2.0;
        
        // Aberración horizontal anamórfica
        float anamorphic = exp(-pow(abs(p.y), 2.0) * 50.0) * exp(-pow(abs(p.x), 2.0) * 0.5);
        vec3 flareCol = mix(colorA, vec3(1.0), 0.5) * flare * anamorphic * (1.0 + high*3.0);
        
        // Occlusion testing for flare (si hay geometría en frente, atenuar)
        if(t < max_d) flareCol *= 0.1; 
        col += flareCol;
    }
    
    fragColor = vec4(col, 1.0);
}
