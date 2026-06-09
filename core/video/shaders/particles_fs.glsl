#version 430
in float pLife;
in float pSize;
out vec4 fragColor;

uniform float high;

void main() {
    vec2 circ = gl_PointCoord * 2.0 - 1.0;
    float dist = dot(circ, circ);
    if(dist > 1.0) discard;
    
    // Suavizado del borde del punto
    float alpha = smoothstep(1.0, 0.5, dist) * pLife;
    
    // Colores cálidos/estelares reactivos a agudos
    vec3 col = vec3(1.0, 0.8 + high*0.2, 0.4 + high*0.6) * (1.0 + high*2.0);
    
    fragColor = vec4(col * alpha * 0.3, 1.0); // Pre-multiplied alpha para aditivo
}
