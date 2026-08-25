# Animationer

An automated pipeline that turns a single topic into a finished, narrated
explainer video, no manual editing. Built to run a YouTube channel end to end:
one script in, one `.mp4` out. Output is landscape 1920x1080 at 30fps, aimed at
a roughly three minute runtime, not vertical short-form.

A script of ~30-100 short beats (narration sentence + image description) goes
in. Each beat becomes one AI-generated still, one narrated audio clip timed to
the narration, and one entry in a final Remotion render with Ken Burns
pan/zoom, cuts and dissolves, and a music bed mixed under the voice.

## Demo

[Why do SOME people believe that the moon landing was fake](https://www.youtube.com/watch?v=702-w9Sanws)

A finished video: written as beats, then generated, narrated and rendered end to
end by this pipeline.

## Why this exists

This is a personal side project to automate a YouTube channel without paying
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
  The fix: batch many beats into a single dialogue request (one performance,
  cut back into per-beat clips on the returned segment boundaries) instead of
  one request per sentence. Batches are budgeted in *characters* against the
  API's documented ceiling rather than in beats, because beat length is
  bimodal (see pacing below) and a beat count was only ever a proxy for the
  limit that actually applies.
- **Not trusting the API's own timestamps.** Cutting a batch on the segment
  boundaries `eleven_v3` reports sounds fine at ~19 words a beat and falls
  apart at 4-8, where the model runs sentences together. Measured on one
  55-beat run: ten beats were severed mid-word, three of them *louder* at the
  cut than their own average volume. No arithmetic on those numbers fixes
  them, so the reported timings were demoted to choosing *which* pause to cut
  on, and `ffmpeg`'s `silencedetect` decides where the cut actually lands.
  A second pass then measures each finished clip's first and last 80ms
  against its own average loudness and flags any that still start or end at
  full speaking volume, with the exact command to re-run just those beats.
- **Music that doesn't fight the narration.** Each video gets its own
  ElevenLabs-composed instrumental bed (from the script's own `music_prompt`),
  measured with `ffmpeg`'s `ebur128` loudness filter and ducked a fixed dB
  *below the narration's actual measured loudness* rather than a blind gain,
  since a freshly composed track's loudness varies run to run.
- **Pacing derived from measurement, not taste.** The words-per-minute figure
  the length estimator uses (177) was measured over 231 shipped beats across
  five finished videos: 4207 spoken words against 1425s of tightly-trimmed
  narration. Beats run on a two-tier rhythm (short ~35 characters, long ~85)
  rather than a uniform length, and boundaries follow the story: beats inside
  one location hard cut, and a change of location dissolves. `pipeline.py`
  estimates a script's finished runtime from its word count and warns when it
  lands outside the target, so a badly-sized script gets caught *before* any
  money is spent generating images or audio for it.
- **A resumable, idempotent CLI.** `pipeline.py` runs each stage
  (script -> images -> voice -> manifest -> music -> render) as a separate,
  file-based step under `output/<run>/`. Finished work is skipped on re-run,
  so a run interrupted an hour in resumes instead of restarting.

## Pipeline

```
prompts/pass1_narration.txt --(LLM, by hand)--> the beats
prompts/pass2_visuals.txt   --(LLM, by hand)--> + image prompts  =  script.json
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
                 remotion/ (Ken Burns + cut/dissolve) -> ffmpeg mix
                                        |
                                        v
                                  output/<run>/final.mp4
```

Every command is also runnable stage-by-stage (`python pipeline.py images`,
`... voice`, `... manifest`, etc.) with `--run <slug>` to target a specific
video, and `python pipeline.py check` reports what's done and what's missing
for the current run.

## Status

Five full videos have been produced end to end with this pipeline, 231 beats
of finished narration in total (`output/`, gitignored - the pipeline writes
real `.mp4` files there, they're just too large to check in). Stage-by-stage:

| Stage | Module | Status |
|---|---|---|
| Script authoring | `prompts/` two-pass template (manual, pasted into an LLM) | working |
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
- **ffmpeg** - audio muxing, silence detection, loudness measurement, speed adjustment
- **OpenAI Whisper** - word-level audio alignment (built, optional dependency,
  not yet wired into rendering)

## Project layout

```
pipeline.py            stage runner / CLI - the main entry point
config.py               every tunable constant (pacing, style prompt, models, dirs)
modules/
  voice_generator.py    ElevenLabs narration, batched for voice consistency
  music_generator.py    ElevenLabs Music, per-video bed
  video_editor.py        drives the Remotion render + ffmpeg music mix
  transcriber.py         Whisper word-alignment (not yet wired into render)
flow_runner/            Playwright automation of Google Flow's web UI
  runner.py              the automation itself
  config.py               every DOM selector, with the failure each one fixes
  test_runner.py         offline tests for the non-browser logic
remotion/                the render project
  src/compositions/LectureVideo.tsx   Ken Burns + cut/dissolve composition
  src/components/KenBurnsImage.tsx    pan/zoom logic
prompts/                the two prompts pasted into an LLM to author a script
  pass1_narration.txt    pass 1: topic and beat count in, narration beats out
  pass2_visuals.txt      pass 2: those beats in, image and music prompts added
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
python3 -m venv .venv && source .venv/bin/activate

pip install -r requirements.txt
pip install -r flow_runner/requirements.txt
playwright install chromium

cd remotion && npm install && cd ..

cp .env.example .env   # fill in the values below
```

Fill in `.env`:

- `ELEVENLABS_API_KEY` - your ElevenLabs key. The only one actually required.
- `ELEVENLABS_VOICES` - comma-separated `name:voice_id` pairs from your
  ElevenLabs account (e.g. `narrator:abc123,sidekick:def456`), and
  `ELEVENLABS_DEFAULT_VOICE` - which of those names to use by default.
- `GOOGLE_FLOW_PROJECT_URL` - the URL of your own project on
  [labs.google/fx/tools/flow](https://labs.google/fx/tools/flow) (create one,
  then copy the URL from the address bar).

Put your character/environment reference art in `assets/reference/` before
running - every generated image is locked to it.

### Trying it without any API keys

`python pipeline.py demo --run demo-1` fabricates a whole run locally:
numbered placeholder images and silent audio sized per beat from its own word
count, driven through the real manifest and Remotion render. It makes no API
calls and needs no keys, so it exercises the timing and composition code end
to end on a fresh clone.

### Tests

```bash
cd flow_runner && python3 test_runner.py
```

Offline checks for the logic that does not need a browser: scene numbering,
resume-after-interrupt, the pacing floors that stop the automation from being
sped up into looking like a bot, rejection-vs-quota message classification, and
`--only` range parsing. Everything Playwright-driven still has to be verified
against a live session by hand.

## Usage

```bash
# 1. Put your topic and beat count in prompts/pass1_narration.txt and paste it
#    into an LLM chat (Claude, with web search on). Out comes the narration.
# 2. Paste that result under "SCRIPT:" in prompts/pass2_visuals.txt and send
#    that. Out comes the same JSON with image prompts and a music prompt added.
python pipeline.py init my-video-slug
# 3. Save the final JSON as output/my-video-slug/script.json.

# 4. Run every stage in order (a Chrome window opens for the image stage -
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
  reference character. Over ~100 generations in one video the drift is visible
  by the end, and catching it currently means watching the render.
- No per-run cost/usage logging, so per-video API spend isn't visible before
  scaling up how many videos get made.
- Scripts are written by pasting a template into an LLM chat by hand rather
  than through an API call. That's deliberate for now: it keeps a human
  judging fact quality and comic timing before any money is spent generating
  images and audio for a bad script.

## License

MIT - see [LICENSE](LICENSE).
