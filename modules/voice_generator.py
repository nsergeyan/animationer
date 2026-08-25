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


# How much shorter than its text a cut beat is allowed to be before the batch
# is rejected. Generous on purpose: a cut includes trailing silence so it is
# normally LONGER than the speech, and eleven_v3's pace varies with the emotion
# tag. This is a guard against a fragment, not a tolerance check - the real
# failures it catches come back at a tenth of their expected length.
MIN_SPEECH_RATIO = 0.45

# A hair of lead-in so a beat does not open hard on a consonant.
GUARD = 0.025

# How far from the timestamp's guess to look for real silence, in seconds.
#
# 0.75 was too tight. On a real 55-beat run three beats still clipped, and in
# every case the correct silence existed but sat just beyond the window - the
# 9/10 boundary needed 0.83s. Widening it is safe because SNAP_BACK_TOLERANCE
# already stops a snap reaching backwards into the beat's own speech, so the
# extra reach only ever goes forward, toward the pause that was missed.
SNAP_WINDOW = 1.3

# How far before a beat's own reported end a boundary may ever be placed.
SNAP_BACK_TOLERANCE = 0.15

# A cut whose last 80ms is within this many dB of the beat's own average volume
# was made while the voice was still speaking. Measured, not guessed: on a real
# 55-beat run the clean beats ended 12 to 45 dB down, and every audibly clipped
# one ended within 3 dB of its own average or LOUDER.
CLIPPED_TAIL_DB = 3.0
TAIL_SECONDS = 0.08


def _silences(path: Path, floor_db: float = -40.0,
              min_len: float = 0.05) -> list[tuple[float, float]]:
    """
    Every stretch of near-silence in a file, via ffmpeg's silencedetect.

    This is the ground truth the reported segment timings are checked against.
    Returns [] on any parsing trouble, which makes the caller fall back to the
    timings alone - the old behaviour.
    """
    out = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(path),
         "-af", f"silencedetect=n={floor_db}dB:d={min_len}", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    spans, start = [], None
    for line in out.splitlines():
        if "silence_start:" in line:
            try:
                start = float(line.split("silence_start:")[1].split()[0])
            except (IndexError, ValueError):
                start = None
        elif "silence_end:" in line and start is not None:
            try:
                spans.append((start, float(line.split("silence_end:")[1].split()[0])))
            except (IndexError, ValueError):
                pass
            start = None
    return spans


def _snap_to_silence(guess: float, silences: list[tuple[float, float]],
                     floor: float) -> float | None:
    """
    Move a boundary onto real silence, or None if there is none nearby.

    Cuts at the END of the silence rather than its middle, keeping the original
    design's intent: the pause belongs to the beat that just finished, because
    the image holds until the next narration starts.
    """
    best, best_distance = None, None
    for lo, hi in silences:
        if hi <= floor:
            continue
        inside = lo <= guess <= hi
        distance = 0.0 if inside else min(abs(lo - guess), abs(hi - guess))
        if distance > SNAP_WINDOW:
            continue
        if best_distance is None or distance < best_distance:
            cut = max(lo + 0.01, hi - GUARD)
            if cut > floor:
                best, best_distance = cut, distance
    return best


def _edge_versus_average(path: Path, head: bool = False) -> float | None:
    """
    How loud a file's first or last TAIL_SECONDS is against its own average.

    Near zero (or positive) means the file starts or ends at full speaking
    volume, which only happens when a cut landed inside a word. The head check
    exists because widening SNAP_WINDOW lets a boundary reach further forward,
    and overshooting eats the NEXT beat's opening instead of this one's tail.
    """
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le",
         "-ac", "1", "-ar", "16000", "-"],
        capture_output=True,
    ).stdout
    import array
    import math
    samples = array.array("h")
    samples.frombytes(raw[:len(raw) // 2 * 2])
    if not len(samples):
        return None

    def rms_db(chunk):
        if not len(chunk):
            return None
        total = sum(float(v) * v for v in chunk)
        if total <= 0:
            return -99.0
        return 20 * math.log10(math.sqrt(total / len(chunk)) / 32768)

    overall = rms_db(samples)
    n = int(TAIL_SECONDS * 16000)
    edge = rms_db(samples[:n] if head else samples[-n:])
    if overall is None or edge is None:
        return None
    return edge - overall


def _minimum_plausible_seconds(text: str) -> float:
    """Shortest run time the words could plausibly have, tags excluded."""
    import re
    words = len(re.sub(r"\[[^\]]*\]", " ", text).split())
    if not words:
        return 0.0
    expected = words / config.WORDS_PER_MINUTE * 60 / config.NARRATION_SPEED
    return expected * MIN_SPEECH_RATIO


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
    # Real silence in the audio, which is what boundaries actually get placed
    # on. The reported timings only choose WHICH silence.
    silences = _silences(batch_path)
    snapped = 0

    bounds, prev_end = [], 0.0
    for i, (start, end) in enumerate(spans):
        if i == len(spans) - 1:
            hi = total
        elif end <= spans[i + 1][0]:
            # There is a real gap between the two. End this beat just before
            # the next one opens, so it keeps its own trailing breath.
            hi = max(end, spans[i + 1][0] - GUARD)
        else:
            # The segments OVERLAP. Two sequential utterances cannot really
            # overlap, so this is timestamp imprecision, and the disputed span
            # has to go to one of them.
            #
            # This used to hand the whole overlap to the NEXT beat
            # (hi = spans[i+1][0]), which silently truncated THIS beat by the
            # full width of the error. That was survivable at nineteen words a
            # beat, where the model always left a clear pause. At four to eight
            # words it runs sentences straight together, overlaps are common,
            # and the clipped syllable is audible.
            #
            # Splitting the overlap means neither beat can lose more than half
            # the error.
            hi = (end + spans[i + 1][0]) / 2

        # Now put it on real silence. eleven_v3's reported timings are simply
        # not reliable for short utterances - on a measured 55-beat run, ten
        # beats were severed at full speaking volume, three of them LOUDER at
        # the cut than their own average. No arithmetic on those numbers can
        # fix that, so the timings are demoted to choosing WHICH silence and
        # the audio itself decides where the cut lands.
        if i != len(spans) - 1 and silences:
            # Never snap back past this beat's OWN reported end. The observed
            # failure is the NEXT beat's start coming back too early while this
            # beat's end is roughly right, so the end is the trustworthy side
            # of the boundary. Without this floor a large timing error can pull
            # the cut onto a pause INSIDE the beat and lop off its last clause,
            # which is a quieter wrong answer than a severed word, not a right
            # one. SNAP_BACK_TOLERANCE leaves a little room for the end itself
            # being slightly late.
            floor = max(prev_end, end - SNAP_BACK_TOLERANCE)
            landed = _snap_to_silence(hi, silences, floor)
            if landed is not None:
                if abs(landed - hi) > 0.001:
                    snapped += 1
                hi = landed

        if hi <= prev_end:
            # Non-monotonic spans would make ffmpeg write an empty file, and a
            # beat with no narration in it is far worse than a slow re-run.
            # Raising falls the whole batch back to one request per beat.
            raise RuntimeError(
                f"beat {i + 1} of the batch got a non-positive span "
                f"({prev_end:.3f} -> {hi:.3f}); segment timings are unusable")
        bounds.append((prev_end, hi))
        prev_end = hi

    results = []
    clipped: list[tuple[int, float, str]] = []
    try:
        for index, (lo, hi), text in zip(indices, bounds, cleaned):
            out_path = out_dir / f"beat_{index:03}.mp3"
            tmp = out_path.with_suffix(".partial.mp3")
            _cut(batch_path, tmp, lo, hi)
            os.replace(tmp, out_path)
            _speed_up(out_path, config.NARRATION_SPEED)
            got = audio_duration(out_path)

            # A cut that came out far shorter than the words could possibly be
            # spoken in means the segment timings were wrong, and the file now
            # holds a fragment of a sentence. Catch it here rather than letting
            # a half-spoken beat reach the render.
            floor = _minimum_plausible_seconds(text)
            if got < floor:
                raise RuntimeError(
                    f"beat {index} cut to {got:.2f}s but its text needs at "
                    f"least {floor:.2f}s - segment timings are unusable")

            # Direct measurement of the actual defect: did this file end while
            # the voice was still going? Reported rather than raised, because
            # rejecting the batch costs all fourteen beats their shared
            # performance, and one bad tail is not worth that trade.
            tail = _edge_versus_average(out_path)
            if tail is not None and tail > -CLIPPED_TAIL_DB:
                clipped.append((index, tail, "end"))
            head = _edge_versus_average(out_path, head=True)
            if head is not None and head > -CLIPPED_TAIL_DB:
                clipped.append((index, head, "start"))
            results.append((out_path, got))
    except Exception:
        for path, _ in results:            # don't leave half a batch behind
            path.unlink(missing_ok=True)
        raise
    finally:
        batch_path.unlink(missing_ok=True)

    if snapped:
        print(f"    [voice] {snapped}/{len(bounds) - 1} boundaries moved onto "
              f"real silence")
    if clipped:
        listed = ", ".join(f"{i} {w} ({d:+.0f}dB)" for i, d, w in clipped[:8])
        print(f"    [voice] WARNING: {len(clipped)} cut(s) landed inside a "
              f"word: {listed}")
        print(f"    [voice] re-run those alone: pipeline.py voice --force "
              f"--only {','.join(str(i) for i, _, _ in sorted(set((c[0],) for c in clipped)))}")

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

# A short beat followed by a long one, so a manual take exercises the two-tier
# rhythm the pipeline actually ships rather than one uniform-length sentence.
TEST_SCRIPT = (
    "[surprised] Nobody signed off on this. "
    "According to the official fanbook, the cursed fingers taste exactly like "
    "ordinary household soap, because of the waxy substance that forms on "
    "bodies sealed away for centuries."
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
