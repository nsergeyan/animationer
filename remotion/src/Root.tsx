import { Composition } from "remotion";
import { LectureVideo } from "./compositions/LectureVideo";
import { FPS, WIDTH, HEIGHT, OUTRO_FRAMES, Beat } from "./constants";

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
        const beats = props.beats ?? [];
        const seqFrames = beats.reduce(
          (sum, b) => sum + Math.max(1, Math.round(b.duration * FPS)),
          0
        );
        // MUST match LectureVideo's timeline exactly. Every beat but the last
        // carries a CROSSFADE_FRAMES tail that its transition then consumes, so
        // the two cancel and the timeline is simply the sum of the audio, plus
        // the outro hold. Subtracting the overlap here (as this used to) caps
        // the composition SHORT of its own content and silently truncates the
        // end - it cut the final beat off entirely.
        return {
          durationInFrames: Math.max(1, seqFrames + OUTRO_FRAMES),
          fps: FPS,
          width: WIDTH,
          height: HEIGHT,
        };
      }}
    />
  );
};
