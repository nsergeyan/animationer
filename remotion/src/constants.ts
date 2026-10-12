// Mirrors the video settings in ../../config.py. Keep them in sync by hand.
export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;

// --- Cutting ---------------------------------------------------------------
// A single 0.5s crossfade on every beat was 8% of a 6.2s beat and would be 25%
// of a 2.0s one - the image would never be cleanly on screen, and 90 identical
// dissolves is the same metronome problem in another form.
//
// So the cut now depends on whether the place changed. Within a location,
// beats hard cut: consecutive images of the same place are a camera angle
// change, and a dissolve between two near-identical frames just reads as mush.
// A change of location dissolves, which is what makes the change legible as a
// change.
export const DISSOLVE_FRAMES = 8;   // 0.27s, on a location change or a redraw

// Beats are padded by this on a hard cut. The narration mp3s are trimmed tight
// (no detectable silence at -30dB), so with no pad at all one sentence starts
// on the exact frame the previous one ends and the read sounds breathless.
// This is picture-held, audio-silent - the cut still lands hard.
export const CUT_PAD_FRAMES = 4;    // 0.13s

// Held on the last image after the final word, so the video does not stop dead
// mid-breath. Counts toward the total length.
export const OUTRO_FRAMES = 30;


export type Beat = {
  index: number;
  narration: string;
  image: string;    // filename, resolved via staticFile + --public-dir
  frames?: string[]; // every frame of the beat, image first; older manifests have none
  frame_starts?: number[]; // seconds from the beat's start, one per frame; else an even split
  redraw?: boolean;  // a fresh picture mid-location: dissolve in rather than jump
  audio: string;    // filename, resolved via staticFile + --public-dir
  duration: number; // seconds
  location?: string; // optional: older manifests predate it, see LectureVideo
};

// --- Timeline ---------------------------------------------------------------
// Root.tsx and LectureVideo.tsx MUST agree on the length of the timeline to the
// frame. When they disagree the composition is capped short of its own content
// and the end is silently truncated - which is exactly what happened when hard
// cuts were introduced, because Root was still assuming every beat's tail got
// eaten by a transition.
//
// That assumption used to hold: every beat carried a crossfade tail and every
// boundary overlapped by the same amount, so the two cancelled and the total
// was just the sum of the audio. A hard cut has no transition to absorb its
// pad, so CUT_PAD_FRAMES is real added timeline.
//
// Rather than restate the rule in both files, both import these.

// Two beats are the same place only if both actually name one and the names
// match. Manifests written before `location` existed carry none, so every
// boundary falls through to a dissolve: the old behaviour, only shorter.
export const sameLocation = (a: Beat, b: Beat): boolean =>
  !!a.location && !!b.location && a.location === b.location;

// True when the boundary AFTER beat i is a dissolve rather than a hard cut.
// A redraw inside a location dissolves too: the whole page changes at once
// there, and a hard cut makes that read as a glitch rather than a new shot.
export const dissolvesAfter = (beats: Beat[], i: number): boolean =>
  i < beats.length - 1 &&
  (!sameLocation(beats[i], beats[i + 1]) || !!beats[i + 1].redraw);

// One beat's own length on the timeline, tail included.
export const beatFrames = (beats: Beat[], i: number): number => {
  const tail =
    i === beats.length - 1
      ? OUTRO_FRAMES
      : dissolvesAfter(beats, i)
        ? DISSOLVE_FRAMES
        : CUT_PAD_FRAMES;
  return Math.max(1, Math.round(beats[i].duration * FPS)) + tail;
};

// The whole composition. Each dissolve overlaps its two neighbours, so it hands
// those frames back; each hard cut does not.
export const totalFrames = (beats: Beat[]): number => {
  let total = 0;
  for (let i = 0; i < beats.length; i++) {
    total += beatFrames(beats, i);
    if (dissolvesAfter(beats, i)) total -= DISSOLVE_FRAMES;
  }
  return Math.max(1, total);
};
