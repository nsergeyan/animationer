"""
Stage: word-level timings, so subtitles highlight the word actually being said.

Without this the Remotion subtitle guesses each word's moment by splitting the
beat up by character count. That is fine for a five second beat and visibly
drifts on a fifteen second one.

Two things worth knowing:

  - We already KNOW the words. Whisper is only being used to find out WHEN each
    one is spoken, so a big model buys nothing: on clean synthetic speech
    'base' and 'small' produce identical output in about a second. Recognition
    accuracy is not the bottleneck, alignment is.

  - Whisper's transcript is therefore not trusted for TEXT. Its words are
    aligned against the script's own words and the script always wins, so a
    misheard word can shift a timing but can never put the wrong word on
    screen.
"""

import difflib
import re
from pathlib import Path

import config

_models = {}


def _model(name: str):
    """Load once and keep it - loading costs about as much as transcribing."""
    if name not in _models:
        import whisper                    # heavy import, only when actually used
        print(f"  [whisper] loading '{name}' model")
        _models[name] = whisper.load_model(name)
    return _models[name]


def strip_tags(text: str) -> str:
    """
    Remove ElevenLabs emotion tags like [surprised].

    They are delivery instructions, consumed by the voice model and never
    spoken, so they must not reach the screen either.
    """
    return re.sub(r"\s+", " ", re.sub(r"\[[^\]]*\]", " ", text)).strip()


def _norm(word: str) -> str:
    return re.sub(r"[^a-z0-9]", "", word.lower())


def transcribe_words(audio_path: Path, language: str = "en") -> list[dict]:
    """Raw Whisper output: [{"word", "start", "end"}, ...]."""
    result = _model(config.WHISPER_MODEL).transcribe(
        str(audio_path), word_timestamps=True, language=language,
        verbose=False,
    )
    return [
        {"word": w["word"].strip(), "start": float(w["start"]), "end": float(w["end"])}
        for seg in result.get("segments", [])
        for w in seg.get("words", [])
    ]


def align(narration: str, audio_path: Path, language: str = "en") -> list[dict]:
    """
    Time the script's own words against the audio.

    Returns [{"w": str, "s": float, "e": float}, ...] using the SCRIPT's words
    with Whisper's timings. Words Whisper missed get interpolated from their
    neighbours rather than dropped, so the list always matches the narration
    one-for-one and the subtitle can never fall out of step with the text.
    """
    script_words = strip_tags(narration).split()
    if not script_words:
        return []

    heard = transcribe_words(audio_path, language)
    if not heard:
        return []

    matcher = difflib.SequenceMatcher(
        a=[_norm(w) for w in script_words],
        b=[_norm(w["word"]) for w in heard],
        autojunk=False,
    )

    timed: list[dict | None] = [None] * len(script_words)
    for ai, bi, size in matcher.get_matching_blocks():
        for k in range(size):
            h = heard[bi + k]
            timed[ai + k] = {"w": script_words[ai + k],
                             "s": round(h["start"], 3), "e": round(h["end"], 3)}

    # Fill gaps by spreading the span between the nearest timed neighbours.
    total = heard[-1]["end"]
    for i, entry in enumerate(timed):
        if entry is not None:
            continue
        prev = next((timed[j] for j in range(i - 1, -1, -1) if timed[j]), None)
        nxt = next((timed[j] for j in range(i + 1, len(timed)) if timed[j]), None)
        start = prev["e"] if prev else 0.0
        end = nxt["s"] if nxt else total
        if end < start:
            end = start
        timed[i] = {"w": script_words[i],
                    "s": round(start, 3), "e": round(max(end, start), 3)}

    return timed
