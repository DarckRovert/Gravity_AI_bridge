import { AbsoluteFill, useCurrentFrame, useVideoConfig, Video, Img, Sequence, Audio, staticFile } from "remotion";
import React, { useMemo } from "react";

type WordTiming = {
  word: string;
  start: number;
  end: number;
};

type Scene = {
  imagePath: string; // Puede ser PNG, JPG o MP4
  audioPath: string; // Audio TTS de la escena
  durationInFrames: number;
  words: WordTiming[]; // Subtítulos de la escena
};

export const LongTemplate: React.FC<{
  scenes: Scene[];
}> = ({ scenes = [] }) => {
  const { fps } = useVideoConfig();

  // Calcular en qué frame empieza cada escena para la secuencia
  const sceneStarts = useMemo(() => {
    let current = 0;
    return scenes.map((s) => {
      const start = current;
      current += s.durationInFrames;
      return start;
    });
  }, [scenes]);

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {scenes.map((scene, i) => {
        const isVideo = scene.imagePath.toLowerCase().endsWith(".mp4");
        
        // Alternar dirección del zoom (Ken Burns)
        const zoomIn = i % 2 === 0;

        // Limpiar path usando staticFile de remotion
        const safeSource = scene.imagePath.startsWith("http") ? scene.imagePath : staticFile(scene.imagePath);
        const safeAudio = scene.audioPath.startsWith("http") ? scene.audioPath : staticFile(scene.audioPath);

        return (
          <Sequence key={i} from={sceneStarts[i]} durationInFrames={scene.durationInFrames}>
            {/* Visual (Imagen con Ken Burns o Video puro) */}
            <AbsoluteFill style={{ overflow: "hidden" }}>
              {isVideo ? (
                <Video 
                  src={safeSource} 
                  style={{ width: "100%", height: "100%", objectFit: "cover" }} 
                />
              ) : (
                <SceneImageWithKenBurns src={safeSource} zoomIn={zoomIn} durationInFrames={scene.durationInFrames} />
              )}
            </AbsoluteFill>

            {/* Audio de la escena */}
            {scene.audioPath && <Audio src={safeAudio} />}

            {/* Subtítulos de la Escena (Estilo Cinematográfico Elegante) */}
            {scene.words && scene.words.length > 0 && (
              <SceneSubtitles words={scene.words} />
            )}
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

// Componente para animar imagen estática
const SceneImageWithKenBurns: React.FC<{ src: string; zoomIn: boolean; durationInFrames: number }> = ({ src, zoomIn, durationInFrames }) => {
  const frame = useCurrentFrame();
  const progress = frame / durationInFrames;
  
  // Si zoomIn es true, va de 1.0 a 1.20. Si es false, va de 1.20 a 1.0.
  const scale = zoomIn ? 1.0 + (progress * 0.20) : 1.20 - (progress * 0.20);
  const translateY = zoomIn ? (progress * -15) : (progress * 15);

  return (
    <Img 
      src={src} 
      style={{
        width: "100%",
        height: "100%",
        objectFit: "cover",
        transform: `scale(${scale}) translateY(${translateY}px)`,
        transformOrigin: "center center",
      }} 
    />
  );
};

// Componente para los subtítulos (Versión YouTube / Horizontal)
const SceneSubtitles: React.FC<{ words: WordTiming[] }> = ({ words }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  const activeWordIndex = words.findIndex(
    (w) => currentTime >= w.start && currentTime <= (w.end + 0.1)
  );

  let visibleWords: WordTiming[] = [];
  if (activeWordIndex !== -1) {
    // Para YouTube, mostramos una frase un poco más larga (5-6 palabras) para que se lea como subtítulo tradicional, pero resaltando la actual
    const groupStart = Math.max(0, activeWordIndex - 2);
    const groupEnd = Math.min(words.length, activeWordIndex + 3);
    visibleWords = words.slice(groupStart, groupEnd);
  }

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          bottom: "8%",
          left: 0,
          right: 0,
          height: "150px",
          display: "flex",
          flexDirection: "row",
          justifyContent: "center",
          alignItems: "center",
          flexWrap: "wrap",
          padding: "0 60px",
          gap: "10px",
        }}
      >
        {visibleWords.map((w, i) => {
          const isActive = currentTime >= w.start && currentTime <= (w.end + 0.1);
          return (
            <span
              key={i}
              style={{
                fontSize: isActive ? "45px" : "38px",
                fontWeight: "bold",
                fontFamily: "sans-serif",
                color: isActive ? "#fbbf24" : "white",
                textShadow: "2px 2px 0px #000, -1px -1px 0px #000, 0px 4px 10px rgba(0,0,0,0.8)",
                transform: isActive ? "scale(1.05) translateY(-2px)" : "scale(1)",
                transition: "all 0.1s ease-out",
              }}
            >
              {w.word}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
