// Mirrors the video settings in ../../config.py. Keep them in sync by hand.
export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;

// --- Motion ----------------------------------------------------------------
// These were rebuilt when the channel moved from 45 beats to 90. The old
// values were 1.00 -> 1.03 spread over a 6.2s beat, which is 0.5% of scale a
// second: about 2.8 pixels of edge movement a second at 1080p, well under what
// reads as movement at all. The result was a slideshow with a fade, and the
// motion was doing nothing to earn its complexity.
//
// A beat is now ~3.0s, so a move has half the time to register and has to be
// several times faster to be seen. A push runs the full 10% across the beat,
// about 3.3% a second, which reads clearly without becoming a zoom effect.
//
// COST OF ZOOM, both real:
//   - Every percent above 1.0 crops a percent of the drawing away. A push
//     starts at zero crop and only reaches 10% at the very end of the beat;
//     a pull is the same trade run backwards. What the old comment complained
//     about was 1.06 held CONSTANT for a whole beat, which is a different and
//     worse deal - so the pan, which is the one move that does hold a fixed
//     scale, is pinned lower at PAN_SCALE.
//   - Source art is 1376x768 upscaled to 1920x1080, so it is already at 1.4x
//     before any zoom. Flat bucket-filled colour upscales cleanly and only the
//     outlines soften, which is why this is affordable here and would not be
//     on photographic art.
//
// config.py's STYLE_BLOCK now asks for clear space around all four edges,
// which is what makes the larger crop safe on newly generated art.
export const ZOOM_MIN = 1.0;      // where a push starts: no crop at all
export const ZOOM_SCALE = 1.1;    // where it ends

// The pan holds a fixed scale for the whole beat, so it pays the crop the
// entire time and is kept lower than the push.
// Safe pan for a given scale: PAN_PERCENT <= 50 * (S - 1) / S
//   1.03 -> 1.46% max     1.06 -> 2.83% max     1.10 -> 4.55% max
export const PAN_SCALE = 1.06;
export const PAN_PERCENT = 2.5;   // under the 2.83% ceiling for 1.06

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
export const DISSOLVE_FRAMES = 8;   // 0.27s, only when the location changes

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
export const dissolvesAfter = (beats: Beat[], i: number): boolean =>
  i < beats.length - 1 && !sameLocation(beats[i], beats[i + 1]);

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
