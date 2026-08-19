"""
Stage: one narration clip per beat, using ElevenLabs.

Ported from the proven generator in Narek's shorts pipeline. Two details from
there are load-bearing and should not be "cleaned up":

  1. The US regional base URL (see config.ELEVENLABS_BASE_URL). The global
     endpoint returns a flat, robotic read on this account.
  2. English uses text_to_dialogue + eleven_v3, not text_to_speech. That is
     what produces the lively delivery and honours inline emotion tags such as
     [surprised] written into the narration.

Returns the audio path AND its duration, because Remotion shows each image for
exactly as long as its narration. The duration is measured AFTER the speed-up,
which is the number the video actually needs.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

# Running this file directly (for the quick test at the bottom) puts modules/
# on sys.path instead of the project root, so `import config` would fail.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elevenlabs.client import ElevenLabs
from elevenlabs.types import DialogueInput, ModelSettingsResponseModel

import config


def _api_keys() -> list[str]:
    """Support several comma-separated keys so one exhausted key can roll over."""
    raw = config.ELEVENLABS_API_KEY or ""
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    if not keys:
        raise RuntimeError(
            "ELEVENLABS_API_KEY is not set. Add it to .env "
            "(comma-separate several keys to allow fallback)."
        )
    return keys


def clean_text_for_speech(text: str) -> str:
    """Flatten whitespace and line breaks before sending text to ElevenLabs."""
    text = text.replace("\n", " ").replace("\r", " ")
    return re.sub(r"\s+", " ", text).strip()


def audio_duration(path: Path) -> float:
    """Exact duration via ffprobe - works for mp3/wav/m4a without extra deps."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def _source_bitrate_k() -> int:
    """
    Bitrate to re-encode at, taken from the requested output format.

    This matters more than it looks. atempo forces a re-encode, and without an
    explicit -b:a ffmpeg falls back to its own default - measured at 64kbps,
    which silently throws away most of the quality of the mp3_44100_192 we
    asked ElevenLabs for.
    """
    tail = config.ELEVENLABS_OUTPUT_FORMAT.rsplit("_", 1)[-1]
    return int(tail) if tail.isdigit() else 192


def _speed_up(path: Path, factor: float) -> None:
    """Apply atempo in place, via a temp file so a failure cannot truncate."""
    if factor == 1.0:
        return
    sped = path.with_suffix(path.suffix + ".fast.mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(path), "-filter:a", f"atempo={factor}",
         "-b:a", f"{_source_bitrate_k()}k", str(sped)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
    )
    os.replace(sped, path)


def _generate_with_key(api_key: str, text: str, out_path: Path,
                       voice_id: str, lang: str) -> bool:
    """One attempt with one key. True on success."""
    client = ElevenLabs(api_key=api_key, base_url=config.ELEVENLABS_BASE_URL)
    tmp_path = out_path.with_suffix(out_path.suffix + ".partial")

    try:
        cleaned = clean_text_for_speech(text)

        if lang in ("ru", "es"):
            stream = client.text_to_speech.convert(
                text=cleaned,
                voice_id=voice_id,
                model_id=config.ELEVENLABS_MODEL_MULTILINGUAL,
                output_format=config.ELEVENLABS_OUTPUT_FORMAT,
            )
        else:
            stream = client.text_to_dialogue.convert(
                inputs=[DialogueInput(text=cleaned, voice_id=voice_id)],
                model_id=config.ELEVENLABS_MODEL_DIALOGUE,
                settings=ModelSettingsResponseModel(
                    stability=config.ELEVENLABS_STABILITY),
                output_format=config.ELEVENLABS_OUTPUT_FORMAT,
            )

        # Write to .partial first: a half-written mp3 left at the real path
        # would be treated as done by the resume check on the next run.
        with open(tmp_path, "wb") as f:
            for chunk in stream:
                f.write(chunk)
        os.replace(tmp_path, out_path)

        _speed_up(out_path, config.NARRATION_SPEED)
        return True

    except Exception as exc:
        if tmp_path.exists():
            tmp_path.unlink()
        print(f"    [voice] key {api_key[:6]}... failed: "
              f"{type(exc).__name__}: {exc}")
        return False


def _resolve_voice_id(voice: str | None) -> str:
    name = voice or config.ELEVENLABS_DEFAULT_VOICE
    return config.ELEVENLABS_VOICES.get(
        name, config.ELEVENLABS_VOICES[config.ELEVENLABS_DEFAULT_VOICE])


def generate(narration: str, index: int, out_dir: Path,
             voice: str | None = None, lang: str = "en") -> tuple[Path, float]:
    """Generate beat_{index:03}.mp3 and return (path, duration_after_speedup)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"beat_{index:03}.mp3"
    voice_id = _resolve_voice_id(voice)

    for api_key in _api_keys():
        if _generate_with_key(api_key, narration, out_path, voice_id, lang):
            return out_path, audio_duration(out_path)
        print("    [voice] trying next key...")

    raise RuntimeError(f"All ElevenLabs keys failed for beat {index}.")


# ===========================================================================
# BATCHED GENERATION - the consistency fix
#
# eleven_v3 is non-deterministic AND is excluded from request stitching, so
# there is no way to condition one request on the last one. Generating beats
# one at a time therefore produces N separate performances that drift apart.
#
# Sending several beats in ONE request makes them a single performance, so
# they match by construction. The reply carries `voice_segments`, each with a
# `dialogue_input_index` naming which beat it came from plus its start and end
# time, so the batch audio can be cut back into the same per-beat files the
# rest of the pipeline already expects. Nothing downstream changes.
# ===========================================================================

def _cut(src: Path, dst: Path, start: float, end: float) -> None:
    """
    Extract start..end from src.

    -ss goes AFTER -i deliberately: before -i is faster but seeks to the
    nearest keyframe, and mp3 frames are ~26ms, which is enough slip to clip a
    consonant off the front of a beat. Re-encoding at the source bitrate for
    the same reason _speed_up does it.
    """
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-ss", f"{start:.3f}",
         "-to", f"{end:.3f}", "-b:a", f"{_source_bitrate_k()}k", str(dst)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
    )


def _spans_from_segments(segments, count: int) -> list[tuple[float, float]]:
    """
    Collapse voice_segments into one (start, end) per dialogue input.

    A single input can come back as more than one segment, so take the
    earliest start and latest end for each index. Raises if any beat is
    unaccounted for, which is the signal to fall back to per-beat generation
    rather than write a file with the wrong audio in it.
    """
    spans: dict[int, list[float]] = {}
    for seg in segments:
        i = seg.dialogue_input_index
        lo, hi = seg.start_time_seconds, seg.end_time_seconds
        if i in spans:
            spans[i] = [min(spans[i][0], lo), max(spans[i][1], hi)]
        else:
            spans[i] = [lo, hi]

    missing = [i for i in range(count) if i not in spans]
    if missing:
        raise RuntimeError(
            f"voice_segments covered {len(spans)} of {count} beats "
            f"(missing input index {missing})")
    return [tuple(spans[i]) for i in range(count)]


def _batch_with_key(api_key: str, narrations: list[str], indices: list[int],
                    out_dir: Path, voice_id: str) -> list[tuple[Path, float]]:
    """One batched attempt with one key. Raises on any problem."""
    import base64

    client = ElevenLabs(api_key=api_key, base_url=config.ELEVENLABS_BASE_URL)
    cleaned = [clean_text_for_speech(t) for t in narrations]

    resp = client.text_to_dialogue.convert_with_timestamps(
        inputs=[DialogueInput(text=t, voice_id=voice_id) for t in cleaned],
        model_id=config.ELEVENLABS_MODEL_DIALOGUE,
        settings=ModelSettingsResponseModel(
            stability=config.ELEVENLABS_STABILITY),
        output_format=config.ELEVENLABS_OUTPUT_FORMAT,
    )

    batch_path = out_dir / f"_batch_{indices[0]:03}_{indices[-1]:03}.mp3"
    batch_path.write_bytes(base64.b64decode(resp.audio_base_64))
    total = audio_duration(batch_path)

    spans = _spans_from_segments(resp.voice_segments, len(cleaned))

    # Cut where the NEXT beat starts speaking, not at the midpoint of the gap.
    #
    # Midpoint looks fairer but breaks whenever the model runs two beats
    # together with no pause: the "middle of the gap" is then inside a word.
    # Ending each beat just before its successor begins cannot do that, and it
    # gives every beat its own trailing breath, which is what you want anyway
    # since the image holds until the next narration starts.
    #
    # GUARD is a hair of lead-in so a beat does not open hard on a consonant.
    # max() keeps it from ever eating the current beat's own last syllable.
    GUARD = 0.025
    bounds, prev_end = [], 0.0
    for i, (start, end) in enumerate(spans):
        if i == len(spans) - 1:
            hi = total
        else:
            # Never past the next beat's first sample: if two segments overlap,
            # losing this beat's trailing decay is far better than lopping the
            # opening consonant off the next one.
            hi = min(max(end, spans[i + 1][0] - GUARD), spans[i + 1][0])
        bounds.append((prev_end, hi))
        prev_end = hi

    results = []
    try:
        for index, (lo, hi) in zip(indices, bounds):
            out_path = out_dir / f"beat_{index:03}.mp3"
            tmp = out_path.with_suffix(".partial.mp3")
            _cut(batch_path, tmp, lo, hi)
            os.replace(tmp, out_path)
            _speed_up(out_path, config.NARRATION_SPEED)
            results.append((out_path, audio_duration(out_path)))
    except Exception:
        for path, _ in results:            # don't leave half a batch behind
            path.unlink(missing_ok=True)
        raise
    finally:
        batch_path.unlink(missing_ok=True)

    return results


def generate_batch(narrations: list[str], indices: list[int], out_dir: Path,
                   voice: str | None = None) -> list[tuple[Path, float]]:
    """
    Generate several beats as ONE performance and cut them apart.

    English only - the ru/es path uses text_to_speech, which has request
    stitching available and does not need this. Raises if every key fails, so
    the caller can fall back to per-beat generation.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    voice_id = _resolve_voice_id(voice)

    last = None
    for api_key in _api_keys():
        try:
            return _batch_with_key(api_key, narrations, indices,
                                   out_dir, voice_id)
        except Exception as exc:
            last = exc
            print(f"    [voice] batch failed on key {api_key[:6]}...: "
                  f"{type(exc).__name__}: {exc}")

    raise RuntimeError(
        f"Batched generation failed for beats "
        f"{indices[0]}-{indices[-1]}: {last}")


# ===========================================================================
# QUICK TEST - run this file directly to hear a script without the pipeline.
#
#     python modules/voice_generator.py
#
# Edit TEST_SCRIPT, pick a voice, set how many takes you want. Files land in
# output/_voicetest/ and are numbered, so you can generate three takes of the
# same line and pick the best. eleven_v3 is not deterministic, so takes differ.
# ===========================================================================

TEST_SCRIPT = (
    "[surprised] According to the official fanbook, the cursed fingers "
    "apparently taste exactly like ordinary household soap. They are coated in "
    "the waxy substance that forms on bodies sealed away for centuries."
)

TEST_VOICE = None      # None = config.ELEVENLABS_DEFAULT_VOICE
TEST_TAKES = 2
TEST_LANG = "en"


if __name__ == "__main__":
    from modules.transcriber import strip_tags

    out_dir = config.OUTPUT_DIR / "_voicetest"
    voice = TEST_VOICE or config.ELEVENLABS_DEFAULT_VOICE
    # Emotion tags are delivery instructions, not spoken words, so they must
    # not count toward the words-per-minute figure printed below.
    words = len(strip_tags(TEST_SCRIPT).split())

    print(f"voice  : {voice} ({config.ELEVENLABS_VOICES.get(voice, '?')})")
    print(f"model  : {config.ELEVENLABS_MODEL_DIALOGUE}")
    print(f"speed  : {config.NARRATION_SPEED}x"
          f"{' (no speed-up)' if config.NARRATION_SPEED == 1.0 else ''}")
    print(f"script : {words} words\n")

    for take in range(1, TEST_TAKES + 1):
        try:
            path, seconds = generate(TEST_SCRIPT, take, out_dir,
                                     voice=voice, lang=TEST_LANG)
        except Exception as exc:
            print(f"take {take}: FAILED - {type(exc).__name__}: {exc}")
            sys.exit(1)

        # Words per minute is the number that actually matters for scripting:
        # it tells you how many words fit in a beat of a given length.
        wpm = words / seconds * 60 if seconds else 0
        print(f"take {take}: {path}  {seconds:.2f}s  ({wpm:.0f} wpm)")

    print(f"\nA {words}-word beat runs ~{seconds:.1f}s at this voice and speed.")
    print(f"Open {out_dir} to listen.")
