#version 330
out vec4 fragColor;
in vec2 uv;
uniform vec2 resolution;
uniform float time, bass, mid, high, pan;
uniform vec3 colorA, colorB; uniform int pose;
uniform sampler2D iChannel0;

''' + COSMOS_LIB + '''

void pR(inout vec2 p, float a) { p = cos(a)*p + sin(a)*vec2(p.y, -p.x); }
float tunnelSDF(vec3 p) {
    vec2 q = abs(p.xy); float d = max(q.x*0.866025 + q.y*0.5, q.y) - 2.0;
    float rings = abs(fract(p.z*2.0 - time*(10.0 + bass*20.0)) - 0.5) - 0.1; return max(-d, rings);
}
float forwardTravel() { return time*(10.0 + mid*10.0); }

vec2 map(vec3 p) {
    float world = tunnelSDF(p);
    vec3 cosmosPos = vec3(0.0, 0.0, forwardTravel() + 4.5);
    cosmosPos.x += sin(time*4.0)*0.2; cosmosPos.y += cos(time*3.0)*0.2;
    vec3 cp = p - cosmosPos;
    cp *= 0.5;
    vec2 cosmicRes = sdCosmos(cp, time, bass, pose);
    cosmicRes.x *= 2.0;
    if(cosmicRes.x < world) return cosmicRes;
    return vec2(world, 0.0);
}

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    
    // === CINEMATIC SHOT MACHINE V1 (QUANTUM TUNNEL) ===
    float shotDur = 5.0;
    float cycleT  = mod(time, shotDur * 3.0);
    int   shotIdx = int(cycleT / shotDur);
    float shotT   = smoothstep(0.0, 1.0, fract(cycleT / shotDur));
    
    float fwd = forwardTravel();
    vec3 ro; float fov = 1.4;
    
    if (shotIdx == 0) {
        // Centrado en el eje del túnel
        ro = vec3(sin(time*0.05)*0.3 + pan, cos(time*0.07)*0.2, fwd);
    } else if (shotIdx == 1) {
        // Descentrado lateral (tensión visual, como un Steadicam)
        ro = vec3(mix(0.0, 1.2, shotT) + pan, mix(0.0, -0.4, shotT), fwd);
        fov = mix(1.4, 1.7, shotT);
    } else {
        // Pull-back dramático: la cámara se aleja del destino
        ro = vec3(pan * 0.3, 0.0, fwd - shotT * 3.0);
        fov = 1.2;
    }
    
    float shakeAmt = max(0.0, bass - 0.75) * 0.02;
    ro.xy += vec2(sin(time * 47.0), cos(time * 43.0)) * shakeAmt;
    
    vec3 rd = normalize(vec3(p.x, p.y, fov));
    pR(rd.xy, sin(time * 0.04) * 0.04); // roll suave y respirado 
    
    float t = 0.0, max_d = 30.0, glow = 0.0; float mat_id = 0.0;
    vec3 particleCol = vec3(0.0);
    for(int i=0; i<50; i++) {
        vec3 pos = ro + rd*t; vec2 res = map(pos);
        if(res.y == 0.0) glow += 0.01 / (0.01 + res.x*res.x);
        if(res.x<0.01 || t>max_d) { mat_id = res.y; break; }
        t += res.x;
        
        particleCol += calcVolumetricParticles(pos, time, bass, mid, high);
    }
    
    vec3 col = colorA * 0.1;
    if(t<max_d) {
        vec3 pos = ro + rd*t;
        if(mat_id == 1.0 || mat_id >= 4.0) { 
            vec3 cosmosPos = vec3(0.0, 0.0, forwardTravel() + 4.5);
            cosmosPos.x += sin(time*4.0)*0.2; cosmosPos.y += cos(time*3.0)*0.2;
            vec3 nor = calcCosmosNormal((pos - cosmosPos) * 0.5, time, bass, pose);
            vec3 lig = normalize(vec3(0.0, 1.0, 1.0));
            float dif = clamp(dot(nor, lig), 0.0, 1.0); 
            float spe = pow(clamp(dot(reflect(rd, nor), lig), 0.0, 1.0), 32.0);
            // IBL Quantum
            vec3 refDir = reflect(rd, nor);
            vec3 envColor = texture(iChannel0, envMapEquirect(refDir)).rgb;
            float fresnel = pow(1.0 - max(dot(nor, -rd), 0.0), 3.0);
            float sss = smoothstep(0.0, 1.0, tunnelSDF(pos + lig * 0.3)) * 0.4;
            col = colorB * dif * 0.3 + spe * vec3(1.0);
            col += envColor * fresnel * 2.5; // PBR Reflection
            col += colorA * sss;
        } else if (mat_id == 2.0) { 
            col = vec3(1.0) + mix(colorA, colorB, 0.5) * (1.0 + bass*4.0);
        } else {
            // Túnel: bandas de color reactivas a la energía del mid
            float band = fract(t * 0.1 + time * 0.05);
            col = mix(colorA, colorB, band);
            col *= 0.8 + mid * 0.5;
        }
    }
    
    // Exponential Tunnel Fog
    float fogDensity = 0.07;
    float fogFactor = 1.0 - exp(-pow(t * fogDensity, 2.0));
    vec3 bgCol = mix(colorA * 0.15, vec3(0.0), 0.6);
    col = mix(col, bgCol, fogFactor);
    
    // Glow de los anillos reactivo al high
    col += mix(colorA, colorB, 0.5) * glow * (0.4 + high * 1.5);
    
    // Sumar partículas volumétricas
    col += particleCol * mix(1.0, 0.1, fogFactor);
    fragColor = vec4(col, 1.0);
}
