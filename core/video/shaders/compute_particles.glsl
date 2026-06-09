#version 430
layout(local_size_x = 256) in;

struct Particle {
    vec4 pos; // xyz, w=vida
    vec4 vel; // xyz, w=tamaño
};

layout(std430, binding = 0) buffer ParticleBuffer {
    Particle particles[];
};

uniform float time;
uniform float bass;
uniform float mid;

float hash(uint n) {
    n = (n << 13U) ^ n;
    n = n * (n * n * 15731U + 789221U) + 1376312589U;
    return float(n & uint(0x7fffffffU)) / float(0x7fffffff);
}

void main() {
    uint idx = gl_GlobalInvocationID.x;
    Particle p = particles[idx];
    
    // Físicas en la GPU
    p.pos.xyz += p.vel.xyz * (0.01 + bass * 0.05);
    p.pos.y += 0.01 * mid;
    p.pos.w -= 0.01; // Envejecer
    
    // Si muere, renacer
    if (p.pos.w <= 0.0) {
        float h1 = hash(idx + uint(time * 1000.0));
        float h2 = hash(idx + 1U + uint(time * 1000.0));
        float h3 = hash(idx + 2U + uint(time * 1000.0));
        
        p.pos.xyz = vec3(h1*20.0-10.0, -2.0, h2*20.0-10.0);
        p.vel.xyz = vec3(0.0, 1.0 + h3 * 2.0, 0.0);
        p.pos.w = 1.0 + h1; // Vida
        p.vel.w = 0.02 + h2 * 0.05; // Tamaño
    }
    
    particles[idx] = p;
}
