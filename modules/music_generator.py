"""
Stage: a music bed composed for this specific video, via ElevenLabs Music.

The prompt comes from the script's own "music_prompt" field, so a bleak what-if
and a silly skit get different beds while still sounding like the same channel.

force_instrumental is always on. Any sung or spoken vocal competes directly with
the narrator for the same frequency range, and no mixing level rescues that.
"""

import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elevenlabs.client import ElevenLabs

import config


def _api_keys() -> list[str]:
    raw = config.ELEVENLABS_API_KEY or ""
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    if not keys:
        raise RuntimeError("ELEVENLABS_API_KEY is not set.")
    return keys


def generate(prompt: str, seconds: float, out_path: Path) -> Path:
    """
    Compose a bed of roughly `seconds` length and write it to out_path.

    Length is clamped to what the API accepts. Coming up short is harmless -
    video_editor loops the bed to cover the video - so it is better to ask for
    a legal length than to fail the whole render over it.
    """
    length_ms = int(max(config.MUSIC_MIN_SECONDS,
                        min(seconds, config.MUSIC_MAX_SECONDS)) * 1000)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".partial")

    last_error = None
    for api_key in _api_keys():
        client = ElevenLabs(api_key=api_key, base_url=config.ELEVENLABS_BASE_URL)
        try:
            stream = client.music.compose(
                prompt=prompt,
                music_length_ms=length_ms,
                # Never let it sing. A vocal line sits exactly where the
                # narrator sits and no mix level fixes that.
                force_instrumental=True,
                output_format=config.ELEVENLABS_OUTPUT_FORMAT,
            )
            with open(tmp_path, "wb") as f:
                for chunk in stream:
                    f.write(chunk)
            os.replace(tmp_path, out_path)
            return out_path
        except Exception as exc:
            last_error = exc
            if tmp_path.exists():
                tmp_path.unlink()
            print(f"  [music] key {api_key[:6]}... failed: "
                  f"{type(exc).__name__}: {exc}")

    raise RuntimeError(f"All ElevenLabs keys failed composing music: {last_error}")


# ===========================================================================
# QUICK TEST - hear a bed without running the pipeline.
#     python modules/music_generator.py
# ===========================================================================

TEST_PROMPT = (
    "Warm, low-key instrumental loop for a deadpan comedy explainer video. "
    "Relaxed lo-fi beat around eighty BPM with soft muted electric piano, "
    "gentle plucked bass and light brushed drums. Flat consistent energy with "
    "no build, no swells and no drops, sitting far in the background under a "
    "spoken narrator with the mid range left clear."
)
TEST_SECONDS = 30

if __name__ == "__main__":
    out = config.OUTPUT_DIR / "_musictest" / "bed.mp3"
    print(f"prompt : {TEST_PROMPT[:70]}...")
    print(f"length : {TEST_SECONDS}s\n")
    path = generate(TEST_PROMPT, TEST_SECONDS, out)
    size = path.stat().st_size // 1024
    print(f"done -> {path}  ({size} KB)")
