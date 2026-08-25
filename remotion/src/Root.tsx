import { Composition } from "remotion";
import { LectureVideo } from "./compositions/LectureVideo";
import { FPS, WIDTH, HEIGHT, Beat, totalFrames } from "./constants";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="LectureVideo"
      component={LectureVideo}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
      // Real duration is computed from the beats passed in as props.
      durationInFrames={1}
      defaultProps={{ beats: [] as Beat[] }}
      calculateMetadata={({ props }) => {
        // MUST match LectureVideo's timeline exactly, or the composition is
        // capped short of its own content and the end is silently truncated.
        // Both sides call totalFrames so the rule lives in exactly one place -
        // see the Timeline section of constants.ts for why summing the audio
        // is no longer enough.
        return {
          durationInFrames: totalFrames(props.beats ?? []),
          fps: FPS,
          width: WIDTH,
          height: HEIGHT,
        };
      }}
    />
  );
};
