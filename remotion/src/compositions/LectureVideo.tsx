import { AbsoluteFill, Audio, OffthreadVideo, Sequence, staticFile } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { StillImage } from "../components/StillImage";
import { DISSOLVE_FRAMES, FPS, Beat, beatFrames, dissolvesAfter } from "../constants";

// One beat: its frames + its narration audio. No captions - the art carries
// the frame and the narration carries the meaning.
//
// A beat's frames are chained edits of one another (pipeline.py build_frames),
// so they hard cut: the change between them IS the animation. Each starts at
// its word when the manifest carries frame_starts (pipeline.py
// _frame_starts), and otherwise the frames share the spoken length evenly.
// The last one also holds through the beat's tail (cut pad, dissolve or outro
// hold), so the picture never runs out before the Sequence does.
const BeatScene: React.FC<{ beat: Beat; durationInFrames: number }> = ({
  beat,
  durationInFrames,
}) => {
  const images = beat.frames?.length ? beat.frames : [beat.image];
  const spoken = Math.min(durationInFrames, Math.max(1, Math.round(beat.duration * FPS)));
  const even = images.map((_, k) => Math.round((k * spoken) / images.length));
  const timed = beat.frame_starts?.length === images.length
    ? beat.frame_starts.map((s) => Math.min(spoken - 1, Math.max(0, Math.round(s * FPS))))
    : null;
  // Python already checks the order; this only guards a hand-edited manifest.
  const starts =
    timed && timed[0] === 0 && timed.every((v, k) => k === 0 || v > timed[k - 1])
      ? timed
      : even;

  return (
    <AbsoluteFill>
      {images.map((src, k) => {
        const from = starts[k];
        const until = k === images.length - 1 ? durationInFrames : starts[k + 1];
        // A drawn-in first frame plays its clip, then the still: the clip ends
        // on the picture itself, so the switch is invisible. When the first
        // edit comes before the drawing would finish, the clip plays faster
        // so it still completes rather than being cut off mid-line.
        const want = k === 0 && beat.draw ? Math.round((beat.draw_seconds ?? 0) * FPS) : 0;
        const drawn = Math.min(until - from, want);
        return (
          <Sequence key={src} from={from} durationInFrames={Math.max(1, until - from)}>
            {drawn > 0 && (
              <Sequence durationInFrames={drawn}>
                <OffthreadVideo
                  src={staticFile(beat.draw!)}
                  playbackRate={want / drawn}
                  muted
                  style={{ width: "100%", height: "100%", objectFit: "cover" }}
                />
              </Sequence>
            )}
            <Sequence from={drawn}>
              <StillImage src={src} />
            </Sequence>
          </Sequence>
        );
      })}
      <Audio src={staticFile(beat.audio)} />
    </AbsoluteFill>
  );
};

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
            <BeatScene beat={beat} durationInFrames={durationInFrames} />
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
