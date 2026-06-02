# 🎬 Remotion Workspace — Gravity AI Bridge V15.2 PRO

Motor de renderizado de **Shorts verticales (9:16)** con subtítulos karaoke interactivos y efectos visuales cinematográficos. Integrado en el pipeline de Video Studio de Gravity AI Bridge.

---

## ¿Qué hace este workspace?

Este módulo de Remotion recibe un video horizontal (resultado del Motor GLSL PBR) y lo convierte en un **Short vertical para TikTok/Instagram Reels**, añadiendo:

- 🎤 **Karaoke interactivo**: cada palabra se resalta individualmente usando timestamps de Whisper ASR
- 🔵 **Tipografía Cyberpunk**: Montserrat/Inter Bold 900 con glow neón `#00f0ff`
- 📺 **VHS Scanlines animados**: interferencia analógica sutil que barre la pantalla
- 🎞️ **Letterbox cinematográfico**: viñeta superior/inferior para encuadre de cine
- 🌆 **Fondo desenfocado dinámico**: el mismo video (blur 30px, escala 1.2x) cubre el fondo 9:16

---

## Arquitectura de Composición

```
AbsoluteFill (1080×1920)
├── Capa 1: Fondo Desenfocado
│   └── <Video> blur(30px) brightness(40%) scale(1.2)
│
├── Capa 2: VHS Scanlines (CSS repeating-gradient)
│   └── translateY(currentTime * 50 % 4px) — barrido temporal
│
├── Capa 3: Video Principal Centrado (pillarbox)
│   └── <Video> objectFit=contain, ancho ajustado
│
├── Capa 4: Letterbox (inset box-shadow)
│   └── 150px top shadow + 300px bottom shadow
│
└── Capa 5: Subtítulos Karaoke
    └── Palabras mapeadas de Whisper → isActive → animación
        ├── Activa:  cyan #00f0ff, scale(1.1), rotate(-2deg), neon glow
        └── Inactiva: blanco 70%, escala normal
```

---

## Composiciones Disponibles

| ID | Dimensiones | FPS | Uso |
|---|---|---|---|
| `ShortTemplate` | 1080×1920 | 30 | TikTok, Instagram Reels, YouTube Shorts |
| `LongTemplate` | 1920×1080 | 30 | Video horizontal largo |

---

## Props del ShortTemplate

```typescript
interface ShortTemplateProps {
  videoPath: string;          // Ruta absoluta al MP4 del video master
  words: WordTimestamp[];     // Array de timestamps por palabra (Whisper)
  durationInFrames: number;   // Duración total en frames (fps × segundos)
}

interface WordTimestamp {
  word: string;    // Texto de la palabra
  start: number;   // Timestamp inicio en segundos
  end: number;     // Timestamp fin en segundos
}
```

---

## Comandos

```bash
# Instalar dependencias
npm install

# Preview interactivo en el navegador
npm run dev

# Render de un Short específico
npx remotion render src/index.ts ShortTemplate output.mp4 \
  --props='{"videoPath":"C:/video.mp4","words":[],"durationInFrames":1740}'

# Render con props desde archivo JSON (usado por el pipeline Python)
npx remotion render src/index.ts ShortTemplate output.mp4 \
  --props=temp_props_video_52_short_part1.json
```

---

## Integración con el Pipeline Python

El módulo `RemotionEngine` en `core/video/renderer.py` orquesta el renderizado:

1. **Extracción de timestamps**: Whisper ASR procesa el audio del short y devuelve un array `words` con `start`/`end` por palabra.
2. **Generación de props**: Los props se serializan a un JSON temporal en `remotion_workspace/`.
3. **Invocación de Remotion**: `npx.cmd remotion render ...` con `--props=<json_path>`.
4. **Copia al destino final**: El MP4 renderizado se mueve a `_videos/`.
5. **Limpieza**: Los archivos temporales (video slice + props JSON) se eliminan.

---

## Dependencias

| Paquete | Versión | Rol |
|---|---|---|
| `remotion` | 4.0.459 | Core del motor de render |
| `@remotion/cli` | 4.0.459 | CLI de renderizado |
| `@remotion/tailwind-v4` | 4.0.459 | Soporte Tailwind en Remotion |
| `react` | 19.2.3 | UI component tree |
| `tailwindcss` | 4.0.0 | Utilidades CSS (en desuso en favor de CSS puro) |

---

## Notas de Producción

> **Chromium headless**: Remotion usa Puppeteer internamente para renderizar cada frame via Chromium. El primer render descarga Chromium (~150 MB). Los renders subsecuentes son más rápidos.

> **Google Fonts en headless**: Las fuentes `Montserrat` e `Inter` se cargan via `@import url(https://fonts.googleapis.com/...)` en `src/index.css`. El servidor debe tener acceso a internet durante el render para descargarlas.

> **Performance**: En una CPU de 4 núcleos, un Short de 60s (1800 frames a 30fps) tarda aproximadamente 8-12 minutos en renderizar. Remotion usa todos los núcleos disponibles en paralelo por defecto.
