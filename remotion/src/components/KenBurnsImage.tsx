import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { ZOOM_MIN, ZOOM_SCALE, PAN_PERCENT } from "../constants";

// Alternates two gentle moves by beat: a slight push in, then a left-to-right
// drift, then push in again, and so on.
//
// Both stay inside ZOOM_SCALE, which is deliberately small. Every percent above
// 1.0 is a percent of the drawing cropped away, and full-bleed scene art has no
// spare margin - 1.06 was visibly eating the edges.
//
// Alternating by INDEX, not at random, so a re-render is byte-identical and two
// renders of the same video can actually be compared.
//
// PAN SAFETY: at scale S the image overhangs by (S-1)/2 each side, so a pan of
// X% is safe while X <= 50*(S-1)/S. At 1.03 the limit is 1.46% and the drift
// uses 1.0%. The push-in move does not pan at all, so it cannot expose an edge.

export const KenBurnsImage: React.FC<{ src: string; index?: number }> = ({
  src,
  index = 0,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const range: [number, number] = [0, durationInFrames];
  const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };
  const drifting = index % 2 === 1;

  // Push in: scale grows, no sideways travel.
  // Drift: scale held at the top so the pan has room; the view travels left
  // to right across the image.
  const scale = drifting
    ? ZOOM_SCALE
    : interpolate(frame, range, [ZOOM_MIN, ZOOM_SCALE], clamp);
  // Note the direction: translating the IMAGE is the opposite of moving the
  // camera. Starting at +PAN and ending at -PAN slides the image leftward,
  // which walks the visible window from the left edge to the right edge -
  // a left-to-right pan. The reverse reads as right-to-left.
  const x = drifting
    ? interpolate(frame, range, [PAN_PERCENT, -PAN_PERCENT], clamp)
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
