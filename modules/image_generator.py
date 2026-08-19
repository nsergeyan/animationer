"""
Stage: one still image per beat, using Gemini image model ("Nano Banana").

Consistency trick: every call also passes the reference art in assets/reference/
so characters and world stay on-model across ~100 generations.

FIRST DRAFT - not yet run against the live API. Check the google-genai response
shape (how image bytes come back) against current SDK docs before trusting.
"""

from pathlib import Path

from google import genai

import config

_client = genai.Client(api_key=config.GEMINI_API_KEY)


def _reference_images():
    """Load every file in assets/reference/ to pass alongside the prompt."""
    if not config.REFERENCE_DIR.exists():
        return []
    return [p for p in sorted(config.REFERENCE_DIR.iterdir()) if p.is_file()]


def generate(image_prompt: str, index: int, run_dir: Path) -> Path:
    """Generate beat_{index:03}.png and return its path."""
    out_path = run_dir / f"beat_{index:03}.png"

    refs = _reference_images()
    # TODO: verify - contents may need genai.types.Part.from_bytes(...) for images.
    contents = [image_prompt]
    for ref in refs:
        contents.append(genai.types.Part.from_bytes(
            data=ref.read_bytes(),
            mime_type="image/png",
        ))

    response = _client.models.generate_content(
        model=config.IMAGE_MODEL,
        contents=contents,
    )

    # TODO: verify - image bytes location in the response object.
    image_bytes = None
    for part in response.candidates[0].content.parts:
        if getattr(part, "inline_data", None):
            image_bytes = part.inline_data.data
            break
    if image_bytes is None:
        raise RuntimeError(f"No image returned for beat {index}")

    out_path.write_bytes(image_bytes)
    print(f"  [image] beat {index:03} -> {out_path.name}")
    return out_path
