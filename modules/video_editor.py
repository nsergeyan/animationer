"""
Stage: turn the manifest into the final video.

This module does NOT do the visual work itself. It hands the beats to the
Remotion project (remotion/) as input props, runs the render, then optionally
mixes a music bed with FFmpeg. Static frames, cuts and dissolves all live in
the Remotion composition.

The run folder is passed as Remotion's --public-dir, so the composition can
load each beat's image/audio by filename via staticFile().
"""

import json
import subprocess
import zlib
from pathlib import Path

import config


def render(manifest_path: Path, run_dir: Path,
           moods: dict[str, str] | None = None) -> Path:
    """
    Render the video from the manifest and return the final .mp4 path.

    `moods` maps location name -> mood. When given, the bed is built from the
    mood library and changes with the scenes (mix_moods); otherwise the single
    bed from find_music (an older run's own music.mp3) is laid under the
    whole video (mix_music).
    """
    out_path = run_dir / "final.mp4"

    beats = json.loads(manifest_path.read_text())
    # Remotion only sees what LectureVideo needs; the sound effects are mixed
    # in afterwards by mix_sfx.
    props = json.dumps({"beats": [{k: v for k, v in b.items() if k != "sfx"}
                                  for b in beats]})

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

    # Measured now, on narration alone: after the music is in, the level would
    # include the bed, and the effects would sit against the wrong number.
    speech = integrated_loudness(out_path) if any(b.get("sfx") for b in beats) else None

    if config.MUSIC_ENABLED:
        if moods:
            mix_moods(out_path, run_dir, beats, moods)
        else:
            mix_music(out_path, run_dir)

    if config.SFX_ENABLED and speech is not None:
        mix_sfx(out_path, beats, speech)

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

    Notes on the filter, because each of these is easy to get wrong:
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


# --- Mood music -------------------------------------------------------------
#
# The bed changes with the story: each location names a mood, each mood is a
# folder of pieces, and the music crossfades where the location changes. Built
# on the same idea as mix_music, but one input per section instead of one bed.

def mood_library() -> dict[str, list[Path]]:
    """Every mood folder under MUSIC_MOODS_DIR, with its audio files."""
    if not config.MUSIC_MOODS_DIR.exists():
        return {}
    return {
        d.name: sorted(p for p in d.iterdir() if p.suffix.lower() in AUDIO_SUFFIXES)
        for d in sorted(config.MUSIC_MOODS_DIR.iterdir())
        if d.is_dir() and not d.name.startswith((".", "_"))
    }


# OUTRO_FRAMES in constants.ts: held on the last picture after the final word.
OUTRO_HOLD_SECONDS = 1.0


def _beat_starts(beats: list[dict]) -> tuple[list[float], float]:
    """
    Each beat's start on the video timeline, and the total length, in seconds.

    Mirrors beatFrames/totalFrames in remotion/src/constants.ts, in frames so
    rounding matches: a beat lasts its audio, plus a cut pad on a hard cut. A
    dissolve's tail is eaten by its overlap, so it adds nothing. mix_moods
    checks the total against the rendered file, so drift gets reported.
    """
    pad = round(config.CUT_PAD_SECONDS * config.FPS)
    outro = round(OUTRO_HOLD_SECONDS * config.FPS)
    starts, frame = [], 0
    for i, beat in enumerate(beats):
        starts.append(frame / config.FPS)
        frame += max(1, round(beat["duration"] * config.FPS))
        if i + 1 < len(beats):
            nxt = beats[i + 1]
            same = bool(beat.get("location")) and beat.get("location") == nxt.get("location")
            if same and not nxt.get("redraw"):
                frame += pad
    return starts, (frame + outro) / config.FPS



def mood_plan(beats: list[dict], moods: dict[str, str], seed: str) -> list[dict]:
    """
    The bed as sections: [{"start", "end", "mood", "piece", "locations"}].

    Neighbouring locations with the same mood are one section, so the piece
    keeps playing instead of restarting. A beat with no location (the outro)
    stays in the section before it. Each mood gets ONE piece per video, so a
    location revisited later brings its music back with it.
    """
    library = mood_library()
    starts, total = _beat_starts(beats)
    sections: list[dict] = []
    for beat, start in zip(beats, starts):
        mood = moods.get(beat.get("location") or "")
        if not mood or (sections and sections[-1]["mood"] == mood):
            if sections and beat.get("location") and beat["location"] not in sections[-1]["locations"]:
                sections[-1]["locations"].append(beat["location"])
            continue
        piece = None
        if mood != config.MUSIC_SILENT_MOOD:
            files = library[mood]
            # crc32 rather than hash(): Python salts str hashes per process, so
            # hash() would pick a different piece on every render.
            piece = files[zlib.crc32(f"{seed}:{mood}".encode()) % len(files)]
        sections.append({"start": 0.0 if not sections else start, "mood": mood,
                         "piece": piece, "locations": [beat["location"]]})
    for k, sec in enumerate(sections):
        sec["end"] = sections[k + 1]["start"] if k + 1 < len(sections) else total
    return sections


def _levelled(piece: Path, cache_dir: Path) -> Path:
    """
    The piece evened out and set to MUSIC_MOOD_LEVEL_LUFS, cached per run.

    dynaudnorm lifts quiet passages and tames loud ones. Classical recordings
    swing from near-silence to full orchestra, and without this a solo piano
    vanished under the voice while an orchestra at the same average level
    still came through.
    """
    out = cache_dir / f"{piece.parent.name}_{piece.stem}.flac"
    if out.exists() and out.stat().st_mtime >= piece.stat().st_mtime:
        return out
    cache_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(piece),
         "-af", f"dynaudnorm=f=500:g=31,loudnorm=I={config.MUSIC_MOOD_LEVEL_LUFS}:LRA=7",
         "-ar", "44100", str(out)],
        check=True,
    )
    return out


def mix_moods(video_path: Path, run_dir: Path, beats: list[dict],
              moods: dict[str, str]) -> bool:
    """
    Lay a bed that follows the scenes under the narration, in place.

    Each section is its own ffmpeg input, trimmed to length and delayed to its
    start. Neighbours overlap by MUSIC_CROSSFADE_SECONDS centred on the
    location change, fading out and in across it. Same filter notes as
    mix_music apply (normalize=0, duration=first, -c:v copy). -stream_loop -1
    on every input lets a piece shorter than its section loop instead of
    ending early.
    """
    sections = mood_plan(beats, moods, run_dir.name)
    if not sections:
        return False

    length = video_duration(video_path)
    _, predicted = _beat_starts(beats)
    if abs(predicted - length) > 0.2:
        print(f"  [music] WARNING: timeline says {predicted:.2f}s, video is "
              f"{length:.2f}s - music switches may miss the scene changes. "
              f"Check _beat_starts against remotion/src/constants.ts.")
    sections[-1]["end"] = length

    speech = integrated_loudness(video_path)
    if speech is None:
        print("  [music] could not measure the narration, leaving audio as is")
        return False

    half = config.MUSIC_CROSSFADE_SECONDS / 2
    inputs, chains = [], []
    for k, sec in enumerate(sections):
        if sec["piece"] is None:
            print(f"  [music] {sec['start']:6.1f}s  silent    "
                  f"({', '.join(sec['locations'])})")
            continue
        piece = _levelled(sec["piece"], run_dir / "music_levelled")
        level = integrated_loudness(piece)
        under = config.MUSIC_MOOD_UNDER_DB + config.MUSIC_MOOD_EXTRA_DB.get(sec["mood"], 0.0)
        gain = (speech - under) - (level if level is not None
                                   else config.MUSIC_MOOD_LEVEL_LUFS)
        lead = half if k > 0 else 0.0
        tail = half if k + 1 < len(sections) else 0.0
        span = (sec["end"] - sec["start"]) + lead + tail
        fade_in = config.MUSIC_CROSSFADE_SECONDS if lead else 0.3
        fade_out = config.MUSIC_CROSSFADE_SECONDS if tail else config.MUSIC_FADE_SECONDS
        offset = 0.0
        if sec["mood"] in config.MUSIC_END_ALIGNED_MOODS:
            offset = max(0.0, video_duration(piece) - span)
        delay = int((sec["start"] - lead) * 1000)
        n = len(chains)
        inputs += ["-stream_loop", "-1", "-i", str(piece)]
        chains.append(
            f"[{n + 1}:a]atrim=start={offset:.2f}:duration={span:.2f},"
            f"asetpts=PTS-STARTPTS,volume={gain:.2f}dB,"
            f"afade=t=in:d={fade_in},"
            f"afade=t=out:st={max(0.0, span - fade_out):.2f}:d={fade_out},"
            f"adelay={delay}|{delay}[m{n}]"
        )
        print(f"  [music] {sec['start']:6.1f}s  {sec['mood']:9} {sec['piece'].name} "
              f"{under:.0f} dB under ({', '.join(sec['locations'])})")

    if not chains:
        return False
    labels = "".join(f"[m{k}]" for k in range(len(chains)))
    # The bed dips under every sound effect mix_sfx is about to lay in, so
    # music never buries one. Quoted because the expression is full of commas,
    # which would otherwise end the filter's argument.
    windows = sfx_windows(beats) if config.SFX_ENABLED else []
    duck = f",volume='{_duck_expr(windows)}':eval=frame" if windows else ""
    filters = ";".join(chains) + (
        f";{labels}amix=inputs={len(chains)}:normalize=0{duck}[bed]"
        f";[0:a][bed]amix=inputs=2:duration=first:normalize=0[out]"
    )
    if windows:
        print(f"  [music] dips {config.SFX_MUSIC_DUCK_DB:.0f} dB under "
              f"{len(windows)} sound effect(s)")
    mixed = video_path.with_suffix(".mixed.mp4")
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path), *inputs,
        "-filter_complex", filters,
        "-map", "0:v", "-map", "[out]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        str(mixed),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("  [music] ffmpeg failed, keeping the unmixed video:")
        print("   ", result.stderr.strip().splitlines()[-1][:160])
        mixed.unlink(missing_ok=True)
        return False

    mixed.replace(video_path)
    print(f"  [music] done, {len(sections)} section(s), "
          f"{config.MUSIC_MOOD_UNDER_DB:.0f} dB under the narration")
    return True


# --- Sound effects ----------------------------------------------------------
#
# Placed by pipeline.py cmd_manifest: every manifest entry may carry
# "sfx": [{"tag", "kind", "file", "at"}], `at` in seconds from the beat's
# start, `file` relative to config.SFX_DIR. The pauses the "after" and
# "transition" kinds need are already inside the beat's duration, so the
# picture timeline (Remotion) and _beat_starts agree on them for free.

def sfx_library() -> dict[str, list[Path]]:
    """Every tag folder under SFX_DIR, with its audio files."""
    if not config.SFX_DIR.exists():
        return {}
    return {
        d.name: sorted(p for p in d.iterdir() if p.suffix.lower() in AUDIO_SUFFIXES)
        for d in sorted(config.SFX_DIR.iterdir())
        if d.is_dir() and not d.name.startswith((".", "_"))
    }


def pick_sfx(files: list[Path], seed: str, tag: str, occurrence: int) -> Path:
    """
    The file for the Nth use of a tag in one video.

    Starts at a per-video offset and then rotates, so the same tag twice in a
    row never plays the same file (while the folder has more than one), and
    every render of the same run picks the same files. crc32, not hash(), for
    the reason given in mood_plan.
    """
    return files[(zlib.crc32(f"{seed}:{tag}".encode()) + occurrence) % len(files)]


def peak_loudness(path: Path) -> float | None:
    """
    The loudest 400ms of a sound (ebur128 momentary max), in LUFS.

    Integrated loudness is meaningless for a 0.3s click (it needs seconds of
    audio and mostly measures the silence around it), so effects are matched
    on their loudest moment instead, the part that actually gets heard.
    """
    result = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af", "apad=pad_dur=0.5,ebur128",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    loudest = None
    for line in result.stderr.splitlines():
        if " M:" in line:
            try:
                m = float(line.split(" M:")[1].split()[0])
            except (ValueError, IndexError):
                continue
            loudest = m if loudest is None else max(loudest, m)
    return loudest


def sfx_windows(beats: list[dict]) -> list[tuple[float, float, dict]]:
    """
    (start, end, effect) on the video timeline for every manifest effect,
    end = start + the length it will actually play (cut to its kind's max).
    Shared by mix_sfx, which plays them, and mix_moods, which dips the music
    under them, so the two always agree on where they are.
    """
    out = []
    for start, beat in zip(_beat_starts(beats)[0], beats):
        for s in beat.get("sfx") or []:
            path = config.SFX_DIR / s["file"]
            if not path.exists():
                continue
            cap = (config.SFX_TRANSITION_MAX_SECONDS if s["kind"] == "transition"
                   else config.SFX_MAX_SECONDS)
            when = start + s["at"]
            out.append((when, when + min(cap, video_duration(path)), s))
    return out


def _duck_expr(windows: list[tuple[float, float, dict]]) -> str:
    """
    A volume expression (for ffmpeg's volume filter, eval=frame) that dips by
    SFX_MUSIC_DUCK_DB inside every window, with a linear ramp either side so
    the bed slides down and back instead of clicking.
    """
    r = config.SFX_DUCK_RAMP_SECONDS
    parts = [f"clip((t-{a - r:.3f})/{r},0,1)*clip(({b + r:.3f}-t)/{r},0,1)"
             for a, b, _ in windows]
    depth = config.SFX_MUSIC_DUCK_DB / 20
    return f"pow(10,-{depth:.3f}*min(1,{'+'.join(parts)}))"


def mix_sfx(video_path: Path, beats: list[dict], speech: float) -> bool:
    """
    Lay every manifest sound effect into the video, in place.

    `speech` is the narration's integrated loudness, measured before the
    music went in. Each effect is cut to its kind's maximum length (with a
    fade), set config.SFX_UNDER_DB[kind] below the narration by its loudest
    moment, and delayed to its spot. Same filter notes as mix_music.
    """
    placed = sfx_windows(beats)
    if not placed:
        return False

    inputs, chains = [], []
    for when, end, s in placed:
        path = config.SFX_DIR / s["file"]
        level = peak_loudness(path) if path.exists() else None
        if level is None:
            print(f"  [sfx] missing or unreadable {s['file']}, skipped")
            continue
        gain = (speech - config.SFX_UNDER_DB[s["kind"]]) - level
        length = end - when
        fade = min(config.SFX_FADE_SECONDS, length / 2)
        delay = max(0, int(when * 1000))
        n = len(chains)
        inputs += ["-i", str(path)]
        chains.append(
            f"[{n + 1}:a]aformat=sample_rates=44100:channel_layouts=stereo,"
            f"atrim=duration={length:.2f},asetpts=PTS-STARTPTS,"
            f"volume={gain:.2f}dB,"
            f"afade=t=out:st={length - fade:.2f}:d={fade:.2f},"
            f"adelay=delays={delay}:all=1[s{n}]"
        )
        print(f"  [sfx] {when:6.1f}s  {s['kind']:10} {s['tag']:10} {path.name}")

    if not chains:
        return False
    labels = "".join(f"[s{k}]" for k in range(len(chains)))
    filters = ";".join(chains) + (
        f";[0:a]{labels}amix=inputs={len(chains) + 1}:duration=first:normalize=0[out]"
    )
    mixed = video_path.with_suffix(".sfx.mp4")
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path), *inputs,
        "-filter_complex", filters,
        "-map", "0:v", "-map", "[out]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        str(mixed),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("  [sfx] ffmpeg failed, keeping the video without effects:")
        print("   ", result.stderr.strip().splitlines()[-1][:160])
        mixed.unlink(missing_ok=True)
        return False

    mixed.replace(video_path)
    print(f"  [sfx] done, {len(chains)} effect(s)")
    return True
