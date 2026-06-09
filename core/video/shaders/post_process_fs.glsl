#version 330
out vec4 fragColor; in vec2 uv; uniform sampler2D tex1; uniform sampler2D tex2; uniform float transition_t; uniform float bass; uniform float high; uniform float time;

// ACES Tone Mapping
vec3 ACESFilm(vec3 x) {
    float a = 2.51; float b = 0.03; float c = 2.43; float d = 0.59; float e = 0.14;
    return clamp((x*(a*x+b))/(x*(c*x+d)+e), 0.0, 1.0);
}

// Pseudo Random for film grain
float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

void main() {
    vec2 st = uv;
    
    // ── Camera shake CONTROLADO: solo en beat drops intensos ─────────────────
    float shakeStrength = max(0.0, bass - 0.82) * 0.018;
    if (shakeStrength > 0.0) {
        st += vec2(sin(time * 53.0) * shakeStrength, cos(time * 47.0) * shakeStrength);
        // Digital Glitch sutil: desplazamiento de scanlines cada 3-4 beats
        float glitchLine = step(0.92, fract(st.y * 18.0 + time * 12.0));
        st.x += (bass - 0.82) * 0.08 * glitchLine * sin(time * 100.0);
    }
    
    // Inversion de color en momentos pico extremos (solo los mas fuertes)
    float glitchLine2 = step(0.93, fract(st.y * 18.0 + time * 12.0));
    bool doInvert = bass > 0.92 && fract(time * 30.0) > 0.88 && glitchLine2 > 0.0;
    
    // Radial Chromatic Aberration
    vec2 dir = st - 0.5;
    float dist = length(dir);
    float ab = bass * 0.03 * dist;
    
    vec3 col1 = vec3(
        texture(tex1, clamp(st + dir * ab, 0.0, 1.0)).r,
        texture(tex1, clamp(st,            0.0, 1.0)).g,
        texture(tex1, clamp(st - dir * ab, 0.0, 1.0)).b
    );
    vec3 col2 = vec3(
        texture(tex2, clamp(st + dir * ab, 0.0, 1.0)).r,
        texture(tex2, clamp(st,            0.0, 1.0)).g,
        texture(tex2, clamp(st - dir * ab, 0.0, 1.0)).b
    );
    
    if (doInvert) { col1.rgb = 1.0 - col1.rgb; col2.rgb = 1.0 - col2.rgb; }
    
    // Warp transition orgánica
    float luma1 = dot(col1, vec3(0.299, 0.587, 0.114));
    vec2 warp_st = st + (luma1 * 0.1 * transition_t);
    vec3 warped_col2 = texture(tex2, clamp(warp_st, 0.0, 1.0)).rgb;
    vec3 final_col = mix(col1, mix(col2, warped_col2, transition_t), transition_t);
    
    // === DEPTH OF FIELD (Lens Bokeh) ===
    // Efecto sutil, activo siempre. Intensidad surge en Closeup (bass bajo)
    float dofStrength = 0.0035 * (1.0 - bass * 0.5);
    vec3 dofBlur = vec3(0.0);
    float dofWeight = 0.0;
    vec2 texelSize = 1.0 / vec2(1280.0, 720.0);
    // Muestreo tipo Bokeh hexagonal (12 taps)
    for (int i = 0; i < 12; i++) {
        float angle2 = float(i) * 0.5235988; // 30 grados
        float r = dofStrength * 40.0 * dist; // Mayor bokeh en bordes (enfoque central)
        vec2 offset2 = vec2(cos(angle2), sin(angle2)) * r;
        float w = 1.0 - float(i) / 12.0;
        dofBlur += texture(tex1, clamp(st + offset2, 0.0, 1.0)).rgb * w;
        dofWeight += w;
    }
    dofBlur /= dofWeight;
    // Mezcla DoF: centro nítido, bordes desenfocados (similar a lente 85mm f/1.8)
    float focusMask = smoothstep(0.0, 0.55, dist);
    final_col = mix(final_col, mix(final_col, dofBlur, focusMask), dofStrength * 150.0);
    
    // High Quality Bloom Multi-tap
    vec3 bloom = vec3(0.0);
    for(int i=-2; i<=2; i++) {
        for(int j=-2; j<=2; j++) {
            vec3 s = texture(tex1, clamp(st + vec2(float(i), float(j)) * texelSize * 4.0, 0.0, 1.0)).rgb;
            bloom += max(vec3(0.0), s - 0.72);
        }
    }
    bloom *= (high * 0.04);
    final_col += bloom;
    
    // Vignette cinematográfica
    float vig = smoothstep(0.95, 0.2, dist * 1.2);
    final_col *= mix(0.25, 1.0, vig);
    
    // ACES Tone mapping
    final_col = ACESFilm(final_col * 1.2);
    
    // Film Grain reactivo a agudos
    float grain = (hash(st + fract(time * 0.017)) - 0.5) * 0.15 * (0.4 + high * 0.7);
    final_col += grain;
    
    fragColor = vec4(final_col, 1.0);
}
