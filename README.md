# Animationer

An automated pipeline that turns a single topic into a finished, narrated, 16:9
animated video, no manual editing. Built to run an anime/history "lore"
YouTube Shorts / TikTok channel end to end: one script in, one `.mp4` out.

A script of ~30-100 short beats (narration sentence + image description) goes
in. Each beat becomes one AI-generated still, one narrated audio clip timed to
the narration, and one entry in a final Remotion render with Ken Burns
pan/zoom, crossfades, and a music bed mixed under the voice.

## Why this exists

This is a personal side project to automate a Shorts channel without paying
for editing time per video. The interesting part isn't "call an AI image API
in a loop", it's the engineering needed to make that loop actually reliable:

- **Character consistency across ~100 generations.** Every image call carries
  the same hand-drawn reference art (`assets/reference/`), and the style
  instructions in `config.py` are written defensively based on real failure
  modes (Nano Banana grounding a photorealistic prompt against a real photo,
  inventing readable-but-garbled text on signs, drawing its own UI chrome
  into the frame). Each rule in there exists because a specific bad output
  happened first.
- **No usable image API on this account**, so `flow_runner/` drives Google
  Flow's actual web UI with Playwright instead: human logs in once, the
  script types prompts, uploads/attaches the reference image, and reads
  results back off the DOM. It paces itself like a human (randomized delays,
  pasted rather than keystroke-perfect text), detects policy rejections vs.
  quota exhaustion vs. one-model-exhausted, and falls back down a model
  ladder (Pro -> Standard -> Lite) rather than stalling the whole run.
- **Non-deterministic TTS drift.** ElevenLabs' `eleven_v3` model isn't
  deterministic and can't be told what a previous call sounded like, so
  generating each beat separately means each one is a different performance.
  The fix: batch ~10 beats into a single dialogue request (one performance,
  cut back into per-beat clips on the returned segment boundaries) instead of
  one request per sentence.
- **Music that doesn't fight the narration.** Each video gets its own
  ElevenLabs-composed instrumental bed (from the script's own `music_prompt`),
  measured with `ffmpeg`'s `ebur128` loudness filter and ducked a fixed dB
  *below the narration's actual measured loudness* rather than a blind gain,
  since a freshly composed track's loudness varies run to run.
- **A resumable, idempotent CLI.** `pipeline.py` runs each stage
  (script -> images -> voice -> manifest -> music -> render) as a separate,
  file-based step under `output/<run>/`. Finished work is skipped on re-run,
  so a run interrupted an hour in resumes instead of restarting.

## Pipeline

```
prompts/manualprompt.txt  --(pasted into an LLM chat by hand)-->  script.json
                                        |
                                        v
                          pipeline.py init / adopt
                                        |
        +-------------------+----------+----------+-------------------+
        v                   v                     v                   v
  cmd_prompts          cmd_images             cmd_voice           (script data)
  scenes.txt      flow_runner/ (Playwright   ElevenLabs, batched
                   on Google Flow) -> PNGs    -> MP3 + duration
        |                   |                     |
        +-------------------+----------+----------+
                                        v
                                 cmd_manifest
                          pairs image+audio, measures
                          durations, adds outro card
                                        |
                                        v
                                  cmd_music
                    ElevenLabs Music, per-video, LUFS-ducked
                                        |
                                        v
                                  cmd_render
                    remotion/ (Ken Burns + crossfade) -> ffmpeg mix
                                        |
                                        v
                                  output/<run>/final.mp4
```

Every command is also runnable stage-by-stage (`python pipeline.py images`,
`... voice`, `... manifest`, etc.) with `--run <slug>` to target a specific
video, and `python pipeline.py check` reports what's done and what's missing
for the current run.

## Status

Two full videos have been produced end to end with this pipeline (`output/`,
gitignored - the pipeline writes real `.mp4` files there, they're just too
large to check in). Stage-by-stage:

| Stage | Module | Status |
|---|---|---|
| Script authoring | `prompts/manualprompt.txt` (manual, pasted into an LLM) | working |
| Images | `flow_runner/` (Playwright + Google Flow) | working, selectors are hand-inspected and will break when Google changes the DOM |
| Narration | `modules/voice_generator.py` (ElevenLabs) | working |
| Manifest / timing | `pipeline.py cmd_manifest` | working |
| Music | `modules/music_generator.py` (ElevenLabs Music) | working |
| Render | `modules/video_editor.py` + `remotion/` | working |
| Captions | `modules/transcriber.py` (Whisper word-alignment) | **not wired in** - the current composition deliberately ships with no burned-in captions ("the art carries the frame, the narration carries the meaning"); the word-timing code exists for a future karaoke-style caption pass |
| Character-consistency scoring | - | not built - no automatic re-roll of an off-model image yet |
| Cost tracking | - | not built - no per-run API call/cost logging yet |

## Tech stack

- **Python** - pipeline orchestration, all API integrations
- **Playwright** - browser automation for image generation (`flow_runner/`)
- **ElevenLabs API** - narration (`eleven_v3` dialogue, batched) and music generation
- **Remotion** (React + TypeScript) - final video composition and render
- **ffmpeg** - audio muxing, loudness measurement, speed adjustment
- **OpenAI Whisper** - word-level audio alignment (built, not yet wired into rendering)

## Project layout

```
pipeline.py            stage runner / CLI - the main entry point
config.py               every tunable constant (pacing, style prompt, models, dirs)
modules/
  image_generator.py    (legacy path) direct Gemini image calls - unused while flow_runner/ handles images
  voice_generator.py    ElevenLabs narration, batched for voice consistency
  music_generator.py    ElevenLabs Music, per-video bed
  video_editor.py        drives the Remotion render + ffmpeg music mix
  transcriber.py         Whisper word-alignment (not yet wired into render)
flow_runner/            Playwright automation of Google Flow's web UI
  runner.py              the automation itself
  config.py               every DOM selector, with the failure each one fixes
remotion/                the render project
  src/compositions/LectureVideo.tsx   Ken Burns + crossfade composition
  src/components/KenBurnsImage.tsx    pan/zoom logic
prompts/                the manual script-writing prompt + its explainer
assets/
  reference/              hand-drawn character/environment art, locked into every image call
  music/                   fallback music bed
  outro/                   cached subscribe/like outro clip (generated once, reused)
output/                  one folder per video run (gitignored, generated)
```

## Setup

Prerequisites: Python 3.11+, Node.js, `ffmpeg` on your `PATH`, and a Chrome/
Chromium install for Playwright.

```bash
pip install -r requirements.txt --break-system-packages
pip install -r flow_runner/requirements.txt --break-system-packages
playwright install chromium

cd remotion && npm install && cd ..

cp .env.example .env   # fill in ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID
```

Put your character/environment reference art in `assets/reference/` before
running - every generated image is locked to it.

## Usage

```bash
# 1. Fill in a topic in prompts/manualprompt.txt and paste the whole file
#    into an LLM chat (Claude, with web search on) to get back script JSON.
python pipeline.py init my-video-slug
# 2. Paste the returned JSON into output/my-video-slug/script.json.

# 3. Run every stage in order (a Chrome window opens for the image stage -
#    log in once, attach the reference image, then let it drive itself):
python pipeline.py --run my-video-slug

# Or run one stage at a time:
python pipeline.py prompts   --run my-video-slug   # script.json -> scenes.txt
python pipeline.py images    --run my-video-slug   # Flow -> images/
python pipeline.py voice     --run my-video-slug   # ElevenLabs -> audio/
python pipeline.py manifest  --run my-video-slug    # pair everything + durations
python pipeline.py music     --run my-video-slug    # compose this video's bed
python pipeline.py render    --run my-video-slug    # Remotion -> final.mp4

python pipeline.py check     --run my-video-slug    # what's done, what's missing
python pipeline.py demo      --run my-video-slug    # fake a full run, no API calls
```

`--run` defaults to the most recently touched run, so it can usually be
dropped after the first command of a session.

## Known limitations

- Image generation depends on Google Flow's current web UI. Every selector in
  `flow_runner/config.py` is documented with the exact failure it was written
  to fix; when Google reshuffles the DOM, that's the only file that needs
  updating.
- No burned-in captions yet (see Status table above).
- No automatic retry when a generated image drifts off-model from the
  reference character.
- No per-run cost/usage logging.

## License

MIT - see [LICENSE](LICENSE).
