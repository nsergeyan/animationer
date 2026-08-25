import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { ZOOM_MIN, ZOOM_SCALE, PAN_SCALE, PAN_PERCENT } from "../constants";

// Four moves cycled by beat index: push in, pan left-to-right, pull out, pan
// right-to-left.
//
// Four rather than the old two because the video now shows twice as many
// images at roughly 3.0s each, and a two-move cycle at that rate is legible as
// a pattern - in, across, in, across. Reversing the direction of each move on
// its second appearance breaks the pattern without introducing a new KIND of
// movement, which would start to look like an effect rather than a camera.
//
// Cycling by INDEX rather than at random keeps a re-render byte-identical, so
// two renders of the same video can still be compared.
//
// PAN SAFETY: at scale S the image overhangs by (S-1)/2 each side, so a pan of
// X% is safe while X <= 50*(S-1)/S. PAN_SCALE and PAN_PERCENT are set against
// that ceiling in constants.ts. The push and pull never pan, so they cannot
// expose an edge at any point in the move.

export const KenBurnsImage: React.FC<{ src: string; index?: number }> = ({
  src,
  index = 0,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const range: [number, number] = [0, durationInFrames];
  const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };
  const move = index % 4;
  const panning = move === 1 || move === 3;

  // A pan holds one scale for the whole beat, so it pays the crop the entire
  // time and sits at the lower PAN_SCALE. A push or pull travels the full zoom
  // range, but starts (or ends) at zero crop.
  const scale = panning
    ? PAN_SCALE
    : interpolate(
        frame,
        range,
        move === 0 ? [ZOOM_MIN, ZOOM_SCALE] : [ZOOM_SCALE, ZOOM_MIN],
        clamp,
      );

  // Note the direction: translating the IMAGE is the opposite of moving the
  // camera. Starting at +PAN and ending at -PAN slides the image leftward,
  // which walks the visible window from the left edge to the right edge - a
  // left-to-right pan. Move 3 runs the same travel the other way.
  const x = panning
    ? interpolate(
        frame,
        range,
        move === 1 ? [PAN_PERCENT, -PAN_PERCENT] : [-PAN_PERCENT, PAN_PERCENT],
        clamp,
      )
    : 0;

  return (
    <AbsoluteFill style={{ backgroundColor: "black", overflow: "hidden" }}>
      <Img
        src={staticFile(src)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale}) translateX(${x}%)`,
        }}
      />
    </AbsoluteFill>
  );
};
