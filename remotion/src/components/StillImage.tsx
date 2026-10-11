import { AbsoluteFill, Img, staticFile } from "remotion";

// No camera movement. Frames are chained edits of one another, so any zoom or
// pan would restart at every cut and make near-identical frames jump. The
// edits between frames are the motion.
export const StillImage: React.FC<{ src: string }> = ({ src }) => (
  <AbsoluteFill style={{ backgroundColor: "black" }}>
    <Img
      src={staticFile(src)}
      style={{ width: "100%", height: "100%", objectFit: "cover" }}
    />
  </AbsoluteFill>
);
