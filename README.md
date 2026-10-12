# Animationer

An automated pipeline that turns a single topic into a finished, narrated
explainer video, no manual editing. Built to run a YouTube channel end to end:
one script in, one `.mp4` out. Output is landscape 1920x1080 at 30fps, aimed at
a roughly three minute runtime, not vertical short-form.

A script of ~30-100 short beats (narration sentence + image description) goes
in. Each beat becomes one narrated audio clip and one or more AI-generated
stills sharing its time, rendered by Remotion with static frames, cuts and
dissolves, and a music bed mixed under the voice.

The stills are **chained**: each location opens with one picture drawn fresh
against the character reference, and every later picture in it is an *edit*
of the one before (the character raises a hand, a sign appears, an object
moves). Cut together at about one picture a second, that reads as animation
rather than a slideshow. In `script.json` a beat carries `image_prompt` /
`image_prompt_alt` when it draws fresh, otherwise an `edits` list with one
change. One picture per beat, so the narration's mix of short (3-5 words),
medium (6-8) and long (9-12) beats sets how long each picture stays up,
~2.4s on average. (An edit may also be `{"at": "six meters", "edit": "..."}`
to put several pictures in one beat, each timed to its word with Whisper.)
Each edit is made in Flow from its parent picture, so a failed frame is
retried once and then the whole run stops, since every later edit in the
chain would have nothing to edit. A fresh drawing in the middle of a location
dissolves in instead of jumping, and after the image stage every edit is compared with the frame it was made from,
so ignored edits (two identical frames) are listed with the command to redo
them. Older scripts with an `image_prompt` on every beat and no edits still
work unchanged.

## Demo

[FORMULA 1 EXPLAINED IN 3 MINUTES](https://youtu.be/F0FqhHIv47I?si=Fp-PyimVVTTh87Xz)

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
  ladder (Nano Banana Pro -> 2.1 -> 2 Lite) rather than stalling the whole run.
- **Non-deterministic TTS drift.** ElevenLabs' `eleven_v4` model isn't
  deterministic and can't be told what a previous call sounded like, so
  generating each beat separately means each one is a different performance.
  The fix: batch many beats into a single dialogue request (one performance,
  cut back into per-beat clips on the returned segment boundaries) instead of
  one request per sentence. Batches are budgeted in *characters* against the
  API's documented ceiling rather than in beats, because beat length is
  bimodal (see pacing below) and a beat count was only ever a proxy for the
  limit that actually applies.
- **Not trusting the API's own timestamps.** Cutting a batch on the segment
  boundaries `eleven_v4` reports sounds fine at ~19 words a beat and falls
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
  frames.json     flow_runner/ (Playwright   ElevenLabs, batched
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
                 remotion/ (still + cut/dissolve) -> ffmpeg mix
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
| Frame timing | `modules/transcriber.py` (Whisper word-alignment) | working - an edit with an `at` word changes picture as that word is spoken, cached per run in `word_times.json` |
| Edit check | `pipeline.py _report_changes` | working - after images, lists edits the model ignored (frame identical to its parent) with the command to redo them |
| Captions | - | not built, on purpose: no burned-in captions ("the art carries the frame, the narration carries the meaning"). The word timings above could feed a karaoke-style pass later |
| Character-consistency scoring | - | not built - no automatic re-roll of an off-model image yet |
| Cost tracking | - | not built - no per-run API call/cost logging yet |

## Tech stack

- **Python** - pipeline orchestration, all API integrations
- **Playwright** - browser automation for image generation (`flow_runner/`)
- **ElevenLabs API** - narration (`eleven_v4` dialogue, batched) and music generation
- **Remotion** (React + TypeScript) - final video composition and render
- **ffmpeg** - audio muxing, silence detection, loudness measurement, speed adjustment
- **OpenAI Whisper** - word-level alignment, used to time a picture change to
  the word it names
- **Pillow** - pixel diff between each edit and its parent (the edit check)

## Project layout

```
pipeline.py            stage runner / CLI - the main entry point
config.py               every tunable constant (pacing, style prompt, models, dirs)
modules/
  voice_generator.py    ElevenLabs narration, batched for voice consistency
  music_generator.py    ElevenLabs Music, per-video bed
  video_editor.py        drives the Remotion render + ffmpeg music mix
  transcriber.py         Whisper word-alignment, times picture changes to words
flow_runner/            Playwright automation of Google Flow's web UI
  runner.py              the automation itself
  config.py               every DOM selector, with the failure each one fixes
  test_runner.py         offline tests for the non-browser logic
remotion/                the render project
  src/compositions/LectureVideo.tsx   still frames + cut/dissolve composition
  src/components/StillImage.tsx      one static frame, no camera move
prompts/                the two prompts pasted into an LLM to author a script
  pass1_narration.txt    pass 1: topic and beat count in, narration beats out
  pass2_visuals.txt      pass 2: those beats in, image and music prompts added
assets/
  reference/              hand-drawn character/environment art, locked into every image call
  music/                   fallback bed for scripts with no music_prompt (empty by default)
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
pip install openai-whisper pillow   # see below

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

`openai-whisper` is only needed when a script's edits name an `at` word (it
times the picture change), and it pulls in torch, a multi-GB download, so it
stays commented out in `requirements.txt`. Pillow is used by the edit check
after the image stage.

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
resume-after-interrupt, which chained frames need redoing (`frames_to_make`),
the pacing floors that stop the automation from being sped up into looking
like a bot, rejection-vs-quota message classification, and
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
#    (Or paste it into NEW_SCRIPT at the top of pipeline.py and run
#    `python pipeline.py` with no arguments: it makes the run folder itself.)

# 4. Run every stage in order (a Chrome window opens for the image stage -
#    log in once, attach the reference image, then let it drive itself):
python pipeline.py --run my-video-slug

# Or run one stage at a time:
python pipeline.py prompts   --run my-video-slug   # script.json -> frames.json
python pipeline.py images    --run my-video-slug   # Flow -> images/
python pipeline.py images    --run my-video-slug --only 12,14.2
                                     # redo beat 12 and frame 2 of beat 14
                                     # (later edits in the same chain too)
python pipeline.py voice     --run my-video-slug   # ElevenLabs -> audio/
python pipeline.py manifest  --run my-video-slug    # pair everything + durations
python pipeline.py music     --run my-video-slug    # compose this video's bed
python pipeline.py render    --run my-video-slug    # Remotion -> final.mp4

python pipeline.py check     --run my-video-slug    # what's done, what's missing, ignored edits
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
