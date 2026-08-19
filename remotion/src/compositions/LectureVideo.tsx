import { AbsoluteFill, Audio, staticFile } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { KenBurnsImage } from "../components/KenBurnsImage";
import { FPS, CROSSFADE_FRAMES, OUTRO_FRAMES, Beat } from "../constants";

// One beat: image (Ken Burns) + its narration audio. No captions - the art
// carries the frame and the narration carries the meaning.
const BeatScene: React.FC<{ beat: Beat; index: number }> = ({ beat, index }) => (
  <AbsoluteFill>
    <KenBurnsImage src={beat.image} index={index} />
    <Audio src={staticFile(beat.audio)} />
  </AbsoluteFill>
);

export const LectureVideo: React.FC<{ beats: Beat[] }> = ({ beats }) => {
  return (
    <TransitionSeries>
      {beats.flatMap((beat, i) => {
        const isLast = i === beats.length - 1;

        // A Transition OVERLAPS its two neighbours rather than sitting between
        // them, so without padding the next beat's audio starts CROSSFADE_FRAMES
        // before this one's finishes and the two narrations talk over each
        // other. Adding that many frames as a silent tail means the overlap
        // eats the tail instead of speech, and beat N+1 begins exactly as beat
        // N's audio ends. The last beat gets OUTRO_FRAMES instead, so the
        // video holds briefly rather than cutting on the final syllable.
        const durationInFrames =
          Math.max(1, Math.round(beat.duration * FPS)) +
          (isLast ? OUTRO_FRAMES : CROSSFADE_FRAMES);

        const seq = (
          <TransitionSeries.Sequence key={`seq-${i}`} durationInFrames={durationInFrames}>
            <BeatScene beat={beat} index={i} />
          </TransitionSeries.Sequence>
        );
        if (isLast) return [seq];
        // Crossfade into the next beat.
        return [
          seq,
          <TransitionSeries.Transition
            key={`t-${i}`}
            presentation={fade()}
            timing={linearTiming({ durationInFrames: CROSSFADE_FRAMES })}
          />,
        ];
      })}
    </TransitionSeries>
  );
};
