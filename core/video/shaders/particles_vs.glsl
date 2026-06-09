#version 430
struct Particle {
    vec4 pos;
    vec4 vel;
};
layout(std430, binding = 0) buffer ParticleBuffer {
    Particle particles[];
};

uniform float time;
uniform float bass;
uniform float pan;
uniform float aspect;

out float pLife;
out float pSize;
uniform int engine_id;

mat2 rot(float a) { float s = sin(a), c = cos(a); return mat2(c, s, -s, c); }

void main() {
    Particle p = particles[gl_VertexID];
    pLife = p.pos.w;
    
    vec3 ro, target;
    
    if (engine_id == 0 || engine_id == -1) { // INCA MATH (Default)
        float ct = mod(time * 0.2 + pan, 20.0); 
        if (ct < 10.0) {
            float t_fase = ct / 10.0;
            ro = vec3(sin(t_fase*3.14)*30.0, 20.0 + t_fase*10.0, 40.0 - t_fase*20.0);
            target = vec3(0.0, 5.0 + t_fase*5.0, -25.0); 
        } else {
            float t_fase = (ct - 10.0) / 10.0;
            ro = vec3(0.0 + sin(t_fase*6.28)*40.0, 30.0 - t_fase*15.0, 20.0 - t_fase*10.0);
            target = vec3(0.0, 10.0, -25.0);
        }
        ro.y += bass * 0.3;
    } else if (engine_id == 1) { // SPACE ODYSSEY
        float shotDur = 6.0; float cycleT = mod(time, shotDur * 4.0);
        int shotIdx = int(cycleT / shotDur); float shotT = smoothstep(0.0, 1.0, fract(cycleT / shotDur));
        target = vec3(0.0, 0.0, -5.0);
        if (shotIdx == 0) {
            float angle = time * 0.08 + pan * 0.5; ro = vec3(sin(angle) * 14.0, 3.5 + sin(time * 0.12) * 1.5, cos(angle) * 14.0 - 5.0);
        } else if (shotIdx == 1) {
            float angle = time * 0.15 + pan * 0.5; ro = vec3(sin(angle) * 8.0, sin(time * 0.2) * 1.2 + 0.5, cos(angle) * 8.0 - 5.0);
        } else if (shotIdx == 2) {
            float angle = time * 0.06 + pan * 0.3; float zoomT = smoothstep(0.0, 1.0, shotT); float dist = mix(9.0, 4.5, zoomT);
            ro = vec3(sin(angle) * dist, 0.8 + sin(time*0.1)*0.4, cos(angle) * dist - 5.0);
        } else {
            float flyT = shotT; float x = mix(-12.0, 12.0, flyT);
            ro = vec3(x, 2.0 + sin(flyT * 3.14159) * 1.0, -3.5 + sin(flyT * 3.14159) * -2.0);
            target = vec3(0.0, 0.0, -5.0) + vec3(sin(flyT * 2.0) * 2.0, 0.0, 0.0);
        }
    } else if (engine_id == 2) { // MANDELBULB
        float shotDur = 8.0; float cycleT = mod(time, shotDur * 3.0);
        int shotIdx = int(cycleT / shotDur); float shotT = smoothstep(0.0, 1.0, fract(cycleT / shotDur));
        target = vec3(0.0); 
        if (shotIdx == 0) {
            ro = vec3(0.0, 0.0, -2.5 - sin(time*0.08)*0.4);
            vec2 rxz = ro.xz; float a1 = time * 0.08 + pan; rxz = cos(a1)*rxz + sin(a1)*vec2(rxz.y, -rxz.x); ro.xz = rxz;
            vec2 rxy = ro.xy; float a2 = time * 0.04; rxy = cos(a2)*rxy + sin(a2)*vec2(rxy.y, -rxy.x); ro.xy = rxy;
        } else if (shotIdx == 1) {
            ro = vec3(sin(time*0.1)*0.5, cos(time*0.07)*0.3, mix(-2.5, -1.8, shotT));
            vec2 rxz = ro.xz; float a = pan * 0.5; rxz = cos(a)*rxz + sin(a)*vec2(rxz.y, -rxz.x); ro.xz = rxz;
        } else {
            ro = vec3(mix(-0.5, 0.5, shotT), 0.0, -2.2);
            vec2 rxz = ro.xz; float a = time * 0.05 + pan; rxz = cos(a)*rxz + sin(a)*vec2(rxz.y, -rxz.x); ro.xz = rxz;
        }
    }
    
    vec3 cw = normalize(target - ro);
    vec3 cu = normalize(cross(cw, vec3(0.0, 1.0, 0.0)));
    vec3 cv = normalize(cross(cu, cw));
    mat3 viewMat = mat3(cu, cv, -cw); // Inversa de la rotación de la cámara
    
    // Convertir mundo a View Space
    vec3 viewPos = viewMat * (p.pos.xyz - ro);
    
    // Proyección simple (Fov = 1.2 adaptado de V13)
    float fov = 1.2;
    vec2 projPos = viewPos.xy / (viewPos.z * -1.0) * fov; // z es negativo en view space OpenGL
    projPos.x /= aspect; // corrección de aspecto
    
    // Clip space projection limits
    float depth = -viewPos.z / 100.0; // Mapeo de profundidad 0 a 1
    
    gl_Position = vec4(projPos * depth * 100.0, depth * 100.0 - 1.0, depth * 100.0);
    
    pSize = p.vel.w;
    gl_PointSize = max(1.0, (pSize * 150.0) / max(0.1, -viewPos.z));
}
