"""
Stage helper: a whiteboard "draw-in" clip of one picture.

The picture is revealed on white paper, lines first, then colors, by the
whiteboard-animation-vi repo (config.DRAW_IN_REPO). It never draws anything
itself: it reveals the finished image's own pixels in a planned order, so the
clip's last frame IS the picture and the still that follows it in the render
cuts in invisibly.

That repo lives in its own Python 3.11 venv (its PyTorch does not run on this
project's Python), so this file is both sides of the bridge: make_clip() runs
in the pipeline and starts the other venv's Python on this same file, and the
__main__ block runs there and does the render. The clip is only the drawing,
no hold, so it never depends on the beat's length.
"""

import subprocess
import sys
from pathlib import Path


def _python() -> Path:
    import config
    return config.DRAW_IN_REPO / ".venv" / "bin" / "python"


def available() -> bool:
    """
    Whether the whiteboard repo and its venv are installed. A fresh clone of
    this repo has neither, and the pipeline then uses plain stills rather
    than stopping over an optional effect (README, Setup > Draw-in).
    """
    return _python().exists()


def make_clip(image: Path, out: Path, seconds: float) -> None:
    """Render `image` drawing itself in over `seconds` to `out` (.mp4)."""
    import config

    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(_python()), __file__, str(config.DRAW_IN_REPO),
                    str(image), str(out), str(seconds),
                    str(config.FPS), str(config.WIDTH), str(config.HEIGHT)],
                   check=True)


if __name__ == "__main__":
    repo, image, out, seconds, fps, width, height = sys.argv[1:]
    sys.path.insert(0, repo)

    import numpy as np
    from PIL import Image
    from handdraw.render import render_video
    from handdraw.settings import Settings

    settings = Settings(
        duration=float(seconds),
        draw_percent=100,          # all drawing, no hold: the still does that
        fps=int(fps), width=int(width), height=int(height),
        fit="cover",               # crops exactly like StillImage's objectFit
        paper_color="#ffffff",
        device="cpu", encoder="cpu",
        show_hand=False,
        # Characters-first needs the ISNet download and was not needed on the
        # doodle style: flat colors on white already color cleanly.
        subject_first=False,
    )
    out = Path(out)
    video, _report = render_video(
        np.asarray(Image.open(image).convert("RGBA")), settings,
        output_dir=out.parent)
    Path(video).replace(out)
    Path(video).with_suffix(".json").unlink(missing_ok=True)
