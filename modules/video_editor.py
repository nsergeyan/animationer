"""
Stage: turn the manifest into the final video.

This module does NOT do the visual work itself. It hands the beats to the
Remotion project (remotion/) as input props, runs the render, then optionally
mixes a music bed with FFmpeg. Ken Burns pan/zoom, crossfades and subtitles
all live in the Remotion composition.

The run folder is passed as Remotion's --public-dir, so the composition can
load each beat's image/audio by filename via staticFile().
"""

import json
import subprocess
from pathlib import Path

import config


def render(manifest_path: Path, run_dir: Path, music_prompt: str | None = None) -> Path:
    """Render the video from the manifest and return the final .mp4 path."""
    out_path = run_dir / "final.mp4"

    beats = json.loads(manifest_path.read_text())
    props = json.dumps({"beats": beats})

    cmd = [
        "npx", "remotion", "render",
        "src/index.ts",                       # entry
        "LectureVideo",                       # composition id
        str(out_path.resolve()),
        f"--props={props}",
        f"--public-dir={run_dir.resolve()}",  # so staticFile() finds the beats
    ]
    print(f"  [video] rendering with Remotion -> {out_path.name}")
    subprocess.run(cmd, cwd=str(config.REMOTION_DIR), check=True)

    if config.MUSIC_ENABLED:
        mix_music(out_path, run_dir)

    return out_path


AUDIO_SUFFIXES = (".mp3", ".wav", ".m4a", ".aac", ".flac")


def find_music(run_dir: Path | None = None) -> Path | None:
    """
    The bed to use: this run's composed music if it has one, else the shared
    fallback in assets/music/. Per-video wins so each script gets its own mood.
    """
    if run_dir is not None:
        own = run_dir / "music.mp3"
        if own.exists():
            return own
    if not config.MUSIC_DIR.exists():
        return None
    return next((p for p in sorted(config.MUSIC_DIR.iterdir())
                 if p.suffix.lower() in AUDIO_SUFFIXES), None)


def video_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def integrated_loudness(path: Path) -> float | None:
    """Integrated loudness in LUFS via ffmpeg's ebur128, or None."""
    result = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af", "ebur128=framelog=verbose", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    for line in reversed(result.stderr.splitlines()):
        if "I:" in line and "LUFS" in line:
            try:
                return float(line.split("I:")[1].split("LUFS")[0].strip())
            except ValueError:
                return None
    return None


def music_gain_db(video_path: Path, music_path: Path) -> float:
    """
    Gain that puts the bed MUSIC_DUCK_DB below the narration.

    Measured rather than assumed, because per-video music comes back at
    whatever level it comes back at. Falls back to MUSIC_VOLUME if either
    measurement fails, so a broken read never stops the render.
    """
    speech = integrated_loudness(video_path)
    music = integrated_loudness(music_path)
    if speech is None or music is None:
        import math
        fallback = 20 * math.log10(config.MUSIC_VOLUME)
        print(f"  [music] could not measure loudness, using {fallback:+.1f} dB")
        return fallback

    gain = (speech - config.MUSIC_DUCK_DB) - music
    print(f"  [music] narration {speech:.1f} LUFS, bed {music:.1f} LUFS "
          f"-> {gain:+.1f} dB to sit {config.MUSIC_DUCK_DB:.0f} dB under")
    return gain


def mix_music(video_path: Path, run_dir: Path | None = None) -> bool:
    """
    Lay the music bed under the narration, in place.

    Notes on the filter, because two of these are easy to get wrong:
      - normalize=0 on amix. Without it amix divides every input by the number
        of inputs, so the narration would come out at half volume purely for
        having music alongside it.
      - -stream_loop -1 repeats a short bed to cover a long video, and
        duration=first ends the mix when the narration track ends rather than
        running on for the length of the loop.
      - -c:v copy leaves the video stream untouched, so this costs seconds and
        loses no quality.
    """
    music = find_music(run_dir)
    if music is None:
        print(f"  [music] no track in {config.MUSIC_DIR.name}/, leaving audio as is")
        return False

    length = video_duration(video_path)
    fade_at = max(0.0, length - config.MUSIC_FADE_SECONDS)
    mixed = video_path.with_suffix(".mixed.mp4")

    gain = music_gain_db(video_path, music)
    filters = (
        f"[1:a]volume={gain:.2f}dB,"
        f"afade=t=out:st={fade_at:.2f}:d={config.MUSIC_FADE_SECONDS}[bed];"
        f"[0:a][bed]amix=inputs=2:duration=first:normalize=0[out]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-stream_loop", "-1", "-i", str(music),
        "-filter_complex", filters,
        "-map", "0:v", "-map", "[out]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(mixed),
    ]
    print(f"  [music] mixing {music.name}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [music] ffmpeg failed, keeping the unmixed video:")
        print("   ", result.stderr.strip().splitlines()[-1][:160])
        mixed.unlink(missing_ok=True)
        return False

    mixed.replace(video_path)
    print(f"  [music] done, faded out over the last "
          f"{config.MUSIC_FADE_SECONDS:.0f}s")
    return True
