import { AbsoluteFill, useCurrentFrame, useVideoConfig, Video } from "remotion";
import React from "react";
import { staticFile } from "remotion";

type WordTiming = {
  word: string;
  start: number;
  end: number;
};

export const ShortTemplate: React.FC<{
  videoPath: string; // Ruta absoluta al video generado por ffmpeg
  words: WordTiming[];
}> = ({ videoPath, words = [] }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Tiempo actual en segundos
  const currentTime = frame / fps;

  // Encontrar la palabra activa
  // Damos un margen de 0.1s para que no parpadee tan rápido entre palabras contiguas
  const activeWordIndex = words.findIndex(
    (w) => currentTime >= w.start && currentTime <= (w.end + 0.1)
  );

  // Seleccionar 3 palabras para mostrar el contexto (la anterior, la actual, la siguiente)
  // o simplemente mostrar la actual resaltada
  
  // Para el efecto Hypnos: mostraremos hasta 4 palabras en pantalla, resaltando la actual.
  let visibleWords: WordTiming[] = [];
  if (activeWordIndex !== -1) {
    // Tomar un grupo para que no salte mucho (agrupar de 3 en 3 aprox)
    const groupStart = Math.max(0, activeWordIndex - 1);
    const groupEnd = Math.min(words.length, activeWordIndex + 2);
    visibleWords = words.slice(groupStart, groupEnd);
  }

  // Si el archivo ya es un enlace absoluto local, Remotion lo bloquea por seguridad.
  // Ahora remotion_engine lo copia a la carpeta public, y pasa solo el nombre del archivo.
  const safeVideoSource = videoPath.startsWith("http") ? videoPath : staticFile(videoPath);

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {/* Fondo Desenfocado (Vertical) */}
      <AbsoluteFill>
        <Video 
          src={safeVideoSource}
          muted={true}
          style={{ 
            width: "100%", 
            height: "100%", 
            objectFit: "cover", 
            filter: "blur(30px) brightness(0.4)",
            transform: "scale(1.2)" 
          }} 
        />
      </AbsoluteFill>

      {/* VHS Scanlines Overlay (Digital Cyberpunk Look) */}
      <AbsoluteFill style={{
        background: "repeating-linear-gradient(0deg, rgba(0,0,0,0.1) 0px, rgba(0,0,0,0.1) 2px, transparent 2px, transparent 4px)",
        pointerEvents: "none",
        opacity: 0.6,
        zIndex: 2, // Por encima del fondo desenfocado pero por debajo del video central
        transform: `translateY(${(currentTime * 50) % 4}px)`, // Ligero movimiento hacia abajo
      }} />


      {/* Video Original (Horizontal) centrado */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <Video 
          src={safeVideoSource} 
          style={{ 
            width: "100%", 
            objectFit: "contain",
            boxShadow: "0 20px 50px rgba(0,0,0,0.5)"
          }} 
        />
      </AbsoluteFill>

      {/* Efecto de viñeta superior/inferior para dar look de cine */}
      <AbsoluteFill style={{ 
        boxShadow: "inset 0 150px 150px -50px rgba(0,0,0,0.8), inset 0 -300px 200px -50px rgba(0,0,0,0.9)",
        pointerEvents: "none"
      }} />

      {/* Subtítulos Dinámicos (Overlay Cinematográfico) */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div
          style={{
            position: "absolute",
            bottom: "12%",
            left: 0,
            right: 0,
            display: "flex",
            flexDirection: "row",
            justifyContent: "center",
            alignItems: "center",
            flexWrap: "wrap",
            padding: "0 60px",
            gap: "18px",
          }}
        >
          {visibleWords.map((w, i) => {
            const isActive = currentTime >= w.start && currentTime <= (w.end + 0.1);
            return (
              <span
                key={i}
                style={{
                  fontSize: isActive ? "85px" : "60px",
                  fontWeight: "900",
                  fontFamily: "'Montserrat', 'Inter', sans-serif",
                  textTransform: "uppercase",
                  color: isActive ? "#00f0ff" : "rgba(255, 255, 255, 0.7)", // Cyberpunk Blue / Sci-Fi White
                  textShadow: isActive 
                    ? "0px 0px 20px rgba(0, 240, 255, 0.8), 0px 10px 15px rgba(0,0,0,0.9), 4px 4px 0px #000" 
                    : "3px 3px 10px rgba(0,0,0,0.8)",
                  transform: isActive ? "scale(1.1) translateY(-10px) rotate(-2deg)" : "scale(1) translateY(0px) rotate(0deg)",
                  transition: "all 0.15s cubic-bezier(0.175, 0.885, 0.32, 1.275)",
                  WebkitTextStroke: isActive ? "2px rgba(255,255,255,0.2)" : "2px black",
                  margin: "0 5px",
                  letterSpacing: isActive ? "2px" : "0px",
                  zIndex: isActive ? 10 : 1,
                }}
              >
                {w.word}
              </span>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
