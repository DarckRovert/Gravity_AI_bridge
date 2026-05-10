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

      {/* Subtítulos Dinámicos (Overlay) */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div
          style={{
            position: "absolute",
            bottom: "15%",
            left: 0,
            right: 0,
            height: "300px",
            display: "flex",
            flexDirection: "row",
            justifyContent: "center",
            alignItems: "center",
            flexWrap: "wrap",
            padding: "0 40px",
            gap: "15px",
          }}
        >
          {visibleWords.map((w, i) => {
            const isActive = currentTime >= w.start && currentTime <= (w.end + 0.1);
            return (
              <span
                key={i}
                style={{
                  fontSize: isActive ? "65px" : "45px",
                  fontWeight: "900",
                  fontFamily: "sans-serif",
                  textTransform: "uppercase",
                  color: isActive ? "#fbbf24" : "white",
                  textShadow: "3px 3px 0px #000, -2px -2px 0px #000, 2px -2px 0px #000, -2px 2px 0px #000, 0px 6px 12px rgba(0,0,0,0.6)",
                  transform: isActive ? "scale(1.05) translateY(-5px)" : "scale(1)",
                  transition: "all 0.1s ease-out",
                  WebkitTextStroke: "1.5px black",
                  margin: "0 5px",
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
