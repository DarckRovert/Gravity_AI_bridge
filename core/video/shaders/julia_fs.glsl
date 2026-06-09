#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, pan;
uniform vec3 colorA, colorB; uniform int pose;
uniform sampler2D iChannel0;

''' + COSMOS_LIB + '''

// Julia con Orbit Trap: retorna (sdf, orbit_trap_min)
vec2 juliaSDF_OT(vec3 p, vec4 c) {
    vec4 z = vec4(p, 0.0); float md2 = 1.0, mz2 = dot(z, z);
    float trap = 1e10; // Orbit Trap: distancia mínima al origen durante la orbita
    for(int i=0; i<14; i++) {       // 14 iteraciones (era 8)
        md2 *= 4.0 * mz2;
        vec4 nz; nz.x = z.x*z.x - dot(z.yzw, z.yzw); nz.yzw = 2.0 * z.x * z.yzw;
        z = nz + c; mz2 = dot(z, z);
        trap = min(trap, length(z.xy));    // Trampa: plano XY (crea patrones de anillos)
        trap = min(trap, abs(z.x) + abs(z.y)); // Trampa cruzada
        if(mz2 > 4.0) break;
    }
    float sdf = 0.25 * log(mz2) * sqrt(mz2 / md2);
    return vec2(sdf, clamp(trap * 0.5, 0.0, 1.0));
}
void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); }

float forwardTravel() { return time * 3.0; }

// orbit_trap almacenado globalmente para uso en iluminación
float g_orbit_trap = 0.0;

vec2 map(vec3 p) {
    vec3 jp = p;
    jp.y -= 1.0; 
    jp.z = mod(jp.z, 8.0) - 4.0;
    vec2 juliaResult = juliaSDF_OT(jp, vec4(sin(time*0.5)*0.5, cos(time*0.3)*0.5, mid*0.5, -0.2));
    float world = juliaResult.x;
    g_orbit_trap = juliaResult.y;   // Guardamos el trap para colorear
    
    vec3 cosmosPos = vec3(0.0, 0.0, forwardTravel() + 2.0);
    vec3 cp = p - cosmosPos;
    cp *= 0.5; // Escalar
    vec2 cosmicRes = sdCosmos(cp, time*(1.0 + bass*2.0), bass, pose);
    cosmicRes.x *= 2.0;
    
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
    
    // === CINEMATIC SHOT MACHINE V1 (JULIA) ===
    float shotDur = 7.0;
    float cycleT  = mod(time, shotDur * 4.0);
    int   shotIdx = int(cycleT / shotDur);
    float shotT   = smoothstep(0.0, 1.0, fract(cycleT / shotDur));
    
    float camZ = forwardTravel() - 3.5;
    vec3 ro; float fov = 1.2;
    
    if (shotIdx == 0) {
        // Plano Maestro: sigue el fractal de lejos con altura variable
        ro = vec3(sin(time*0.08)*2.5, 1.5 + sin(time*0.12)*0.8, camZ);
    } else if (shotIdx == 1) {
        // Zoom de seguimiento suave (dolly-in)
        float zoomT = smoothstep(0.0, 1.0, shotT);
        ro = vec3(sin(time*0.1)*mix(2.0, 0.8, zoomT), mix(1.5, 0.6, zoomT), camZ);
        fov = mix(1.2, 1.8, zoomT);
    } else if (shotIdx == 2) {
        // Lateral (travelling): la cámara se desplaza en X
        ro = vec3(mix(-2.5, 2.5, shotT), 0.8 + sin(time*0.15)*0.5, camZ + 1.0);
    } else {
        // Dutch angle + pull-back
        ro = vec3(cos(time*0.08)*2.0, 2.2, camZ - shotT * 2.0);
        fov = 1.1;
    }
    
    pR(ro.xz, pan * 0.3);
    float shakeAmt = max(0.0, bass - 0.75) * 0.025;
    ro += vec3(sin(time * 47.0) * shakeAmt, cos(time * 43.0) * shakeAmt, 0.0);
    
    vec3 ww = normalize(vec3(0.0, 0.0, 1.0));
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = normalize(cross(uu, ww));
    vec3 rd = normalize(p.x * uu + p.y * vv + fov * ww);
    
    float t = 0.0, max_d = 12.0, iter = 0.0;
    float mat_id = 0.0; vec3 particleCol = vec3(0.0);
    
    for(int i=0; i<64; i++) {
        vec3 pos = ro + rd*t; vec2 res = map(pos);
        if(res.x<0.002 || t>max_d) { mat_id = res.y; break; }
        t += res.x; iter++;
        
        particleCol += calcVolumetricParticles(pos, time, bass, mid, high);
    }
    
    vec3 lig = normalize(vec3(1.0, 1.5, -1.0)); 
    
    vec3 col = colorA * 0.1;
    if(t<max_d) {
        vec3 pos = ro + rd*t;
        if(mat_id == 1.0) { 
            // Cosmos: SSS y Fresnel intensificado
            vec3 nor = calcCosmosNormal((pos - vec3(0.0, 0.0, forwardTravel() + 2.0)) * 0.5, time*(1.0 + bass*2.0), bass, pose);
            float dif = clamp(dot(nor, lig), 0.0, 1.0);
            float spe = pow(clamp(dot(reflect(rd, nor), lig), 0.0, 1.0), 32.0);
            float sh = softshadow(pos, lig, 0.05, 3.0, 8.0); 
            // IBL en Fractal + Cosmos
            vec3 refDir = reflect(rd, nor);
            vec3 envColor = texture(iChannel0, envMapEquirect(refDir)).rgb;
            float fresnel = pow(1.0 - max(dot(nor, -rd), 0.0), 2.5);
            float sss = smoothstep(0.0, 1.0, map(pos + lig * 0.2).x) * 0.5;
            
            col = colorB * (0.15 + dif*0.8*sh) + spe * high * sh * vec3(1.0);
            col += envColor * fresnel * 2.0; // Rim light PBR
            col += colorA * sss;
        } else if (mat_id == 2.0) { 
            col = vec3(1.0) + colorA * (1.0 + bass*4.0); // Emisivo fuerte
        } else if (mat_id == 3.0) {
            // Campo de Plasma en Julia
            vec3 plasmaCol = mix(colorA, colorB, 0.5 + 0.5 * sin(time * 3.0 + pos.x * 5.0));
            float pulse = 0.5 + 0.5 * sin(time * 8.0 + length(pos) * 10.0);
            col = plasmaCol * (1.5 + bass * 2.0) * (0.6 + pulse * 0.4);
            col += vec3(1.0) * high * 0.5;
        } else { 
            // Fractal: Iluminación mejorada con Orbit Traps y Volumetric SSS
            float sh = softshadow(pos, lig, 0.05, 3.0, 8.0);
            // Orbit Trap coloring: el color base depende de cuán cerca pasó del origen
            vec3 baseCol = mix(colorA, colorB, g_orbit_trap);
            // Patrones espirales/venas adicionales usando el trap
            float veins = smoothstep(0.1, 0.2, fract(g_orbit_trap * 10.0 + time));
            vec3 diffuse = mix(baseCol, vec3(1.0), veins * 0.3 * high);
            
            float ao = clamp(1.0 - iter/64.0, 0.0, 1.0); // Simple AO based on iterations
            
            col = diffuse * sh * ao;
            col += high * 0.5 * sh * g_orbit_trap; // Specular trap-based
        }
    }
    
    // Exponential Distance Fog
    float fogDensity = 0.15;
    float fogFactor = 1.0 - exp(-pow(t * fogDensity, 2.0));
    vec3 bgCol = mix(colorA * 0.2, vec3(0.0), 0.7); 
    
    // Ambient glow from iterations
    vec3 glowCol = colorA * (iter / 64.0) * bass * 0.3;
    
    col = mix(col, bgCol + glowCol, fogFactor);
    
    // Sumar partículas volumétricas
    col += particleCol * mix(1.0, 0.3, fogFactor);
    
    fragColor = vec4(col, 1.0);
}
