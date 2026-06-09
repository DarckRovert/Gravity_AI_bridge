#version 330
out vec4 fragColor;
in vec2 uv;
uniform sampler2D tex_base;      // Imagen fotorrealista de Pollinations/Fooocus
uniform sampler2D tex_overlay;   // GLSL procedural (personaje + efectos)
uniform sampler2D tex_overlay2;  // Segunda escena para crossfade
uniform sampler2D tex_base2;     // Segunda imagen para crossfade de fondos
uniform float transition_t;
uniform float time;
uniform float bass;
uniform float mid;
uniform float high;
uniform float ken_burns_t;       // 0.0-1.0 progreso del zoom Ken Burns en esta escena
uniform float breath;            // Lens Breathing: 0.0-1.0 energia acumulada
uniform float beat_hit;          // Sincronización rítmica (1.0 en el golpe exacto, decae suavemente)

// ACES Tone Mapping
vec3 ACESFilm(vec3 x) {
    float a=2.51, b=0.03, c=2.43, d=0.59, e=0.14;
    return clamp((x*(a*x+b))/(x*(c*x+d)+e), 0.0, 1.0);
}
float hash2(vec2 p) { p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }

void main() {
    vec2 st = uv;

    // ── Lens Breathing (micro-zoom organico reactivo al audio) ──────────────────
    // Simula el micro-zoom que produce un lente real al cambiar el plano de enfoque
    float breathZoom = 1.0 + breath * 0.012;
    float zoom = (1.0 + ken_burns_t * 0.08) * breathZoom;
    float driftX = (ken_burns_t - 0.5) * 0.04;
    float driftY = sin(ken_burns_t * 3.14159) * 0.02;
    vec2 kb_uv = (st - 0.5) / zoom + 0.5 + vec2(driftX, driftY);
    kb_uv = clamp(kb_uv, 0.001, 0.999);

    // ── Leer imagen base con crossfade y Chromatic Aberration reactiva ───────
    vec2 dir = st - 0.5;
    float ab = bass * 0.018 * length(dir);
    
    vec3 base1, base2;
    base1.g = texture(tex_base, kb_uv).g;
    base1.r = texture(tex_base, kb_uv + dir * ab).r;
    base1.b = texture(tex_base, kb_uv - dir * ab).b;
    
    base2.g = texture(tex_base2, kb_uv).g;
    base2.r = texture(tex_base2, kb_uv + dir * ab).r;
    base2.b = texture(tex_base2, kb_uv - dir * ab).b;
    
    vec3 base = mix(base1, base2, transition_t);

    // ── Leer overlay GLSL ────────────────────────────────────────────────────
    vec4 ov1 = texture(tex_overlay, st);
    vec4 ov2 = texture(tex_overlay2, st);

    // Overlay brightness → alpha: pixeles muy oscuros del GLSL se vuelven transparentes
    // Esto hace que el fondo AI "se vea" donde el GLSL no tiene acción
    float luma1 = dot(ov1.rgb, vec3(0.299, 0.587, 0.114));
    float luma2 = dot(ov2.rgb, vec3(0.299, 0.587, 0.114));
    
    // El personaje SDF y el plasma tienen luma alta → opacos
    // El fondo negro del GLSL tiene luma 0 → transparente → muestra la imagen AI
    float alpha1 = smoothstep(0.04, 0.18, luma1);
    float alpha2 = smoothstep(0.04, 0.18, luma2);

    // Crossfade con warp orgánico entre las dos escenas GLSL
    vec2 warp_st = st + dir * luma1 * 0.06 * transition_t;
    vec4 ov2_warped = texture(tex_overlay2, warp_st);
    float alpha2w = smoothstep(0.04, 0.18, dot(ov2_warped.rgb, vec3(0.299, 0.587, 0.114)));
    
    vec3 overlay = mix(ov1.rgb, ov2_warped.rgb, transition_t);
    float alpha_ov = mix(alpha1, alpha2w, transition_t);

    // Bloom del overlay GLSL (aura de luz alrededor del personaje y plasma)
    vec3 bloom = vec3(0.0);
    vec2 texel = vec2(1.0/1280.0, 1.0/720.0);
    for(int i=-3; i<=3; i++) {
        for(int j=-3; j<=3; j++) {
            vec4 s = texture(tex_overlay, st + vec2(float(i),float(j)) * texel * 5.0);
            float sl = dot(s.rgb, vec3(0.299, 0.587, 0.114));
            bloom += max(vec3(0.0), s.rgb - 0.5) * smoothstep(0.05, 0.18, sl);
        }
    }
    bloom *= (0.3 + high * 0.5) * (1.0 / 49.0);

    // ── Composición final ────────────────────────────────────────────────────
    vec3 col = mix(base, base * 0.4 + overlay, alpha_ov);  // Imagen AI visible bajo el overlay
    col += bloom;                                            // Aura luminosa del overlay

    // Tinte global del overlay sobre el fondo (colores del GLSL tiñen sutilmente la imagen)
    col = mix(col, col * (0.6 + overlay * 0.5), 0.3 * alpha_ov);
    
    // ── Hollywood Grade Post-Processing (Bloom + Chromatic Aberration Rítmica) ──
    // Flash de aberración cromática en el golpe del beat
    float beat_aberration = beat_hit * 0.05 * length(dir);
    if (beat_hit > 0.0) {
        vec3 col_ab;
        col_ab.r = mix(base1, base2, transition_t).r; // Fallback simple para el rojo desplazado
        col_ab.g = col.g;
        col_ab.b = texture(tex_base, kb_uv - dir * beat_aberration).b; 
        col = mix(col, col_ab, beat_hit * 0.8);
        
        // Destello de exposición cinematográfica (Flash cut)
        col += vec3(beat_hit * 0.15); 
    }
    
    // Viñeta óptica profunda
    float vignette = 1.0 - dot(dir, dir) * 1.5;
    col *= smoothstep(0.0, 0.5, vignette);

    // ── Camera shake & Cyber Glitch en beat drops ────────────────────────────
    if (bass > 0.85 || beat_hit > 0.8) {
        float shake = max((bass - 0.85) * 0.025, beat_hit * 0.015);
        vec2 shakeUV = kb_uv + vec2(sin(time * 50.0) * shake, cos(time * 47.0) * shake);
        
        // Digital Glitch (Desplazamiento horizontal de scanlines)
        float glitchLine = step(0.9, fract(st.y * 20.0 + time * 15.0));
        float glitchShift = max((bass - 0.85) * 0.15, beat_hit * 0.1) * glitchLine * sin(time * 120.0);
        shakeUV.x += glitchShift;
        
        // Chromatic Aberration extrema en el Glitch
        vec3 shakeCol;
        shakeCol.r = texture(tex_base, clamp(shakeUV + vec2(shake * 2.5, 0.0), 0.001, 0.999)).r;
        shakeCol.g = texture(tex_base, clamp(shakeUV, 0.001, 0.999)).g;
        shakeCol.b = texture(tex_base, clamp(shakeUV - vec2(shake * 2.5, 0.0), 0.001, 0.999)).b;
        
        col = mix(col, shakeCol + overlay * alpha_ov + bloom, 0.7);
        
        // Invertir colores esporádicamente en la franja del glitch (Flash subliminal)
        if (fract(time * 42.0) > 0.85 && glitchLine > 0.0) {
            col.rgb = 1.0 - col.rgb;
        }
    }

    // ── Vignette cinematográfica profunda ────────────────────────────────────
    float vdist = length(dir * vec2(1.0, 1.2));
    float vig = smoothstep(0.95, 0.2, vdist);
    col *= mix(0.2, 1.0, vig); // Viñeta más agresiva en los bordes

    // ── ACES Tone Mapping + Halation (resplandor fotoquímico en halos altos) ──────
    // Halation: zonas de alta luminosidad emiten un halo rojizo-ananaranjado
    float luma_col = dot(col, vec3(0.299, 0.587, 0.114));
    float halation = smoothstep(0.6, 1.0, luma_col) * (0.15 + breath * 0.1);
    col += vec3(halation * 0.9, halation * 0.3, halation * 0.05); // Halo rojo-calido
    
    col = ACESFilm(col * 1.15);
    float grain = (hash2(st + fract(time * 0.017)) - 0.5) * 0.18 * (0.4 + high * 0.8);
    col += grain;

    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
