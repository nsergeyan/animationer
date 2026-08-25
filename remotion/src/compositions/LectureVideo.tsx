import { AbsoluteFill, Audio, staticFile } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { KenBurnsImage } from "../components/KenBurnsImage";
import { DISSOLVE_FRAMES, Beat, beatFrames, dissolvesAfter } from "../constants";

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
        const dissolving = dissolvesAfter(beats, i);

        // A Transition OVERLAPS its two neighbours rather than sitting between
        // them, so without padding the next beat's audio would start
        // DISSOLVE_FRAMES before this one's finished and the two narrations
        // would talk over each other. Padding by exactly the overlap means the
        // overlap eats silence instead of speech, and beat N+1 begins as beat
        // N's audio ends.
        //
        // A hard cut has no overlap to absorb, so its pad is a real gap and is
        // deliberately much shorter - a breath, not a beat. The last beat gets
        // OUTRO_FRAMES so the video holds rather than cutting on the final
        // syllable. All three cases live in beatFrames, which Root.tsx also
        // uses to size the composition.
        const durationInFrames = beatFrames(beats, i);

        const seq = (
          <TransitionSeries.Sequence key={`seq-${i}`} durationInFrames={durationInFrames}>
            <BeatScene beat={beat} index={i} />
          </TransitionSeries.Sequence>
        );

        // Omitting the Transition IS the hard cut - TransitionSeries plays
        // adjacent Sequences back to back with nothing between them.
        if (!dissolving) return [seq];
        return [
          seq,
          <TransitionSeries.Transition
            key={`t-${i}`}
            presentation={fade()}
            timing={linearTiming({ durationInFrames: DISSOLVE_FRAMES })}
          />,
        ];
      })}
    </TransitionSeries>
  );
};
