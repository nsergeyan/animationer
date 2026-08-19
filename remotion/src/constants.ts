// Mirrors the video settings in ../../config.py. Keep them in sync by hand.
export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;

// The still drifts slowly left to right. ZOOM_SCALE exists only to give that
// drift room to travel - every percent above 1.0 is a percent of the drawing
// cropped away, so keep it as low as the pan allows.
//
// Safe pan for a given scale: PAN_PERCENT <= 50 * (S - 1) / S
//   1.03 -> 1.46% max     1.06 -> 2.83% max     1.10 -> 4.55% max
export const ZOOM_MIN = 1.0;        // where a push-in starts (no crop at all)
export const ZOOM_SCALE = 1.03;    // where it ends, and where the drift sits
export const PAN_PERCENT = 1.0;

// Crossfade overlap between beats, in frames (0.5s at 30fps).
export const CROSSFADE_FRAMES = 15;

// Held on the last image after the final word, so the video does not stop dead
// mid-breath. Counts toward the total length.
export const OUTRO_FRAMES = 30;


export type Beat = {
  index: number;
  narration: string;
  image: string;   // filename, resolved via staticFile + --public-dir
  audio: string;   // filename, resolved via staticFile + --public-dir
  duration: number; // seconds
};
