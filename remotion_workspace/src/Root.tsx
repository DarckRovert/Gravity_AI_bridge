import React from "react";
import "./index.css";
import { Composition } from "remotion";
import { ShortTemplate } from "./ShortTemplate";
import { LongTemplate } from "./LongTemplate";

// Schema predeterminado para pruebas locales
const defaultProps = {
  videoPath: "",
  words: [],
  durationInFrames: 150
};

const defaultLongProps = {
  scenes: [],
  durationInFrames: 150
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ShortTemplate"
        component={ShortTemplate}
        calculateMetadata={({ props }) => {
          return {
            durationInFrames: props.durationInFrames || 150,
            props,
          };
        }}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={defaultProps}
      />
      
      <Composition
        id="LongTemplate"
        component={LongTemplate}
        calculateMetadata={({ props }) => {
          return {
            durationInFrames: props.durationInFrames || 150,
            props,
          };
        }}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={defaultLongProps}
      />
    </>
  );
};
